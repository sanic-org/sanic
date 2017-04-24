from sanic import Sanic

from sanic_session import InMemorySessionInterface
from sanic_jinja2 import SanicJinja2

import json
import plotly

import pandas as pd
import numpy as np

app = Sanic(__name__)

jinja = SanicJinja2(app)
session = InMemorySessionInterface(cookie_name=app.name, prefix=app.name)

@app.middleware('request')
async def print_on_request(request):
	print(request.headers)
	await session.open(request)

@app.middleware('response')
async def print_on_response(request, response):
	await session.save(request, response)



@app.route('/')
async def index(request):
    rng = pd.date_range('1/1/2011', periods=7500, freq='H')
    ts = pd.Series(np.random.randn(len(rng)), index=rng)

    graphs = [
        dict(
            data=[
                dict(
                    x=[1, 2, 3],
                    y=[10, 20, 30],
                    type='scatter'
                ),
            ],
            layout=dict(
                title='first graph'
            )
        ),

        dict(
            data=[
                dict(
                    x=[1, 3, 5],
                    y=[10, 50, 30],
                    type='bar'
                ),
            ],
            layout=dict(
                title='second graph'
            )
        ),

        dict(
            data=[
                dict(
                    x=ts.index,  # Can use the pandas data structures directly
                    y=ts
                )
            ]
        )
    ]

    # Add "ids" to each of the graphs to pass up to the client
    # for templating
    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    return jinja.render('index.html', request,
                           ids=ids,
                           graphJSON=graphJSON)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)