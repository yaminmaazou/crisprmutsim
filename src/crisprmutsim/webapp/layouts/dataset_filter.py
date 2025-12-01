from dash import dcc, html


def dataset_filter_layout(page: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Label("File:"),
                    dcc.Dropdown([], None, id={"type": "file-dropdown", "page": page}),
                ],
                style={
                    # "width": "50%",
                    # "display": "inline-block",
                    # "paddingRight": "10px",
                },
            ),
            html.Div(
                [
                    html.Label("Array lengths to include (number of repeats):"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("Min:", style={"marginRight": "5px"}),
                                    dcc.Input(
                                        id={
                                            "type": "array-length-min-input",
                                            "page": page,
                                        },
                                        type="number",
                                        min=0,
                                        max=200,
                                        step=1,
                                        value=0,
                                        style={"width": "80px", "marginRight": "15px"},
                                    ),
                                    html.Label("Max:", style={"marginRight": "5px"}),
                                    dcc.Input(
                                        id={
                                            "type": "array-length-max-input",
                                            "page": page,
                                        },
                                        type="number",
                                        min=0,
                                        max=200,
                                        step=1,
                                        value=200,
                                        style={"width": "80px"},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "marginBottom": "10px",
                                },
                            ),
                            dcc.RangeSlider(
                                id={"type": "array-length-slider", "page": page},
                                min=0,
                                max=200,
                                step=1,
                                value=[0, 200],
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": True,
                                },
                                marks=None,
                            ),
                        ]
                    ),
                ],
                style={
                    "paddingTop": "15px",
                },
            ),
            html.Div(
                [
                    html.Label("Repeat lengths to include (number of bases):"),
                    html.Div(
                        [
                            html.Label("Min:", style={"marginRight": "5px"}),
                            dcc.Input(
                                id={"type": "repeat-length-min-input", "page": page},
                                type="number",
                                min=0,
                                max=100,
                                step=1,
                                value=0,
                                style={"width": "80px", "marginRight": "15px"},
                            ),
                            html.Label("Max:", style={"marginRight": "5px"}),
                            dcc.Input(
                                id={"type": "repeat-length-max-input", "page": page},
                                type="number",
                                min=0,
                                max=100,
                                step=1,
                                value=100,
                                style={"width": "80px"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "marginBottom": "10px",
                        },
                    ),
                    dcc.RangeSlider(
                        id={"type": "repeat-length-slider", "page": page},
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
                style={
                    "paddingTop": "15px",
                },
            ),
            html.Div(
                [
                    html.Label("CAS types to include:"),
                    dcc.Checklist(
                        id={"type": "cas-type-filter", "page": page},
                        options=[],
                        value=[],
                        inline=True,
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Select All",
                                id={"type": "cas-select-all", "page": page},
                                n_clicks=0,
                                style={"marginRight": "5px"},
                            ),
                            html.Button(
                                "Select None",
                                id={"type": "cas-select-none", "page": page},
                                n_clicks=0,
                                style={"marginRight": "5px"},
                            ),
                            html.Span(
                                id={"type": "cas-individual-buttons", "page": page}
                            ),
                        ],
                        style={"marginTop": "5px"},
                    ),
                ],
                id={"type": "cas-type-filter-container", "page": page},
                style={
                    "paddingTop": "15px",
                },
            ),
            html.Div(
                [
                    html.Label("Mutation Patterns to exclude:"),
                    dcc.Checklist(
                        id={"type": "pattern-filter", "page": page},
                        options=[
                            {"label": "None", "value": 0},
                            {"label": "Anchored line", "value": 1},
                            {"label": "Floating line", "value": 2},
                            {"label": "Split line", "value": 3},
                            {"label": "Dotted", "value": 4},
                            {"label": "Dotted at proximal", "value": 5},
                            {"label": "Dotted at distal", "value": 6},
                        ],
                        value=[],
                        inline=True,
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Select All",
                                id={"type": "pattern-select-all", "page": page},
                                n_clicks=0,
                                style={"marginRight": "5px"},
                            ),
                            html.Button(
                                "Select None",
                                id={"type": "pattern-select-none", "page": page},
                                n_clicks=0,
                                style={"marginRight": "5px"},
                            ),
                        ],
                        style={"marginTop": "5px"},
                    ),
                ],
                id={"type": "pattern-filter-container", "page": page},
                style={
                    "paddingTop": "15px",
                    "paddingBottom": "15px",
                },
            ),
        ]
    )
