from dash import Dash, html
import dash_cytoscape as cyto

app = Dash(__name__)

app.layout = html.Div([
    html.P("Dash Cytoscape:"),
    cyto.Cytoscape(
        id='network-graphs-x-cytoscape',
        elements=[
            {'data': {'id': 'ca', 'label': 'Canada'}}, 
            {'data': {'id': 'on', 'label': 'Ontario'}}, 
            {'data': {'id': 'qc', 'label': 'Quebec'}},
            {'data': {'source': 'ca', 'target': 'on'}}, 
            {'data': {'source': 'ca', 'target': 'qc'}}
        ],
        layout={'name': 'breadthfirst'},
        style={'width': '1920px', 'height': '1080px'}
    )
])


if __name__ == "__main__":
    app.run_server(debug=True)
