import pandas as pd


def parse_datetime_index(df_raw, date_column="date"):
    """
    Parses a specified column into datetime objects and sets it as the DataFrame index.

    This function is crucial for preparing raw data (df_raw) for time series analysis
    by ensuring the DataFrame is indexed by the correct datetime type.

    Parameters
    ----------
    df_raw : pd.DataFrame
        The raw DataFrame containing the data, including the column with date strings.
    date_column : str, optional
        The name of the column in 'df_raw' that contains the date/time information.
        Defaults to "date".

    Returns
    -------
    df_ts : pd.DataFrame
        A copy of the original DataFrame with the specified date column removed
        and set as the DatetimeIndex. Ready for time series plotting.
    original_dates : pd.Series
        The original Series containing the date strings/objects, which was used
        to create the new index.
    """

    date_parsed = pd.to_datetime(df_raw[date_column])
    df_ts = df_raw.copy()
    original_dates = df_raw[date_column]
    df_ts.drop(columns=[date_column], inplace=True)
    df_ts.set_index(date_parsed, inplace=True)

    return df_ts, original_dates
