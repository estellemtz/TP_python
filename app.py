# %%
import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd

# Lecture des données
data_path = r"C:\Users\33783\Downloads\data.csv"
sales_data = pd.read_csv(data_path)
sales_data.columns = sales_data.columns.str.strip()
sales_data["Date"] = pd.to_datetime(sales_data["Date"], errors='coerce')
sales_data = sales_data.head(5000)

locations = sorted(sales_data["Location"].dropna().unique())

# App Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([

    # HEADER avec fond bleu  + filtre à droite
    dbc.Row([
        dbc.Col(html.H2("ECAP Store", className="text-white"),
                width=9, style={"backgroundColor": "#b3d9f5", "padding": "20px"}),

        dbc.Col(
            dcc.Dropdown(
                id="location-filter",
                options=[{"label": loc, "value": loc} for loc in locations],
                value=[locations[0]],
                multi=True,
                placeholder="Choisissez des zones"
            ),
            width=3,
            style={"backgroundColor": "#b3d9f5", "padding": "20px"}
        )
    ], className="mb-2"),

    # Indicateurs dynamiques à gauche + Line chart à droite
dbc.Row([
    dbc.Col([
        dbc.Row([
            dbc.Col(dbc.Card([
                html.H4("Chiffre d'affaires total", className="text-center"),
                html.H1(id="ca-total", className="text-center"),
                html.H5(id="ca-evolution", className="text-center")
            ], body=True), width=6),

            dbc.Col(dbc.Card([
                html.H4("Quantité vendue", className="text-center"),
                html.H1(id="quantite-total", className="text-center"),
                html.H5(id="quantite-evolution", className="text-center")
            ], body=True), width=6),
        ])
    ], width=6),

    dbc.Col(
        dcc.Graph(id="line-chart", style={"height": "300px"}),
        width=6
    )
], className="mt-1"),

    # Graphique horizontal (empilé) à gauche + tableau à droite
    dbc.Row([
        dbc.Col(dcc.Graph(id="bar-chart"), width=6),

        dbc.Col([
            html.H5("Table des 50 dernières ventes", className="mb-2"),
            dash_table.DataTable(
                id="sales-table",
                columns=[{"name": col, "id": col} for col in sales_data.columns],
                data=sales_data.to_dict('records'),
                page_size=10,
                filter_action='native',
                sort_action='native',
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
            )
        ], width=6)
    ])
], fluid=True)


# CALLBACK principal
@app.callback(
    [Output("bar-chart", "figure"),
     Output("line-chart", "figure"),
     Output("sales-table", "data"),
     Output("ca-total", "children"),
     Output("ca-evolution", "children"),
     Output("quantite-total", "children"),
     Output("quantite-evolution", "children")],
    [Input("location-filter", "value")]
)
def update_dashboard(selected_locations):
    filtered = sales_data.copy()
    if selected_locations:
        filtered = filtered[filtered["Location"].isin(selected_locations)]
    # --- BAR CHART : Ventes empilées H/F par catégorie ---
    top_categories = (
        filtered.groupby("Product_Category")["Quantity"]
        .sum().sort_values(ascending=False).head(10).index
    )
    top_data = filtered[filtered["Product_Category"].isin(top_categories)]
    bar_chart = go.Figure()
    colors = {"M": "blue", "F": "red"}

    for gender in ["F", "M"]:
        gender_data = top_data[top_data["Gender"] == gender]
        grouped = gender_data.groupby("Product_Category")["Quantity"].sum().reindex(top_categories).fillna(0)
        bar_chart.add_trace(go.Bar(
            x=grouped.values,
            y=top_categories,
            name="Femme" if gender == "F" else "Homme",
            orientation='h',
            marker_color=colors[gender]
        ))

    bar_chart.update_layout(
        title="Frequence des 10 meilleures ventes",
        barmode='stack',
        xaxis_title="Total vente",
        yaxis_title="Catégorie du produit",
        height=450,  
        margin=dict(t=30, b=20, l=100, r=20)  
)
    

    # --- LINE CHART : CA par semaine ---
    if "Offline_Spend" in filtered.columns:
        weekly = filtered.groupby(pd.Grouper(key="Date", freq="W"))["Offline_Spend"].sum().reset_index()
        line_chart = go.Figure([go.Scatter(
            x=weekly["Date"], y=weekly["Offline_Spend"], mode='lines', line=dict(color="blue")
        )])
        line_chart.update_layout(
            title="Evolution du chiffre d'affaire par semaine",
            xaxis_title="Semaine",
            yaxis_title="Chiffre d'affaire"
        )
    else:
        line_chart = go.Figure()

    # --- KPI 1 : Chiffre d'affaires total et évolution ---
    current_month = filtered[filtered["Date"].dt.month == filtered["Date"].max().month]
    last_month = filtered[filtered["Date"].dt.month == (filtered["Date"].max().month - 1)]

    ca_current = current_month["Offline_Spend"].sum()
    ca_last = last_month["Offline_Spend"].sum()
    ca_delta = ca_current - ca_last
    ca_sign = "▲" if ca_delta >= 0 else "▼"
    ca_color = "text-success" if ca_delta >= 0 else "text-danger"

    ca_display = f"{ca_current/1000:.0f}k"
    ca_delta_display = f"{ca_sign} {abs(ca_delta)/1000:.0f}k"

    # --- KPI 2 : Quantité totale et évolution ---
    qte_current = current_month["Quantity"].sum()
    qte_last = last_month["Quantity"].sum()
    qte_delta = qte_current - qte_last
    qte_sign = "▲" if qte_delta >= 0 else "▼"
    qte_color = "text-success" if qte_delta >= 0 else "text-danger"

    qte_display = f"{qte_current:.0f}"
    qte_delta_display = f"{qte_sign} {abs(qte_delta):.0f}"

    return (
        bar_chart,
        line_chart,
        filtered.to_dict('records'),
        ca_display,
        html.H5(ca_delta_display, className=f"{ca_color} text-center"),
        qte_display,
        html.H5(qte_delta_display, className=f"{qte_color} text-center")
    )
if __name__ == '__main__':
    app.run_server(debug=True, port=8055, jupyter_mode='external')



