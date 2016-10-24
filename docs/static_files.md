# Static Files

Both directories and files can be served by registering with static

## Example

```python
app = Sanic(__name__)

# Serves files from the static folder to the URL /static
app.static('./static', '/static')

# Serves the file /home/ubuntu/test.png when the URL /the_best.png
# is requested
app.static('/home/ubuntu/test.png', '/the_best.png')

app.run(host="0.0.0.0", port=8000)
```
