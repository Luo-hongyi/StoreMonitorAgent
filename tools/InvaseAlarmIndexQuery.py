import uuid
import pymysql
import json
from datetime import timedelta
from connection import db

from agentscope.service import(
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.utils.common import _if_change_database

def InvaseAlarmPictureQuery(id: str) -> str:
    """
    Query multiple images for a single intrusion event by id.
    Prefer this tool when only one event id is needed.

    Args:
        id (str): event id

    Returns:
        str: JSON with image urls and timestamps.
    """

    query = (
        "SELECT id, alarm_time, alarm_pic_url "
        "FROM t_qyrq_alarm_msg "
        "WHERE id = %s "
        "    OR (alarm_time > (SELECT alarm_time FROM t_qyrq_alarm_msg WHERE id = %s) "
        "        AND alarm_time <= (SELECT alarm_time FROM t_qyrq_alarm_msg WHERE id = %s) + INTERVAL 10 MINUTE) "
        "ORDER BY alarm_time ASC"
    )

    try:
        conn = db.get_connection()

        with conn.cursor() as cursor:
            cursor.execute(query, (id, id, id))
            if _if_change_database(query):
                conn.commit()
            results = cursor.fetchall()

        if not results:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=json.dumps({"message": f"No intrusion event found for id {id}."}, ensure_ascii=True),
            )

        filtered_results = []
        last_time = None
        for result in results:
            current_time = result['alarm_time']
            if last_time is None or (current_time - last_time) <= timedelta(minutes=2):
                filtered_results.append(result)
                last_time = current_time
            else:
                break

        if len(filtered_results) <= 5:
            selected_results = filtered_results
        else:
            # compute five-point sampling indices across the sequence
            indices = [
                0,
                len(filtered_results) // 4,
                len(filtered_results) // 2,
                (3 * len(filtered_results)) // 4,
                len(filtered_results) - 1
            ]
            selected_results = [filtered_results[i] for i in indices]

        content = {
            "query_id": str(uuid.uuid4())[:8],
            "query_type": "intrusion_event_images_by_id",
            "events": [
                {
                    "alarm_time": result["alarm_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "url": result["alarm_pic_url"],
                }
                for result in selected_results
            ],
        }
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=json.dumps(content, ensure_ascii=True),
        )
        
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=json.dumps({"error": str(e)}, ensure_ascii=True),
        )


#print(InvaseAlarmIndexQuery("66416"))
