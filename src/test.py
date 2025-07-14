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
    dcc.Store(id='filtered-table-store'),  # <--- Add this line
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

