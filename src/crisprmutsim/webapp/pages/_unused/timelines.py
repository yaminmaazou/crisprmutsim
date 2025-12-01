# # type: ignore
# from collections import Counter
# from urllib.parse import parse_qs
# import dash
# from dash import callback, dcc, html, Input, Output
# from dash.exceptions import PreventUpdate
# import plotly.express as px
# import pandas as pd


# # dash.register_page(__name__)


# def generate_timeline_figure(simulation_index: int = 0):
#     event_dict = event_list_to_dict(simulation_data[simulation_index])
#     event_types: Counter[str] = Counter(event_dict["event_id"])

#     fig = px.scatter(
#         event_dict,
#         x="timestamp",
#         y=[0] * len(event_dict["time"]),  # 1D line
#         custom_data=["index", "event_id", "args", "response"],
#         color="event_id",
#     )

#     fig.update_layout(
#         xaxis=dict(title="Time", rangemode="tozero"),
#         yaxis=dict(visible=False),
#         height=150,
#         margin=dict(l=40, r=40, t=40, b=40),
#         legend=dict(title="", orientation="v"),
#     )
#     fig.update_traces(
#         mode="markers",
#         marker=dict(
#             size=max(
#                 3, 10 * (1 - min(len(event_dict), 1000) / 1000)
#             ),  # Adjust marker size based on number of events
#             opacity=0.5,
#         ),
#         hovertemplate="%{customdata[0]}: %{customdata[1]}<br>Args: %{customdata[2]}<br>Result: %{customdata[3]}<br>Time: %{x}<extra></extra>",
#     )

#     return fig


# def layout(simulation: str = "0"):

#     layout = html.Div(
#         [
#             html.H2("Event Timeline"),
#             dcc.Dropdown(
#                 [i for i in range(len(simulation_data))],
#                 int(simulation),
#                 id="timeline-dropdown",
#             ),
#             dcc.Graph(id="timeline-graph"),
#         ]
#     )

#     return layout


# @callback(
#     Output("timeline-graph", "figure"),
#     Input("timeline-dropdown", "value"),
# )
# def update_timeline(simulation_index):
#     if simulation_index is None:
#         raise PreventUpdate

#     fig = generate_timeline_figure(simulation_index)
#     return fig


# @callback(
#     Output("current-url", "href"),
#     Input("timeline-graph", "clickData"),
#     Input("timeline-dropdown", "value"),
#     prevent_initial_call=True,
# )
# def open_event_diff(clickData, simulation_index):
#     if not clickData or "points" not in clickData:
#         raise PreventUpdate
#     point_index = clickData["points"][0]["customdata"][0]

#     return f"/event-diff?simulation={simulation_index}&event={point_index}"


# # @callback(
# #     Output('event-diff-url', 'href'),
# #     Input('url', 'search'),
# #     Input('timeline-graph', 'clickData'),
# #     prevent_initial_call=True
# # )
# # def on_event_click(search, clickData):
# #     simulation_index = parse_qs(search.lstrip('?')).get("simulation", [None])[0]
# #     if simulation_index is None:
# #         return "/event_diff"
# #     simulation_index = int(simulation_index)

# #     if not clickData or 'points' not in clickData:
# #         raise PreventUpdate
# #     point_index = clickData['points'][0]['pointIndex']

# #     return f"/event_diff?simulation={simulation_index}&event={point_index}"
