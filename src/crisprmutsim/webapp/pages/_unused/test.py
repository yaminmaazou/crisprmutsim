# # type:ignore

# import dash
# from dash import Dash, html, dcc, Input, Output, callback, ctx

# dash.register_page(__name__)


# def layout():
#     return html.Div(
#         [
#             dcc.Store(id="store-circular", data=False),
#             dcc.Slider(
#                 id="slider-circular",
#                 min=0,
#                 max=20,
#                 marks={i: str(i) for i in range(21)},
#                 value=3,
#             ),
#             dcc.Input(id="input-circular", type="number", min=0, max=20, value=3),
#             html.Div(id="output-circular"),
#         ]
#     )


# # @callback(
# #     Output("input-circular", "value"),
# #     Output("slider-circular", "value"),
# #     #Input("input-circular", "value"),
# #     Input("slider-circular", "value"),
# # )
# # def tcallback(slider_value):
# #     print(f"Triggered by: {ctx.triggered_id}")
# #     value = slider_value
# #     return value, value + 1

# # @callback(
# #     Output("output-circular", "children"),
# #     Input("slider-circular", "value")
# # )
# # def update_output(value):
# #     print(f"Updating output with value: {value}")
# #     return f"You have selected {value}"


# @callback(
#     Output("output-circular", "children"),
#     Input("store-circular", "data"),
# )
# def update_output(store_data):
#     print(f"####Updating output with store data: {store_data}")
#     return f"Store data is {store_data}"


# @callback(
#     Output("store-circular", "data"),
#     Input("store-circular", "data"),
# )
# def update_store(data):
#     print(f"####Updating store with data: {data}")
#     data = not data
#     return data
