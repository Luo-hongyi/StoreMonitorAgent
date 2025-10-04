import agentscope
from agentscope.agents import UserAgent
from agents.QueryAgent import QueryAgent
from agents.ChatAgent import ChatAgent

from tools.InvaseAlarmEventsQuery import InvaseAlarmEventsQuery
from tools.FlowQuery import FlowQuery
from tools.FlowDistributeQuery import FlowDistribution
from tools.LeaveRecordsQuery import LeaveRecordsQuery
from tools.MultiInvaseAlarmIndexQuery import MultiInvaseAlarmPictureQuery
from tools.InvaseAlarmIndexQuery import InvaseAlarmPictureQuery

from agentscope.service import ServiceToolkit
from agentscope.message import Msg
from connection import db
from loguru import logger

db.connect()

agentscope.init(model_configs='configs/model_configs.json')

service_toolkit = ServiceToolkit()
service_toolkit.add(FlowQuery)
service_toolkit.add(FlowDistribution)

service_toolkit.add(LeaveRecordsQuery)

service_toolkit.add(MultiInvaseAlarmPictureQuery)
service_toolkit.add(InvaseAlarmPictureQuery)
service_toolkit.add(InvaseAlarmEventsQuery)

dialog_prompt = '''
You are a multimodal smart store assistant. Follow these rules:

0) Scope:
If a user asks for non-store-monitoring topics, do not call the planner; answer directly using common sense.

Data you can access:
1. Passenger flow
2. Intrusion events
3. Intrusion event images
4. Employee leave-post records

When the above can address the user's needs, follow:
1) Memory check: If you already have enough information in memory, answer directly. If memory is empty or insufficient, reply only with: "Plan." to trigger planning. When a user asks for images, reply "Plan." to fetch via planner + query agent.
2) Response rules: Never fabricate; if insufficient info, reply only: "Plan." Do not imitate other agents' answers.
3) Presentation: The user cannot see raw reports/internal data. Provide clear, structured, readable answers. Use lists/tables if helpful. To insert specific query results, place "[xxxxx]" where xxxxx is the query_id from results.
4) Trigger: Replying "Plan." triggers the planner and query agent. You should use placeholders like [query_id] to show results where appropriate.
5) Confidentiality: Be professional and friendly. Ensure accuracy and clarity.
'''

plan_prompt = '''
Role: Planner for a multimodal video monitoring system

Main tasks:
1) Infer user needs from the Chat Assistant conversation
2) Turn needs into concrete monitoring queries (keep simple; split into smaller queries)
3) Do not ask follow-up questions; just produce a plan
4) In an appendix, list prior query results required by this plan, using placeholders like [query_id]

Principles:
1) Summarize user needs first
2) Only include monitoring-related queries within system capability
3) Default to today's records unless specified

Available query types:
1) Passenger flow statistics across time ranges
2) Passenger flow distribution within a single time range
3) Intrusion events in a time range
4) Intrusion event images by event_id
5) Multiple intrusion event images by a set of event_ids
6) Leave-post records in a time range

Output format:
1) Use a numbered list to present the query plan
2) Each query must state the query type
3) In the appendix, include needed prior query results as [query_id]

Cautions:
1) Stay strictly in scope
2) Keep the plan concise; only query what is needed
'''

react_prompt = '''
You are the Query Agent of the monitoring system.
Your task is to query the database according to the planner's plan and return results.
Notes:
1) Return raw results (no summary)
2) Your reply must only contain the full results returned by the tools
3) The query date is fixed to 2024-05-27
'''

summarize_prompt = '''
You are the Summarizer of the monitoring system.
Summarize the query results concisely and present them clearly:
1) Provide a brief summary for each query result (<= 20 words)
2) Provide initial analysis
3) Insert the corresponding [query_id] placeholder for each result
4) Repeat for each query result

Notes:
1) If no valid data is received, report an error
2) The reply should be well-structured
'''

planAgent = ChatAgent(name="Planner", model_config_name="qwen", sys_prompt=plan_prompt)
userAgent = UserAgent(name="User")
reactAgent = QueryAgent(name="QueryAgent", model_config_name="qwen_zero_temp", verbose=True, service_toolkit=service_toolkit, sys_prompt="", max_iters=10)
summarizeAgent = ChatAgent(name="Summarizer", model_config_name="qwen", sys_prompt=summarize_prompt)
dialogAgent = ChatAgent(name="ChatAssistant", model_config_name="qwen", sys_prompt=dialog_prompt)

msg = None  # Agent message
query_result = Msg(name="QueryAgent", content='', role='assistant')  # last query result
summarize = Msg(name="Summarizer", content='', role='assistant')  # last summary
dialog = []  # dialogue history for planner and summarizer
#query_prompt = reactAgent.memory.get_memory()

dialogAgent.speak('Hello, I am your smart store assistant. How can I help today?')

while True:
    dialog.clear()  # reduce token usage
    dialog_itr = 0  # feed query result in first round
    dialogAgent = ChatAgent(name="ChatAssistant", model_config_name="qwen", sys_prompt=dialog_prompt)

    while msg is None or not msg.content.endswith("Plan."):
        msg = userAgent(msg)
        if msg.content == 'exit':
            break
        dialog.append(msg)
        if dialog_itr == 0:
            msg = dialogAgent([query_result, summarize, msg], query_result)
            dialog_itr += 1
        else:
            msg = dialogAgent(msg, query_result)

        dialog.append(msg)
    
    if msg.content == 'exit':
            logger.info('Conversation ended by user')
            break
    
    # Remove last turn ("Plan.") from dialog history to avoid planner confusion
    dialog.remove(msg)
    plan_input = []
    plan_input.append(query_result)
    plan_input.extend(dialog)

    msg = planAgent(plan_input, query_result)

    msg = reactAgent(msg)

    query_result = msg
    # Recreate query agent to reduce context length if needed
    reactAgent = QueryAgent(name="QueryAgent", model_config_name="qwen_zero_temp", verbose=True, service_toolkit=service_toolkit, sys_prompt="", max_iters=10)

    summarize_input = []
    summarize_input.extend(dialog)
    #summarize_input.append(summarize)
    summarize_input.append(msg)
    msg = summarizeAgent(summarize_input, query_result)
    #summarizeAgent.memory.clear()  # clear summarizer memory if needed
    summarizeAgent = ChatAgent(name="Summarizer", model_config_name="qwen", sys_prompt=summarize_prompt)
    summarize = msg



