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
from dash import dash_table  # Add this import
from utils.helpers import get_all_storage_results, sync_web_data_to_db

# =========================
# Data Sync & Load
# =========================
# Sync web data to database if needed
sync_web_data_to_db(db_path="storage_data.db", web_data_dir="./web_data")

# Load all storage results into DataFrame
data = get_all_storage_results()
df = pd.DataFrame(data)

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
        dim1, dim2 = sorted([width, length])
        footprint = f"{dim1:g}x{dim2:g}"
        height_val = height if height is not None else np.nan
        return (footprint, height_val)
    return (np.nan, np.nan)

df[['footprint', 'height']] = df['unit_size'].apply(lambda x: pd.Series(parse_unit_size(x)))

# Helper for sorting footprints numerically, with "Parking" last
def get_footprint_sort_key(footprint):
    if footprint == "Parking":
        return float('inf')
    try:
        return float(footprint.split('x')[0])
    except Exception:
        return float('inf')

# Add sort key and sort DataFrame
df['footprint_sort'] = df['footprint'].apply(get_footprint_sort_key)
df = df.sort_values(['footprint_sort', 'footprint', 'facility_name', 'price'])

# =========================
# Dropdown & Label Setup
# =========================

# Ordered list of unique footprints for dropdowns and x-axis
ordered_footprints = (
    df['footprint']
    .drop_duplicates()
    .sort_values(key=lambda x: x.apply(get_footprint_sort_key))
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
    html.H1("Storage Unit Prices by Size"),

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
        html.Button("Reset Filters", id="reset-filters-btn", n_clicks=0, style={"margin-top": "10px"})
    ], style={"width": "50%", "margin-bottom": "20px"}),

    # Graphs side by side using flexbox
    html.Div([
        dcc.Graph(id='price-bar-graph', style={"flex": "1", "min-width": "350px"}),
        dcc.Graph(id='price-line-graph', style={"flex": "1", "min-width": "350px"})
    ], style={
        "display": "flex",
        "flexWrap": "wrap",
        "gap": "20px",
        "margin-bottom": "30px"
    }),

    # Data table always shown under graphs
    html.Div([
        html.H3("Filtered Data"),
        dash_table.DataTable(
            id='filtered-data-table',
            columns=[
                {"name": col, "id": col}
                for col in ["facility_name", "footprint", "unit_type", "price", "date_acquired"]
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
    Output('price-bar-graph', 'figure'),
    Output('price-line-graph', 'figure'),
    Output('filtered-data-table', 'data'),  # Add output for table
    Input('facility-dropdown', 'value'),
    Input('unit-size-dropdown', 'value'),
    Input('reset-filters-btn', 'n_clicks'),
    prevent_initial_call=False
)
def update_all(selected_facilities, selected_sizes, reset_clicks):
    triggered_id = ctx.triggered_id if hasattr(ctx, "triggered_id") else None

    # Reset filters if reset button is clicked
    if triggered_id == "reset-filters-btn":
        selected_facilities = []
        selected_sizes = []

    filtered_df = df.copy()
    # Filter to only the most recent date_acquired for bar chart
    if not filtered_df.empty and 'date_acquired' in filtered_df.columns:
        most_recent_date = filtered_df['date_acquired'].max()
        filtered_df_bar = filtered_df[filtered_df['date_acquired'] == most_recent_date]
    else:
        filtered_df_bar = filtered_df

    # Filter by selected facilities
    if selected_facilities:
        filtered_df_bar = filtered_df_bar[filtered_df_bar['facility_name'].isin(selected_facilities)]
        filtered_df = filtered_df[filtered_df['facility_name'].isin(selected_facilities)]

    # Update available footprints based on filtered facilities
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

    # --- Bar Chart & Color Dict ---
    FACILITY_COLORS = [
        "#2e8287", "#ef3023", "#67b471", "#17633d", "#ffc52e"
    ]
    unique_facilities = sorted(df['facility_name'].unique())
    facility_color_dict = {
        facility: FACILITY_COLORS[i % len(FACILITY_COLORS)]
        for i, facility in enumerate(unique_facilities)
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
                    customdata=[[row['unit_type']]],
                    hovertemplate=(
                        f'Facility: {row["facility_name"]}<br>'
                        f'Footprint: {row["footprint"]}<br>'
                        'Unit Type: %{customdata[0]}<br>'
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
            title="Storage Unit Prices by Size",
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
    if filtered_df.empty:
        import plotly.express as px
        line_fig = px.line(title="No Data Available")
    else:
        line_fig = go.Figure()
        # Add dummy traces for legend (one per facility)
        for facility in sorted(filtered_df['facility_name'].unique()):
            line_fig.add_trace(
                go.Scatter(
                    x=[None], y=[None],
                    mode='lines',
                    name=facility,
                    line=dict(width=2, color=facility_color_dict.get(facility, "#333333")),
                    showlegend=True,
                    legendgroup=facility
                )
            )
        # Add real traces for each (facility, footprint, unit_type)
        group_cols = ['facility_name', 'footprint', 'unit_type']
        grouped = filtered_df.groupby(group_cols)
        for (facility, footprint, unit_type), group in grouped:
            group_sorted = group.sort_values('date_acquired')
            line_fig.add_trace(
                go.Scatter(
                    x=group_sorted['date_acquired'],
                    y=group_sorted['price'],
                    mode='lines+markers',
                    name=f"{facility} - {footprint} - {unit_type}",
                    marker=dict(size=7, color=facility_color_dict.get(facility, "#333333")),
                    line=dict(width=2, color=facility_color_dict.get(facility, "#333333")),
                    customdata=group_sorted[['unit_type']],
                    hovertemplate=(
                        f'Facility: {facility}<br>'
                        f'Footprint: {footprint}<br>'
                        f'Unit Type: {unit_type}<br>'
                        'Date: %{x|%Y-%m-%d}<br>'
                        'Price: $%{y}<extra></extra>'
                    ),
                    showlegend=False,
                    legendgroup=facility
                )
            )
        line_fig.update_layout(
            title="Price History Over Time",
            xaxis_title="Date Acquired",
            yaxis_title="Price ($)",
            legend_title="Facility",
            hovermode="closest"
        )

    # Prepare filtered data for table (show all filtered rows, not just bar chart)
    table_columns = ["facility_name", "footprint", "unit_type", "price", "date_acquired"]
    filtered_table_data = filtered_df[table_columns].sort_values(
        ["facility_name", "footprint", "unit_type", "date_acquired"]
    ).to_dict("records") if not filtered_df.empty else []

    return selected_facilities, unit_size_options, selected_sizes, bar_fig, line_fig, filtered_table_data

# =========================
# Optional: Open in Browser
# =========================

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