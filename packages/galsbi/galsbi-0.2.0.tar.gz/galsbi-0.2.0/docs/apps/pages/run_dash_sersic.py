# Copyright (C) 2024 ETH Zurich
# Institute for Particle Physics and Astrophysics
# Author: Silvan Fischbacher
# created: Mon Nov 25 2024

import dash
import numpy as np
import plotly.graph_objects as go
from cosmic_toolbox import colors
from dash import callback, dcc, html
from dash.dependencies import Input, Output
from scipy.stats import betaprime

dash.register_page(__name__)

C = colors.get_colors()

# Generate x values
x = np.linspace(0, 10, 100)

# Initialize Dash app
# app = dash.Dash(__name__)
title = "Sérsic indices"

# Layout for the app
layout = html.Div(
    [
        html.Div(
            [
                html.Label("Blue Mode"),
                dcc.Slider(
                    id="blue_mode",
                    min=0.5,
                    max=5,
                    step=0.5,
                    value=1.5,
                    marks={i: str(i) for i in np.linspace(0.5, 5.5, 11)},
                ),
                html.Label("Blue Size"),
                dcc.Slider(
                    id="blue_size",
                    min=2,
                    max=20,
                    step=2,
                    value=5,
                    marks={i: str(i) for i in range(2, 20, 2)},
                ),
                html.Label("Red Mode"),
                dcc.Slider(
                    id="red_mode",
                    min=0.5,
                    max=5,
                    step=0.5,
                    value=3,
                    marks={i: str(i) for i in np.linspace(0.5, 5.5, 11)},
                ),
                html.Label("Red Size"),
                dcc.Slider(
                    id="red_size",
                    min=10,
                    max=100,
                    step=5,
                    value=50,
                    marks={i: str(i) for i in range(10, 101, 10)},
                ),
            ],
            style={"padding": "20px"},
        ),
        dcc.Graph(id="galaxy-plot"),
    ]
)


# Callback to update the plot
@callback(
    Output("galaxy-plot", "figure"),
    [
        Input("blue_mode", "value"),
        Input("blue_size", "value"),
        Input("red_mode", "value"),
        Input("red_size", "value"),
    ],
)
def update_plot(blue_mode, blue_size, red_mode, red_size):
    # Blue galaxy parameters
    a_blue = blue_mode * (blue_size + 1) + 1
    b_blue = blue_size
    y_blue = betaprime.pdf(x, a=a_blue, b=b_blue)

    # Red galaxy parameters
    a_red = red_mode * (red_size + 1) + 1
    b_red = red_size
    y_red = betaprime.pdf(x, a=a_red, b=b_red)

    # Create the plot
    fig = go.Figure()

    # Blue galaxy trace
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y_blue,
            mode="lines",
            name="blue galaxies",
            line=dict(color=C["b"]),
        )
    )

    # Red galaxy trace
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y_red,
            mode="lines",
            name="red galaxies",
            line=dict(color=C["r"]),
        )
    )

    # Add layout
    fig.update_layout(
        title="Sérsic index distribution",
        xaxis_title="Sérsic index",
        # yaxis_title='Density',
        template="plotly_white",
    )
    fig.update_xaxes(range=[0, 10])
    fig.update_yaxes(range=[0, 1.5], showticklabels=False)
    return fig
