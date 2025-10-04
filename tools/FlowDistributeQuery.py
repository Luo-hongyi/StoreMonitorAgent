import pymysql
import json
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from connection import db

from agentscope.service import(
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.utils.common import _if_change_database

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

def FlowDistribution(time_range: str, num_segments: str) -> str:
    """
    Query passenger flow distribution over sub-intervals within a time range.
    Prefer passenger flow statistics for high-level summaries.

    Args:
        time_range (str): "YYYY-MM-DD hh:mm:ss - YYYY-MM-DD hh:mm:ss"
        num_segments (str): number of segments (int as string)

    Returns:
        str: JSON string with passenger flow per segment.
    """
    try:
        start_time, end_time = time_range.split(' - ')
        start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        num_segments = int(num_segments)

        if num_segments <= 0:
            return ServiceResponse(
                status=ServiceExecStatus.ERROR,
                content=json.dumps({"error": "num_segments must be greater than 0"}, ensure_ascii=True),
            )

        segment_duration = (end_datetime - start_datetime) / num_segments
        results = []

        conn = db.get_connection()

        for i in range(num_segments):
            segment_start = start_datetime + i * segment_duration
            segment_end = segment_start + segment_duration

            query = (
                "SELECT SUM(person_num) as total_flow "
                "FROM t_kltj_alarm_msg "
                "WHERE create_time BETWEEN %s AND %s"
            )

            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        segment_start.strftime("%Y-%m-%d %H:%M:%S"),
                        segment_end.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                if _if_change_database(query):
                    conn.commit()
                result = cursor.fetchone()

            total_flow = float(result['total_flow']) if result and result['total_flow'] else 0
            
            results.append({
                "start_time": segment_start.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": segment_end.strftime("%Y-%m-%d %H:%M:%S"),
                "passenger_flow": total_flow
            })

        if results:
            content = {
                "query_id": str(uuid.uuid4())[:8],
                "query_type": "passenger_flow_distribution",
                "total_segments": num_segments,
                "segments": results,
            }
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=json.dumps(content, ensure_ascii=True, cls=DecimalEncoder),
            )
        else:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=json.dumps({"message": "No passenger flow data found in the given time range."}, ensure_ascii=True),
            )
        
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=json.dumps({"error": str(e)}, ensure_ascii=True),
        )

# Example usage
# time_range = "2024-05-27 11:00:00 - 2024-05-27 12:00:00"
# num_segments = "6"
# print(FlowDistribution(time_range, num_segments))
