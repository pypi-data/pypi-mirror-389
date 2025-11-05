import hashlib
import os
from itertools import count
from pathlib import Path
from typing import Callable, Iterator, Mapping, Optional, Union

import msgspec.json
import polars as pl
from polars._typing import ParallelStrategy
from polars.io.plugins import register_io_source

from polars_pf._polars_pf import PyPFrame, PyPTable, canonicalize, map_predicate
from polars_pf.json.filter import PTableRecordFilter
from polars_pf.json.join import CreateTableRequest
from polars_pf.json.spec import (
    AxisId,
    AxisSpec,
    AxisType,
    ColumnType,
    PTableColumnId,
    PTableColumnIdAxis,
    PTableColumnIdColumn,
    PTableColumnSpec,
    PTableColumnSpecAxis,
    PTableColumnSpecs,
)
from polars_pf.log import Logger, LogLevel
from polars_pf.perf_timer import PerfTimer


def pframes_to_polars_type(type: Union[AxisType, ColumnType]) -> pl.DataType:
    match type:
        case AxisType.Int | ColumnType.Int:
            return pl.Int32
        case AxisType.Long | ColumnType.Long:
            return pl.Int64
        case ColumnType.Float:
            return pl.Float32
        case ColumnType.Double:
            return pl.Float64
        case AxisType.String | ColumnType.String:
            return pl.String


def axis_ref(spec: AxisSpec) -> str:
    return canonicalize(
        AxisId(name=spec.name, type=spec.type, domain=spec.domain)
    ).decode("utf-8")


def column_ref(spec: PTableColumnSpec) -> str:
    if isinstance(spec, PTableColumnSpecAxis):
        return axis_ref(spec.spec)
    return spec.id


class PFramesCache:
    """
    Global cache of PFrames and PTables instances.

    This cache manages the lifecycle of PFrames and PTables instances,
    providing acquire methods to get or create resources and an idempotent
    dispose method to dispose everything in the cache.
    """

    def __init__(self):
        """Initialize empty cache."""
        # Maps resolved Path -> (PyPFrame, counter iterator)
        self._pframes: dict[Path, tuple[PyPFrame, Iterator[int]]] = {}
        # Maps (resolved Path, request hash) -> (PyPTable, table_id)
        self._ptables: dict[tuple[Path, bytes], tuple[PyPTable, str]] = {}

    def acquire_frame(
        self,
        resolved_path: Path,
        spill_path: Optional[Path] = None,
        logger: Optional[Logger] = None,
    ) -> PyPFrame:
        """
        Acquire a PFrame instance, creating or reusing from cache.

        Args:
            resolved_path: Resolved Path to the directory containing the frame data
            spill_path: Optional Path for spilling data to disk
            logger: Optional logger for cache operations

        Returns:
            PyPFrame instance (new or cached)
        """
        if resolved_path not in self._pframes:
            pframe = PyPFrame(
                str(resolved_path), str(spill_path) if spill_path else None, logger
            )
            self._pframes[resolved_path] = (pframe, count(1))
            logger and logger(
                LogLevel.Info,
                f'PFrame "{resolved_path.name}" created',
            )
        else:
            logger and logger(
                LogLevel.Info,
                f'PFrame "{resolved_path.name}" reused',
            )

        pframe, _ = self._pframes[resolved_path]
        return pframe

    def acquire_table(
        self,
        resolved_path: Path,
        request: CreateTableRequest,
        logger: Optional[Logger] = None,
    ) -> PyPTable:
        """
        Acquire a PyPTable instance, creating or reusing from cache.

        The cache key is a combination of the resolved path and
        the SHA256 hash of the canonicalized request. Using SHA256 provides
        efficient lookups even for large requests.

        Args:
            resolved_path: Resolved Path to the directory containing the frame data
            request: Table creation request
            logger: Optional logger for cache operations

        Returns:
            PyPTable instance (new or cached)
        """
        key = (resolved_path, hashlib.sha256(canonicalize(request)).digest())
        if key not in self._ptables:
            pframe_entry = self._pframes.get(resolved_path)
            if pframe_entry is None:
                raise RuntimeError(f"PFrame not found in cache for {resolved_path}")

            pframe, counter = pframe_entry
            frame_id = resolved_path.name
            table_id = f"{frame_id}_{next(counter)}"

            ptable = pframe.create_table(request, table_id)
            self._ptables[key] = (ptable, table_id)
            logger and logger(
                LogLevel.Info,
                f'PTable "{table_id}" created',
            )
        else:
            _, table_id = self._ptables[key]
            logger and logger(
                LogLevel.Info,
                f'PTable "{table_id}" reused',
            )

        ptable, _ = self._ptables[key]
        return ptable

    def dispose(self, logger: Optional[Logger] = None) -> None:
        """
        Dispose all cached resources.

        Args:
            logger: Optional logger for cache operations
        """
        logger and logger(
            LogLevel.Info,
            f"Disposing {len(self._pframes)} PFrames and {len(self._ptables)} PTables",
        )

        for ptable, _ in self._ptables.values():
            ptable.dispose()
        self._ptables.clear()

        for pframe, _ in self._pframes.values():
            pframe.dispose()
        self._pframes.clear()


# Global singleton cache instance
_global_cache = PFramesCache()


def pframe_source(
    input_path: Path,
    request: CreateTableRequest,
    *,
    spill_path: Optional[Path] = None,
    column_ref: Callable[[PTableColumnSpec], str] = column_ref,
    logger: Optional[Logger] = None,
    parallel: ParallelStrategy = "auto",
    low_memory: bool = False,
) -> tuple[pl.LazyFrame, PFramesCache]:
    """
    Create PTable and export it as Polars LazyFrame with resource cache.

    This function creates a resource cache that manages PyPFrame and PyPTable
    instances. The cache provides acquire methods to get or create resources
    and an idempotent dispose method for cleanup.

    Args:
        input_path: Path to the directory containing the frame data
        request: Table creation request
        spill_path: Optional path for spilling data to disk
        column_ref: Function to generate column references
        logger: Optional logger function
        parallel: Polars parallel strategy for reading parquet files
        low_memory: Whether to use low memory mode for parquet reading

    Returns:
        Tuple of (LazyFrame, PFramesCache) where the cache should be
        disposed after all queries are complete
    """
    if not input_path.is_dir():
        raise ValueError(f'Input path "{input_path}" is not an existing directory')

    resolved_path = input_path.resolve()
    frame_id = resolved_path.name

    logger and logger(
        LogLevel.Info,
        f'PFrame "{frame_id}" registration as Polars source started, '
        f'input_path: "{resolved_path}", '
        f"request: {msgspec.json.encode(request).decode()}",
    )
    timer: PerfTimer = PerfTimer.start()

    try:
        pframe = _global_cache.acquire_frame(resolved_path, spill_path, logger)

        column_refs: list[str] = []
        schema: Mapping[str, pl.DataType] = {}
        column_ref_to_column_id: Mapping[str, PTableColumnId] = {}
        temp_table = pframe.create_table(request, f"{frame_id}_temp")
        try:
            fields: list[str] = temp_table.get_fields()
            specs: PTableColumnSpecs = temp_table.get_spec()
            for field, spec_item in zip(fields, specs):
                ref: str = column_ref(spec_item)
                column_refs.append(ref)
                schema[ref] = pframes_to_polars_type(
                    spec_item.spec.type
                    if isinstance(spec_item, PTableColumnSpecAxis)
                    else spec_item.spec.value_type
                )
                column_ref_to_column_id[ref] = (
                    PTableColumnIdAxis(id=spec_item.id)
                    if isinstance(spec_item, PTableColumnSpecAxis)
                    else PTableColumnIdColumn(id=spec_item.id)
                )
        finally:
            temp_table.dispose()

        def source_generator(
            with_columns: Optional[list[str]],
            predicate: Optional[pl.Expr],
            n_rows: Optional[int],
            batch_size: Optional[int],
        ) -> Iterator[pl.DataFrame]:
            logger and logger(
                LogLevel.Info,
                f'PFrame "{frame_id}" Polars source generator started, '
                f"with_columns: {with_columns}, "
                f"predicate: {predicate is not None}, "
                f"n_rows: {n_rows}, "
                f"batch_size: {batch_size}",
            )
            timer: PerfTimer = PerfTimer.start()
            try:
                pframe_filters: list[PTableRecordFilter] = []
                polars_filters: list[pl.Expr] = []
                if predicate is not None:
                    pframe_filter: PTableRecordFilter | None = map_predicate(
                        predicate, column_ref_to_column_id
                    )
                    if pframe_filter is not None:
                        pframe_filters.append(pframe_filter)
                    else:
                        polars_filters.append(predicate)

                new_request = CreateTableRequest(
                    src=request.src, filters=request.filters + pframe_filters
                )

                ptable = _global_cache.acquire_table(resolved_path, new_request, logger)

                table_path: str = ptable.get_path()
                table_rows: int = ptable.get_rows()
                logger and logger(
                    LogLevel.Info,
                    f'PFrame "{frame_id}" Polars source generator got table path "{table_path}", '
                    f"took {timer.elapsed()} (overall), {table_rows} rows, "
                    f"path exists: {os.path.exists(table_path)}",
                )

                if table_rows > 0:
                    column_ref_to_field: Mapping[str, str] = {}
                    fields: list[str] = ptable.get_fields()
                    specs: PTableColumnSpecs = ptable.get_spec()
                    for field, spec_item in zip(fields, specs):
                        ref: str = column_ref(spec_item)
                        column_ref_to_field[ref] = field

                    with_columns_set: set[str] = set(with_columns or [])
                    select_exprs: list[pl.Expr] = []
                    for col_ref, field in column_ref_to_field.items():
                        if not with_columns_set or col_ref in with_columns_set:
                            select_exprs.append(pl.col(field).alias(col_ref))

                    lf: pl.LazyFrame = pl.scan_parquet(
                        table_path, parallel=parallel, low_memory=low_memory
                    ).select(select_exprs)
                    if polars_filters:
                        lf = lf.filter(polars_filters)
                    if n_rows is not None:
                        lf = lf.limit(n_rows)

                    if batch_size is not None:
                        sort_exprs: list[str] = []
                        for col_ref in column_refs:
                            if not with_columns_set or col_ref in with_columns_set:
                                sort_exprs.append(col_ref)
                        # slice without sort will return continuous row batches from random offsets
                        lf = lf.sort(sort_exprs, maintain_order=True)

                        offset = 0
                        while True:
                            batch_lf: pl.LazyFrame = lf.slice(offset, batch_size)
                            offset += batch_size

                            df_batch: pl.DataFrame = batch_lf.collect()
                            if len(df_batch) == 0:
                                break

                            logger and logger(
                                LogLevel.Warning,
                                f'PFrame "{frame_id}" table path "{table_path}": '
                                f"yielding batch at offset {offset} ({len(df_batch)} rows)",
                            )
                            yield df_batch
                    else:
                        df: pl.DataFrame = lf.collect()
                        logger and logger(
                            LogLevel.Warning,
                            f'PFrame "{frame_id}" table path "{table_path}": '
                            f"yielding full data ({len(df)} rows)",
                        )
                        yield df

                logger and logger(
                    LogLevel.Info,
                    f'PFrame "{frame_id}" Polars source generator finished, '
                    f"took {timer.elapsed()} (overall)",
                )
            except Exception as e:
                logger and logger(
                    LogLevel.Error,
                    f'PFrame "{frame_id}" Polars source generator error: {e}',
                )
                raise

        lf: pl.LazyFrame = register_io_source(
            source_generator, schema=schema, is_pure=True
        )
        logger and logger(
            LogLevel.Info,
            f'PFrame "{frame_id}" registration as Polars source finished, '
            f"took {timer.elapsed()} (overall), "
            f"schema: {schema}",
        )
        return lf, _global_cache
    except Exception as e:
        logger and logger(
            LogLevel.Error,
            f'PFrame "{frame_id}" registration as Polars source error: {e}',
        )
        raise
