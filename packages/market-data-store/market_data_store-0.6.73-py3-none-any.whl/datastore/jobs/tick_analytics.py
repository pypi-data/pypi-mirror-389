"""
Phase 4 – Tick Analytics Maintenance Jobs

Optional helper to manually refresh continuous aggregates on tick_data.
Timescale's add_continuous_aggregate_policy already handles ongoing refresh;
this is mainly for backfill / ad-hoc maintenance.
"""

import os
import asyncio
import logging

import asyncpg

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://postgres:postgres@md_postgres:5432/market_data",
)

AGG_VIEWS = [
    "tick_agg_1m",
    "tick_agg_5m",
    "tick_agg_1h",
    "tick_vwap_daily",
    "tick_spread_stats",
    "tick_rate_stats",
]


async def refresh_all_continuous_aggregates() -> None:
    """Refresh all tick analytics continuous aggregates."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        for view in AGG_VIEWS:
            try:
                # Refresh the full range; policies handle incremental updates.
                log.info("Refreshing continuous aggregate %s", view)
                await conn.execute(
                    f"CALL refresh_continuous_aggregate('{view}'::regclass, NULL, NULL);"
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("Failed to refresh continuous aggregate %s: %s", view, exc)
    finally:
        await conn.close()


def main() -> None:
    """Main entry point for manual refresh."""
    asyncio.run(refresh_all_continuous_aggregates())


if __name__ == "__main__":
    main()
