import os
import pymysql
from typing import Any, Dict, List, Optional
from loguru import logger


class MockCursor:
    def __init__(self, conn: "MockConnection") -> None:
        self._conn = conn
        self._results: List[Dict[str, Any]] = []

    def __enter__(self) -> "MockCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        # Very lightweight mock based on table keywords in the query
        self._conn._call_count += 1
        if "FROM t_kltj_alarm_msg" in query:
            # passenger flow sum
            val = 10 + (self._conn._call_count % 10)
            self._results = [{"total_flow": val}]
        elif "FROM t_lgsb_alarm_record" in query:
            self._results = [
                {"time_slot_start": "080000", "time_slot_end": "082000", "interval_time": 20},
                {"time_slot_start": "103000", "time_slot_end": "105000", "interval_time": 20},
            ]
        elif "FROM t_qyrq_alarm_msg" in query and "SELECT alarm_time, id" in query:
            self._results = [
                {"alarm_time": pymysql.Timestamp(2024, 5, 27, 11, 7, 31), "id": 66406},
                {"alarm_time": pymysql.Timestamp(2024, 5, 27, 11, 13, 50), "id": 66414},
                {"alarm_time": pymysql.Timestamp(2024, 5, 27, 11, 25, 39), "id": 66428},
            ]
        elif "FROM t_qyrq_alarm_msg" in query and "alarm_pic_url" in query:
            self._results = [
                {"id": 66406, "alarm_time": pymysql.Timestamp(2024, 5, 27, 11, 7, 31), "alarm_pic_url": "http://example.com/1.jpg"},
                {"id": 66414, "alarm_time": pymysql.Timestamp(2024, 5, 27, 11, 13, 50), "alarm_pic_url": "http://example.com/2.jpg"},
                {"id": 66428, "alarm_time": pymysql.Timestamp(2024, 5, 27, 11, 25, 39), "alarm_pic_url": "http://example.com/3.jpg"},
            ]
        else:
            self._results = []

    def fetchone(self) -> Optional[Dict[str, Any]]:
        return self._results[0] if self._results else None

    def fetchall(self) -> List[Dict[str, Any]]:
        return list(self._results)


class MockConnection:
    def __init__(self) -> None:
        self._call_count = 0

    def cursor(self, *_args, **_kwargs) -> MockCursor:
        return MockCursor(self)

    def commit(self) -> None:
        return None

    def close(self) -> None:
        return None


class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        use_mock = os.getenv("USE_MOCK_DB", "0").lower() in {"1", "true", "yes"}
        if use_mock:
            self.connection = MockConnection()
            logger.info("Using Mock DB connection (USE_MOCK_DB=1)")
            return

        host = os.getenv("DB_HOST")
        port = int(os.getenv("DB_PORT", "3306"))
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME")

        missing = [k for k, v in {
            "DB_HOST": host,
            "DB_USER": user,
            "DB_PASSWORD": password,
            "DB_NAME": database,
        }.items() if not v]
        if missing:
            raise RuntimeError(
                f"Missing required DB env vars: {', '.join(missing)}. "
                "Set USE_MOCK_DB=1 to run without a real database."
            )

        try:
            self.connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=10,
                read_timeout=30,
                write_timeout=30,
                cursorclass=pymysql.cursors.DictCursor,
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.exception(f"Failed to connect to database: {e}")
            raise

    def get_connection(self):
        return self.connection

    def close_connection(self):
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            finally:
                self.connection = None


db = DatabaseConnection()
