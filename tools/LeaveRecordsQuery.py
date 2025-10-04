import uuid
import pymysql
import json

from connection import db

from agentscope.service import(
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.utils.common import _if_change_database

def LeaveRecordsQuery(start_time: str, end_time: str) -> str:
    """
    Query leave-post records within a time range.

    Args:
        start_time (str): "YYYY-MM-DD hh:mm:ss"
        end_time (str): "YYYY-MM-DD hh:mm:ss"

    Returns:
        str: JSON string of leave records.
    """
    try:
        conn = db.get_connection()

        query = (
            "SELECT time_slot_start, time_slot_end, interval_time "
            "FROM t_lgsb_alarm_record "
            "WHERE alarm_time BETWEEN %s AND %s "
            "ORDER BY alarm_time"
        )

        results = []

        with conn.cursor() as cursor:
            cursor.execute(query, (start_time, end_time))
            if _if_change_database(query):
                conn.commit()
            records = cursor.fetchall()

            for record in records:
                results.append({
                    "time_slot_start": record['time_slot_start'],
                    "time_slot_end": record['time_slot_end'],
                    "interval_time": str(record['interval_time'])
                })

        if results:
            content = {
                "query_id": str(uuid.uuid4())[:8],
                "query_type": "leave_post_records",
                "total_records": len(results),
                "leave_post_records": results,
            }
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=json.dumps(content, ensure_ascii=True),
            )
        else:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=json.dumps({"message": "No leave-post records found in the given time range."}, ensure_ascii=True),
            )
        
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=json.dumps({"error": str(e)}, ensure_ascii=True),
        )
