# Run with: python simple_server.py
import ujson
from tornado import ioloop, web


class MainHandler(web.RequestHandler):
    def get(self):
        self.write(ujson.dumps({'test': True}))


app = web.Application([
    (r'/', MainHandler)
],  debug=False,
    compress_response=False,
    static_hash_cache=True
)

app.listen(8000)
ioloop.IOLoop.current().start()
