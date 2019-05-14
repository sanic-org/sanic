# Getting Started

Make sure you have both [pip](https://pip.pypa.io/en/stable/installing/) and at
least version 3.6 of Python before starting. Sanic uses the new `async`/`await`
syntax, so earlier versions of python won't work.

## 1. Install Sanic

  ```
  pip3 install sanic
  ```

To install sanic without `uvloop` or `ujson` using bash, you can provide either or both of these environmental variables
using any truthy string like `'y', 'yes', 't', 'true', 'on', '1'` and setting the `SANIC_NO_X` (`X` = `UVLOOP`/`UJSON`) 
to true will stop that features installation.

```bash
SANIC_NO_UVLOOP=true SANIC_NO_UJSON=true pip3 install sanic
```

##  2. Create a file called `main.py`

  ```python
  from sanic import Sanic
  from sanic.response import json

  app = Sanic()

  @app.route("/")
  async def test(request):
      return json({"hello": "world"})

  if __name__ == "__main__":
      app.run(host="0.0.0.0", port=8000)
  ```

## 3. Run the server

  ```
  python3 main.py
  ```

## 4. Check your browser

Open the address `http://0.0.0.0:8000` in your web browser. You should see
the message *Hello world!*.

You now have a working Sanic server!
