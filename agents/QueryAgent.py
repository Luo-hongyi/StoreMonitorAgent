
from typing import Any, Optional, Union, Sequence

from loguru import logger


from agentscope.exception import ResponseParsingError, FunctionCallError
from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.parsers import MarkdownJsonDictParser
from agentscope.service import ServiceToolkit
from agentscope.service.service_toolkit import ServiceFunction




import json

INSTRUCTION_PROMPT = """## What You Should Do:
1. First, analyze the current situation, and determine your goal.
2. Then, check if your goal is already achieved. If so, try to generate a response. Otherwise, think about how to achieve it with the help of provided tool functions. Only use the tool provided, do not make up tools.
3. Respond in the required format.

## Note:
1. Fully understand the tool functions and their arguments before using them.
2. You should decide if you need to use the tool functions, if not then return an empty list in "function" field.
3. Make sure the types and values of the arguments you provided to the tool functions are correct.
4. Do not make assumptions. If needed, use tools to query information.
5. If the function execution fails, analyze the error and try to solve it.
6. Do not invent functions. If the provided function cannot meet your needs, say so.
"""

QUERY_PROMPT = """
You are the Query Agent of a multi-agent monitoring system.
Your task is to read the provided plan and return a JSON response to call the given tools.

Tasks:
1. Assess what you already know and what you need; determine your goal.
2. If the goal is already achieved, put "Done" in the "thought" field and an empty array [] in the "function" field.
3. If not, decide how to use the provided tools. Put your reasoning in "thought" and fill "function" with the tool call(s).
4. Only perform required queries; do not execute beyond the plan.

Notes:
1. Understand tool functions, their arguments, and return values before use.
2. Provide correct argument types and values.
3. Assume today is 2024-05-27 23:59:59 unless specified; default to today when time is not declared.
4. On failures, analyze the error and try to fix.
5. Do not invent functions.
6. Prefer solving in as few iterations as possible; combine independent calls when possible.
7. When one tool depends on another's output, call them sequentially across iterations.
8. Response must be a JSON object. Ensure "function" is an array and "arguments" is a JSON object (not a string).
"""

FUN_FORMAT = """
  "thought": "Your brief thought (<=10 chars)",
  "function": [
    {
      "name": "function_name",
      "arguments": {"arg1": "value1", "arg2": "value2"}
    }
  ]
"""


class QueryAgent(AgentBase):

    def __init__(
        self,
        name: str,
        model_config_name: str,
        service_toolkit: ServiceToolkit = None,
        sys_prompt: str = "You're a helpful assistant. Your name is {name}.",
        max_iters: int = 10,
        verbose: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize the ReAct agent with the given name, model config name
        and tools.

        Args:
            name (`str`):
                The name of the agent.
            sys_prompt (`str`):
                The system prompt of the agent.
            model_config_name (`str`):
                The name of the model config, which is used to load model from
                configuration.
            service_toolkit (`ServiceToolkit`):
                A `ServiceToolkit` object that contains the tool functions.
            max_iters (`int`, defaults to `10`):
                The maximum number of iterations of the reasoning-acting loops.
            verbose (`bool`, defaults to `True`):
                Whether to print the detailed information during reasoning and
                acting steps. If `False`, only the content in speak field will
                be print out.
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
        )

        self.service_toolkit = service_toolkit
        self.verbose = verbose
        self.max_iters = max_iters

        # Write system prompt
        if not sys_prompt.endswith("\n"):
            sys_prompt = sys_prompt + "\n"

        self.sys_prompt = "\n".join(
            [
                # agent name
                sys_prompt.format(name=self.name),
                # tool instructions
                self.service_toolkit.tools_instruction,
                # run guidance
                QUERY_PROMPT,
            ],
        )

        # Save system prompt to memory
        self.memory.add(Msg("system", self.sys_prompt, role="system"))

        # Initialize parser
        self.parser = MarkdownJsonDictParser(
            content_hint={
                "thought": "your reasoning",
                "function": [
                    {
                    "name": "function_name",
                    "arguments": {
                        "arg1": "value1",
                        "arg2": "value2"
                    }
                    }   
                ]
            },
            required_keys=["thought", "function"],
            # Only print the speak field when verbose is False
            keys_to_content=True if self.verbose else "thought",
        )



    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """The reply function that achieves the ReAct algorithm.
        The more details please refer to https://arxiv.org/abs/2210.03629"""


        self.memory.add(x)  # record input

        query_results = ""

        for _ in range(self.max_iters):
            # Step 1: Think
            if self.verbose:
                self.speak(f" ITER {_+1}, thinking... ".center(70, "#"))

            # Prepare a hint message to constrain model output
            hint_msg = Msg(
                "system",
                self.parser.format_instruction,
                role="system",
                echo=self.verbose,
            )

            # Prepare prompt
            prompt = self.model.format(self.memory.get_memory(), hint_msg)
            
            # Generate current step and parse
            try:
                res = self.model(
                    prompt,
                    parse_func=self.parser.parse,
                    max_retries=1,
                )


                # Remember the chosen function call
                self.memory.add(
                    Msg(
                        name=self.name,
                        content="Prepared to execute functions: " + str(res.parsed["function"]) + ".",
                        role="assistant",
                    ),
                )

                # Show information
                msg_returned = Msg(
                    self.name,
                    self.parser.to_content(res.parsed),
                    "assistant",
                )
                self.speak(msg_returned)

                # If the function field is empty, we are done
                arg_function = res.parsed["function"]
                if (
                    isinstance(arg_function, str)
                    and arg_function in ["[]", ""]
                    or isinstance(arg_function, list)
                    and len(arg_function) == 0
                ):
                    # Only the speak field is exposed to users or other agents
                    self.speak("Query results:" + query_results)
                    #self.memory.clear()
                    return Msg(self.name, query_results, "assistant")

            # Error handling and recording
            except ResponseParsingError as e:
                # Print out raw response from models for developers to debug
                response_msg = Msg(self.name, e.raw_response, "assistant")
                self.speak(response_msg)

                # Re-correct by model itself
                error_msg = Msg("system", str(e), "system")
                self.speak(error_msg)

                # Remember error
                self.memory.add([response_msg, error_msg])

                # Skip execution and think again
                continue
            
            # Step 2: Act
            if self.verbose:
                self.speak(f" ITER {_+1}, calling tools... ".center(70, "#"))

            # Parse the "function" field and call tools accordingly
            try:
                execute_results = self.service_toolkit.parse_and_call_func(
                    json.dumps(res.parsed["function"]),
                )

                # Note: Observing the execution results and generate response
                # are finished in the next reasoning step. We just put the
                # execution results into memory, and wait for the next loop
                # to generate response.

                # Record execution results into memory as system message

                # Inform success
                msg_res = Msg("system", "Executed functions successfully: " + str(res.parsed["function"]) + ".", "system")
                self.speak(msg_res)
                self.memory.add(msg_res)

                query_results += execute_results

                # Record execution results
                self.memory.add(Msg("system", "Obtained results:" + execute_results, "system"))


            except FunctionCallError as e:
                # Error during tool call
                error_msg = Msg("system", str(e), "system")
                self.speak(error_msg)
                self.memory.add(error_msg)


        # Outside the loop: if no reply generated within max iterations, return
        #hint_msg = Msg(
        #    "system",
        #    "You have failed to generate a response in the maximum "
        #    "iterations. Now generate a reply by summarizing the current "
        #    "situation.",
        #    role="system",
        #    echo=self.verbose,
        #)

        # Generate a reply by summarizing the current situation
        #prompt = self.model.format(self.memory.get_memory(), hint_msg)
        #res = self.model(prompt)
        
        # Return current results
        res_msg = Msg(self.name, query_results, "assistant")
        self.speak(res_msg)
        #self.memory.clear()
        return res_msg
