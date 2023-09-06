# Templating

Sanic Extensions can easily help you integrate templates into your route handlers. 

## Dependencies

**Currently, we only support [Jinja](https://github.com/pallets/jinja/).**

[Read the Jinja docs first](https://jinja.palletsprojects.com/en/3.1.x/) if you are unfamiliar with how to create templates.

Sanic Extensions will automatically setup and load Jinja for you if it is installed in your environment. Therefore, the only setup that you need to do is install Jinja:

```
pip install Jinja2
```

## Rendering a template from a file

There are three (3) ways for you:

1. Using a decorator to pre-load the template file
1. Returning a rendered `HTTPResponse` object
1. Hybrid pattern that creates a `LazyResponse`

Let's imagine you have a file called `./templates/foo.html`:

```html
<!DOCTYPE html>
<html lang="en">

    <head>
        <title>My Webpage</title>
    </head>

    <body>
        <h1>Hello, world!!!!</h1>
        <ul>
            {% for item in seq %}
            <li>{{ item }}</li>
            {% endfor %}
        </ul>
    </body>

</html>
```

Let's see how you could render it with Sanic + Jinja.

### Option 1 - as a decorator

.. column::

    The benefit of this approach is that the templates can be predefined at startup time. This will mean that less fetching needs to happen in the handler, and should therefore be the fastest option.

.. column::

    ```python
    @app.get("/")
    @app.ext.template("foo.html")
    async def handler(request: Request):
        return {"seq": ["one", "two"]}
    ```

### Option 2 - as a return object

.. column::

    This is meant to mimic the `text`, `json`, `html`, `file`, etc pattern of core Sanic. It will allow the most customization to the response object since it has direct control of it. Just like in other `HTTPResponse` objects, you can control headers, cookies, etc.

.. column::

    ```python
    from sanic_ext import render

    @app.get("/alt")
    async def handler(request: Request):
        return await render(
            "foo.html", context={"seq": ["three", "four"]}, status=400
        )
    ```

### Option 3 - hybrid/lazy

.. column::

    In this approach, the template is defined up front and not inside the handler (for performance). Then, the `render` function returns a `LazyResponse` that can be used to build a proper `HTTPResponse` inside the decorator.

.. column::

    ```python
    from sanic_ext import render

    @app.get("/")
    @app.ext.template("foo.html")
    async def handler(request: Request):
        return await render(context={"seq": ["five", "six"]}, status=400)
    ```

## Rendering a template from a string

.. column::

    Sometimes you may want to write (or generate) your template inside of Python code and _not_ read it from an HTML file. In this case, you can still use the `render` function we saw above. Just use `template_source`.

.. column::

    ```python
    from sanic_ext import render
    from textwrap import dedent

    @app.get("/")
    async def handler(request):
        template = dedent("""
            <!DOCTYPE html>
            <html lang="en">

                <head>
                    <title>My Webpage</title>
                </head>

                <body>
                    <h1>Hello, world!!!!</h1>
                    <ul>
                        {% for item in seq %}
                        <li>{{ item }}</li>
                        {% endfor %}
                    </ul>
                </body>

            </html>
        """)
        return await render(
            template_source=template,
            context={"seq": ["three", "four"]},
            app=app,
        )
    ```



.. note:: 

    In this example, we use `textwrap.dedent` to remove the whitespace in the beginning of each line of the multi-line string. It is not necessary, but just a nice touch to keep both the code and the generated source clean.



## Development and auto-reload

If auto-reload is turned on, then changes to your template files should trigger a reload of the server.

## Configuration

See `templating_enable_async` and `templating_path_to_templates` in [settings](./configuration.md#settings).
