---
title: Sanic Extensions - Configuration
---

# Configuration

Sanic Extensions can be configured in all of the same ways that [you can configure Sanic](../../guide/deployment/configuration.md). That makes configuring Sanic Extensions very easy.

```python
app = Sanic("MyApp")
app.config.OAS_URL_PREFIX = "/apidocs"
```

However, there are a few more configuration options that should be considered.

## Manual `extend`

.. column:: 

    Even though Sanic Extensions will automatically attach to your application, you can manually choose `extend`. When you do that, you can pass all of the configuration values as a keyword arguments (lowercase).

.. column:: 

    ```python
    app = Sanic("MyApp")
    app.extend(oas_url_prefix="/apidocs")
    ```

.. column:: 

    Or, alternatively they could be passed all at once as a single `dict`.

.. column:: 

    ```python
    app = Sanic("MyApp")
    app.extend(config={"oas_url_prefix": "/apidocs"})
    ```

.. column:: 

    Both of these solutions suffers from the fact that the names of the configuration settings are not discoverable by an IDE. Therefore, there is also a type annotated object that you can use. This should help the development experience.

.. column:: 

    ```python
    from sanic_ext import Config

    app = Sanic("MyApp")
    app.extend(config=Config(oas_url_prefix="/apidocs"))
    ```

## Settings

.. note::

    Often, the easiest way to change these for an application (since they likely are not going to change dependent upon an environment), is to set them directly on the `app.config` object.

    Simply use the capitalized version of the configuration key as shown here:

    ```python
    app = Sanic("MyApp")
    app.config.OAS_URL_PREFIX = "/apidocs"
    ```

### `cors`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to enable CORS protection

### `cors_allow_headers`

- **Type**: `str`
- **Default**: `"*"`
- **Description**: Value of the header: `access-control-allow-headers`

### `cors_always_send`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to always send the header: `access-control-allow-origin`

### `cors_automatic_options`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to automatically generate `OPTIONS` endpoints for routes that do *not* already have one defined

### `cors_expose_headers`

- **Type**: `str`
- **Default**: `""`
- **Description**: Value of the header: `access-control-expose-headers`

### `cors_max_age`

- **Type**: `int`
- **Default**: `5`
- **Description**: Value of the header: `access-control-max-age`

### `cors_methods`

- **Type**: `str`
- **Default**: `""`
- **Description**: Value of the header: `access-control-access-control-allow-methods`

### `cors_origins`

- **Type**: `str`
- **Default**: `""`
- **Description**: Value of the header: `access-control-allow-origin`


.. warning:: 
    
    Be very careful if you place `*` here. Do not do this unless you know what you are doing as it can be a security issue.


### `cors_send_wildcard`

- **Type**: `bool`
- **Default**: `False`
- **Description**: Whether to send a wildcard origin instead of the incoming request origin

### `cors_supports_credentials`

- **Type**: `bool`
- **Default**: `False`
- **Description**: Value of the header: `access-control-allow-credentials`

### `cors_vary_header`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to add the `vary` header

### `http_all_methods`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Adds the HTTP `CONNECT` and `TRACE` methods as allowable

### `http_auto_head`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Automatically adds `HEAD` handlers to any `GET` routes

### `http_auto_options`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Automatically adds `OPTIONS` handlers to any routes without

### `http_auto_trace`

- **Type**: `bool`
- **Default**: `False`
- **Description**: Automatically adds `TRACE` handlers to any routes without

### `oas`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to enable OpenAPI specification generation

### `oas_autodoc`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to automatically extract OpenAPI details from the docstring of a route function

### `oas_ignore_head`

- **Type**: `bool`
- **Default**: `True`
- **Description**: WHen `True`, it will not add `HEAD` endpoints into the OpenAPI specification

### `oas_ignore_options`

- **Type**: `bool`
- **Default**: `True`
- **Description**: WHen `True`, it will not add `OPTIONS` endpoints into the OpenAPI specification

### `oas_path_to_redoc_html`

- **Type**: `Optional[str]`
- **Default**: `None`
- **Description**: Path to HTML file to override the existing Redoc HTML

### `oas_path_to_swagger_html`

- **Type**: `Optional[str]`
- **Default**: `None`
- **Description**: Path to HTML file to override the existing Swagger HTML

### `oas_ui_default`

- **Type**: `Optional[str]`
- **Default**: `"redoc"`
- **Description**: Which OAS documentation to serve on the bare `oas_url_prefix` endpoint; when `None` there will be no documentation at that location

### `oas_ui_redoc`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to enable the Redoc UI

### `oas_ui_swagger`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to enable the Swagger UI

### `oas_ui_swagger_version`

- **Type**: `str`
- **Default**: `"4.1.0"`
- **Description**: Which Swagger version to use

### `oas_uri_to_config`

- **Type**: `str`
- **Default**: `"/swagger-config"`
- **Description**: Path to serve the Swagger configuration

### `oas_uri_to_json`

- **Type**: `str`
- **Default**: `"/openapi.json"`
- **Description**: Path to serve the OpenAPI JSON

### `oas_uri_to_redoc`

- **Type**: `str`
- **Default**: `"/redoc"`
- **Description**: Path to Redoc

### `oas_uri_to_swagger`

- **Type**: `str`
- **Default**: `"/swagger"`
- **Description**: Path to Swagger

### `oas_url_prefix`

- **Type**: `str`
- **Default**: `"/docs"`
- **Description**: URL prefix for the Blueprint that all of the OAS documentation witll attach to

### `swagger_ui_configuration`

- **Type**: `Dict[str, Any]`
- **Default**: `{"apisSorter": "alpha", "operationsSorter": "alpha", "docExpansion": "full"}`
- **Description**: The Swagger documentation to be served to the frontend

### `templating_enable_async`

- **Type**: `bool`
- **Default**: `True`
- **Description**: Whether to set `enable_async` on the Jinja `Environment`

### `templating_path_to_templates`

- **Type**: `Union[str, os.PathLike, Sequence[Union[str, os.PathLike]]] `
- **Default**: `templates`
- **Description**: A single path, or multiple paths to where your template files are located

### `trace_excluded_headers`

- **Type**: `Sequence[str]`
- **Default**: `("authorization", "cookie")`
- **Description**: Which headers should be suppresed from responses to `TRACE` requests
