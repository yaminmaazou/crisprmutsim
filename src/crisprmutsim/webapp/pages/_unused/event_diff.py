#### UNUSED ####


# type: ignore
# import dash
# from dash import dcc, html, Input, Output
# from dash.exceptions import PreventUpdate
# from urllib.parse import parse_qs
# import plotly.graph_objects as go
# import pandas as pd

# from CRISPR.crispr_array import CRISPRArray


# # dash.register_page(__name__)


# def generate_diff_figure(simulation_index, event_index):

#     # Determine CRISPRArray at given index
#     array = CRISPRArray(initial_array)
#     array.apply_events(simulation_data[simulation_index][: event_index + 1])

#     # Convert repeats to DataFrame of characters
#     df = pd.DataFrame([list(seq) for seq in array])
#     repeat_count, repeat_length = df.shape

#     # Compute consensus
#     consensus = df.mode().iloc[0]
#     consensus_df = pd.DataFrame([consensus.tolist()])

#     # Combine consensus and repeats
#     df_with_consensus = pd.concat([consensus_df, df], ignore_index=True)
#     row_labels = ["Consensus"] + [f"Repeat {i}" for i in range(repeat_count)]

#     # Compute mismatch mask relative to consensus
#     mismatch_mask = df_with_consensus != consensus
#     z_data = mismatch_mask.astype(float).values
#     z_data[0] = [0.5] * repeat_length

#     # Prepare visible text: only show mismatches or consensus row
#     text = df_with_consensus.astype(str).values
#     text_display = [
#         [
#             text[i][j] if (i == 0 or mismatch_mask.iloc[i, j]) else ""
#             for j in range(repeat_length)
#         ]
#         for i in range(len(text))
#     ]

#     # Create heatmap with conditional text
#     fig = go.Figure(
#         data=go.Heatmap(
#             z=z_data,
#             x=[f"{i}" for i in range(repeat_length)],
#             y=row_labels,
#             text=text_display,
#             texttemplate="%{text}",
#             hoverinfo="skip",
#             colorscale=[[0, "white"], [0.5, "lightblue"], [1, "salmon"]],
#             zmin=0,
#             zmax=1,
#             showscale=False,
#         )
#     )

#     fig.update_layout(
#         xaxis_title="Position in Repeat",
#         yaxis_title="Sequence",
#         xaxis_range=[-0.5, repeat_length - 0.5],
#         # xaxis=dict(side="bottom",
#         #     fixedrange=True,
#         #     tickmode="linear",
#         #     tick0=1,
#         #     dtick=1,
#         #     range=[-0.5, repeat_length - 0.5]  # aligns leftmost cell
#         # ),
#         # yaxis_autorange='reversed',
#         yaxis_range=[repeat_count + 0.5, -0.5],
#         # yaxis_scaleanchor="x",
#         # height= 500,#(repeat_count + 1) * 50,  # Adjust height based on number of repeats
#         # width= repeat_length * 60,  # Adjust width based on repeat length
#     )
#     # fig.update_yaxes(scaleanchor="x")

#     return fig


# def layout(simulation=None, event=None):
#     if simulation is None or event is None:
#         return html.Div("Missing simulation or event parameters.")

#     simulation_index = int(simulation)
#     event_index = int(event)

#     before_fig = generate_diff_figure(simulation_index, event_index - 1)
#     before_fig.update_layout(title=f"Before:")
#     after_fig = generate_diff_figure(simulation_index, event_index)
#     after_fig.update_layout(title=f"After:")

#     layout = html.Div(
#         [
#             html.H2(
#                 f"Diff View for Event {simulation_data[simulation_index][event_index]}"
#             ),
#             dcc.Graph(figure=before_fig),
#             dcc.Graph(figure=after_fig),
#             dcc.Link(
#                 "Back to Timeline",
#                 href="/timelines?simulation=" + str(simulation_index),
#             ),
#         ]
#     )

#     return layout
