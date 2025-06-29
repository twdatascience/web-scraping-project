import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import webbrowser
import threading
import os
from utils.helpers import get_all_storage_results
import numpy as np
import re
import pdb
from dash import ctx  # Add this import for callback context
from utils.helpers import sync_web_data_to_db


# sync web data to database if needed
sync_web_data_to_db(db_path="storage_data.db", web_data_dir="./web_data")

# Convert data to DataFrame
data = get_all_storage_results()
df = pd.DataFrame(data)


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

# Data cleaning: extract footprint and height from unit_size


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

def get_footprint_sort_key(footprint):
    if footprint == "Parking":
        return float('inf')
    try:
        return float(footprint.split('x')[0])
    except Exception:
        return float('inf')

df['footprint_sort'] = df['footprint'].apply(get_footprint_sort_key)
df = df.sort_values(['footprint_sort', 'footprint', 'facility_name', 'price'])

# For the dropdown and x-axis order
ordered_footprints = (
    df['footprint']
    .drop_duplicates()
    .sort_values(key=lambda x: x.apply(get_footprint_sort_key))
    .tolist()
)

df['x_group'] = df['footprint']

df['x_label'] = df['footprint'] + " | " + df['facility_name'] + " | " + df['unit_type']


footprints = df['footprint'].unique()


# Dash app
app = dash.Dash(__name__)
app.title = "Storage Pricing Dashboard"

# Layout
app.layout = html.Div([
    html.H1("Storage Unit Prices by Size"),
    
    html.Div([
        html.Label("Facility"),
        dcc.Dropdown(
            id='facility-dropdown',
            options=[{"label": f, "value": f} for f in sorted(df['facility_name'].unique())],
            value=[],
            placeholder="Select facility",
            multi=True  # Allow multiple selection
        ),
        
        html.Label("Footprint (Size)"),
        dcc.Dropdown(
            id='unit-size-dropdown',
            options=[{"label": u, "value": u} for u in ordered_footprints],
            value=[],
            placeholder="Select footprint size",
            multi=True  # Allow multiple selection
        ),
        html.Button("Reset Filters", id="reset-filters-btn", n_clicks=0, style={"margin-top": "10px"})
    ], style={"width": "50%", "margin-bottom": "20px"}),

    dcc.Graph(id='price-bar-graph')
])

# Callback for filtering and reset
@app.callback(
    Output('facility-dropdown', 'value'),
    Output('unit-size-dropdown', 'options'),
    Output('unit-size-dropdown', 'value'),
    Output('price-bar-graph', 'figure'),
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
    # Filter to only the most recent date_acquired
    if not filtered_df.empty and 'date_acquired' in filtered_df.columns:
        most_recent_date = filtered_df['date_acquired'].max()
        filtered_df = filtered_df[filtered_df['date_acquired'] == most_recent_date]
    if selected_facilities:
        filtered_df = filtered_df[filtered_df['facility_name'].isin(selected_facilities)]

    # Update available footprints based on filtered facilities
    available_footprints = (
        filtered_df['footprint']
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
        filtered_df = filtered_df[filtered_df['footprint'].isin(selected_sizes)]

    if filtered_df.empty:
        import plotly.express as px
        return selected_facilities, unit_size_options, selected_sizes, px.bar(title="No Data Available")

    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df['bar_label'] = (
        filtered_df['footprint'].astype(str) +
        (filtered_df.groupby(['facility_name', 'footprint']).cumcount() + 1).astype(str)
    )

    fig = go.Figure()

    # Define a fixed color palette
    FACILITY_COLORS = [
        "#2e8287", "#ef3023", "#67b471", "#17633d", "#ffc52e"
    ]

    # Create a dictionary mapping facility names to colors
    unique_facilities = sorted(df['facility_name'].unique())
    
    facility_color_dict = {
        facility: FACILITY_COLORS[i % len(FACILITY_COLORS)]
        for i, facility in enumerate(unique_facilities)
    }

    for i, row in filtered_df.iterrows():
        fig.add_trace(
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
                showlegend=not any([t.name == row['facility_name'] for t in fig.data])
        )
        )
    # Only show selected sizes on x-axis if any are selected, else show all available
    if selected_sizes:
        x_categories = [f for f in ordered_footprints if f in selected_sizes]
    else:
        x_categories = [f for f in ordered_footprints if f in available_footprints]

    fig.update_layout(
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
    return selected_facilities, unit_size_options, selected_sizes, fig

# Optional: open in browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050")

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()
    app.run(debug=True)