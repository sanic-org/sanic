SSL Example
-----------

Optionally pass in an SSLContext:

.. code:: python

  import ssl
  context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
  context.load_cert_chain("/path/to/cert", keyfile="/path/to/keyfile")

  app.run(host="0.0.0.0", port=8443, ssl=context)

You can also pass in the locations of a certificate and key as a dictionary:


.. code:: python

  ssl = {'cert': "/path/to/cert", 'key': "/path/to/keyfile"}
  app.run(host="0.0.0.0", port=8443, ssl=ssl)
