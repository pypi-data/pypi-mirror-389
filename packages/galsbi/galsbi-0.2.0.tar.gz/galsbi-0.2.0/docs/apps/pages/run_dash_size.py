# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Mon Nov 25 2024


import os

import dash
import numpy as np
import plotly.colors
import plotly.graph_objects as go
from cosmic_toolbox import colors
from dash import Input, Output, State, callback, dcc, html
from plotly.subplots import make_subplots

C = colors.get_colors()

dash.register_page(__name__)


# Define functions for blue and red galaxies
def mu_logR50_blue(M, alpha=-0.4, beta=-0.3, gamma=0.1, M0=-20.5, **kwargs):
    return (
        -0.4 * alpha * M
        + (beta - alpha) * np.log10(1 + 10 ** (-0.4 * (M - M0)))
        + gamma
    )


def sigma_logR50(M, sigma1=0.5, sigma2=0.3, M0=-20.5, **kwargs):
    return sigma2 + (sigma1 - sigma2) / (1 + 10 ** (-0.8 * (M - M0)))


def mu_logR50_red(M, a=-0.4, b=0.2, **kwargs):
    return -0.4 * a * M + b


def load_png_data_as_array(population, parameter, value):
    # TODO: Replace this with the actual path to the processed images
    here = os.path.dirname(os.path.abspath(__file__))
    filename = (
        f"{here}/size_data/processed_images_{population}/"
        f"{parameter}_{value:.4f}_normalized.npy"
    )
    try:
        return np.load(filename)
    except FileNotFoundError:
        print(f"File {filename} not found")
        # Return an array of zeros if the file is not found
        return np.zeros((100, 100))  # Adjust dimensions if needed


def make_mathjax(string):
    return dcc.Markdown(string, mathjax=True)


blue_defaults = {
    "alpha": 0.25,
    "beta": 0.65,
    "gamma": -1.25,
    "sigma1": 0.1,
    "sigma2": 0.5,
    "eta": -0.75,
}
red_defaults = {"a": 0.65, "b": -5, "sigma1": 0.7, "sigma2": 0.75, "eta": -1}
n_sliders = 11
central = n_sliders // 2

# Generate parameter values for sliders separately for blue and red populations
blue_alpha_values = np.linspace(-0.35, 0.85, n_sliders)
blue_beta_values = np.linspace(-0.85, 2.15, n_sliders)
blue_gamma_values = np.linspace(-5, 2.5, n_sliders)
blue_sigma1_values = np.linspace(0, 0.2, n_sliders)
blue_sigma2_values = np.linspace(0, 1, n_sliders)
blue_eta_values = np.linspace(-1.5, 0, n_sliders)
red_a_values = np.linspace(0.15, 1.15, n_sliders)
red_b_values = np.linspace(-10, 0, n_sliders)
red_sigma1_values = np.linspace(0.4, 1, n_sliders)
red_sigma2_values = np.linspace(0.5, 1, n_sliders)
red_eta_values = np.linspace(-2, 0, n_sliders)

# Redshifts and corresponding colors
redshifts = np.linspace(0, 5, 11)
colors = plotly.colors.sequential.Viridis
z_colors = [
    colors[int((i / (len(redshifts) - 1)) * (len(colors) - 1))]
    for i in range(len(redshifts))
]

# Generate M (absolute magnitude) values
M = np.linspace(-25, -15, 100)

# Dash app initialization
# app = dash.Dash(__name__)

# Dropdown for population selection
layout = html.Div(
    [
        dcc.Store(id="last-selected-param-size", data="alpha"),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="population-dropdown-size",
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
                            id="param-dropdown-size",
                            style={"width": "100%", "padding": "15px"},
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
            id="param-slider-size",
            min=0,
            max=n_sliders - 1,
            step=1,
            value=5,
            tooltip={"placement": "bottom", "always_visible": False},
            updatemode="drag",
        ),
        dcc.Graph(id="graph-size", mathjax=True),
    ]
)


# Update parameters based on selected population
@callback(
    Output("param-dropdown-size", "options"),
    Output("param-dropdown-size", "value"),
    Input("population-dropdown-size", "value"),
)
def update_parameter_dropdown(selected_population):
    if selected_population == "blue":
        return [
            {"label": make_mathjax("$\\alpha$"), "value": "alpha"},
            {"label": make_mathjax("$\\beta$"), "value": "beta"},
            {"label": make_mathjax("$\\gamma$"), "value": "gamma"},
            {"label": make_mathjax("$\\sigma_1$"), "value": "sigma1"},
            {"label": make_mathjax("$\\sigma_2$"), "value": "sigma2"},
            {"label": make_mathjax("$\\eta$"), "value": "eta"},
        ], "alpha"
    elif selected_population == "red":
        return [
            {"label": make_mathjax("$a$"), "value": "a"},
            {"label": make_mathjax("$b$"), "value": "b"},
            {"label": make_mathjax("$\\sigma_1$"), "value": "sigma1"},
            {"label": make_mathjax("$\\sigma_2$"), "value": "sigma2"},
            {"label": make_mathjax("$\\eta$"), "value": "eta"},
        ], "a"


# Update graph based on selected population and parameter
@callback(
    [
        Output("graph-size", "figure"),
        Output("param-slider-size", "value"),
        Output("param-slider-size", "marks"),
        Output("last-selected-param-size", "data"),
    ],
    [
        Input("population-dropdown-size", "value"),
        Input("param-dropdown-size", "value"),
        Input("param-slider-size", "value"),
    ],
    State("last-selected-param-size", "data"),
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
                blue_beta_values
                if selected_param == "beta"
                else (
                    blue_gamma_values
                    if selected_param == "gamma"
                    else (
                        blue_sigma1_values
                        if selected_param == "sigma1"
                        else (
                            blue_sigma2_values
                            if selected_param == "sigma2"
                            else blue_eta_values
                        )
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
            "beta": (
                selected_param_value
                if selected_param == "beta"
                else blue_defaults["beta"]
            ),
            "gamma": (
                selected_param_value
                if selected_param == "gamma"
                else blue_defaults["gamma"]
            ),
            "sigma1": (
                selected_param_value
                if selected_param == "sigma1"
                else blue_defaults["sigma1"]
            ),
            "sigma2": (
                selected_param_value
                if selected_param == "sigma2"
                else blue_defaults["sigma2"]
            ),
            "eta": (
                selected_param_value
                if selected_param == "eta"
                else blue_defaults["eta"]
            ),
        }
        red_values = red_defaults  # Use red defaults if blue is selected

    elif selected_population == "red":
        param_values = (
            red_a_values
            if selected_param == "a"
            else (
                red_b_values
                if selected_param == "b"
                else (
                    red_sigma1_values
                    if selected_param == "sigma1"
                    else (
                        red_sigma2_values
                        if selected_param == "sigma2"
                        else red_eta_values
                    )
                )
            )
        )
        updated_slider_value = central if is_dropdown_changed else slider_value
        selected_param_value = param_values[updated_slider_value]

        red_values = {
            "a": (selected_param_value if selected_param == "a" else red_defaults["a"]),
            "b": (selected_param_value if selected_param == "b" else red_defaults["b"]),
            "sigma1": (
                selected_param_value
                if selected_param == "sigma1"
                else red_defaults["sigma1"]
            ),
            "sigma2": (
                selected_param_value
                if selected_param == "sigma2"
                else red_defaults["sigma2"]
            ),
            "eta": (
                selected_param_value if selected_param == "eta" else red_defaults["eta"]
            ),
        }
        blue_values = blue_defaults

    # Create plot with the specified parameter values for each population
    fig = make_subplots(
        rows=3,
        cols=2,
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"colspan": 2, "type": "heatmap"}, None],
        ],
        row_heights=[0.2, 0.1, 0.7],
        column_widths=[0.5, 0.5],
        vertical_spacing=0.1,
        subplot_titles=[
            "Blue size distribution",
            "Red size distribution",
            "Blue size scatter",
            "Red size scatter",
            "HSC-deep-field simulation",
        ],
    )

    # Plot blue population
    for z in redshifts:
        mu = np.exp(mu_logR50_blue(M, **blue_values)) * (1 + z) ** blue_values["eta"]
        sigma = sigma_logR50(M, **blue_values)
        fig.add_trace(
            go.Scatter(
                x=M,
                y=mu,
                mode="lines",
                name=f"$z={z}$",
                line=dict(width=2, color=z_colors[int((z / 5) * (len(z_colors) - 1))]),
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(
            x=M,
            y=sigma,
            mode="lines",
            line=dict(width=2, color=C["b"]),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    # Plot red population
    for z in redshifts:
        mu = np.exp(mu_logR50_red(M, **red_values)) * (1 + z) ** red_values["eta"]
        sigma = sigma_logR50(M, **red_values)
        fig.add_trace(
            go.Scatter(
                x=M,
                y=mu,
                mode="lines",
                name=f"$z={z}$",
                line=dict(width=2, color=z_colors[int((z / 5) * (len(z_colors) - 1))]),
                showlegend=False,
            ),
            row=1,
            col=2,
        )
    fig.add_trace(
        go.Scatter(
            x=M,
            y=sigma,
            mode="lines",
            line=dict(width=2, color=C["r"]),
            showlegend=False,
        ),
        row=2,
        col=2,
    )

    # Update layout for plots
    fig.update_layout(
        title=f"Size distribution for {selected_population.capitalize()} Population",
        xaxis_title="M",
        yaxis_title="Luminosity Function",
        template="plotly_white",
        showlegend=True,
        height=1200,
        width=800,
    )

    fig.update_xaxes(row=1, col=1, title="$M$", range=[-25, -15], autorange="reversed")
    fig.update_yaxes(
        row=1,
        col=1,
        title="$\\mu_{\\log r_{50}}(M) \\, \\mathrm{[kpc]}$",
        type="log",
        range=[-3, 2],
    )

    fig.update_xaxes(row=1, col=2, title="$M$", range=[-25, -15], autorange="reversed")
    fig.update_yaxes(row=1, col=2, type="log", range=[-3, 2])

    fig.update_xaxes(row=2, col=1, title="$M$", range=[-25, -15], autorange="reversed")
    fig.update_yaxes(row=2, col=1, title="$\\sigma_{\\log r_{50}}(M)$", range=[0, 1])

    fig.update_xaxes(row=2, col=2, title="$M$", range=[-25, -15], autorange="reversed")
    fig.update_yaxes(row=2, col=2, range=[0, 1])

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
        row=3,
        col=1,
    )
    fig.update_xaxes(row=3, col=1, showticklabels=False)
    fig.update_yaxes(row=3, col=1, showticklabels=False)

    # Update slider marks
    slider_marks = {
        i: f"{v:.3f}" if selected_param == "phi1" else f"{v:.2f}"
        for i, v in enumerate(param_values)
    }
    return fig, updated_slider_value, slider_marks, selected_param
