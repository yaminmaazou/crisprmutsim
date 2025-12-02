from collections.abc import Callable
import os
import threading
from typing import TYPE_CHECKING
import dash
from dash import callback, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate

if TYPE_CHECKING:
    from crisprmutsim.CRISPR.raw_crispr_array import RawCRISPRArray
from crisprmutsim.CRISPR.simulation.events.crispr_event import (
    ICRISPREvent,
    ICRISPREventGenerator,
)
from crisprmutsim.CRISPR.simulation.events.deletion import (
    DeletionGenerator,
    DeletionRateConverter,
)
from crisprmutsim.CRISPR.simulation.events.insertion import InsertionGenerator
from crisprmutsim.CRISPR.simulation.events.insertion_deletion import (
    InsertionDeletionGenerator,
    InsertionDeletionRateConverter,
)
from crisprmutsim.CRISPR.simulation.events.mutation import (
    MutationGenerator,
    MutationRateConverter,
)
import crisprmutsim.CRISPR.simulation.simulation as simulation
from crisprmutsim.simulation.event import EventParametersType


dash.register_page(__name__, path="/")


simulation_progress = {
    "current": 0,
    "total": 0,
    "running": False,
    "error": None,
    "filename": None,
}

layout = html.Div(
    [
        html.H2("CRISPR Mutation Simulation"),
        html.H3(
            "Array Parameters", style={"marginTop": "20px", "marginBottom": "10px"}
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Array length (number of repeats):"),
                        dcc.Input(
                            id="home--array-length-input",
                            type="number",
                            min=1,
                            value=18,
                            style={
                                "width": "100px",
                                "display": "block",
                                "marginTop": "5px",
                            },
                        ),
                    ],
                    style={"marginBottom": "15px"},
                ),
                html.Div(
                    [
                        html.Label("Repeat length (number of bases):"),
                        dcc.Input(
                            id="home--repeat-length-input",
                            type="number",
                            min=1,
                            value=32,
                            style={
                                "width": "100px",
                                "display": "block",
                                "marginTop": "5px",
                            },
                        ),
                    ],
                    style={"marginBottom": "15px"},
                ),
            ],
        ),
        html.H3(
            "Simulation Parameters", style={"marginTop": "20px", "marginBottom": "10px"}
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Seed:"),
                        dcc.Input(
                            id="home--seed-input",
                            type="number",
                            min=1,
                            step=1,
                            placeholder="Random if empty",
                            style={
                                "width": "200px",
                                "display": "block",
                                "marginTop": "5px",
                            },
                        ),
                    ],
                    style={"marginBottom": "15px"},
                ),
                html.Div(
                    [
                        html.Label("End time:"),
                        dcc.Input(
                            id="home--end-time-input",
                            type="number",
                            min=0.01,
                            value=1,
                            style={
                                "width": "100px",
                                "display": "block",
                                "marginTop": "5px",
                            },
                        ),
                    ],
                    style={"marginBottom": "15px"},
                ),
                html.Div(
                    [
                        html.Label("Number of runs:"),
                        dcc.Input(
                            id="home--num-runs-input",
                            type="number",
                            min=1,
                            value=1000,
                            style={
                                "width": "100px",
                                "display": "block",
                                "marginTop": "5px",
                            },
                        ),
                    ],
                    style={"marginBottom": "15px"},
                ),
                html.Div(
                    [
                        html.Label("Number of workers (CPU cores):"),
                        dcc.Input(
                            id="home--num-workers-input",
                            type="number",
                            min=1,
                            max=32,
                            value=os.process_cpu_count() or os.cpu_count() or 4,
                            style={
                                "width": "100px",
                                "display": "block",
                                "marginTop": "5px",
                            },
                        ),
                    ],
                    style={"marginBottom": "15px"},
                ),
            ],
        ),
        html.H3(
            "Event Parameters", style={"marginTop": "20px", "marginBottom": "10px"}
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H4("Mutation", style={"marginBottom": "10px"}),
                        html.Div(
                            [
                                html.Label("Rate per base:"),
                                dcc.Input(
                                    id="home--mutation-rate-input",
                                    type="number",
                                    min=0.0,
                                    step=0.1,
                                    value=1.0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Allow same base mutation:"),
                                dcc.Checklist(
                                    id="home--mutation-allow-same-base-input",
                                    options=[{"label": " Yes", "value": "yes"}],
                                    value=[],
                                    style={"marginTop": "5px"},
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                    ],
                    style={
                        "marginBottom": "20px",
                        "padding": "10px",
                        "border": "1px solid #ddd",
                        "borderRadius": "5px",
                    },
                ),
                html.Div(
                    [
                        html.H4("Insertion/Deletion", style={"marginBottom": "10px"}),
                        html.Div(
                            [
                                html.Label("Rate per repeat:"),
                                dcc.Input(
                                    id="home--indel-rate-input",
                                    type="number",
                                    min=0.0,
                                    step=0.1,
                                    value=0.0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Insertion anchor:"),
                                dcc.RadioItems(
                                    id="home--indel-anchor",
                                    options=[
                                        {"label": "Proximal", "value": "proximal"},
                                        {"label": "Distal", "value": "distal"},
                                    ],
                                    value="proximal",
                                    labelStyle={"display": "block"},
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Randomize insertion index:"),
                                dcc.RadioItems(
                                    id="home--indel-randomize",
                                    options=[
                                        {"label": "No", "value": "none"},
                                        {"label": "Uniform", "value": "uniform"},
                                        {
                                            "label": "Exponential",
                                            "value": "exponential",
                                        },
                                    ],
                                    value="none",
                                    labelStyle={"display": "block"},
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Exponential lambda factor:"),
                                dcc.Input(
                                    id="home--indel-exp-lambda-factor-input",
                                    type="number",
                                    min=0.001,
                                    step=0.001,
                                    value=0.01,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Leader deletion offset:"),
                                dcc.Input(
                                    id="home--indel-leader-offset-input",
                                    type="number",
                                    min=0,
                                    value=0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Distal deletion offset:"),
                                dcc.Input(
                                    id="home--indel-distal-offset-input",
                                    type="number",
                                    min=0,
                                    value=0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Split deletion offset (-1 = no splits):"),
                                dcc.Input(
                                    id="home--indel-split-offset-input",
                                    type="number",
                                    min=-1,
                                    value=0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                    ],
                    style={
                        "marginBottom": "20px",
                        "padding": "10px",
                        "border": "1px solid #ddd",
                        "borderRadius": "5px",
                    },
                ),
                html.Div(
                    [
                        html.H4("Insertion", style={"marginBottom": "10px"}),
                        html.Div(
                            [
                                html.Label("Rate:"),
                                dcc.Input(
                                    id="home--insertion-rate-input",
                                    type="number",
                                    min=0.0,
                                    step=0.1,
                                    value=6522.0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Anchor:"),
                                dcc.RadioItems(
                                    id="home--insertion-anchor",
                                    options=[
                                        {"label": "Proximal", "value": "proximal"},
                                        {"label": "Distal", "value": "distal"},
                                    ],
                                    value="proximal",
                                    labelStyle={"display": "block"},
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Randomize insertion index:"),
                                dcc.RadioItems(
                                    id="home--insertion-randomize",
                                    options=[
                                        {"label": "No", "value": "none"},
                                        {"label": "Uniform", "value": "uniform"},
                                        {
                                            "label": "Exponential",
                                            "value": "exponential",
                                        },
                                    ],
                                    value="none",
                                    labelStyle={"display": "block"},
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Exponential lambda factor:"),
                                dcc.Input(
                                    id="home--insertion-exp-lambda-factor-input",
                                    type="number",
                                    min=0.001,
                                    step=0.001,
                                    value=0.01,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                    ],
                    style={
                        "marginBottom": "20px",
                        "padding": "10px",
                        "border": "1px solid #ddd",
                        "borderRadius": "5px",
                    },
                ),
                html.Div(
                    [
                        html.H4("Deletion", style={"marginBottom": "10px"}),
                        html.Div(
                            [
                                html.Label("Rate per repeat:"),
                                dcc.Input(
                                    id="home--deletion-rate-input",
                                    type="number",
                                    min=0.0,
                                    step=0.1,
                                    value=137.0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Leader offset:"),
                                dcc.Input(
                                    id="home--deletion-leader-offset-input",
                                    type="number",
                                    min=0,
                                    value=0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Distal offset:"),
                                dcc.Input(
                                    id="home--deletion-distal-offset-input",
                                    type="number",
                                    min=0,
                                    value=0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Split offset (-1 = no splits):"),
                                dcc.Input(
                                    id="home--deletion-split-offset-input",
                                    type="number",
                                    min=-1,
                                    value=0,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Geometric mean block deletion length:"),
                                dcc.Input(
                                    id="home--deletion-mean-block-length-input",
                                    type="number",
                                    min=1.0,
                                    value=2.73,
                                    style={
                                        "width": "100px",
                                        "display": "block",
                                        "marginTop": "5px",
                                    },
                                ),
                            ],
                            style={"marginBottom": "10px"},
                        ),
                    ],
                    style={
                        "marginBottom": "20px",
                        "padding": "10px",
                        "border": "1px solid #ddd",
                        "borderRadius": "5px",
                    },
                ),
            ],
        ),
        html.H3("Output", style={"marginTop": "20px", "marginBottom": "10px"}),
        html.Div(
            [
                html.Label("Output filename:"),
                dcc.Input(
                    id="home--filename-input",
                    type="text",
                    value="",
                    placeholder="Auto-generated if empty",
                    style={"width": "400px", "display": "block", "marginTop": "5px"},
                ),
            ],
            style={"marginBottom": "20px"},
        ),
        html.Button(
            "Run Simulation",
            id="home--run-button",
            n_clicks=0,
            style={
                "padding": "10px 20px",
                "fontSize": "16px",
                "cursor": "pointer",
            },
        ),
        html.Div(
            id="home--progress-container",
            children=[
                html.Div(
                    id="home--progress-text",
                    style={
                        "marginTop": "20px",
                        "fontSize": "14px",
                        "fontWeight": "bold",
                    },
                ),
                html.Progress(
                    id="home--progress-bar",
                    max="100",
                    value="0",
                    style={
                        "width": "100%",
                        "height": "30px",
                        "marginTop": "10px",
                    },
                ),
            ],
            style={"display": "none"},
        ),
        html.Div(
            id="home--output-message",
            style={"marginTop": "20px", "fontSize": "14px"},
        ),
        dcc.Interval(
            id="home--progress-interval",
            interval=200,
            disabled=True,
        ),
        dcc.Store(id="home--simulation-running", data=False),
    ]
)


@callback(
    Output("home--simulation-running", "data"),
    Output("home--progress-interval", "disabled"),
    Output("home--run-button", "disabled"),
    Input("home--run-button", "n_clicks"),
    State("home--array-length-input", "value"),
    State("home--repeat-length-input", "value"),
    State("home--seed-input", "value"),
    State("home--end-time-input", "value"),
    State("home--num-runs-input", "value"),
    State("home--num-workers-input", "value"),
    State("home--mutation-rate-input", "value"),
    State("home--mutation-allow-same-base-input", "value"),
    State("home--indel-rate-input", "value"),
    State("home--indel-anchor", "value"),
    State("home--indel-randomize", "value"),
    State("home--indel-exp-lambda-factor-input", "value"),
    State("home--indel-leader-offset-input", "value"),
    State("home--indel-distal-offset-input", "value"),
    State("home--indel-split-offset-input", "value"),
    State("home--insertion-rate-input", "value"),
    State("home--insertion-anchor", "value"),
    State("home--insertion-randomize", "value"),
    State("home--insertion-exp-lambda-factor-input", "value"),
    State("home--deletion-rate-input", "value"),
    State("home--deletion-leader-offset-input", "value"),
    State("home--deletion-distal-offset-input", "value"),
    State("home--deletion-split-offset-input", "value"),
    State("home--deletion-mean-block-length-input", "value"),
    State("home--filename-input", "value"),
    prevent_initial_call=True,
)
def start_simulation(
    n_clicks,
    array_length,
    repeat_length,
    seed,
    end_time,
    num_runs,
    num_workers,
    mutation_rate,
    mutation_allow_same_base,
    indel_rate,
    indel_anchor,
    indel_randomize,
    indel_exp_lambda_factor,
    indel_leader_offset,
    indel_distal_offset,
    indel_split_offset,
    ins_rate,
    ins_anchor,
    ins_randomize,
    ins_exp_lambda_factor,
    del_rate,
    del_leader_offset,
    del_distal_offset,
    del_split_offset,
    del_mean_block_length,
    filename,
):
    global simulation_progress

    if n_clicks == 0:
        raise PreventUpdate

    if not all([array_length, repeat_length, end_time, num_runs, num_workers]):
        simulation_progress["error"] = "Error: All parameters must be filled."
        return False, True, False

    if seed is None:
        seed = int.from_bytes(os.urandom(4), "little")
    if mutation_rate is None:
        mutation_rate = 0.0
    if indel_rate is None:
        indel_rate = 0.0
    if ins_rate is None:
        ins_rate = 0.0
    if del_rate is None:
        del_rate = 0.0

    if indel_leader_offset is None:
        indel_leader_offset = 0
    if indel_distal_offset is None:
        indel_distal_offset = 0
    if indel_split_offset is None:
        indel_split_offset = 0
    if del_leader_offset is None:
        del_leader_offset = 0
    if del_distal_offset is None:
        del_distal_offset = 0
    if del_split_offset is None:
        del_split_offset = 0
    if del_mean_block_length is None:
        del_mean_block_length = 1.0

    if not filename or filename.strip() == "":
        filename = f"sim_{end_time}_{num_runs}_mut_{mutation_rate}_indel_{indel_rate}_ins_{ins_rate}_del_{del_rate}.db"
    elif not filename.endswith(".db"):
        filename = filename + ".db"

    simulation_progress["current"] = 0
    simulation_progress["total"] = num_runs
    simulation_progress["running"] = True
    simulation_progress["error"] = None
    simulation_progress["filename"] = filename

    def run_simulation_thread():
        global simulation_progress
        try:
            event_generators: list[
                ICRISPREventGenerator[EventParametersType, ICRISPREvent]
            ] = []
            meta = ""

            if mutation_rate > 0.0:
                allow_same_base = (
                    "yes" in mutation_allow_same_base
                    if mutation_allow_same_base
                    else False
                )

                mutgen = MutationGenerator(
                    {"allow_same_base": allow_same_base},
                    rate=MutationRateConverter(mutation_rate),
                )
                event_generators.append(mutgen)
                meta += f"Mutation rate: {mutation_rate}\n"

            if indel_rate > 0.0:
                indelgen = InsertionDeletionGenerator(
                    {
                        "insertion_anchor": indel_anchor,
                        "insertion_randomize": indel_randomize,
                        "insertion_exp_lambda_factor": indel_exp_lambda_factor,
                        "leader_offset": indel_leader_offset,
                        "distal_offset": indel_distal_offset,
                        "split_offset": indel_split_offset,
                    },
                    rate=InsertionDeletionRateConverter(indel_rate),
                )
                event_generators.append(indelgen)
                meta += f"Insertion/Deletion rate: {indel_rate}\n"

            if ins_rate > 0.0:
                insgen = InsertionGenerator(
                    {
                        "anchor": ins_anchor,
                        "randomize": ins_randomize,
                        "exp_lambda_factor": ins_exp_lambda_factor,
                    },
                    rate=ins_rate,
                )
                event_generators.append(insgen)

            if del_rate > 0.0:
                delgen = DeletionGenerator(
                    {
                        "leader_offset": del_leader_offset,
                        "distal_offset": del_distal_offset,
                        "split_offset": del_split_offset,
                        "mean_block_deletion_length": del_mean_block_length,
                    },
                    rate=DeletionRateConverter(del_rate),
                )
                event_generators.append(delgen)
                meta += f"Deletion rate: {del_rate}\n"

            def progress_update(current, total):
                simulation_progress["current"] = current
                simulation_progress["total"] = total

            simulation.run_and_store_results(
                filename,
                seed,
                end_time,
                array_length,
                repeat_length,
                event_generators,
                num_runs,
                meta,
                num_workers,
                progress_callback=progress_update,
            )

            simulation_progress["running"] = False

        except Exception as e:
            simulation_progress["error"] = f"Error running simulation: {str(e)}"
            simulation_progress["running"] = False

    # very hacky way to run the simulation in the background without freezing the UI
    #   on a real server, we would need to use proper background callbacks etc.
    thread = threading.Thread(target=run_simulation_thread, daemon=True)
    thread.start()

    return True, False, True


@callback(
    Output("home--progress-container", "style"),
    Output("home--progress-text", "children"),
    Output("home--progress-bar", "value"),
    Output("home--output-message", "children"),
    Output("home--output-message", "style"),
    Output("home--simulation-running", "data", allow_duplicate=True),
    Output("home--progress-interval", "disabled", allow_duplicate=True),
    Output("home--run-button", "disabled", allow_duplicate=True),
    Input("home--progress-interval", "n_intervals"),
    State("home--simulation-running", "data"),
    prevent_initial_call=True,
)
def update_progress(n_intervals, is_running):
    global simulation_progress

    if not is_running and not simulation_progress["running"]:
        raise PreventUpdate

    current = simulation_progress["current"]
    total = simulation_progress["total"]
    running = simulation_progress["running"]
    error = simulation_progress["error"]
    filename = simulation_progress["filename"]

    if error:
        return (
            {"display": "none"},
            "",
            "0",
            error,
            {"marginTop": "20px", "fontSize": "14px", "color": "red"},
            False,
            True,
            False,
        )

    if running:
        percentage = (current / total * 100) if total > 0 else 0
        progress_text = (
            f"Running simulation: {current}/{total} runs completed ({percentage:.1f}%)"
        )

        return (
            {"display": "block"},
            progress_text,
            str(int(percentage)),
            "",
            {"marginTop": "20px", "fontSize": "14px"},
            True,
            False,
            True,
        )
    else:
        return (
            {"display": "none"},
            "",
            "0",
            f"Simulation completed. File saved as: {filename}",
            {"marginTop": "20px", "fontSize": "14px", "color": "green"},
            False,
            True,
            False,
        )
