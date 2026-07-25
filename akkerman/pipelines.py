"""Item pipelines for the akkerman project.

The primary pipeline (``ParquetPipeline``) buffers scraped items in memory and,
when the spider finishes, writes them out to a single compressed Parquet file
using pandas + pyarrow. This satisfies the project's core goal of landing data
in a compact, columnar, query-friendly format.

For very large crawls consider swapping the buffered write for an incremental
``pyarrow.parquet.ParquetWriter`` (see ``_write_incremental`` note below).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class ParquetPipeline:
    """Collect items and write them to a Parquet file on spider close."""

    def __init__(self, output_dir: str, compression: str):
        self.output_dir = Path(output_dir)
        self.compression = None if compression.lower() == "none" else compression
        self._items: list[dict] = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_dir=crawler.settings.get("PARQUET_OUTPUT_DIR", "data"),
            compression=crawler.settings.get("PARQUET_COMPRESSION", "snappy"),
        )

    def open_spider(self, spider):
        self._items = []
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_item(self, item, spider):
        self._items.append(dict(ItemAdapter(item).asdict()))
        return item

    def close_spider(self, spider):
        if not self._items:
            logger.warning("ParquetPipeline: no items scraped, nothing to write.")
            return

        # Import here so the rest of Scrapy still works even if pandas/pyarrow
        # are not installed (e.g. when running unrelated commands).
        import pandas as pd

        df = pd.DataFrame(self._items)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = self.output_dir / f"{spider.name}_{timestamp}.parquet"

        df.to_parquet(out_path, engine="pyarrow", compression=self.compression, index=False)

        logger.info(
            "ParquetPipeline: wrote %d items to %s (compression=%s)",
            len(df),
            out_path,
            self.compression,
        )
