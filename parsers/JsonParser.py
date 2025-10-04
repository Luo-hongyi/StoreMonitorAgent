import json
import re
from datetime import datetime, timedelta


def parse_json(json_data, input_string):
    data_list = json_data
    reports = {}
    if json_data == "":
        return input_string
    for data in data_list:
        query_id = data.get("query_id")
        query_type = data.get("query_type")

        if query_type == "leave_post_records":
            report = process_leave_post_records(data)
        elif query_type == "multiple_intrusion_event_images":
            report = process_multiple_intrusion_events(data)
        elif query_type == "intrusion_event_images_by_id":
            report = process_specific_intrusion_event(data)
        elif query_type == "intrusion_events_in_time_range":
            report = process_time_range_intrusion_records(data)
        elif query_type == "passenger_flow_statistics":
            report = process_passenger_flow_statistics(data)
        elif query_type == "passenger_flow_distribution":
            report = process_passenger_flow_distribution(data)
        else:
            report = f"Unknown query type: {query_type}"

        reports[query_id] = report

    def replace_query_id(match):
        mid = match.group(1)
        return reports.get(mid, f"[Query ID not found: {mid}]")

    result = re.sub(r"\[([a-zA-Z0-9-]+)\]", replace_query_id, input_string)
    return result


def format_time(time_str):
    return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"


def format_duration(duration):
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours} hours {minutes} minutes {seconds} seconds"


def process_leave_post_records(data):
    query_id = data["query_id"]
    total_records = data["total_records"]
    records = data["leave_post_records"]

    report = f"Query ID: {query_id} (leave-post records)\n"
    report += f"Total records: {total_records}\n"
    report += "Details:\n"

    for index, record in enumerate(records, 1):
        start_time = format_time(record["time_slot_start"])
        end_time = format_time(record["time_slot_end"])

        start_datetime = datetime.strptime(start_time, "%H:%M:%S")
        end_datetime = datetime.strptime(end_time, "%H:%M:%S")
        interval = end_datetime - start_datetime
        if interval < timedelta(0):
            interval += timedelta(hours=24)

        formatted_interval = format_duration(interval)

        report += f"  Record {index}:\n"
        report += f"    Start: {start_time}\n"
        report += f"    End: {end_time}\n"
        report += f"    Duration: {formatted_interval}\n\n"

    return report


def process_multiple_intrusion_events(data):
    query_id = data["query_id"]
    events = data["events"]

    report = f"Query ID: {query_id} (multiple intrusion event images)\n"
    report += f"Total events: {len(events)}\n"
    report += "Details:\n"

    for index, event in enumerate(events, 1):
        report += f"  Event {index}:\n"
        report += f"    ID: {event['id']}\n"
        report += f"    Alarm time: {event['alarm_time']}\n"
        report += f"    Image URL: {event['url']}\n\n"

    return report


def process_specific_intrusion_event(data):
    query_id = data["query_id"]
    events = data["events"]

    report = f"Query ID: {query_id} (intrusion event images by id)\n"
    report += f"Total images: {len(events)}\n"
    report += "Details:\n"

    for index, event in enumerate(events, 1):
        report += f"  Image {index}:\n"
        report += f"    Alarm time: {event['alarm_time']}\n"
        report += f"    Image URL: {event['url']}\n\n"

    return report


def process_time_range_intrusion_records(data):
    query_id = data["query_id"]
    total_events = data["total_events"]
    events = data["events"]

    report = f"Query ID: {query_id} (intrusion events in time range)\n"
    report += f"Total events: {total_events}\n"
    report += "Details:\n"

    for index, event in enumerate(events, 1):
        report += f"  Event {index}:\n"
        report += f"    Alarm time: {event['alarm_time']}\n"
        report += f"    ID: {event['id']}\n\n"

    return report


def process_passenger_flow_statistics(data):
    query_id = data["query_id"]
    total_periods = data["total_periods"]
    periods = data["periods"]

    report = f"Query ID: {query_id} (passenger flow statistics)\n"
    report += f"Total periods: {total_periods}\n"
    report += "Details:\n"

    for index, period in enumerate(periods, 1):
        report += f"  Period {index}:\n"
        report += f"    Start: {period['start_time']}\n"
        report += f"    End: {period['end_time']}\n"
        report += f"    Passenger flow: {period['passenger_flow']}\n\n"

    return report


def process_passenger_flow_distribution(data):
    query_id = data["query_id"]
    total_segments = data["total_segments"]
    segments = data["segments"]

    report = f"Query ID: {query_id} (passenger flow distribution)\n"
    report += f"Total segments: {total_segments}\n"
    report += "Details:\n"

    for index, segment in enumerate(segments, 1):
        report += (
            f"  Segment {index}: {segment['start_time']} - {segment['end_time']}, "
            f"Passenger flow: {segment['passenger_flow']}\n"
        )

    return report


def test_parser():
    test_data = json.dumps([
        {
            "query_id": "a1b2c3",
            "query_type": "leave_post_records",
            "total_records": 2,
            "leave_post_records": [
                {"time_slot_start": "090000", "time_slot_end": "093000"},
                {"time_slot_start": "140000", "time_slot_end": "141500"},
            ],
        },
        {
            "query_id": "d4e5f6",
            "query_type": "multiple_intrusion_event_images",
            "events": [
                {"id": "001", "alarm_time": "2023-05-01 10:00:00", "url": "http://example.com/image1.jpg"},
                {"id": "002", "alarm_time": "2023-05-01 11:30:00", "url": "http://example.com/image2.jpg"},
            ],
        },
        {
            "query_id": "g7h8i9",
            "query_type": "intrusion_event_images_by_id",
            "events": [
                {"alarm_time": "2023-05-01 15:45:00", "url": "http://example.com/image3.jpg"}
            ],
        },
        {
            "query_id": "e4afea46",
            "query_type": "intrusion_events_in_time_range",
            "total_events": 3,
            "events": [
                {"alarm_time": "2024-05-27 11:07:31", "id": 66406},
                {"alarm_time": "2024-05-27 11:13:50", "id": 66414},
                {"alarm_time": "2024-05-27 11:25:39", "id": 66428},
            ],
        },
        {
            "query_id": "f90efeff",
            "query_type": "passenger_flow_statistics",
            "total_periods": 1,
            "periods": [
                {"start_time": "2024-05-27 00:00:00", "end_time": "2024-05-27 23:59:59", "passenger_flow": 349.0},
                {"start_time": "2024-05-27 00:00:00", "end_time": "2024-05-27 23:59:59", "passenger_flow": 349.0},
            ],
        },
        {
            "query_id": "5a823393",
            "query_type": "passenger_flow_distribution",
            "total_segments": 10,
            "segments": [
                {"start_time": "2024-05-27 00:00:00", "end_time": "2024-05-27 02:23:59", "passenger_flow": 36.0},
                {"start_time": "2024-05-27 02:23:59", "end_time": "2024-05-27 04:47:59", "passenger_flow": 26.0},
                {"start_time": "2024-05-27 04:47:59", "end_time": "2024-05-27 07:11:59", "passenger_flow": 36.0},
            ],
        },
    ])

    input_string = (
        "This is the result [a1b2c3]. Another is [d4e5f6]. "
        "Last is [g7h8i9]. New result is [e4afea46]. "
        "Flow statistics is [f90efeff]. Distribution is [5a823393]. Unknown [x1y2z3]."
    )

    print(parse_json(json.loads(test_data), input_string))

# Run test
#test_parser()
