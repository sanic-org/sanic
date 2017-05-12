from sanic import Sanic
from sanic.response import html
import plotly
import plotly.graph_objs as go

app = Sanic(__name__)


@app.route('/')
async def index(request):
    trace1 = go.Scatter(
        x=[0, 1, 2, 3, 4, 5],
        y=[1.5, 1, 1.3, 0.7, 0.8, 0.9]
    )
    trace2 = go.Bar(
        x=[0, 1, 2, 3, 4, 5],
        y=[1, 0.5, 0.7, -1.2, 0.3, 0.4]
    )

    data = [trace1, trace2]
    return html(plotly.offline.plot(data, auto_open=False, output_type='div'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
