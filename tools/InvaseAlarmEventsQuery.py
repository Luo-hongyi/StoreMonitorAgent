import uuid
import pymysql
import json
from datetime import datetime, timedelta

from connection import db

from agentscope.service import(
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.utils.common import _if_change_database




def InvaseAlarmEventsQuery(start_time: str, end_time: str) -> str:
    """
    Query intrusion events within a given time range. You may expand the time
    range moderately (10–60 minutes) to avoid missing events when appropriate.

    Args:
        start_time (str): "YYYY-MM-DD hh:mm:ss"
        end_time (str): "YYYY-MM-DD hh:mm:ss"

    Returns:
        str: JSON string with event ids and alarm_time.
    """

    query = (
        "SELECT alarm_time, id "
        "FROM t_qyrq_alarm_msg "
        "WHERE alarm_time BETWEEN %s AND %s "
        "ORDER BY alarm_time ASC"
    )


    try:
        conn = db.get_connection()
        
        with conn.cursor() as cursor:
            cursor.execute(query, (start_time, end_time))
            if _if_change_database(query):
                conn.commit()
            results = cursor.fetchall()

        filtered_results = []
        last_time = None
        for result in results:
            current_time = result['alarm_time']
            if last_time is None or (current_time - last_time) >= timedelta(minutes=2):
                filtered_results.append({
                    "alarm_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "id": result['id']
                })
                last_time = current_time

        if filtered_results:
            content = {
                "query_id": str(uuid.uuid4())[:8],
                "query_type": "intrusion_events_in_time_range",
                "total_events": len(filtered_results),
                "events": filtered_results,
            }
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=json.dumps(content, ensure_ascii=True),
            )
        else:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=json.dumps({"message": "No intrusion events found in the given time range."}, ensure_ascii=True),
            )
        
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=json.dumps({"error": str(e)}, ensure_ascii=True),
        )

#print(InvaseAlarmEventsQuery("2024-05-27 11:00:00", "2024-05-27 12:00:00"))
