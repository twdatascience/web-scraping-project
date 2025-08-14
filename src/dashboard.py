# =========================
# Imports & Constants
# =========================
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import re
import os
import threading
import webbrowser
from dash import dash_table  
from utils.helpers import get_all_storage_results, sync_web_data_to_db
from dash_extensions.enrich import DashProxy, html

# =========================
# Data Sync & Load
# =========================
# Sync web data to database if needed
sync_web_data_to_db(db_path="storage_data.db", web_data_dir="./web_data")

# Load all storage results into DataFrame
data = get_all_storage_results()
df = pd.DataFrame(data)
# print(f"[DEBUG] Loaded {len(df)} rows into initial DataFrame.")

# =========================
# Data Cleaning & Parsing
# =========================

# Convert 'date_acquired' to datetime for better plotting
df['date_acquired'] = pd.to_datetime(df['date_acquired'])

# Convert 'price' to float, remove rows where conversion fails (e.g., "Sold Out")
def is_float(val):
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False

df = df[df['price'].apply(is_float)].copy()
df['price'] = df['price'].astype(float)

# Parse unit size strings into footprint and height
def parse_unit_size(size_str):
    """
    Parses a unit size string like '10x10x8', '13.5x18.5', or 'Outdoor' into (footprint, height).
    Ensures footprint is always smaller_number x larger_number.
    Returns (footprint, height) as strings or np.nan for missing height.
    """
    if not isinstance(size_str, str):
        return (np.nan, np.nan)
    if size_str.strip().lower() == "outdoor":
        return ("Parking", np.nan)
    # Match patterns like 13.5x18.5x8 or 13.5x18.5
    match = re.match(r'^\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)(?:\s*[xX]\s*(\d+(?:\.\d+)?))?', size_str)
    if match:
        width = float(match.group(1))
        length = float(match.group(2))
        height = match.group(3)
        # Always order as smaller x larger
        # dim1, dim2 = sorted([width, length])
        # footprint = f"{dim1:g}x{dim2:g}"
        footprint = f"{width:g}x{length:g}"
        height_val = height if height is not None else np.nan
        return (footprint, height_val)
    return (np.nan, np.nan)

df[['footprint', 'height']] = df['unit_size'].apply(lambda x: pd.Series(parse_unit_size(x)))

# Append height to unit_type if height is present
def append_height_to_unit_type(row):
    if pd.notna(row['height']):
        return f"{row['unit_type']} height: {row['height']}"
    return row['unit_type']

df['unit_type'] = df.apply(append_height_to_unit_type, axis=1)

# Helper for sorting footprints numerically, with "Parking" last
def get_footprint_sort_key(footprint):
    if footprint == "Parking":
        return (float('inf'), float('inf'))
    try:
        parts = footprint.split('x')
        if len(parts) == 2:
            return (float(parts[0]), float(parts[1]))
        else:
            return (float(parts[0]), 0)
    except Exception:
        return (float('inf'), float('inf'))

# Ordered list of unique footprints for dropdowns and x-axis
ordered_footprints = (
    df['footprint']
    .drop_duplicates()
    .sort_values(key=lambda x: x.apply(lambda f: get_footprint_sort_key(f)))
    .tolist()
)

df['x_group'] = df['footprint']
df['x_label'] = df['footprint'] + " | " + df['facility_name'] + " | " + df['unit_type']

# =========================
# Dash App Setup
# =========================

app = dash.Dash(__name__)
app.title = "Storage Pricing Dashboard"

# =========================
# App Layout
# =========================

app.layout = html.Div([
    html.H1("Storage Unit Price Comparisons"),

    html.Div([
        html.Label("Facility"),
        dcc.Dropdown(
            id='facility-dropdown',
            options=[{"label": f, "value": f} for f in sorted(df['facility_name'].unique())],
            value=["Basalt Mini Storage", "StorageMart"],  # Default selected facilities
            placeholder="Select facility",
            multi=True
        ),

        html.Label("Footprint (Size)"),
        dcc.Dropdown(
            id='unit-size-dropdown',
            options=[{"label": u, "value": u} for u in ordered_footprints],
            value=[],
            placeholder="Select footprint size",
            multi=True
        ),

        html.Label("Climate Controlled"),
        dcc.Dropdown(
            id='climate-dropdown',
            options=[
                {"label": "All", "value": "all"},
                {"label": "Yes", "value": "True"},
                {"label": "No", "value": "False"}
            ],
            value="all",
            clearable=False,
            multi=False
        ),

        html.Label("Tier"),
        dcc.Dropdown(
            id='tier-dropdown',
            options=[
                {"label": "All", "value": "all"}
            ] + [
                {"label": t, "value": t}
                for t in sorted(df['tier'].dropna().unique())
                if t not in [None, "", "all"]
            ],
            value="all",
            clearable=False,
            multi=False
        ),
        html.Span(
            "Disclaimer: All tiers are assigned and may not be accurate.",
            style={"fontSize": "12px", "color": "#a00", "marginLeft": "10px"}
        ),

        html.Button("Reset Filters", id="reset-filters-btn", n_clicks=0, style={"margin-top": "10px"})
    ], style={"width": "50%", "margin-bottom": "20px"}),

    # Graphs stacked vertically
    html.Div([
        html.Div([
            html.Div(id="bar-chart-date-label", style={"fontWeight": "bold", "marginBottom": "10px"}),
            html.Button(
                "Toggle Legend", id="toggle-legend-btn", n_clicks=0,
                style={"width": "150px", "margin-bottom": "10px", "float": "right"}
            ),
        ], style={"display": "flex", "justifyContent": "space-between", "width": "100%"}),
        dcc.Graph(id='price-line-graph', style={"flex": "1", "min-width": "350px"}),
        dcc.Graph(id='price-bar-graph', style={"flex": "1", "min-width": "350px"})
    ], style={
        "display": "flex",
        "flexDirection": "column",
        "gap": "20px",
        "margin-bottom": "30px"
    }),

    # Button to download data as XLSX
    html.Div([
        html.Button("Download Data as XLSX", id="btn_xslx", n_clicks=0, style={"margin-bottom": "20px"}),
        dcc.Download(id="download_xslx")
    ], style={"textAlign": "center"}),

    # Data table always shown under graphs
    dcc.Store(id='filtered-table-store'), 
    html.Div([
        html.H3("Filtered Data"),
        dash_table.DataTable(
            id='filtered-data-table',
            columns=[
                {"name": col, "id": col}
                for col in ["facility_name", "footprint", "unit_type", "price", "date_acquired", "climate_controlled", "tier"]
                if col in df.columns
            ],
            data=[],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "5px"},
            style_header={"backgroundColor": "#f0f0f0", "fontWeight": "bold"},
        )
    ])
])

# =========================
# Callback: Filtering, Reset, and Plotting
# =========================

@app.callback(
    Output('facility-dropdown', 'value'),
    Output('unit-size-dropdown', 'options'),
    Output('unit-size-dropdown', 'value'),
    Output('climate-dropdown', 'value'),
    Output('tier-dropdown', 'value'),
    Output('price-bar-graph', 'figure'),
    Output('price-line-graph', 'figure'),
    Output('filtered-data-table', 'data'),
    Output('filtered-table-store', 'data'),
    Output('bar-chart-date-label', 'children'),  # <--- Add this line
    Input('facility-dropdown', 'value'),
    Input('unit-size-dropdown', 'value'),
    Input('climate-dropdown', 'value'),
    Input('tier-dropdown', 'value'),
    Input('reset-filters-btn', 'n_clicks'),
    Input('toggle-legend-btn', 'n_clicks'),
    prevent_initial_call=False
)
def update_all(selected_facilities, selected_sizes, selected_climate, selected_tier, reset_clicks, toggle_legend_clicks):
    triggered_id = ctx.triggered_id if hasattr(ctx, "triggered_id") else None

    # Reset filters if reset button is clicked
    if triggered_id == "reset-filters-btn":
        selected_facilities = []
        selected_sizes = []
        selected_climate = "all"
        selected_tier = "all"

    filtered_df = df.copy() 

    # print(f"[DEBUG] Filtered DataFrame after initial copy: {len(filtered_df)} rows")

    # Filter to only the most recent date_acquired for bar chart
    if not filtered_df.empty and 'date_acquired' in filtered_df.columns:
        most_recent_date = filtered_df['date_acquired'].max()
        filtered_df_bar = filtered_df[filtered_df['date_acquired'] == most_recent_date]
        bar_chart_date_label = f"Most Recent Data: {most_recent_date.strftime('%Y-%m-%d')}"
    else:
        filtered_df_bar = filtered_df
        bar_chart_date_label = "No recent date available"

    # print(f"[DEBUG] Filtered DataFrame for bar chart: {len(filtered_df_bar)} rows")

    # Filter by selected facilities
    if selected_facilities:
        filtered_df_bar = filtered_df_bar[filtered_df_bar['facility_name'].isin(selected_facilities)]
        filtered_df = filtered_df[filtered_df['facility_name'].isin(selected_facilities)]

    # print(f"[DEBUG] After facility filter: {len(filtered_df)} rows (table), {len(filtered_df_bar)} rows (bar)")

    # Filter by climate_controlled
    if selected_climate and selected_climate != "all":
        filtered_df_bar = filtered_df_bar[filtered_df_bar['climate_controlled'].astype(str) == selected_climate]
        filtered_df = filtered_df[filtered_df['climate_controlled'].astype(str) == selected_climate]

    # print(f"[DEBUG] After climate filter: {len(filtered_df)} rows (table), {len(filtered_df_bar)} rows (bar)")

    # Filter by tier
    if selected_tier and selected_tier != "all":
        filtered_df_bar = filtered_df_bar[filtered_df_bar['tier'] == selected_tier]
        filtered_df = filtered_df[filtered_df['tier'] == selected_tier]

    # print(f"[DEBUG] After tier filter: {len(filtered_df)} rows (table), {len(filtered_df_bar)} rows (bar)")

    # Update available footprints based on filtered facilities and filters
    available_footprints = (
        filtered_df_bar['footprint']
        .drop_duplicates()
        .sort_values(key=lambda x: x.apply(get_footprint_sort_key))
        .tolist()
    )
    unit_size_options = [{"label": u, "value": u} for u in available_footprints]

    # Remove any selected sizes that are no longer available
    if selected_sizes:
        selected_sizes = [s for s in selected_sizes if s in available_footprints]
    if triggered_id == "reset-filters-btn":
        selected_sizes = []

    # Further filter by selected sizes
    if selected_sizes:
        filtered_df_bar = filtered_df_bar[filtered_df_bar['footprint'].isin(selected_sizes)]
        filtered_df = filtered_df[filtered_df['footprint'].isin(selected_sizes)]

    # print(f"[DEBUG] After size filter: {len(filtered_df)} rows (table), {len(filtered_df_bar)} rows (bar)")

    # --- Bar Chart & Color Dict ---
    facility_color_dict = {
        # Assign colors to facilities in a consistent manner
        # Using a predefined set of colors for better visibility
        # Colors are assigned based on the order of unique facilities
        # This ensures that the same facility always has the same color
        # Feel free to adjust the colors as needed
        "All Hours Storage": "#2f8e93",
        "Basalt Mini Storage": "#f12e26",
        "Carbondale Mini Storage": "#67b471",
        "Sopris Self Storage": "#1a633b",
        "StorageMart": "#ffc52e",
        "StorQuest Self Storage": "#565a5e",
        # Add more facilities and their colors as needed
    }

    # --- Bar Chart ---
    if filtered_df_bar.empty:
        bar_fig = px.bar(title="No Data Available")
    else:
        filtered_df_bar = filtered_df_bar.reset_index(drop=True)
        filtered_df_bar['bar_label'] = (
            filtered_df_bar['footprint'].astype(str) +
            (filtered_df_bar.groupby(['facility_name', 'footprint']).cumcount() + 1).astype(str)
        )
        

        bar_fig = go.Figure()
        for i, row in filtered_df_bar.iterrows():
            bar_fig.add_trace(
                go.Bar(
                    x=[row['x_group']],
                    y=[row['price']],
                    name=row['facility_name'],
                    marker_color=facility_color_dict.get(row['facility_name'], "#333333"),
                    customdata=[[row['unit_type'], row.get('climate_controlled', ''), row.get('tier', ''), row.get('date_acquired', '')]],
                    hovertemplate=(
                        f'Facility: {row["facility_name"]}<br>'
                        f'Footprint: {row["footprint"]}<br>'
                        'Unit Type: %{customdata[0]}<br>'
                        'Climate Controlled: %{customdata[1]}<br>'
                        'Tier: %{customdata[2]}<br>'
                        'Date: %{customdata[3]|%Y-%m-%d}<br>'
                        'Price: $%{y}<extra></extra>'
                    ),
                    offsetgroup=row['facility_name'] + row['unit_type'],
                    legendgroup=row['facility_name'],
                    showlegend=not any([t.name == row['facility_name'] for t in bar_fig.data])
                )
            )
        if selected_sizes:
            x_categories = [f for f in ordered_footprints if f in selected_sizes]
        else:
            x_categories = [f for f in ordered_footprints if f in available_footprints]

        bar_fig.update_layout(
            title="Storage Unit Prices by Size (Most Recent Data)",
            xaxis_title="Footprint (Size)",
            yaxis_title="Price ($)",
            barmode='group',
            bargap=0.2,
            yaxis=dict(type='linear', autorange=True),
            xaxis=dict(
                categoryorder='array',
                categoryarray=x_categories
            )
        )

    # --- Line Chart ---
    show_legend = (toggle_legend_clicks or 0) % 2 == 0  # Show legend on even clicks

    if filtered_df.empty:
        import plotly.express as px
        line_fig = px.line(title="No Data Available")
    else:
        line_fig = go.Figure()
        # Add real traces for each (facility, footprint, unit_type)
        # print(f"[DEBUG] Preparing line chart with {len(filtered_df)} rows")
        # print(f"[DEBUG] Filtered DataFrame columns: {filtered_df.columns.tolist()}")
        group_cols = ['facility_name', 'footprint', 'unit_type']
        grouped = filtered_df.groupby(group_cols, dropna=False)
        for (facility, footprint, unit_type), group in grouped:
            group_sorted = group.sort_values('date_acquired')
            # Remove this check to include single-point groups
            # if len(group_sorted) < 2:
            #     continue
            # Prepare customdata for all points in this group
            customdata = group_sorted[['unit_type', 'climate_controlled', 'tier']].values
            line_fig.add_trace(
                go.Scatter(
                    x=group_sorted['date_acquired'],
                    y=group_sorted['price'],
                    mode='lines+markers',
                    name=f"{facility} - {footprint} - {unit_type}",
                    marker=dict(size=7, color=facility_color_dict.get(facility, "#333333")),
                    line=dict(width=2, color=facility_color_dict.get(facility, "#333333")),
                    customdata=customdata,
                    hovertemplate=(
                        f'Facility: {facility}<br>'
                        f'Footprint: {footprint}<br>'
                        'Unit Type: %{customdata[0]}<br>'
                        'Climate Controlled: %{customdata[1]}<br>'
                        'Tier: %{customdata[2]}<br>'
                        'Date: %{x|%Y-%m-%d}<br>'
                        'Price: $%{y}<extra></extra>'
                    ),
                    showlegend=True,
                    legendgroup=facility,
                    connectgaps=True  # Ensures lines connect even if some dates are missing
                )
            )
        line_fig.update_layout(
            title="Price History",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            legend_title="Facility",
            hovermode="closest",
            showlegend=show_legend  # Control legend visibility
        )

    # Prepare filtered data for table (show all filtered rows, not just bar chart)
    table_columns = ["facility_name", "footprint", "unit_type", "price", "date_acquired", "climate_controlled", "tier"]
    filtered_table_data = filtered_df[table_columns].sort_values(
        ["facility_name", "footprint", "unit_type", "date_acquired"]
    ).to_dict("records") if not filtered_df.empty else []

    return (
        selected_facilities,
        unit_size_options,
        selected_sizes,
        selected_climate,
        selected_tier,
        bar_fig,
        line_fig,
        filtered_table_data,
        filtered_table_data,
        bar_chart_date_label  # <--- Add this line
    )

@app.callback(
    Output("download_xslx", "data"),
    Input("btn_xslx", "n_clicks"),
    State("filtered-table-store", "data"),  # <--- Use State to get the data
    prevent_initial_call=True,
)
def generate_xlsx(n_clicks, filtered_table_data):
    if not filtered_table_data:
        return dash.no_update

    df = pd.DataFrame(filtered_table_data)
    def to_xlsx(bytes_io):
        xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")
        df.to_excel(xslx_writer, index=False, sheet_name="sheet1")
        xslx_writer.close()

    return dcc.send_bytes(to_xlsx, "data_download.xlsx")

def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050")

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()
    app.run(
        debug=True,
        dev_tools_ui=False,           # Disable Dash GUI in bottom right
        dev_tools_props_check=False   # Optional: disables extra property checks
    )

