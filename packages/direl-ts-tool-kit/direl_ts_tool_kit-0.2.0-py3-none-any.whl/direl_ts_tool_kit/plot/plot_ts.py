from .plot_style import *


def plot_time_series(
    df1, variable, units="", color="BLUE_LINES", time_unit="Year", rot=90, method=True
):
    """
    Plots a time series with custom styling and dual-level grid visibility.

    This function automatically sets major and minor time-based locators
    on the x-axis based on the specified time unit, and formats the y-axis
    to use scientific notation.

    Parameters
    ----------
    df1 : pd.DataFrame
        The DataFrame containing the time series data. Must have a DatetimeIndex.
    variable : str
        The name of the column to plot. The label is automatically formatted
        (e.g., 'total_sales' becomes 'Total Sales').
    units : str, optional
        Units to display next to the variable name on the y-axis (e.g., 'USD').
        Defaults to "".
    color : str, optional
        Key corresponding to the line color in the global 'paper_colors' dictionary.
        Defaults to "BLUE_LINES".
    time_unit : str, optional
        The time granularity of the data to define x-axis tick locators.
        Options include 'Year', 'Month', 'Weekday', or 'Day'. Defaults to "Year".
    rot : int, optional
        Rotation angle (in degrees) for the x-axis tick labels. Defaults to 90.
    method : bool, optional
        Used internally for label formatting logic. Defaults to True.

    Returns
    -------
    matplotlib.figure.Figure
        The generated matplotlib figure object.

    Notes
    -----
    Major grid lines are displayed with a dashed line ('--'), and minor grid
    lines are displayed with a dotted line (':') for detailed temporal analysis.
    """

    fig, ax = plt.subplots()
    ax.plot(df1.index, df1[variable], linewidth=3, color=paper_colors[color])

    if "-" in variable:
        variable = "-".join(
            [
                j.title() if i == 0 else j.lower()
                for i, j in enumerate(variable.split("-"))
            ]
        )
    elif "_" in variable:
        variable = " ".join(
            [
                j.title() if i == 0 else j.lower()
                for i, j in enumerate(variable.split("_"))
            ]
        )
    else:
        variable = (
            " ".join(
                [
                    j.title() if i == 0 else j.lower()
                    for i, j in enumerate(variable.split())
                ]
            )
            if method
            else variable
        )

    ax.set(xlabel=f"{time_unit}", ylabel=f"{variable} {units}")
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))

    if time_unit == "Year":
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_minor_locator(mdates.MonthLocator())

    if time_unit == "Month":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator())

    if time_unit == "Weekday":
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        ax.xaxis.set_minor_locator(mdates.DayLocator())

    if time_unit == "Day":
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_minor_locator(mdates.HourLocator())

    ax.tick_params(axis="x", rotation=rot)
    ax.grid(which="both")
    ax.grid(which="minor", alpha=0.6, linestyle=":")
    ax.grid(which="major", alpha=0.8, linestyle="--")

    return fig
