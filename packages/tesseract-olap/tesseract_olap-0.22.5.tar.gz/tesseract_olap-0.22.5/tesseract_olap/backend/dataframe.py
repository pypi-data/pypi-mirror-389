"""DataFrame operations for OLAP queries.

This module provides utilities for transforming and manipulating Polars DataFrames
in the context of OLAP data queries. Key functionality includes:

- Time-based period calculations: Generate lag columns and delta expressions for
  various time scales (year, quarter, month, day)
- Growth calculations: Support period-over-period, CAGR, and fixed-period growth
  calculations on time series data
- Top-K filtering: Rank and filter top K values based on specified measures and levels
- Join operations: Execute multi-step joins with caching and pagination support
- Column renaming: Apply aliases to levels and measures based on query specifications
"""

import hashlib
from datetime import datetime, timezone
from typing import Literal, Optional, TypedDict, Union

import polars as pl
from dateutil.relativedelta import relativedelta

from tesseract_olap.exceptions.query import InvalidQuery
from tesseract_olap.query import (
    AnyQuery,
    DataQuery,
    JoinIntent,
    JoinOnColumns,
    LevelField,
    PaginationIntent,
)
from tesseract_olap.schema import DataType, DimensionType, TimeScale

from .models import Result


def generate_lag_column(
    lvlfi: LevelField,
    series: pl.Series,
    delta: int,
) -> pl.Expr:
    """Generate a Polars expression for a lag of delta periods.

    Creates an expression that shifts time period values backward by a specified
    number of periods. Supports different time scales: year, quarter, month, and day.

    Args:
        lvlfi: Level field information containing time scale metadata
        series: Series with time period values to lag
        delta: Number of periods to lag by

    Returns:
        Polars expression representing lagged time values

    Raises:
        ValueError: If the level is not time-based or time format is invalid

    """
    time_scale = lvlfi.level.time_scale

    if time_scale is None:
        msg = f"Level {lvlfi.name!r} does not belong to a Time-based dimension."
        raise ValueError(msg)

    if time_scale is TimeScale.YEAR:
        # assumes integer column
        return pl.col(series.name) - delta

    if time_scale is TimeScale.QUARTER:
        template = quarter_template(str(series[0]))
        return pl.col(series.name).map_elements(
            lambda x: int(template.format(*shift_quarter(str(x), delta)))
            if series.dtype.is_integer()
            else template.format(*shift_quarter(str(x), delta)),
            return_dtype=series.dtype,
        )
    if time_scale is TimeScale.MONTH:
        # assumes integer format YYYYMM
        return pl.col(series.name).map_elements(
            lambda x: shift_month(str(x), delta),
            return_dtype=series.dtype,
        )
    # TODO: TimeScale.WEEK
    if time_scale is TimeScale.DAY:
        # assumes integer format YYYYMMDD
        return pl.col(series.name).map_elements(
            lambda x: shift_day(str(x), delta),
            return_dtype=series.dtype,
        )

    msg = f"Invalid time_id format: {series[0]}"
    raise ValueError(msg)


def parse_quarter(value: str) -> tuple[int, int]:
    """Parse a quarter identifier into year and quarter number.

    Args:
        value: Quarter identifier string (e.g., "2024Q1" or "2024-1")

    Returns:
        Tuple of (year, quarter_number)

    """
    return int(value[0:4]), int(value[4:].replace("-", "").replace("Q", ""))


def quarter_template(value: str) -> str:
    """Generate a template string for formatting quarter values.

    Extracts the format pattern from a quarter value to enable consistent
    formatting of shifted quarter values.

    Args:
        value: Original quarter identifier

    Returns:
        Template string with placeholders for year and quarter

    """
    year, quarter = parse_quarter(value)
    pre, _, post = value.rpartition(str(quarter))
    return "{}".join([pre.replace(str(year), "{}", 1), post])


def shift_quarter(time_id: str, amount: int) -> tuple[int, int]:
    """Shift a quarter identifier backward by a specified amount.

    Args:
        time_id: Original quarter identifier
        amount: Number of quarters to shift backward

    Returns:
        Tuple of (shifted_year, shifted_quarter)

    """
    year, quarter = parse_quarter(time_id)
    curr_date = datetime(year, (quarter - 1) * 3 + 1, 1, tzinfo=timezone.utc)
    prev_date = curr_date - relativedelta(months=3 * amount)
    prev_quarter = (prev_date.month - 1) // 3 + 1
    return prev_date.year, prev_quarter


def shift_month(time_id: str, amount: int) -> int:
    """Shift a month identifier backward by a specified amount.

    Args:
        time_id: Month identifier in YYYYMM format
        amount: Number of months to shift backward

    Returns:
        Shifted month identifier in YYYYMM format

    """
    current_date = datetime.strptime(f"{time_id[0:4]}-{time_id[4:6]}", "%Y-%m")
    prev_date = current_date - relativedelta(months=amount)
    return int(prev_date.strftime("%Y%m"))


def shift_day(time_id: str, amount: int) -> int:
    """Shift a day identifier backward by a specified amount.

    Args:
        time_id: Day identifier in YYYYMMDD format
        amount: Number of days to shift backward

    Returns:
        Shifted day identifier in YYYYMMDD format

    """
    date = datetime.strptime(time_id, "%Y%m%d")
    new_date = date - relativedelta(days=amount)
    return int(new_date.strftime("%Y%m%d"))


def day_delta(time_id: str, time_init: str) -> int:
    """Calculate the number of days between two date identifiers.

    Args:
        time_id: End date in YYYYMMDD format
        time_init: Start date in YYYYMMDD format

    Returns:
        Number of days difference

    """
    time_day_init = datetime.strptime(str(time_init), "%Y%m%d")
    time = datetime.strptime(time_id, "%Y%m%d")

    return (time - time_day_init).days


def month_delta(time_id: str, year_init: int, month_init: int) -> int:
    """Calculate the number of months between two month identifiers.

    Args:
        time_id: End month in YYYYMM format
        year_init: Start year
        month_init: Start month

    Returns:
        Number of months difference

    """
    year = int(time_id[0:4])
    month = int(time_id[4::])

    return (year - year_init) * 12 + (month - month_init)


def quarter_delta(time_id: str, year_init: int, quarter_init: int) -> int:
    """Calculate the number of quarters between two quarter identifiers.

    Args:
        time_id: End quarter identifier
        year_init: Start year
        quarter_init: Start quarter

    Returns:
        Number of quarters difference

    """
    year, quarter = parse_quarter(time_id)
    return (year - year_init) * 4 + (quarter - quarter_init)


def generate_delta(
    lvlfi: LevelField,
    series: pl.Series,
    time_init: Union[str, int],
) -> pl.Expr:
    """Generate a Polars expression for calculating time delta from an initial period.

    Creates an expression that computes the difference in periods between each value
    in the series and a reference initial time period. Supports different time scales.

    Args:
        lvlfi: Level field information containing time scale metadata
        series: Series with time period values
        time_init: Initial reference time period

    Returns:
        Polars expression representing time delta values

    Raises:
        ValueError: If the level is not time-based or time format is invalid

    """
    time_scale = lvlfi.level.time_scale

    if time_scale is None:
        msg = f"Level {lvlfi.name!r} does not belong to a Time-based dimension."
        raise ValueError(msg)

    if time_scale is TimeScale.YEAR:
        # assumes integer column
        return pl.col(series.name) - int(time_init)

    if time_scale is TimeScale.QUARTER:
        year_init, quarter_init = parse_quarter(str(time_init))

        return pl.col(series.name).map_elements(
            lambda x: quarter_delta(str(x), year_init, quarter_init),
            return_dtype=pl.Int64,
        )

    if time_scale is TimeScale.MONTH:
        year_init = int(str(time_init)[0:4])
        month_init = int(str(time_init)[4::])

        # assumes integer format YYYYMM
        return pl.col(series.name).map_elements(
            lambda x: month_delta(str(x), year_init, month_init),
            return_dtype=pl.Int64,
        )

    # TODO: TimeScale.WEEK
    if time_scale is TimeScale.DAY:
        # assumes integer format YYYYMMDD
        return pl.col(series.name).map_elements(
            lambda x: day_delta(str(x), str(time_init)),
            return_dtype=pl.Int64,
        )

    msg = f"Invalid time_id format: {series[0]}"
    raise ValueError(msg)


def growth_calculation(query: AnyQuery, df: pl.DataFrame) -> pl.DataFrame:
    """Calculate growth metrics on a DataFrame for OLAP queries.

    Supports three growth calculation methods:
    - Period-over-period: Compare current period to N periods ago
    - CAGR: Compound Annual Growth Rate from initial period
    - Fixed period: Compare to a specific historical period

    Adds growth columns to the DataFrame including absolute change and percentage change.

    Args:
        query: OLAP query containing growth specification
        df: DataFrame with time series data

    Returns:
        DataFrame with added growth calculation columns

    Raises:
        InvalidQuery: If required time level is not available as drilldown

    """
    # Return df unchanged if Growth does not apply
    if df.is_empty() or not isinstance(query, DataQuery) or query.growth is None:
        return df

    # define parameters
    time_name = query.growth.time_level
    measure = query.growth.measure
    method = query.growth.method
    filter_ = query.growth.filter

    try:
        hiefi, lvlfi = next(
            (hiefi, lvlfi)
            for hiefi in query.fields_qualitative
            if hiefi.dimension.dim_type is DimensionType.TIME
            for lvlfi in hiefi.drilldown_levels
            if lvlfi.name == time_name
        )
    except StopIteration:
        msg = f"Time level '{time_name}' is required as a drilldown for its own growth calculation"
        raise InvalidQuery(msg) from None

    time_id = (
        lvlfi.name
        if lvlfi.level.get_name_column(query.locale) is None
        else f"{lvlfi.name} ID"
    )
    topk = f"Top {query.topk.measure}" if query.topk else None

    # include different measures
    cols_measure = {
        measure.name
        for msrfi in query.fields_quantitative
        for measure in msrfi.measure.and_submeasures()
    }
    cols_timelevels = {
        column.alias
        for lvlfi in hiefi.drilldown_levels
        for column in lvlfi.iter_columns(query.locale)
    }
    cols_drill_without_time_measure = set(df.columns) - (
        {topk, *cols_measure, *cols_timelevels}
    )

    if method[0] == "period":
        amount = method[1]

        expr_prev_period = generate_lag_column(lvlfi, df[time_id], amount)
        df_current = df.with_columns(expr_prev_period.alias("time_prev"))

        df = df_current.join(
            # filter the time_prev column string if it exists
            df.select([*cols_drill_without_time_measure, time_id, measure]).rename(
                {time_id: "time_prev", measure: "previous_measure"},
            ),
            on=[*cols_drill_without_time_measure, "time_prev"],
            how="left",
        )

        expr_prev_measure = pl.col("previous_measure").cast(pl.Float64)
        # calculate the absolute change
        col_growth_value = pl.col(measure).cast(pl.Float64) - expr_prev_measure
        # calculate the percentage change
        col_growth = col_growth_value / expr_prev_measure

        df = df.with_columns(
            col_growth_value.alias(f"{measure} Growth Value"),
            col_growth.alias(f"{measure} Growth"),
        )

        # filter the base periods for which growth cannot be calculated
        if filter_:
            # the number of periods that would be filtered depends on the amount
            # so if we are using a value less than the time in the data as the
            # base period, it is discarded
            time_min = df.select(pl.min(time_id)).item()
            df = df.filter(pl.col("time_prev") >= time_min)

    elif method[0] == "cagr":
        time_init = df.select(pl.min(time_id)).item()

        df_init = df.filter(pl.col(time_id) == time_init).rename(
            {measure: "previous_measure", time_id: "time_prev"},
        )

        df = df.with_columns(pl.lit(time_init).alias("time_prev"))

        df = df.join(
            df_init,
            on=[*cols_drill_without_time_measure, "time_prev"],
            how="left",
        )

        expr_delta = generate_delta(lvlfi, df[time_id], time_init)
        df = df.with_columns(expr_delta.alias("delta"))

        # calculate cagr
        col_growth = (
            (pl.col(measure) / pl.col("previous_measure")) ** (1 / pl.col("delta"))
        ) - 1

        # comparing equal final and initial periods, there is no time variation and growth should not be calculated
        df = df.with_columns(
            pl.when(pl.col("delta") != 0)
            .then(col_growth.cast(pl.Float64).alias(f"{measure} Growth"))
            .otherwise(None),
        )

        # filter the base periods for which growth cannot be calculated
        if filter_:
            df = df.filter(pl.col(time_id) != time_init)

    else:
        type_caster = lvlfi.level.key_type.get_caster()
        member_key = type_caster(method[1])

        if len(cols_drill_without_time_measure) == 0:
            # create a "dummy" column in case there are no columns for the join
            df = df.with_columns([pl.lit(1).alias("dummy")])
            cols_drill_without_time_measure.add("dummy")

        # first, we get the values ​​at fixed time per group
        df_fixed = (
            df.filter(pl.col(time_id) == member_key)
            .select([*cols_drill_without_time_measure, measure])
            .rename({measure: "previous_measure"})
        )

        # join the fixed values ​​to the original df
        df = df.join(df_fixed, on=list(cols_drill_without_time_measure), how="left")

        # calculate the absolute change with a conditional
        col_growth_value = (
            pl.when(pl.col(time_id) < member_key)
            .then(
                pl.col("previous_measure").cast(pl.Float64)
                - pl.col(measure).cast(pl.Float64),
            )
            .otherwise(
                pl.col(measure).cast(pl.Float64)
                - pl.col("previous_measure").cast(pl.Float64),
            )
        )

        # calculate the percentage change with a conditional
        col_growth = (
            pl.when(pl.col(time_id) < member_key)
            .then(col_growth_value / pl.col(measure).cast(pl.Float64))
            .otherwise(col_growth_value / pl.col("previous_measure").cast(pl.Float64))
        )

        df = df.with_columns(
            col_growth_value.alias(f"{measure} Growth Value"),
            col_growth.alias(f"{measure} Growth"),
        )

        # filter the base periods for which growth cannot be calculated
        if filter_:
            df = df.filter(pl.col(time_id) != member_key)

    # remove temporary column 'previous measure' and 'dummy'
    columns_to_drop = ["previous_measure", "time_prev", "dummy", "delta"]
    existing_columns = [col for col in columns_to_drop if col in df.columns]
    df = df.drop(existing_columns)

    return df


def topk_calculation(query: AnyQuery, df: pl.DataFrame) -> pl.DataFrame:
    """Calculate and filter top-K values based on specified measures and levels.

    Ranks values within groups defined by levels and filters to the top K results.
    Only applies when growth calculations are present in the query.

    Args:
        query: OLAP query containing topK specification
        df: DataFrame to rank and filter

    Returns:
        DataFrame filtered to top K values with ranking column added

    """
    if df.is_empty() or not isinstance(query, DataQuery) or query.topk is None:
        return df

    # Calculate topK on dataframe if growth is requested
    if not query.growth:
        return df

    topk_measure = query.topk.measure
    topk_levels = query.topk.levels
    topk_colname = f"Top {topk_measure}"
    topk_desc = query.topk.order == "desc"

    return (
        df.with_columns(
            pl.col(topk_measure)
            .rank(method="dense", descending=topk_desc)
            .over(topk_levels)
            .alias(topk_colname),
        )
        .filter(pl.col(topk_colname) <= query.topk.amount)
        .sort((*topk_levels, topk_measure), descending=topk_desc)
    )


class JoinParameters(TypedDict, total=False):
    """Parameters for Polars DataFrame join operations.

    All fields are optional to support different join configurations.
    """

    on: Union[str, list[str]]
    left_on: Union[str, list[str]]
    right_on: Union[str, list[str]]
    coalesce: Optional[bool]
    nulls_equal: bool
    suffix: str
    validate: Literal["m:m", "m:1", "1:m", "1:1"]


class JoinStep:
    """Represents a step in a multi-stage join operation with caching support.

    Maintains join state including data, cache keys, and validation statuses
    to enable efficient chained join operations with proper cache management.
    """

    data: pl.DataFrame
    keys: list[str]
    statuses: list[str]

    def __init__(
        self,
        data: pl.DataFrame,
        *,
        keys: list[str],
        statuses: list[str],
    ):
        """Initialize a join step with data and metadata.

        Args:
            data: DataFrame result of join operation
            keys: List of cache keys from joined results
            statuses: List of cache status strings from joined results

        """
        self.data = data
        self.keys = keys
        self.statuses = statuses

    def join_with(self, result: Result[pl.DataFrame], join: JoinIntent):
        """Perform a join with another result using join intent specification.

        Args:
            result: Result to join with
            join: Join configuration specifying how to join

        Returns:
            New JoinStep with joined data and updated metadata

        """
        params: JoinParameters = {
            "suffix": join.suffix or "_",
            "validate": join.validate_relation,
            "nulls_equal": join.join_nulls,
            "coalesce": join.coalesce,
        }

        if isinstance(join.on, (str, list)):
            params.update(on=join.on)
        elif isinstance(join.on, JoinOnColumns):
            params.update(left_on=join.on.left_on, right_on=join.on.right_on)

        return JoinStep(
            self.data.join(result.data, how=join.how.value, **params),
            keys=[*self.keys, result.cache["key"]],
            statuses=[*self.statuses, result.cache["status"]],
        )

    def get_result(self, pagi: PaginationIntent):
        """Generate final result with pagination and cache metadata.

        Args:
            pagi: Pagination intent specifying offset and limit

        Returns:
            Result object with paginated data, column types, and cache information

        """
        df = self.data

        cache_key = "/".join(self.keys).encode("utf-8")
        return Result(
            data=df.slice(pagi.offset, pagi.limit or None),
            columns={
                k: DataType.from_polars(v)
                for k, v in dict(zip(df.columns, df.dtypes)).items()
            },
            cache={
                "key": hashlib.md5(cache_key, usedforsecurity=False).hexdigest(),
                "status": ",".join(self.statuses),
            },
            page={"limit": pagi.limit, "offset": pagi.offset, "total": df.height},
        )

    @classmethod
    def new(cls, result: Result[pl.DataFrame]):
        """Create a new JoinStep from an initial result.

        Args:
            result: Initial result to start the join chain

        Returns:
            New JoinStep initialized with result data and metadata

        """
        return cls(
            result.data,
            keys=[result.cache["key"]],
            statuses=[result.cache["status"]],
        )


def rename_columns(query: DataQuery, df: pl.DataFrame) -> pl.DataFrame:
    """Apply column aliases to DataFrame based on query specifications.

    Renames level and measure columns according to aliases defined in the query.
    Handles both regular columns and derived columns (ID columns, growth metrics,
    rankings, top-K indicators).

    Args:
        query: Data query containing alias specifications
        df: DataFrame to rename

    Returns:
        DataFrame with columns renamed according to aliases

    """
    aliases_level = {
        template.format(name=lvlfi.level.name): template.format(name=lvlfi.column_alias)
        for hiefi in query.fields_qualitative
        for lvlfi in hiefi.drilldown_levels
        if lvlfi.column_alias is not None
        for template in ("{name}", "{name} ID")
    }
    aliases_level_id = {
        f"{key} ID": f"{value} ID"
        for key, value in aliases_level.items()
        if f"{key} ID" in df.columns
    }
    aliases_measure = {
        measure.name: measure.name.replace(msrfi.measure.name, msrfi.column_alias)
        for msrfi in query.fields_quantitative
        if msrfi.column_alias
        for measure in msrfi.measure.and_submeasures()
    }
    aliases_measure_extras = {
        template.format(name=msrfi.measure.name): template.format(
            name=msrfi.column_alias,
        )
        for msrfi in query.fields_quantitative
        if msrfi.column_alias
        for template in (
            "{name} Ranking",
            "Top {name}",
            "{name} Growth",
            "{name} Growth Value",
        )
    }
    aliases = {
        **aliases_level,
        **aliases_level_id,
        **aliases_measure,
        **aliases_measure_extras,
    }
    return df.rename(aliases, strict=False)
