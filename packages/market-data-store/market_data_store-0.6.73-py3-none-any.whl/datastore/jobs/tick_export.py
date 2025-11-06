"""
Phase 5 – Tick Export Jobs

Export tick_data, aggregates, and signals to Parquet for offline backtests/ML.
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List

import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgres://postgres:postgres@md_postgres:5432/market_data",
)


async def export_ticks_to_parquet(
    provider: str,
    symbols: List[str],
    start_ts: datetime,
    end_ts: datetime,
    output_path: Path,
    job_run_id: int | None = None,
) -> int:
    """
    Export tick_data to Parquet file.

    Args:
        provider: Provider name
        symbols: List of symbols
        start_ts: Start timestamp
        end_ts: End timestamp
        output_path: Output file path
        job_run_id: Optional job run ID for tracking

    Returns:
        Number of rows exported
    """
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Fetch ticks
        rows = await conn.fetch(
            """
            SELECT provider, symbol, price, ts, size, bid, ask, created_at
            FROM tick_data
            WHERE provider = $1
              AND symbol = ANY($2)
              AND ts >= $3
              AND ts < $4
            ORDER BY ts ASC
            """,
            provider,
            symbols,
            start_ts,
            end_ts,
        )

        if not rows:
            logger.warning("No ticks found for export")
            return 0

        # For now, write CSV (Parquet requires pyarrow)
        # TODO: Add pyarrow dependency and write actual Parquet
        output_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path = output_path.with_suffix(".csv")

        with open(csv_path, "w") as f:
            # Header
            f.write("provider,symbol,price,ts,size,bid,ask,created_at\n")

            # Data
            for row in rows:
                f.write(
                    f"{row['provider']},{row['symbol']},{row['price']},"
                    f"{row['ts']},{row['size']},{row['bid']},{row['ask']},{row['created_at']}\n"
                )

        logger.info(f"Exported {len(rows)} ticks to {csv_path}")
        return len(rows)

    finally:
        await conn.close()


async def export_bars_to_parquet(
    provider: str,
    symbols: List[str],
    start_ts: datetime,
    end_ts: datetime,
    interval: str,
    output_path: Path,
    job_run_id: int | None = None,
) -> int:
    """
    Export tick aggregates (1m/5m/1h) to Parquet.

    Args:
        provider: Provider name
        symbols: List of symbols
        start_ts: Start timestamp
        end_ts: End timestamp
        interval: "1m", "5m", or "1h"
        output_path: Output file path
        job_run_id: Optional job run ID

    Returns:
        Number of rows exported
    """
    view_map = {"1m": "tick_agg_1m", "5m": "tick_agg_5m", "1h": "tick_agg_1h"}
    view_name = view_map.get(interval)

    if not view_name:
        raise ValueError(f"Invalid interval: {interval}. Must be one of {list(view_map.keys())}")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            f"""
            SELECT provider, symbol, bucket, open, high, low, close, volume, tick_count
            FROM {view_name}
            WHERE provider = $1
              AND symbol = ANY($2)
              AND bucket >= $3
              AND bucket < $4
            ORDER BY bucket ASC
            """,
            provider,
            symbols,
            start_ts,
            end_ts,
        )

        if not rows:
            logger.warning(f"No bars found in {view_name} for export")
            return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path = output_path.with_suffix(".csv")

        with open(csv_path, "w") as f:
            f.write("provider,symbol,bucket,open,high,low,close,volume,tick_count\n")

            for row in rows:
                f.write(
                    f"{row['provider']},{row['symbol']},{row['bucket']},"
                    f"{row['open']},{row['high']},{row['low']},{row['close']},"
                    f"{row['volume']},{row['tick_count']}\n"
                )

        logger.info(f"Exported {len(rows)} bars from {view_name} to {csv_path}")
        return len(rows)

    finally:
        await conn.close()


async def export_signals_to_parquet(
    provider: str,
    symbols: List[str],
    start_ts: datetime,
    end_ts: datetime,
    output_path: Path,
    signal_names: List[str] | None = None,
    job_run_id: int | None = None,
) -> int:
    """
    Export signals to Parquet.

    Args:
        provider: Provider name
        symbols: List of symbols
        start_ts: Start timestamp
        end_ts: End timestamp
        output_path: Output file path
        signal_names: Optional list of signal names to filter
        job_run_id: Optional job run ID

    Returns:
        Number of rows exported
    """
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if signal_names:
            rows = await conn.fetch(
                """
                SELECT provider, symbol, ts, name, value, score, metadata, created_at
                FROM signals
                WHERE provider = $1
                  AND symbol = ANY($2)
                  AND ts >= $3
                  AND ts < $4
                  AND name = ANY($5)
                ORDER BY ts ASC
                """,
                provider,
                symbols,
                start_ts,
                end_ts,
                signal_names,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT provider, symbol, ts, name, value, score, metadata, created_at
                FROM signals
                WHERE provider = $1
                  AND symbol = ANY($2)
                  AND ts >= $3
                  AND ts < $4
                ORDER BY ts ASC
                """,
                provider,
                symbols,
                start_ts,
                end_ts,
            )

        if not rows:
            logger.warning("No signals found for export")
            return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path = output_path.with_suffix(".csv")

        with open(csv_path, "w") as f:
            f.write("provider,symbol,ts,name,value,score,metadata,created_at\n")

            for row in rows:
                metadata_str = str(row["metadata"]).replace(",", ";") if row["metadata"] else ""
                f.write(
                    f"{row['provider']},{row['symbol']},{row['ts']},{row['name']},"
                    f"{row['value']},{row['score']},{metadata_str},{row['created_at']}\n"
                )

        logger.info(f"Exported {len(rows)} signals to {csv_path}")
        return len(rows)

    finally:
        await conn.close()


def main():
    """CLI entry point for manual exports."""
    import argparse

    parser = argparse.ArgumentParser(description="Export market data to files")
    parser.add_argument("dataset", choices=["ticks", "bars", "signals"])
    parser.add_argument("--provider", required=True)
    parser.add_argument("--symbols", required=True, help="Comma-separated symbols")
    parser.add_argument("--start", required=True, help="Start timestamp (ISO format)")
    parser.add_argument("--end", required=True, help="End timestamp (ISO format)")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--interval", help="Interval for bars (1m/5m/1h)")

    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",")]
    start_ts = datetime.fromisoformat(args.start)
    end_ts = datetime.fromisoformat(args.end)
    output_path = Path(args.output)

    if args.dataset == "ticks":
        rows = asyncio.run(
            export_ticks_to_parquet(args.provider, symbols, start_ts, end_ts, output_path)
        )
    elif args.dataset == "bars":
        if not args.interval:
            raise ValueError("--interval required for bars export")
        rows = asyncio.run(
            export_bars_to_parquet(
                args.provider, symbols, start_ts, end_ts, args.interval, output_path
            )
        )
    elif args.dataset == "signals":
        rows = asyncio.run(
            export_signals_to_parquet(args.provider, symbols, start_ts, end_ts, output_path)
        )

    print(f"Exported {rows} rows to {output_path}")


if __name__ == "__main__":
    main()
