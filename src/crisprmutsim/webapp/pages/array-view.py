import dash
from dash import callback, dcc, html, Input, Output
import plotly.graph_objects as go

from crisprmutsim.CRISPR.crispr_array import CRISPRArray
import crisprmutsim.CRISPR.storage as db
from crisprmutsim.webapp.config.graph_config import graph_config
from crisprmutsim.webapp.layouts.dataset_filter import dataset_filter_layout


dash.register_page(__name__)


def generate_figure(array: CRISPRArray):
    array_length = array.repeat_stats.array_length
    repeat_length = array.repeat_stats.repeat_length
    consensus = array.repeat_stats.consensus_repeat

    all_sequences = [consensus] + list(array.as_raw_array())
    row_labels = ["Consensus"] + [f"Repeat {i}" for i in range(array_length)]
    z_data = []
    text_display = []

    for i, seq in enumerate(all_sequences):
        z_row = []
        text_row = []
        for j in range(repeat_length):
            base = seq[j]
            if i == 0:
                z_row.append(0.5)
                text_row.append(base)
            else:
                is_mismatch = base != consensus[j]
                z_row.append(1.0 if is_mismatch else 0.0)
                text_row.append(base if is_mismatch else "")
        z_data.append(z_row)
        text_display.append(text_row)

    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=[f"{i}" for i in range(repeat_length)],
            y=row_labels,
            text=text_display,
            texttemplate="%{text}",
            hoverinfo="skip",
            colorscale=[[0, "white"], [0.5, "lightblue"], [1, "salmon"]],
            zmin=0,
            zmax=1,
            showscale=False,
        )
    )

    fig.update_layout(
        margin_t=15,
        xaxis_title="Position in Repeat",
        yaxis_title="Sequence",
        xaxis_range=[-0.5, repeat_length - 0.5],
        yaxis_range=[array_length + 0.5, -0.5],
    )

    return fig


def layout():
    return html.Div(
        [
            html.H3(f"CRISPR array repeat view"),
            dataset_filter_layout(__name__),
            html.Div(
                [
                    html.Label("ID/Name:"),
                    dcc.Dropdown([], None, id="array-view--id-dropdown"),
                ],
            ),
            html.Div(
                id="array-view--array-info",
                style={
                    "paddingTop": "15px",
                    "paddingBottom": "15px",
                    "fontSize": "16px",
                },
            ),
            html.Div(
                id="array-view--figure-container",
            ),
        ]
    )


@callback(
    Output("array-view--id-dropdown", "options"),
    Input({"type": "file-dropdown", "page": __name__}, "value"),
    Input({"type": "array-length-slider", "page": __name__}, "value"),
    Input({"type": "repeat-length-slider", "page": __name__}, "value"),
    Input({"type": "cas-type-filter", "page": __name__}, "value"),
    Input({"type": "pattern-filter", "page": __name__}, "value"),
    prevent_initial_call=True,
)
def update_id_options(
    filename, array_length_filter, repeat_length_filter, cas_type_filter, pattern_filter
):
    if filename is None:
        return []

    with db.database(filename) as con:
        ids = db.load_array_ids(
            con,
            min_array_length=array_length_filter[0],
            max_array_length=array_length_filter[1],
            min_repeat_length=repeat_length_filter[0],
            max_repeat_length=repeat_length_filter[1],
            cas_types=cas_type_filter,
            patterns_to_exclude=pattern_filter,
        )
    return ids


@callback(
    Output("array-view--figure-container", "children"),
    Output("array-view--array-info", "children"),
    Input({"type": "file-dropdown", "page": __name__}, "value"),
    Input("array-view--id-dropdown", "value"),
    prevent_initial_call=True,
)
def update_array_view(filename, id) -> tuple[list, list]:
    if filename is None or id is None:
        return [], []

    with db.database(filename) as con:
        array = db.load_array(con, id)
        if array is None:
            return [], []

    fig = generate_figure(array)
    fig_container = dcc.Graph(figure=fig, config=graph_config)

    pattern_labels = [
        "Anchored line",
        "Floating line",
        "Split line",
        "Dotted",
        "Dotted at proximal",
        "Dotted at distal",
    ]
    active_patterns = [pattern_labels[i - 1] for i in array.repeat_stats.patterns]
    patterns_text = ", ".join(active_patterns) if active_patterns else "None"

    info_children = [
        html.Div(
            [
                html.Strong("CAS Type: "),
                html.Span(array.cas_type),
            ]
        ),
        html.Div(
            [
                html.Strong("Active Mutation Patterns: "),
                html.Span(patterns_text),
            ]
        ),
    ]

    return [fig_container], info_children
