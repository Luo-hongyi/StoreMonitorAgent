# StoreMonitorAgent

## Overview
Store monitoring multi-agent system with database-backed tools and a minimal one-command demo.

## Quickstart (one command)

1) Install deps

```
pip install -r requirements.txt
```

2) Run the demo (uses mock DB by default)

```
python demo.py
```

You should see a ServiceResponse-style JSON string for passenger flow distribution. To run against a real DB, configure env vars below and unset `USE_MOCK_DB`.

## Configuration

Environment variables:
- `USE_MOCK_DB` (default: on for `demo.py` if unset): set to `1` to use in-memory mock DB
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: required when `USE_MOCK_DB` is not set to `1`

Fail-fast: if any required DB env var is missing, startup fails with a clear error.

## Project Structure

- `app.py`: Interactive multi-agent loop (now English prompts). Requires Agentscope model config at `configs/model_configs.json`.
- `agents/`: Chat and Query agent implementations.
- `tools/`: Database-backed tool functions returning structured JSON strings.
- `parsers/`: Helpers to extract tool results and merge into chat responses.
- `test_data/`: Sample SQL schemas/data (comments translated to English).
- `runs/`: Ignored. Local run artifacts/logs (not tracked).

## Notes

- Agentscope model config file is at `configs/model_configs.json`. Provide your own API keys via your environment or Agentscope’s mechanisms.
- Demo prints a serialized ServiceResponse string from tools to show end-to-end flow.

## Demo Run

This demo illustrates an end-to-end interaction investigating correlation between leave-post records and intrusion events (adapted to English prompts and current JSON keys).

---

**ChatAssistant**: Hello, I am your smart store assistant. How can I help today?

**User**: Investigate correlation between leave-post records and intrusion events

**ChatAssistant**: Plan.

**Planner**:
1. Query today's leave-post records for a specific time range (default: today)
2. Query today's intrusion events for a specific time range (default: today)
3. Analyze [leave_records_id] and [intrusion_events_id] correlation (time and space)

**QueryAgent**: ITER 1, thinking...

**System**: Respond a JSON dictionary in a markdown's fenced code block as follows:

```
{"thought": "your reasoning", "function": [{"name": "function_name", "arguments": {"arg1": "value1", "arg2": "value2"}}]}
```

**QueryAgent**: 
```
{"thought": "First, query today's leave-post records (full day).", "function": [{"name": "LeaveRecordsQuery", "arguments": {"start_time": "2024-05-27 00:00:00", "end_time": "2024-05-27 23:59:59"}}]}
```

**QueryAgent**: ITER 1, calling tools...

**System**: Executed functions successfully: 
```
[{'name': 'LeaveRecordsQuery', 'arguments': {'start_time': '2024-05-27 00:00:00', 'end_time': '2024-05-27 23:59:59'}}]
```

**QueryAgent**: ITER 2, thinking...

**System**: Respond a JSON dictionary in a markdown's fenced code block as follows:
```
{"thought": "your reasoning", "function": [{"name": "function_name", "arguments": {"arg1": "value1", "arg2": "value2"}}]}
```

**QueryAgent**:
```
{"thought": "Now query today's intrusion events (full day).", "function": [{"name": "InvaseAlarmEventsQuery", "arguments": {"start_time": "2024-05-27 00:00:00", "end_time": "2024-05-27 23:59:59"}}]}
```

**QueryAgent**: ITER 2, calling tools...

**System**: Executed functions successfully: 
```
[{'name': 'InvaseAlarmEventsQuery', 'arguments': {'start_time': '2024-05-27 00:00:00', 'end_time': '2024-05-27 23:59:59'}}]
```

**QueryAgent**: ITER 3, thinking...

**System**: Respond a JSON dictionary in a markdown's fenced code block as follows:
```
{"thought": "your reasoning", "function": [{"name": "function_name", "arguments": {"arg1": "value1", "arg2": "value2"}}]}
```

**QueryAgent**:
```
{"thought": "Tools don't support correlation analysis directly; stop here per instructions.", "function": []}
```

**QueryAgent**: Query results:

1. Execute function LeaveRecordsQuery

   - ARGUMENTS:
       start_time: 2024-05-27 00:00:00
       end_time: 2024-05-27 23:59:59
   - STATUS: SUCCESS
   - RESULT:
```
{"query_id": "f71ec3e7", "query_type": "leave_post_records", "total_records": 10, "leave_post_records": [{"time_slot_start": "080000", "time_slot_end": "082000", "interval_time": "20"}, {"time_slot_start": "090000", "time_slot_end": "091500", "interval_time": "15"}, {"time_slot_start": "103000", "time_slot_end": "105000", "interval_time": "20"}, {"time_slot_start": "114500", "time_slot_end": "120500", "interval_time": "20"}, {"time_slot_start": "130000", "time_slot_end": "132500", "interval_time": "25"}, {"time_slot_start": "143000", "time_slot_end": "145000", "interval_time": "20"}, {"time_slot_start": "154500", "time_slot_end": "161500", "interval_time": "30"}, {"time_slot_start": "170000", "time_slot_end": "172000", "interval_time": "20"}, {"time_slot_start": "183000", "time_slot_end": "184500", "interval_time": "15"}, {"time_slot_start": "194500", "time_slot_end": "201500", "interval_time": "30"}]}
```

1. Execute function InvaseAlarmEventsQuery

   - ARGUMENTS:
       start_time: 2024-05-27 00:00:00
       end_time: 2024-05-27 23:59:59
   - STATUS: SUCCESS
   - RESULT:
```
{"query_id": "8efd3b0e", "query_type": "intrusion_events_in_time_range", "total_events": 16, "events": [{"alarm_time": "2024-05-27 11:07:31", "id": 66406}, {"alarm_time": "2024-05-27 11:13:50", "id": 66414}, {"alarm_time": "2024-05-27 11:25:39", "id": 66428}, {"alarm_time": "2024-05-27 11:30:31", "id": 66429}, {"alarm_time": "2024-05-27 11:38:50", "id": 66432}, {"alarm_time": "2024-05-27 11:42:36", "id": 66434}, {"alarm_time": "2024-05-27 12:26:24", "id": 66440}, {"alarm_time": "2024-05-27 12:37:13", "id": 66442}, {"alarm_time": "2024-05-27 13:12:02", "id": 66447}, {"alarm_time": "2024-05-27 14:03:16", "id": 66449}, {"alarm_time": "2024-05-27 15:37:20", "id": 66450}, {"alarm_time": "2024-05-27 15:39:20", "id": 66464}, {"alarm_time": "2024-05-27 15:41:57", "id": 66474}, {"alarm_time": "2024-05-27 15:44:00", "id": 66489}, {"alarm_time": "2024-05-27 15:46:44", "id": 66493}, {"alarm_time": "2024-05-27 15:54:14", "id": 66503}]}
```

**Summarizer**: Leave-post records [`f71ec3e7`]: 10 occurrences, concentrated around noon and evening; max duration 30 minutes. Intrusion events overview [`8efd3b0e`]: 16 events, mainly between 11:00 and 15:40 with several consecutive incidents.

**Preliminary analysis**: time overlap exists between leave periods and some intrusion events (notably 11:00–12:00 and after 15:00). Recommend reviewing footage for those periods to confirm correlation.

---