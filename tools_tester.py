from tools.InvaseAlarmEventsQuery import InvaseAlarmEventsQuery
from tools.FlowQuery import FlowQuery
from tools.FlowDistributeQuery import FlowDistribution
from tools.LeaveRecordsQuery import LeaveRecordsQuery
from tools.MultiInvaseAlarmIndexQuery import MultiInvaseAlarmPictureQuery
from tools.InvaseAlarmIndexQuery import InvaseAlarmPictureQuery
from connection import db
from loguru import logger

db.connect()

# Example usage
start_time = "2024-05-27 00:00:00"
end_time = "2024-05-27 23:59:59"
logger.info("Running tool test for FlowDistribution")
print(FlowDistribution(start_time + " - " + end_time, "10"))
