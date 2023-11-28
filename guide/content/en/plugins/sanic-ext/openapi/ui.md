# UI

Sanic Extensions comes with both Redoc and Swagger interfaces. You have a choice to use one, or both of them. Out of the box, the following endpoints are setup for you, with the bare `/docs` displaying Redoc.

- `/docs`
- `/docs/openapi.json`
- `/docs/redoc`
- `/docs/swagger`
- `/docs/openapi-config`

## Config options

| **Key**                    | **Type**        | **Default**         | **Desctiption**                                              |
| -------------------------- | --------------- | ------------------- | ------------------------------------------------------------ |
| `OAS_IGNORE_HEAD`          | `bool`          | `True`              | Whether to display `HEAD` endpoints.                         |
| `OAS_IGNORE_OPTIONS`       | `bool`          | `True`              | Whether to display `OPTIONS` endpoints.                      |
| `OAS_PATH_TO_REDOC_HTML`   | `Optional[str]` | `None`              | Path to HTML to override the default Redoc HTML              |
| `OAS_PATH_TO_SWAGGER_HTML` | `Optional[str]` | `None`              | Path to HTML to override the default Swagger HTML            |
| `OAS_UI_DEFAULT`           | `Optional[str]` | `"redoc"`           | Can be set to `redoc` or `swagger`. Controls which UI to display on the base route. If set to `None`, then the base route will not be setup. |
| `OAS_UI_REDOC`             | `bool`          | `True`              | Whether to enable Redoc UI.                                  |
| `OAS_UI_SWAGGER`           | `bool`          | `True`              | Whether to enable Swagger UI.                                |
| `OAS_URI_TO_CONFIG`        | `str`           | `"/openapi-config"` | URI path to the OpenAPI config used by Swagger               |
| `OAS_URI_TO_JSON`          | `str`           | `"/openapi.json"`   | URI path to the JSON document.                               |
| `OAS_URI_TO_REDOC`         | `str`           | `"/redoc"`          | URI path to Redoc.                                           |
| `OAS_URI_TO_SWAGGER`       | `str`           | `"/swagger"`        | URI path to Swagger.                                         |
| `OAS_URL_PREFIX`           | `str`           | `"/docs"`           | URL prefix to use for the Blueprint for OpenAPI docs.        |
