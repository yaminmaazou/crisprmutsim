from dash import dcc


graph_config: dcc.Graph.Config = {
    "displaylogo": False,
    "scrollZoom": True,
    "toImageButtonOptions": {
        "format": "svg",
        "filename": "crisprmutsim_graph",
    },
}
