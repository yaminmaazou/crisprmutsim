import dash
from dash import callback, dcc, html, Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go

from crisprmutsim.CRISPR.dataset_stats import DatasetStats
import crisprmutsim.CRISPR.storage as db
from crisprmutsim.webapp.config.graph_config import graph_config
from crisprmutsim.webapp.layouts.dataset_filter import dataset_filter_layout


dash.register_page(__name__)


def generate_array_lengths_figure(lengths: dict[int, float]) -> go.Figure:
    if not lengths:
        lengths = {0: 0}

    fig = px.bar(
        x=list(lengths.keys()),
        y=list(lengths.values()),
    )
    fig.update_layout(
        margin_t=25,
        xaxis_title="Array Length (number of repeats)",
        yaxis_title="Proportion of Arrays",
    )
    return fig


def generate_repeat_lengths_figure(lengths: dict[int, float]) -> go.Figure:
    if not lengths:
        lengths = {0: 0}

    fig = px.bar(
        x=list(lengths.keys()),
        y=list(lengths.values()),
    )
    fig.update_layout(
        margin_t=25,
        xaxis_title="Repeat Length (number of bases) per Array",
        yaxis_title="Proportion of Arrays",
    )
    return fig


def generate_mutation_counts_figure(counts: dict[int, float]) -> go.Figure:
    if not counts:
        counts = {0: 0}

    fig = px.bar(
        x=list(counts.keys()),
        y=list(counts.values()),
    )
    fig.update_layout(
        margin_t=25,
        xaxis_title="Number of Mutations per Array",
        yaxis_title="Proportion of Arrays",
    )
    return fig


def generate_cas_type_counts_figure(counts: dict[str, float]) -> go.Figure:
    if not counts:
        counts = {" ": 0}

    sorted_keys = sorted(counts.keys())
    fig = px.bar(
        x=sorted_keys,
        y=[counts[key] for key in sorted_keys],
    )
    fig.update_layout(
        margin_t=25,
        xaxis_title="CAS Type",
        yaxis_title="Proportion of Arrays",
    )

    return fig


def generate_pattern_counts_figure(patterns: dict[int, float]) -> go.Figure:
    if not patterns:
        patterns = {i: 0 for i in range(7)}

    fig = go.Figure(
        data=[
            go.Bar(
                x=[
                    "None",
                    "Anchored Line",
                    "Floating Line",
                    "Split Line",
                    "Dotted",
                    "Dotted at proximal",
                    "Dotted at distal",
                ],
                y=[patterns[key] for key in sorted(patterns.keys())],
            )
        ]
    )
    fig.update_layout(
        margin_t=25,
        xaxis_title="Mutation Pattern",
        yaxis_title="Proportion of Arrays",
    )

    return fig


def generate_pattern_counts_by_cas_type_figure(
    patterns_by_cas_type: dict[str, dict[int, float]],
    normalize: bool = False,
):
    if not patterns_by_cas_type:
        patterns_by_cas_type = {" ": {i: 0 for i in range(7)}}

    fig = go.Figure()

    sorted_cas_types = sorted(patterns_by_cas_type.keys())

    if normalize:
        cas_type_totals = {
            cas_type: sum(patterns.values())
            for cas_type, patterns in patterns_by_cas_type.items()
        }

    for i in range(7):
        if normalize:
            y_values = [
                (
                    (
                        patterns_by_cas_type[cas_type][i]
                        / cas_type_totals[cas_type]  # type: ignore
                    )
                    if cas_type_totals[cas_type] > 0  # type: ignore
                    else 0
                )
                for cas_type in sorted_cas_types
            ]
        else:
            y_values = [
                patterns_by_cas_type[cas_type][i] for cas_type in sorted_cas_types
            ]

        fig.add_bar(
            x=sorted_cas_types,
            y=y_values,
            name=[
                "None",
                "Anchored Line",
                "Floating Line",
                "Split Line",
                "Dotted",
                "Dotted at proximal",
                "Dotted at distal",
            ][i],
        )

    fig.update_layout(
        margin_t=25,
        xaxis_title="CAS Type",
        yaxis_title="Proportion of Arrays" if normalize else "Proportion of Arrays",
        barmode="group",
    )

    return fig


def generate_diff_figure(mutation_matrix: list[list[float]]) -> go.Figure:
    if not mutation_matrix:
        mutation_matrix = [[0]]

    fig = px.imshow(
        mutation_matrix,
        labels={
            "x": "Base position in repeat",
            "y": "Repeat position in array",
            "color": "Mutations",
        },
        zmin=0,
        aspect="auto",
    )

    fig.update_traces(
        hovertemplate=f"Repeat %{{y}}, Base %{{x}}<br>Mutations: %{{z}}<extra></extra>"
    )

    fig.update_layout(margin_t=25)

    return fig


def generate_diff_from_distal_figure(mutation_matrix: list[list[float]]) -> go.Figure:
    if not mutation_matrix:
        mutation_matrix = [[0]]

    fig = px.imshow(
        mutation_matrix,
        labels={
            "x": "Base position from distal end of repeat",
            "y": "Repeat position from distal end of array",
            "color": "Mutations",
        },
        zmin=0,
        aspect="auto",
    )

    fig.update_traces(
        hovertemplate=f"Repeat from distal: %{{y}}, Base from distal: %{{x}}<br>Mutations: %{{z}}<extra></extra>"
    )

    fig.update_layout(margin_t=25)

    return fig


def generate_mutations_per_repeat_figure(
    mutations_per_repeat: dict[int, float],
) -> go.Figure:
    if not mutations_per_repeat:
        mutations_per_repeat = {0: 0}

    positions = sorted(mutations_per_repeat.keys())

    fig = px.bar(
        x=positions,
        y=[mutations_per_repeat[pos] for pos in positions],
    )

    fig.update_layout(
        margin_t=25,
        xaxis_title="Repeat position in array",
        yaxis_title="Proportion of mutations",
    )

    fig.update_traces(
        hovertemplate=f"Repeat %{{x}}<br>Mutations: %{{y}}<extra></extra>"
    )

    return fig


def generate_mutations_per_repeat_normalized_figure(
    mutations_per_repeat_normalized: dict[int, float],
) -> go.Figure:
    if not mutations_per_repeat_normalized:
        mutations_per_repeat_normalized = {0: 0}

    positions = sorted(mutations_per_repeat_normalized.keys())

    fig = px.bar(
        x=positions,
        y=[mutations_per_repeat_normalized[pos] for pos in positions],
    )

    fig.update_layout(
        margin_t=25,
        xaxis_title="Repeat position in array",
        yaxis_title="Number of mutations<br> / Number of arrays with length > position",
    )

    fig.update_traces(
        hovertemplate=f"Repeat %{{x}}<br>Normalized Mutations: %{{y}}<extra></extra>"
    )

    return fig


def generate_mutations_per_repeat_from_distal_figure(
    mutations_per_repeat_from_distal: dict[int, float],
) -> go.Figure:
    if not mutations_per_repeat_from_distal:
        mutations_per_repeat_from_distal = {0: 0}

    positions = sorted(mutations_per_repeat_from_distal.keys())

    fig = px.bar(
        x=positions,
        y=[mutations_per_repeat_from_distal[pos] for pos in positions],
    )

    fig.update_layout(
        margin_t=25,
        xaxis_title="Repeat position from distal end",
        yaxis_title="Proportion of mutations",
    )

    fig.update_traces(
        hovertemplate=f"Position from distal: %{{x}}<br>Mutations: %{{y}}<extra></extra>"
    )

    return fig


def generate_mutations_per_base_figure(
    mutations_per_base: dict[int, float],
) -> go.Figure:
    if not mutations_per_base:
        mutations_per_base = {0: 0}

    positions = sorted(mutations_per_base.keys())

    fig = px.bar(
        x=positions,
        y=[mutations_per_base[pos] for pos in positions],
    )

    fig.update_layout(
        margin_t=25,
        xaxis_title="Base position in repeat",
        yaxis_title="Proportion of mutations",
    )

    fig.update_traces(hovertemplate=f"Base %{{x}}<br>Mutations: %{{y}}<extra></extra>")

    return fig


def generate_mutations_per_base_from_distal_figure(
    mutations_per_base: dict[int, float],
) -> go.Figure:
    if not mutations_per_base:
        mutations_per_base = {0: 0}

    positions = sorted(mutations_per_base.keys())
    mutation_counts = [mutations_per_base[pos] for pos in positions]

    fig = px.bar(
        x=positions,
        y=mutation_counts,
    )

    fig.update_layout(
        margin_t=25,
        xaxis_title="Base position from distal end of repeat",
        yaxis_title="Proportion of mutations",
    )

    fig.update_traces(
        hovertemplate=f"Base position from distal: %{{x}}<br>Mutations: %{{y}}<extra></extra>"
    )

    return fig


def layout():
    return html.Div(
        [
            html.H3(f"Dataset statistics"),
            dataset_filter_layout(__name__),
            html.Div(
                [
                    html.Label("Mutation reference:"),
                    dcc.RadioItems(
                        id="dataset-stats--reference-mode",
                        options=[
                            {
                                "label": "Consensus",
                                "value": "consensus",
                            },
                            {
                                "label": "Proximal Repeat",
                                "value": "proximal",
                            },
                            {
                                "label": "Distal Repeat",
                                "value": "distal",
                            },
                        ],
                        value="consensus",
                        inline=True,
                    ),
                ],
                style={
                    "paddingTop": "10px",
                },
            ),
            html.Div(
                [
                    html.Button(
                        "Expand All Graphs",
                        id="dataset-stats--expand-all",
                        n_clicks=0,
                        style={
                            "marginRight": "10px",
                            "padding": "5px 15px",
                            "cursor": "pointer",
                        },
                    ),
                    html.Button(
                        "Collapse All Graphs",
                        id="dataset-stats--collapse-all",
                        n_clicks=0,
                        style={
                            "padding": "5px 15px",
                            "cursor": "pointer",
                        },
                    ),
                ],
                style={
                    "paddingTop": "15px",
                    "paddingBottom": "10px",
                },
            ),
            #### METADATA ####
            html.Hr(),
            html.Div(
                id="dataset-stats--dataset-info",
                style={
                    "paddingTop": "15px",
                    "paddingBottom": "15px",
                },
            ),
            html.Hr(),
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong("Total arrays: "),
                            html.Span("", id="dataset-stats--total-arrays"),
                        ]
                    ),
                    html.Div(
                        [
                            html.Strong("Mean array length: "),
                            html.Span("", id="dataset-stats--mean-array-length"),
                        ]
                    ),
                    html.Div(
                        [
                            html.Strong("Mean repeat length: "),
                            html.Span("", id="dataset-stats--mean-repeat-length"),
                        ]
                    ),
                    html.Div(
                        [
                            html.Strong("Mean mutations per array: "),
                            html.Span("", id="dataset-stats--mean-mutations-per-array"),
                        ]
                    ),
                ],
                id="dataset-stats--dataset-stats-container",
                style={
                    "paddingTop": "15px",
                },
            ),
            html.Details(
                [
                    html.Summary(
                        "Array Length Distribution",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(id="dataset-stats--array-lengths"),
                ],
                open=False,
                id="dataset-stats--details-array-lengths",
            ),
            html.Details(
                [
                    html.Summary(
                        "Repeat Length Distribution",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(id="dataset-stats--repeat-lengths"),
                ],
                open=False,
                id="dataset-stats--details-repeat-lengths",
            ),
            html.Details(
                [
                    html.Summary(
                        "Mutation Count Distribution",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(id="dataset-stats--mutation-counts"),
                ],
                open=False,
                id="dataset-stats--details-mutation-counts",
            ),
            html.Details(
                [
                    html.Summary(
                        "CAS Type Distribution",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(id="dataset-stats--cas-type-counts"),
                ],
                open=False,
                id="dataset-stats--details-cas-type-counts",
            ),
            html.Details(
                [
                    html.Summary(
                        "Pattern Distribution",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(id="dataset-stats--pattern-counts"),
                ],
                open=False,
                id="dataset-stats--details-pattern-counts",
            ),
            html.Details(
                [
                    html.Summary(
                        "Pattern Distribution by CAS Type",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(
                        [
                            html.Label("Display Mode:"),
                            dcc.RadioItems(
                                id="dataset-stats--pattern-normalize-radio",
                                options=[
                                    {"label": "Absolute", "value": "absolute"},
                                    {"label": "Normalized (%)", "value": "normalized"},
                                ],
                                value="absolute",
                                inline=True,
                                style={"marginLeft": "10px"},
                            ),
                        ],
                        style={
                            "paddingTop": "10px",
                        },
                    ),
                    html.Div(
                        id="dataset-stats--pattern-counts-by-cas-type",
                    ),
                ],
                open=False,
                id="dataset-stats--details-pattern-counts-by-cas-type",
            ),
            html.Details(
                [
                    html.Summary(
                        "Total Mutation Heatmap",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(
                        id="dataset-stats--heatmap",
                    ),
                ],
                open=False,
                id="dataset-stats--details-heatmap",
            ),
            html.Details(
                [
                    html.Summary(
                        "Total Mutation Heatmap (from distal end)",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(
                        id="dataset-stats--heatmap-from-distal",
                    ),
                ],
                open=False,
                id="dataset-stats--details-heatmap-from-distal",
            ),
            html.Details(
                [
                    html.Summary(
                        "Mutations per Repeat Position",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(
                        id="dataset-stats--array",
                    ),
                ],
                open=False,
                id="dataset-stats--details-array",
            ),
            html.Details(
                [
                    html.Summary(
                        "Mutations per Repeat Position (Normalized)",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(
                        id="dataset-stats--array-normalized",
                    ),
                ],
                open=False,
                id="dataset-stats--details-array-normalized",
            ),
            html.Details(
                [
                    html.Summary(
                        "Mutations per Repeat Position (from distal end)",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(
                        id="dataset-stats--array-from-distal",
                    ),
                ],
                open=False,
                id="dataset-stats--details-array-from-distal",
            ),
            html.Details(
                [
                    html.Summary(
                        "Mutations per Base Position",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Array position range (which repeats to include):"
                            ),
                            dcc.RangeSlider(
                                id="dataset-stats--repeat-range",
                                min=0,
                                max=100,
                                step=1,
                                value=[0, 100],
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": True,
                                },
                                marks=None,
                            ),
                        ],
                        id="dataset-stats--repeat-range-container",
                        style={
                            "paddingBottom": "20px",
                        },
                    ),
                    html.Div(
                        id="dataset-stats--repeat",
                    ),
                ],
                open=False,
                id="dataset-stats--details-repeat",
            ),
            html.Details(
                [
                    html.Summary(
                        "Mutations per Base Position (from distal end)",
                        style={
                            "fontSize": "16px",
                            "fontWeight": "bold",
                            "cursor": "pointer",
                            "padding": "10px",
                            "backgroundColor": "#f0f0f0",
                            "borderRadius": "5px",
                            "marginTop": "15px",
                        },
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Array position range from distal end (which repeats to include):"
                            ),
                            dcc.RangeSlider(
                                id="dataset-stats--repeat-range-from-distal",
                                min=0,
                                max=100,
                                step=1,
                                value=[0, 100],
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": True,
                                },
                                marks=None,
                            ),
                        ],
                        id="dataset-stats--repeat-range-from-distal-container",
                        style={
                            "paddingBottom": "20px",
                        },
                    ),
                    html.Div(
                        id="dataset-stats--repeat-from-distal",
                    ),
                ],
                open=False,
                id="dataset-stats--details-repeat-from-distal",
            ),
        ]
    )


@callback(
    Output("dataset-stats--details-array-lengths", "open"),
    Output("dataset-stats--details-repeat-lengths", "open"),
    Output("dataset-stats--details-mutation-counts", "open"),
    Output("dataset-stats--details-cas-type-counts", "open"),
    Output("dataset-stats--details-pattern-counts", "open"),
    Output("dataset-stats--details-pattern-counts-by-cas-type", "open"),
    Output("dataset-stats--details-heatmap", "open"),
    Output("dataset-stats--details-heatmap-from-distal", "open"),
    Output("dataset-stats--details-array", "open"),
    Output("dataset-stats--details-array-normalized", "open"),
    Output("dataset-stats--details-array-from-distal", "open"),
    Output("dataset-stats--details-repeat", "open"),
    Output("dataset-stats--details-repeat-from-distal", "open"),
    Input("dataset-stats--expand-all", "n_clicks"),
    Input("dataset-stats--collapse-all", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_all_details(expand_clicks, collapse_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "dataset-stats--expand-all":
        return (
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
        )
    elif trigger_id == "dataset-stats--collapse-all":
        return (
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        )

    raise PreventUpdate


@callback(
    Output("dataset-stats--repeat-range", "max"),
    Output("dataset-stats--repeat-range-from-distal", "max"),
    Input({"type": "array-length-slider", "page": __name__}, "value"),
    prevent_initial_call=True,
)
def update_repeat_range_sliders(
    array_length_value: list[int],
):
    return (
        array_length_value[1] - 1,
        array_length_value[1] - 1,
    )


@callback(
    # meta
    Output("dataset-stats--dataset-info", "children"),
    #
    Output("dataset-stats--total-arrays", "children"),
    Output("dataset-stats--mean-array-length", "children"),
    Output("dataset-stats--mean-repeat-length", "children"),
    Output("dataset-stats--mean-mutations-per-array", "children"),
    #
    Output("dataset-stats--array-lengths", "children"),
    Output("dataset-stats--repeat-lengths", "children"),
    Output("dataset-stats--mutation-counts", "children"),
    Output("dataset-stats--cas-type-counts", "children"),
    Output("dataset-stats--pattern-counts", "children"),
    Output("dataset-stats--pattern-counts-by-cas-type", "children"),
    Output("dataset-stats--heatmap", "children"),
    Output("dataset-stats--heatmap-from-distal", "children"),
    Output("dataset-stats--array", "children"),
    Output("dataset-stats--array-normalized", "children"),
    Output("dataset-stats--array-from-distal", "children"),
    Output("dataset-stats--repeat", "children"),
    Output("dataset-stats--repeat-from-distal", "children"),
    #
    Input({"type": "file-dropdown", "page": __name__}, "value"),
    Input({"type": "array-length-slider", "page": __name__}, "value"),
    Input({"type": "repeat-length-slider", "page": __name__}, "value"),
    Input({"type": "cas-type-filter", "page": __name__}, "value"),
    Input({"type": "pattern-filter", "page": __name__}, "value"),
    Input("dataset-stats--reference-mode", "value"),
    Input("dataset-stats--pattern-normalize-radio", "value"),
    Input("dataset-stats--repeat-range", "value"),
    Input("dataset-stats--repeat-range-from-distal", "value"),
    prevent_initial_call=True,
)
def update_figures(
    filename,
    array_length_filter,
    repeat_length_filter,
    cas_type_filter,
    pattern_filter,
    reference_mode,
    pattern_normalize_mode,
    repeat_range,
    repeat_range_from_distal,
):
    if filename is None:
        raise PreventUpdate

    with db.database(filename) as con:
        arrays = db.load_arrays(
            con,
            min_array_length=array_length_filter[0],
            max_array_length=array_length_filter[1],
            min_repeat_length=repeat_length_filter[0],
            max_repeat_length=repeat_length_filter[1],
            cas_types=cas_type_filter,
            patterns_to_exclude=pattern_filter,
        )
        dataset_info = html.Div("Loaded from CSV")
        try:
            sim_info = db.load_simulation_info(con)
            if sim_info is not None:
                dataset_info = html.Div(
                    [
                        html.Strong("Simulation Info: "),
                    ]
                    + [html.Div(f"{key}: {value}") for key, value in sim_info.items()]
                )
        except:
            pass

    if len(arrays) == 0:
        return ("", 0, 0, 0, 0) + tuple([[] for _ in range(13)])

    stats = DatasetStats.from_arrays(
        arrays, reference_mode, repeat_range, repeat_range_from_distal
    )

    #### figures ####
    figs: list[go.Figure] = []

    figs.append(generate_array_lengths_figure(stats.array_length_distribution))
    figs.append(generate_repeat_lengths_figure(stats.repeat_length_distribution))
    figs.append(generate_mutation_counts_figure(stats.mutation_count_distribution))
    figs.append(generate_cas_type_counts_figure(stats.cas_type_distribution))
    figs.append(generate_pattern_counts_figure(stats.pattern_counts))
    normalize = pattern_normalize_mode == "normalized"
    figs.append(
        generate_pattern_counts_by_cas_type_figure(
            stats.pattern_counts_by_cas_type, normalize=normalize
        )
    )
    figs.append(generate_diff_figure(stats.mutation_matrix))
    figs.append(generate_diff_from_distal_figure(stats.mutation_matrix_from_distal))
    figs.append(
        generate_mutations_per_repeat_figure(stats.mutations_per_repeat_position)
    )
    figs.append(
        generate_mutations_per_repeat_normalized_figure(
            stats.mutations_per_repeat_normalized
        )
    )
    figs.append(
        generate_mutations_per_repeat_from_distal_figure(
            stats.mutations_per_repeat_position_from_distal
        )
    )

    figs.append(generate_mutations_per_base_figure(stats.mutations_per_base_position))
    figs.append(
        generate_mutations_per_base_from_distal_figure(
            stats.mutations_per_base_position_from_distal
        )
    )

    return (
        dataset_info,
        stats.total_arrays,
        f"{stats.mean_array_length:.2f}",
        f"{stats.mean_repeat_length:.2f}",
        f"{stats.mean_mutations_per_array:.2f}",
    ) + tuple([dcc.Graph(figure=fig, config=graph_config) for fig in figs])
