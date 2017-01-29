SSL Example
-----------

Optionally pass in an SSLContext:

.. code:: python

  import ssl
  context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
  context.load_cert_chain("/path/to/cert", keyfile="/path/to/keyfile")

  app.run(host="0.0.0.0", port=8443, ssl=context)