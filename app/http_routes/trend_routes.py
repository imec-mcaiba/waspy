from app.trends.trend import Trend
from datetime import datetime, timedelta


def build_trend_routes(router, trend: Trend):
    @router.get("/api/trends/values", tags=["TREND API"])
    async def get_values(start: datetime, end: datetime, step: timedelta):
        return trend.get_values(start, end, step)

    @router.get("/api/trends/minutes", tags=["TREND API"])
    async def get_values():
        return trend.get_last_10_minutes()

    @router.get("/api/trends/hours", tags=["TREND API"])
    async def get_values():
        return trend.get_last_hour()

    @router.get("/api/trends/days", tags=["TREND API"])
    async def get_values():
        return trend.get_last_day()
