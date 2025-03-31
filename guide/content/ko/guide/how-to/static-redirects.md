# "Static" Redirects

> How do I configure static redirects?

## `app.py`

```python
### SETUP ###
import typing
import sanic, sanic.response

# Create the Sanic app
app = sanic.Sanic(__name__)

# This dictionary represents your "static"
# redirects. For example, these values
# could be pulled from a configuration file.
REDIRECTS = {
    '/':'/hello_world',                     # Redirect '/' to '/hello_world'
    '/hello_world':'/hello_world.html'      # Redirect '/hello_world' to 'hello_world.html'
}

# This function will return another function
# that will return the configured value
# regardless of the arguments passed to it.
def get_static_function(value:typing.Any) -> typing.Callable[..., typing.Any]:
    return lambda *_, **__: value

### ROUTING ###
# Iterate through the redirects
for src, dest in REDIRECTS.items():                            
    # Create the redirect response object         
    response:sanic.HTTPResponse = sanic.response.redirect(dest)

    # Create the handler function. Typically,
    # only a sanic.Request object is passed
    # to the function. This object will be 
    # ignored.
    handler = get_static_function(response)

    # Route the src path to the handler
    app.route(src)(handler)

# Route some file and client resources
app.static('/files/', 'files')
app.static('/', 'client')

### RUN ###
if __name__ == '__main__':
    app.run(
        '127.0.0.1',
        10000
    )
```

## `client/hello_world.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello World</title>
</head>
<link rel="stylesheet" href="/hello_world.css">
<body>
    <div id='hello_world'>
        Hello world!
    </div>
</body>
</html>
```

## `client/hello_world.css`

```css
#hello_world {
    width: 1000px;
    margin-left: auto;
    margin-right: auto;
    margin-top: 100px;

    padding: 100px;
    color: aqua;
    text-align: center;
    font-size: 100px;
    font-family: monospace;

    background-color: rgba(0, 0, 0, 0.75);

    border-radius: 10px;
    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.75);
}

body {
    background-image: url("/files/grottoes.jpg");
    background-repeat: no-repeat;
    background-size: cover;
}
```

## `files/grottoes.jpg`

![lake](/assets/images/grottoes.jpg)

---

Also, checkout some resources from the community:

- [Static Routing Example](https://github.com/Perzan/sanic-static-routing-example)
