import dash
from dash import Dash, dcc, html

app = Dash(
    __name__,
    use_pages=True,
    url_base_pathname='/galsbi-dash/'
)


app.layout = html.Div(
    [
        dash.page_container,
    ]
)


if __name__ == "__main__":
    app.run(debug=True, port=80, host="0.0.0.0")
