# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Mon Nov 25 2024

import os
import sys

import dash
import numpy as np
import plotly.colors
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html
from plotly.subplots import make_subplots

dash.register_page(__name__)


def lumfunc_m(
    m,
    z=0,
    alpha=-1.2,
    phi1=0.006,
    phi2=-0.1,
    m1=-20,
    m2=-3,
    z0=5,
    parametrization="truncated_logexp",
):
    phi_star = phistar(z, phi1, phi2, parametrization)
    m_star = mstar(z, m1, m2, z0, parametrization)
    return (
        0.4
        * np.log(10)
        * phi_star
        * 10 ** ((m_star - m) * (alpha + 1))
        * np.exp(-(10 ** (0.4 * (m_star - m))))
    )


def phistar(z, phi1, phi2, parametrization="truncated_logexp"):
    if parametrization == "linexp":
        return phi1 * np.exp(phi2 * z)
    elif parametrization == "logpower":
        return phi1 * (1 + z) ** phi2
    elif parametrization == "truncated_logexp":
        return phi1 * np.exp(phi2 * z)


def mstar(z, m1, m2, z0, parametrization="truncated_logexp"):
    if parametrization == "linexp":
        return m1 + m2 * z
    elif parametrization == "logpower":
        return m1 + m2 * np.log10(1 + z)
    elif parametrization == "truncated_logexp":
        return m1 + np.where(z > z0, m2 * np.log10(1 + z0), m2 * np.log10(1 + z))


def load_png_data_as_array(population, parameter, value):
    # TODO: Replace this with the actual path to the processed images
    here = os.path.dirname(os.path.abspath(__file__))
    filename = (
        f"{here}/lumfunc_data/processed_images_{population}"
        f"/{parameter}_{value:.4f}_normalized.npy"
    )
    print(filename, flush=True, file=sys.stderr)
    try:
        return np.load(filename)
    except FileNotFoundError:
        print(f"File {filename} not found")
        # Return an array of zeros if the file is not found
        return np.zeros((100, 100))  # Adjust dimensions if needed


def make_mathjax(string):
    return dcc.Markdown(string, mathjax=True)


blue_defaults = {"alpha": -1.2, "phi1": 0.006, "m1": -20, "phi2": -0.1, "m2": -3}

red_defaults = {"alpha": -0.5, "phi1": 0.004, "m1": -21, "phi2": -0.7, "m2": 0}

# Default parameter ranges for blue and red populations
blue_d_alpha, blue_d_phi1, blue_d_phi2, blue_d_m1, blue_d_m2 = 0.5, 0.005, 1.5, 5, 5
red_d_alpha, red_d_phi1, red_d_phi2, red_d_m1, red_d_m2 = 0.5, 0.0025, 2, 5, 5
n_sliders = 11
central = n_sliders // 2

# Generate parameter values for sliders separately for blue and red populations
blue_alpha_values = np.linspace(
    blue_defaults["alpha"] - blue_d_alpha,
    blue_defaults["alpha"] + blue_d_alpha,
    n_sliders,
)
blue_phi1_values = np.linspace(
    blue_defaults["phi1"] - blue_d_phi1, blue_defaults["phi1"] + blue_d_phi1, n_sliders
)
blue_m1_values = np.linspace(
    blue_defaults["m1"] - blue_d_m1, blue_defaults["m1"] + blue_d_m1, n_sliders
)
blue_phi2_values = np.linspace(
    blue_defaults["phi2"] - blue_d_phi2, blue_defaults["phi2"] + blue_d_phi2, n_sliders
)
blue_m2_values = np.linspace(
    blue_defaults["m2"] - blue_d_m2, blue_defaults["m2"] + blue_d_m2, n_sliders
)

red_alpha_values = np.linspace(
    red_defaults["alpha"] - red_d_alpha, red_defaults["alpha"] + red_d_alpha, n_sliders
)
red_phi1_values = np.linspace(
    red_defaults["phi1"] - red_d_phi1, red_defaults["phi1"] + red_d_phi1, n_sliders
)
red_m1_values = np.linspace(
    red_defaults["m1"] - red_d_m1, red_defaults["m1"] + red_d_m1, n_sliders
)
red_phi2_values = np.linspace(
    red_defaults["phi2"] - red_d_phi2, red_defaults["phi2"] + red_d_phi2, n_sliders
)
red_m2_values = np.linspace(
    red_defaults["m2"] - red_d_m2, red_defaults["m2"] + red_d_m2, n_sliders
)


# Redshifts and corresponding colors
redshifts = np.linspace(0, 5, 11)
colors = plotly.colors.sequential.Viridis
z_colors = [
    colors[int((i / (len(redshifts) - 1)) * (len(colors) - 1))]
    for i in range(len(redshifts))
]

# Generate M (absolute magnitude) values
M = np.linspace(-30, -15, 100)

# Dash app initialization
# app = dash.Dash(__name__)

# Dropdown for population selection
layout = html.Div(
    [
        dcc.Store(id="last-selected-param", data="alpha"),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="population-dropdown",
                            options=[
                                {
                                    "label": make_mathjax("Blue Population"),
                                    "value": "blue",
                                },
                                {
                                    "label": make_mathjax("Red Population"),
                                    "value": "red",
                                },
                            ],
                            value="blue",  # default to blue population
                            style={"width": "100%", "padding": "15px"},
                            searchable=False,
                        ),
                        dcc.Dropdown(
                            id="param-dropdown",
                            options=[
                                {"label": make_mathjax("$\\phi_1^*$"), "value": "phi1"},
                                {"label": make_mathjax("$\\phi_2^*$"), "value": "phi2"},
                                {"label": make_mathjax("$M_1^*$"), "value": "m1"},
                                {"label": make_mathjax("$M_2^*$"), "value": "m2"},
                                {"label": make_mathjax("$\\alpha$"), "value": "alpha"},
                            ],
                            value="phi1",
                            style={"width": "100%", "padding": "15px"},
                            searchable=False,
                        ),
                    ],
                    style={
                        "display": "flex",
                        "gap": "15px",
                        "width": "60%",
                        "justify-content": "center",
                    },
                ),
            ]
        ),
        dcc.Slider(
            id="param-slider",
            min=0,
            max=n_sliders - 1,
            step=1,
            value=central,
            tooltip={"placement": "bottom", "always_visible": False},
            updatemode="drag",
        ),
        dcc.Graph(id="luminosity-graph", mathjax=True),
    ]
)


@callback(
    [
        Output("luminosity-graph", "figure"),
        Output("param-slider", "value"),
        Output("param-slider", "marks"),
        Output("last-selected-param", "data"),
    ],
    [
        Input("population-dropdown", "value"),
        Input("param-dropdown", "value"),
        Input("param-slider", "value"),
    ],
    State("last-selected-param", "data"),
)
def update_graph(
    selected_population, selected_param, slider_value, last_selected_param
):
    is_dropdown_changed = selected_param != last_selected_param

    # Determine which set of parameter ranges and values to use
    if selected_population == "blue":
        param_values = (
            blue_alpha_values
            if selected_param == "alpha"
            else (
                blue_phi1_values
                if selected_param == "phi1"
                else (
                    blue_m1_values
                    if selected_param == "m1"
                    else (
                        blue_phi2_values if selected_param == "phi2" else blue_m2_values
                    )
                )
            )
        )
        updated_slider_value = central if is_dropdown_changed else slider_value
        selected_param_value = param_values[updated_slider_value]

        blue_values = {
            "alpha": (
                selected_param_value
                if selected_param == "alpha"
                else blue_defaults["alpha"]
            ),
            "phi1": (
                selected_param_value
                if selected_param == "phi1"
                else blue_defaults["phi1"]
            ),
            "m1": (
                selected_param_value if selected_param == "m1" else blue_defaults["m1"]
            ),
            "phi2": (
                selected_param_value
                if selected_param == "phi2"
                else blue_defaults["phi2"]
            ),
            "m2": (
                selected_param_value if selected_param == "m2" else blue_defaults["m2"]
            ),
        }
        red_values = red_defaults  # Use red defaults if blue is selected

    elif selected_population == "red":
        param_values = (
            red_alpha_values
            if selected_param == "alpha"
            else (
                red_phi1_values
                if selected_param == "phi1"
                else (
                    red_m1_values
                    if selected_param == "m1"
                    else red_phi2_values
                    if selected_param == "phi2"
                    else red_m2_values
                )
            )
        )
        updated_slider_value = central if is_dropdown_changed else slider_value
        selected_param_value = param_values[updated_slider_value]

        red_values = {
            "alpha": (
                selected_param_value
                if selected_param == "alpha"
                else red_defaults["alpha"]
            ),
            "phi1": (
                selected_param_value
                if selected_param == "phi1"
                else red_defaults["phi1"]
            ),
            "m1": (
                selected_param_value if selected_param == "m1" else red_defaults["m1"]
            ),
            "phi2": (
                selected_param_value
                if selected_param == "phi2"
                else red_defaults["phi2"]
            ),
            "m2": (
                selected_param_value if selected_param == "m2" else red_defaults["m2"]
            ),
        }
        blue_values = blue_defaults  # Use blue defaults if red is selected

    # Create plot with the specified parameter values for each population
    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"colspan": 2, "type": "heatmap"}, None],
        ],
        row_heights=[0.3, 0.7],
        column_widths=[0.5, 0.5],
        vertical_spacing=0.1,
        subplot_titles=[
            "Blue Luminosity Function",
            "Red Luminosity Function",
            "HSC-deep-field simulation",
        ],
    )

    # Plot blue population
    for z in redshifts:
        lumfunc_values_blue = lumfunc_m(M, z=z, **blue_values)
        fig.add_trace(
            go.Scatter(
                x=M,
                y=lumfunc_values_blue,
                mode="lines",
                name=f"$z={z}$",
                line=dict(width=2, color=z_colors[int((z / 5) * (len(z_colors) - 1))]),
            ),
            row=1,
            col=1,
        )

    # Plot red population
    for z in redshifts:
        lumfunc_values_red = lumfunc_m(M, z=z, **red_values)
        fig.add_trace(
            go.Scatter(
                x=M,
                y=lumfunc_values_red,
                mode="lines",
                showlegend=False,
                line=dict(width=2, color=z_colors[int((z / 5) * (len(z_colors) - 1))]),
            ),
            row=1,
            col=2,
        )

    # Update layout for plots
    fig.update_layout(
        title=f"Luminosity Function for {selected_population.capitalize()} Population",
        xaxis_title="M",
        yaxis_title="Luminosity Function",
        template="plotly_white",
        showlegend=True,
        height=1200,
        width=800,
    )

    fig.update_xaxes(row=1, col=1, title="$M$", range=[-30, -15], autorange="reversed")
    fig.update_yaxes(
        row=1, col=1, title="Luminosity function $\\phi(M)$", type="log", range=[-10, 1]
    )

    fig.update_xaxes(row=1, col=2, title="$M$", range=[-30, -15], autorange="reversed")
    fig.update_yaxes(row=1, col=2, type="log", range=[-10, 1])

    # Load and display image
    normalized_data = load_png_data_as_array(
        selected_population, selected_param, selected_param_value
    )
    fig.add_trace(
        go.Heatmap(
            z=normalized_data,
            colorscale="Gray",
            showscale=False,
            zmin=0,
            zmax=1,
        ),
        row=2,
        col=1,
    )
    fig.update_xaxes(row=2, col=1, showticklabels=False)
    fig.update_yaxes(row=2, col=1, showticklabels=False)

    # Update slider marks
    slider_marks = {
        i: f"{v:.3f}" if selected_param == "phi1" else f"{v:.2f}"
        for i, v in enumerate(param_values)
    }
    return fig, updated_slider_value, slider_marks, selected_param
