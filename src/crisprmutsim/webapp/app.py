import json
import os
import dash
from dash import ALL, MATCH, Dash, Input, Output, State, callback, html, dcc
from dash.exceptions import PreventUpdate

import crisprmutsim.CRISPR.storage as db


app = Dash(
    __name__,
    use_pages=True,
)


app.layout = html.Div(
    [
        dcc.Store(id="signal--loaded", data=False),
        dcc.Store(id="data--db_files", data=[]),
        dcc.Store(id="data--db_ids", data={}),
        dcc.Location(id="current-url"),
        html.H2("CRISPR Mutation Simulation and Analysis"),
        html.Div(
            id="navbar",
            children=[
                dcc.Link("Home/Simulation", href="/", style={"margin-right": "10px"}),
                # dcc.Link(
                #     "Event Timelines", href="/timelines", style={"margin-right": "10px"}
                # ),
                # dcc.Link(
                #     "Event Diff", href="/event-diff", style={"margin-right": "10px"}
                # ),
                dcc.Link(
                    "Dataset Statistics",
                    href="/dataset-stats",
                    style={"margin-right": "10px"},
                ),
                dcc.Link("Array View", href="/array-view"),
            ],
        ),
        html.Br(),
        html.Div(
            dash.page_container,
            style={
                "max-width": "1200px",
                "margin-left": "auto",
                "margin-right": "auto",
                "padding-left": "20px",
                "padding-right": "20px",
            },
        ),
    ]
)


folder: str = ""
db_files: list[str] = []
db_ids: dict[str, list[str]] = {}


# load db list into browser cache (should be guaranteed to be filled since run() is called before app.run())
@app.callback(
    Output("signal--loaded", "data"),
    Output("data--db_files", "data"),
    Output("data--db_ids", "data"),
    Input("signal--loaded", "data"),
)
def update_on_load(loaded):
    if loaded:
        raise PreventUpdate
    return True, db_files, db_ids


@callback(
    Output({"type": "file-dropdown", "page": MATCH}, "options"),
    Input("signal--loaded", "data"),
    State("data--db_files", "data"),
)
def update_file_options(loaded, db_files):
    if not loaded or not db_files:
        raise PreventUpdate
    return db_files


@callback(
    Output({"type": "array-length-slider", "page": MATCH}, "min"),
    Output({"type": "array-length-slider", "page": MATCH}, "max"),
    Output({"type": "array-length-slider", "page": MATCH}, "value"),
    Output({"type": "array-length-min-input", "page": MATCH}, "min"),
    Output({"type": "array-length-min-input", "page": MATCH}, "max"),
    Output({"type": "array-length-min-input", "page": MATCH}, "value"),
    Output({"type": "array-length-max-input", "page": MATCH}, "min"),
    Output({"type": "array-length-max-input", "page": MATCH}, "max"),
    Output({"type": "array-length-max-input", "page": MATCH}, "value"),
    Output({"type": "repeat-length-slider", "page": MATCH}, "min"),
    Output({"type": "repeat-length-slider", "page": MATCH}, "max"),
    Output({"type": "repeat-length-slider", "page": MATCH}, "value"),
    Output({"type": "repeat-length-min-input", "page": MATCH}, "min"),
    Output({"type": "repeat-length-min-input", "page": MATCH}, "max"),
    Output({"type": "repeat-length-min-input", "page": MATCH}, "value"),
    Output({"type": "repeat-length-max-input", "page": MATCH}, "min"),
    Output({"type": "repeat-length-max-input", "page": MATCH}, "max"),
    Output({"type": "repeat-length-max-input", "page": MATCH}, "value"),
    Output({"type": "cas-type-filter", "page": MATCH}, "options"),
    Output({"type": "cas-type-filter", "page": MATCH}, "value"),
    Output({"type": "cas-individual-buttons", "page": MATCH}, "children"),
    Input({"type": "file-dropdown", "page": MATCH}, "value"),
    State({"type": "file-dropdown", "page": MATCH}, "id"),
)
def update_filters(filename, file_dropdown_id):
    if filename is None:
        raise PreventUpdate

    with db.database(filename) as con:
        min_array_length, max_array_length = db.get_min_max_array_length(con)
        min_repeat_length, max_repeat_length = db.get_min_max_repeat_length(con)
        cas_types = db.get_cas_types(con)

    individual_buttons = [
        html.Button(
            cas_type,
            id={
                "type": "cas-individual-button",
                "page": file_dropdown_id["page"],
                "index": cas_type,
            },
            n_clicks=0,
            style={"marginRight": "5px"},
        )
        for cas_type in cas_types
    ]

    return (
        # array length slider
        min_array_length,
        max_array_length,
        [min_array_length, max_array_length],
        # array length min input
        min_array_length,
        max_array_length,
        min_array_length,
        # array length max input
        min_array_length,
        max_array_length,
        max_array_length,
        # repeat length slider
        min_repeat_length,
        max_repeat_length,
        [min_repeat_length, max_repeat_length],
        # repeat length min input
        min_repeat_length,
        max_repeat_length,
        min_repeat_length,
        # repeat length max input
        min_repeat_length,
        max_repeat_length,
        max_repeat_length,
        # cas types and selection
        cas_types,
        cas_types,
        individual_buttons,
    )


@callback(
    Output(
        {"type": "array-length-slider", "page": MATCH}, "value", allow_duplicate=True
    ),
    Output(
        {"type": "array-length-min-input", "page": MATCH}, "value", allow_duplicate=True
    ),
    Output(
        {"type": "array-length-max-input", "page": MATCH}, "value", allow_duplicate=True
    ),
    Input({"type": "array-length-slider", "page": MATCH}, "value"),
    Input({"type": "array-length-min-input", "page": MATCH}, "value"),
    Input({"type": "array-length-max-input", "page": MATCH}, "value"),
    prevent_initial_call=True,
)
def sync_array_length_filters(slider_value, min_input, max_input):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    triggered_prop = json.loads(ctx.triggered[0]["prop_id"].rstrip(".value"))["type"]

    if triggered_prop == "array-length-slider":
        return slider_value, slider_value[0], slider_value[1]
    elif triggered_prop == "array-length-min-input":
        if min_input is not None and max_input is not None:
            return [min_input, max_input], min_input, max_input
    elif triggered_prop == "array-length-max-input":
        if min_input is not None and max_input is not None:
            return [min_input, max_input], min_input, max_input

    raise PreventUpdate


@callback(
    Output(
        {"type": "repeat-length-slider", "page": MATCH}, "value", allow_duplicate=True
    ),
    Output(
        {"type": "repeat-length-min-input", "page": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Output(
        {"type": "repeat-length-max-input", "page": MATCH},
        "value",
        allow_duplicate=True,
    ),
    Input({"type": "repeat-length-slider", "page": MATCH}, "value"),
    Input({"type": "repeat-length-min-input", "page": MATCH}, "value"),
    Input({"type": "repeat-length-max-input", "page": MATCH}, "value"),
    prevent_initial_call=True,
)
def sync_repeat_length_filters(slider_value, min_input, max_input):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    triggered_prop = json.loads(ctx.triggered[0]["prop_id"].rstrip(".value"))["type"]

    if triggered_prop == "repeat-length-slider":
        return slider_value, slider_value[0], slider_value[1]
    elif triggered_prop == "repeat-length-min-input":
        if min_input is not None and max_input is not None:
            return [min_input, max_input], min_input, max_input
    elif triggered_prop == "repeat-length-max-input":
        if min_input is not None and max_input is not None:
            return [min_input, max_input], min_input, max_input

    raise PreventUpdate


@callback(
    Output({"type": "cas-type-filter", "page": MATCH}, "value", allow_duplicate=True),
    Input({"type": "cas-select-all", "page": MATCH}, "n_clicks"),
    Input({"type": "cas-select-none", "page": MATCH}, "n_clicks"),
    Input(
        {"type": "cas-individual-button", "page": MATCH, "index": ALL},
        "n_clicks",
    ),
    State({"type": "cas-type-filter", "page": MATCH}, "options"),
    State({"type": "cas-individual-button", "page": MATCH, "index": ALL}, "id"),
    prevent_initial_call=True,
)
def update_cas_selection(
    select_all_clicks,
    select_none_clicks,
    individual_clicks,
    cas_options,
    individual_ids,
):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    triggered_prop = json.loads(ctx.triggered[0]["prop_id"].rstrip(".n_clicks"))
    triggered_button = triggered_prop["type"]

    if triggered_button == "cas-select-all":
        return cas_options
    elif triggered_button == "cas-select-none":
        return []
    else:
        return [triggered_prop["index"]]


@callback(
    Output({"type": "pattern-filter", "page": MATCH}, "value", allow_duplicate=True),
    Input({"type": "pattern-select-all", "page": MATCH}, "n_clicks"),
    Input({"type": "pattern-select-none", "page": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def update_pattern_selection(select_all_clicks, select_none_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_button = json.loads(ctx.triggered[0]["prop_id"].rstrip(".n_clicks"))["type"]

    if trigger_button == "pattern-select-all":
        return [0, 1, 2, 3, 4, 5, 6]
    elif trigger_button == "pattern-select-none":
        return []

    raise PreventUpdate


def run(folder_path: str = "."):
    # hacky way to set db lists before the dash app runs (dash multipage caching quirks)
    global folder, db_files, db_ids

    folder = folder_path

    # get all db filenames
    db_files = sorted([f for f in os.listdir(folder) if f.endswith(".db")])

    for db_file in db_files:
        with db.database(os.path.join(folder, db_file)) as con:
            try:
                ids = con.execute("SELECT id FROM arrays").fetchall()
                db_ids[db_file] = [id[0] for id in ids]
            except Exception as e:
                ...

    app.run(debug=True)
