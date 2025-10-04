import uuid
import pymysql
import json
from datetime import datetime
from decimal import Decimal

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

def FlowQuery(time_ranges: str) -> str:
    """
    Query passenger flow totals for multiple time ranges.

    Args:
        time_ranges (str): Comma-separated time ranges in the format
            "YYYY-MM-DD hh:mm:ss - YYYY-MM-DD hh:mm:ss,YYYY-MM-DD hh:mm:ss - YYYY-MM-DD hh:mm:ss,..."

    Returns:
        str: JSON string with passenger flow per range.
    """
    time_ranges = [range.strip() for range in time_ranges.split(',')]
    results = []

    try:
        conn = db.get_connection()
        
        for time_range in time_ranges:
            start_time, end_time = time_range.split(' - ')
            
            query = (
                "SELECT SUM(person_num) as total_flow "
                "FROM t_kltj_alarm_msg "
                "WHERE create_time BETWEEN %s AND %s"
            )

            with conn.cursor() as cursor:
                cursor.execute(query, (start_time, end_time))
                if _if_change_database(query):
                    conn.commit()
                result = cursor.fetchone()

            total_flow = float(result['total_flow']) if result and result['total_flow'] else 0
            
            results.append({
                "start_time": start_time,
                "end_time": end_time,
                "passenger_flow": total_flow
            })

        if results:
            content = {
                "query_id": str(uuid.uuid4())[:8],
                "query_type": "passenger_flow_statistics",
                "total_periods": len(results),
                "periods": results,
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
# time_ranges = "2024-05-27 11:00:00 - 2024-05-27 12:00:00,2024-05-27 13:00:00 - 2024-05-27 14:00:00"
# print(FlowQuery(time_ranges))
