# Deploying

When it comes to deploying Sanic, there's not much to it, but there are
a few things to take note of.

## Workers

By default, Sanic listens in the main process using only 1 CPU core.
To crank up the juice, just specify the number of workers in the run
arguments like so:

```python
app.run(host='0.0.0.0', port=1337, workers=4)
```

Sanic will automatically spin up multiple processes and route
traffic between them.  We recommend as many workers as you have
available cores.

## Running via Command

If you like using command line arguments, you can launch a sanic server
by executing the module.  For example, if you initialized sanic as
app in a file named server.py, you could run the server like so:

`python -m sanic server.app --host=0.0.0.0 --port=1337 --workers=4`

With this way of running sanic, it is not necessary to run app.run in
your python file.  If you do, just make sure you wrap it in name == main
like so:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, workers=4)
```