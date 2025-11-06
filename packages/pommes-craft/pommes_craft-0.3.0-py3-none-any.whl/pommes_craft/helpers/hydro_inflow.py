import pandas as pd


def compute_weekly_inflows(
        prod_df: pd.DataFrame,
        stock_df: pd.DataFrame,
        prod_col: str = "prod_MW",
        stock_col: str = "stock_MWh",
        timestamp_col_prod: str = "timestamp",
        timestamp_col_stock: str = "week_start",
) -> pd.Series:
    """
    Compute weekly hydro inflows using weekly stock and weekly production totals.

    Args:
        prod_df (pd.DataFrame): Hourly production data with columns [timestamp_col_prod, prod_col].
        stock_df (pd.DataFrame): Weekly stock data with columns [timestamp_col_stock, stock_col].
        prod_col (str): Name of production column. Defaults to "prod_MW".
        stock_col (str): Name of stock column. Defaults to "stock_MWh".
        timestamp_col_prod (str): Timestamp column in production data.
        timestamp_col_stock (str): Timestamp column in stock data.

    Returns:
        pd.Series: Weekly inflow series indexed by week start.
    """
    # --- Ensure naive datetime indices ---
    prod_df = prod_df.copy()
    prod_df.index = pd.to_datetime(prod_df[timestamp_col_prod])
    prod_df.index = prod_df.index.tz_convert("UTC")

    stock_df = stock_df.copy()
    stock_df.index = pd.to_datetime(stock_df[timestamp_col_stock])
    stock_df.index = stock_df.index.tz_localize("UTC")

    # Aggregate production to weekly totals
    prod_weekly = prod_df[prod_col].resample("W-MON").sum()

    # Compute weekly delta stock
    delta_S = stock_df[stock_col].diff().fillna(0)

    # Align prod_weekly and delta_S
    common_index = prod_weekly.index.intersection(delta_S.index)
    prod_weekly = prod_weekly[common_index]
    delta_S = delta_S[common_index]

    # Weekly inflows: production + change in stock
    inflow_weekly = prod_weekly + delta_S

    return inflow_weekly


def interpolate_weekly_to_hourly(
        inflow_weekly: pd.Series,
        target_index: pd.DatetimeIndex,
) -> pd.Series:
    """
    Interpolate weekly inflows to hourly values.

    Args:
        inflow_weekly (pd.Series): Weekly inflows indexed by week start.
        target_index (pd.DatetimeIndex): Hourly timestamps for interpolation.
        method (str): Interpolation method. Defaults to 'linear'.

    Returns:
        pd.Series: Hourly inflows aligned with target_index.
    """
    # --- Ensure naive datetime ---
    inflow_weekly.index = pd.to_datetime(inflow_weekly.index).tz_localize(None)
    target_index = pd.to_datetime(target_index).tz_localize(None)

    # Combine indices and interpolate
    hourly_inflow = (
                        inflow_weekly
                        .reindex(target_index.union(inflow_weekly.index))
                        .interpolate(method="spline", order=2)
                        .bfill()
                        .clip(0.)
                        .reindex(target_index)
                    ) / 168.

    return hourly_inflow


def generate_hourly_inflow_dataset(
        prod_df: pd.DataFrame,
        stock_df: pd.DataFrame,
        prod_col: str = "prod_MW",
        stock_col: str = "stock_MWh",
        timestamp_col_prod: str = "timestamp",
        timestamp_col_stock: str = "week_start",
) -> pd.DataFrame:
    """
    Generate an hourly hydro inflow dataset from hourly production and weekly stock.

    Steps:
      1. Compute weekly inflows from weekly stock and weekly production totals.
      2. Interpolate weekly inflows to hourly values.
      3. Return DataFrame with hourly production and inflows.

    Args:
        prod_df (pd.DataFrame): Hourly production data.
        stock_df (pd.DataFrame): Weekly stock data.
        prod_col (str): Production column name.
        stock_col (str): Stock column name.
        timestamp_col_prod (str): Timestamp column in production data.
        timestamp_col_stock (str): Timestamp column in stock data.

    Returns:
        pd.DataFrame: Hourly dataset with columns [prod_col, inflow_MWh].
    """

    # --- Compute weekly inflows ---
    inflow_weekly = compute_weekly_inflows(
        prod_df, stock_df, prod_col, stock_col, timestamp_col_prod, timestamp_col_stock
    )

    # --- Interpolate to hourly inflows ---
    hourly_inflow = interpolate_weekly_to_hourly(
        inflow_weekly, pd.DatetimeIndex(prod_df[timestamp_col_prod])
    )

    # --- Construct final hourly dataset ---
    df_out = pd.DataFrame({
        prod_col: prod_df[prod_col].values,
        "inflow_MWh": hourly_inflow.values,
    })

    return df_out


def create_week_start(year: int) -> pd.DatetimeIndex:
    """
    Generate a DatetimeIndex of week start dates (Monday) for a given year.

    Args:
        year (int): Year for which to generate weekly start dates.

    Returns:
        pd.DatetimeIndex: Start of each week (Monday), length 52 (or 53 if ISO weeks overlap).
    """
    # First day of the year
    first_day = pd.Timestamp(f"{year}-01-01")
    # Align to the first Monday of the year
    first_monday = first_day + pd.offsets.Week(weekday=0)
    # Generate 52 weeks
    week_starts = pd.date_range(first_monday, periods=52, freq="W-MON")
    return week_starts
