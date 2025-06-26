import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import webbrowser
import threading
import os
from utils.helpers import get_all_storage_results
import numpy as np
import re
import pdb

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

# Data cleaning: extract footprint and height from unit_size


def parse_unit_size(size_str):
    """
    Parses a unit size string like '10x10x8', '13.5x18.5', or 'Outdoor' into (footprint, height).
    Returns (footprint, height) as strings or np.nan for missing height.
    """
    if not isinstance(size_str, str):
        return (np.nan, np.nan)
    if size_str.strip().lower() == "outdoor":
        return ("Parking", np.nan)
    # Match patterns like 13.5x18.5x8 or 13.5x18.5
    match = re.match(r'^\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)(?:\s*[xX]\s*(\d+(?:\.\d+)?))?', size_str)
    if match:
        width = match.group(1)
        length = match.group(2)
        height = match.group(3)
        footprint = f"{width}x{length}"
        height_val = height if height is not None else np.nan
        return (footprint, height_val)
    return (np.nan, np.nan)

df[['footprint', 'height']] = df['unit_size'].apply(lambda x: pd.Series(parse_unit_size(x)))
# pdb.set_trace()

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
            value=None,
            placeholder="Select facility",
            multi=False
        ),
        
        html.Label("Footprint (Size)"),
        dcc.Dropdown(
            id='unit-size-dropdown',
            options=[{"label": u, "value": u} for u in sorted(df['footprint'].unique())],
            value=None,
            placeholder="Select footprint size",
            multi=False
        )
    ], style={"width": "50%", "margin-bottom": "20px"}),

    dcc.Graph(id='price-bar-graph')
])

# Callback for filtering
@app.callback(
    Output('price-bar-graph', 'figure'),
    Input('facility-dropdown', 'value'),
    Input('unit-size-dropdown', 'value')
)
def update_graph(selected_facility, selected_size):
    filtered_df = df.copy()

    # Filter to only the most recent date_acquired
    if not filtered_df.empty and 'date_acquired' in filtered_df.columns:
        most_recent_date = filtered_df['date_acquired'].max()
        filtered_df = filtered_df[filtered_df['date_acquired'] == most_recent_date]
    
    if selected_facility:
        filtered_df = filtered_df[filtered_df['facility_name'] == selected_facility]
    if selected_size:
        filtered_df = filtered_df[filtered_df['footprint'] == selected_size]

    if filtered_df.empty:
        return px.bar(title="No Data Available")

    # Create a unique label for each bar
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df['bar_label'] = (
        filtered_df['footprint'].astype(str) +
        (filtered_df.groupby(['facility_name', 'footprint']).cumcount() + 1).astype(str)
    )

    fig = px.bar(
        filtered_df,
        x='bar_label',               # X-axis is now unique per row
        y='price',
        color='facility_name',       # Color/group by facility
        barmode='group',             # Side-by-side bars
        hover_data=['unit_type', 'date_acquired', 'footprint'],  # Add more info
        title="Unit Prices by Size and Facility",
        labels={"price": "Price ($)", "bar_label": "Unit (Facility | Size | #)", "facility_name": "Facility"}
    )

    fig.update_traces(marker_line_width=1.5)
    fig.update_layout(legend_title="Facility", xaxis_title="Unit (Facility | Size | #)", yaxis_title="Price ($)")
    return fig

# Optional: open in browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050")

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()
    app.run(debug=True)