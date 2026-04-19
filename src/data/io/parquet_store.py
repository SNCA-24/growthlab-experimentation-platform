from __future__ import annotations

from pathlib import Path
from typing import Mapping

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def write_parquet_table(path: str | Path, frame: pd.DataFrame) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, output_path, compression="zstd")


def write_tables_to_parquet(output_dir: str | Path, tables: Mapping[str, pd.DataFrame]) -> None:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    for table_name, frame in tables.items():
        write_parquet_table(root / f"{table_name}.parquet", frame)

