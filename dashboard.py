# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair",
#     "folium",
#     "marimo",
#     "pandas",
# ]
# ///
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="Stations dashboard")

with app.setup:
    import io
    import urllib.request

    import altair as alt
    import folium
    import marimo as mo
    import pandas as pd

    REQUIRED_COLUMNS = (
        "station_id",
        "region",
        "lat",
        "lon",
        "elevation_m",
        "temp_mean_c",
        "precip_annual_mm",
    )
    VARIABLES = {
        "Mean temperature (°C)": "temp_mean_c",
        "Annual precipitation (mm)": "precip_annual_mm",
    }
    MAP_CENTER = (-33.0, -71.0)
    VIRIDIS = ("#440154", "#3b528b", "#21918c", "#5ec962", "#fde725")


@app.function
def load_stations(path: str) -> pd.DataFrame:
    """Load the stations table and validate its schema.

    Args:
        path: Local path or URL of the stations CSV.

    Returns:
        DataFrame with one row per station.

    Raises:
        ValueError: If required columns are missing or the table is empty.
    """
    # Read URLs as raw bytes: GitHub Pages sends Content-Encoding: gzip, the
    # browser already decompresses, and pandas would try to gunzip again.
    if path.startswith(("http://", "https://")):
        with urllib.request.urlopen(path) as response:
            source = io.BytesIO(response.read())
    else:
        source = path
    stations = pd.read_csv(source)
    missing = set(REQUIRED_COLUMNS) - set(stations.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
    if stations.empty:
        raise ValueError(f"No rows in {path}")
    return stations


@app.function
def filter_stations(
    stations: pd.DataFrame, regions: list[str], elevation_range: list[float]
) -> pd.DataFrame:
    """Keep stations in the selected regions and elevation range.

    Args:
        stations: Stations table.
        regions: Region names to keep.
        elevation_range: Inclusive [min, max] elevation in metres.

    Returns:
        Filtered copy of the stations table.
    """
    low, high = elevation_range
    mask = stations["region"].isin(regions) & stations["elevation_m"].between(
        low, high
    )
    return stations.loc[mask].reset_index(drop=True)


@app.function
def make_map(stations: pd.DataFrame, variable: str, label: str) -> folium.Map:
    """Build a point map coloured by the selected variable.

    Args:
        stations: Stations table with lat/lon columns.
        variable: Column used for the colour scale.
        label: Human-readable name of the variable.

    Returns:
        Folium map with one marker per station.
    """
    fmap = folium.Map(location=MAP_CENTER, zoom_start=6, tiles="OpenStreetMap")
    if stations.empty:
        return fmap
    values = stations[variable]
    colormap = folium.LinearColormap(
        VIRIDIS, vmin=values.min(), vmax=values.max()
    )
    colormap.caption = label
    for row in stations.itertuples(index=False):
        value = getattr(row, variable)
        folium.CircleMarker(
            location=(row.lat, row.lon),
            radius=6,
            color=colormap(value),
            fill=True,
            fill_opacity=0.85,
            tooltip=f"{row.station_id} · {row.region}: {value}",
        ).add_to(fmap)
    colormap.add_to(fmap)
    fmap.fit_bounds(
        [
            [stations["lat"].min(), stations["lon"].min()],
            [stations["lat"].max(), stations["lon"].max()],
        ]
    )
    return fmap


@app.function
def make_scatter(stations: pd.DataFrame, variable: str, label: str) -> alt.Chart:
    """Build an elevation-vs-variable scatter plot coloured by region.

    Args:
        stations: Stations table.
        variable: Column plotted on the y axis.
        label: Human-readable name of the variable.

    Returns:
        Altair chart.
    """
    return (
        alt.Chart(stations)
        .mark_circle(size=70, opacity=0.8)
        .encode(
            x=alt.X("elevation_m:Q", title="Elevation (m)"),
            y=alt.Y(f"{variable}:Q", title=label),
            color=alt.Color("region:N", title="Region"),
            tooltip=["station_id", "region", "elevation_m", variable],
        )
        .properties(height=380)
    )


@app.cell
def _():
    stations = load_stations(str(mo.notebook_location() / "public" / "stations.csv"))
    return (stations,)


@app.cell
def _(stations):
    regions = sorted(stations["region"].unique())
    elevation_max = int(stations["elevation_m"].max() // 100 + 1) * 100
    region_select = mo.ui.multiselect(options=regions, value=regions, label="Region")
    elevation_slider = mo.ui.range_slider(
        start=0,
        stop=elevation_max,
        step=100,
        value=[0, elevation_max],
        label="Elevation (m)",
        show_value=True,
    )
    variable_select = mo.ui.dropdown(
        options=VARIABLES, value=next(iter(VARIABLES)), label="Variable"
    )
    return elevation_slider, region_select, variable_select


@app.cell
def _(elevation_slider, region_select, stations):
    filtered = filter_stations(stations, region_select.value, elevation_slider.value)
    return (filtered,)


@app.cell
def _(elevation_slider, filtered, region_select, stations, variable_select):
    variable = variable_select.value
    label = variable_select.selected_key
    mo.vstack(
        [
            mo.md("# Stations dashboard"),
            mo.hstack(
                [region_select, elevation_slider, variable_select],
                justify="start",
                gap=2,
                wrap=True,
            ),
            mo.md(f"**{len(filtered)}** of {len(stations)} stations shown"),
            mo.hstack(
                [
                    mo.Html(make_map(filtered, variable, label)._repr_html_()),
                    mo.ui.altair_chart(make_scatter(filtered, variable, label)),
                ],
                widths=[1, 1],
                wrap=True,
            ),
            mo.ui.table(filtered, selection=None),
        ],
        gap=1.5,
    )
    return


if __name__ == "__main__":
    app.run()
