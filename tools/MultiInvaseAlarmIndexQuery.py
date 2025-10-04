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



def MultiInvaseAlarmPictureQuery(ids: list) -> str:
    """
    Query images for multiple intrusion events by ids.

    Args:
        ids (list): list of event ids

    Returns:
        str: JSON with image urls per event.
    """

    placeholders = ", ".join(["%s"] * len(ids)) if ids else "%s"
    query = (
        "SELECT id, alarm_time, alarm_pic_url "
        "FROM t_qyrq_alarm_msg "
        f"WHERE id IN ({placeholders}) "
        "ORDER BY alarm_time ASC"
    )


    try:
        conn = db.get_connection()

        with conn.cursor() as cursor:
            cursor.execute(query, tuple(ids) if ids else (None,))
            if _if_change_database(query):
                conn.commit()
            results = cursor.fetchall()

        if not results:
            return ServiceResponse(
                status=ServiceExecStatus.SUCCESS,
                content=json.dumps({"message": "No intrusion events found for the specified ids."}, ensure_ascii=True),
            )

        content = {
            "query_id": str(uuid.uuid4())[:8],
            "query_type": "multiple_intrusion_event_images",
            "events": [
                {
                    "id": result["id"],
                    "alarm_time": result["alarm_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "url": result["alarm_pic_url"],
                }
                for result in results
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
