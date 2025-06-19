import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import sqlite3
import webbrowser
import threading
from utils.helpers import get_all_storage_results

# Convert data to DataFrame
data = get_all_storage_results()
df = pd.DataFrame(data)


# Convert 'date_acquired' to datetime for better plotting
df['date_acquired'] = pd.to_datetime(df['date_acquired'])

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
        
        html.Label("Unit Size"),
        dcc.Dropdown(
            id='unit-size-dropdown',
            options=[{"label": u, "value": u} for u in sorted(df['unit_size'].unique())],
            value=None,
            placeholder="Select unit size",
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
    
    if selected_facility:
        filtered_df = filtered_df[filtered_df['facility_name'] == selected_facility]
    if selected_size:
        filtered_df = filtered_df[filtered_df['unit_size'] == selected_size]

    if filtered_df.empty:
        return px.bar(title="No Data Available")

    fig = px.bar(
        filtered_df,
        x='unit_size',
        y='price',
        color='facility_name',
        barmode='group',
        hover_data=['unit_type'],
        title="Unit Prices by Size and Facility",
        labels={"price": "Price ($)", "unit_size": "Unit Size", "facility_name": "Facility"}
    )

    fig.update_traces(marker_line_width=1.5)
    fig.update_layout(legend_title="Facility", xaxis_title="Unit Size", yaxis_title="Price ($)")
    return fig

# Optional: open in browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=True)