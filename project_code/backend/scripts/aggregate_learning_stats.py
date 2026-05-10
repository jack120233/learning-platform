"""手动重建学习统计聚合。"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.dependencies import AsyncSessionLocal
from app.services.learning_statistics_service import learning_statistics_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="重建学习统计聚合")
    parser.add_argument("--date", dest="single_date", help="单日聚合，格式 YYYY-MM-DD")
    parser.add_argument("--start-date", help="区间开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", help="区间结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=7, help="未指定日期时重建最近 N 天，默认 7 天")
    return parser.parse_args()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


async def main() -> None:
    args = parse_args()
    today = date.today()

    if args.single_date:
        start_date = end_date = parse_date(args.single_date)
    elif args.start_date or args.end_date:
        if not args.start_date or not args.end_date:
            raise SystemExit("--start-date 和 --end-date 必须同时提供")
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
    else:
        days = max(args.days, 1)
        end_date = today
        start_date = today - timedelta(days=days - 1)

    async with AsyncSessionLocal() as session:
        results = await learning_statistics_service.aggregate_range(session, start_date, end_date)
        await session.commit()

    for item in results:
        print(
            f"{item['stat_date']}: sessions={item['session_count']} "
            f"students={item['student_count']} courses={item['course_count']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
