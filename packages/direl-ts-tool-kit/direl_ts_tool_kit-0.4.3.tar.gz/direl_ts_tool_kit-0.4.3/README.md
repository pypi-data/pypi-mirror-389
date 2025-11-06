# direl-ts-tool-kit: A Toolbox for Time Series Analysis and Visualization
A lightweight Python library developed to streamline common tasks in time series processing, including data preparation,
visualization with a consistent aesthetic style, and handling irregular indices.

## Key features and functions

The library provides the following key functionalities, primarily centered around data preparation and plotting.

### Data preparation and index management

| Function                                          | Description                                                                                                                                                                                                       |
|---------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| parse_datetime_index(df_raw, date_column, format) | Converts a specified column (defaults to "date") from a raw DataFrame into a proper DatetimeIndex. It handles specific format strings to ensure correct date parsing, and returns the cleaned, indexed DataFrame. |
| generate_dates(df_ts, freq)                       | Creates a complete and regular pd.DatetimeIndex spanning from the first to the last date found in the input DataFrame's index. This is primarily used to define a target index for reindexing operations.         |
| reindex_and_aggregate(df_ts, column_name)         | Aligns an irregularly indexed time series DataFrame to a regular frequency. It aggregates data within each time step (e.g., calculates the mean) and fills any resulting time gaps with NaN values.               |

### Visualization and styling

| Function / Object                      | Description                                                                                                                                                                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| plot_time_series(df_ts, variable, ...) | Generates a customizable time series plot using Matplotlib. It automatically handles x-axis localization based on time_unit (Year, Month, etc.), applies a consistent aesthetic style, and supports automatic formatting of the Y-axis label. |
| paper_colors (Dictionary)              | A global dictionary containing a predefined palette of high-contrast, professional color codes (hex values). These color keys (e.g., "BLUE_LINES", "ORANGE_BARS") are used to ensure visual consistency across all generated plots.           |
