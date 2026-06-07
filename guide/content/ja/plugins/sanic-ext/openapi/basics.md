---
title: サニックエクステンション - Basic OAS
---

# 基本

.. note::

```
Sanic ExtensionsのOpenAPI実装は、[`sanic-openapi`](https://github.com/sanic-org/sanic-openapi)のOAS3実装に基づいています。 実際、Sanic Extensionsは、Sanic Extensionsのリリース時にメンテナンスモードになったプロジェクトの後継者として大きな意味を持っています。 以前に `sanic-openapi` を使用していた場合は、Sanic Extensionsへのアップグレードの簡単なパスが必要です。 残念ながら、このプロジェクトは OAS2 仕様をサポートしていません。
```

.. 列::

```
Sanic Extensionsは、[v3.0 OpenAPI仕様](https://swagger.io/specification/)を使用して自動的に生成されたAPIドキュメントを提供しています。特別なことはありません。
```

.. 列::

````
```python
from sanic import Sanic

app = Sanic("MyApp")

# Add all of your views
```
````

これを行うと、既存のアプリケーションに基づいてすでに生成された美しいドキュメントが表示されます。

- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/docs/redoc](http://localhost:8000/docs/redoc)
- [http://localhost:8000/docs/swagger](http://localhost:8000/docs/swagger)

ドキュメントのルート変更について学ぶには、[section on configuration](../configuration.md) をチェックしてください。 2 つの UI のいずれかをオフにして、`/docs` ルートでどのUIが利用できるかをカスタマイズすることもできます。

.. 列::

```
Using [Redoc](https://github.com/Redocly/redoc)

![Redoc](/assets/images/sanic-ext-redoc.png)
```

.. 列::

```
or [Swagger UI](https://github.com/swagger-api/swagger-ui)

![Swagger UI](/assets/images/sanic-ext-swagger.png)
```

## 仕様メタデータの変更

.. 列::

```
メタデータを変更したい場合は、 `describe` メソッドを使用してください。

`dedent` の例では、複数行の文字列を少しクリーナーにするために `description` 引数を使用しています。 これは必要ありません。任意の文字列値を渡すことができます。
```

.. 列::

````
```python
from textwrap import dedent

app.ext.openapi.describe(
    "Testing API",
    version="1.2.3",
    description=dedent(
        """
        # Info
        This is a description. It is a good place to add some _extra_ doccumentation.

        **MARKDOWN** is supported.
        """
    ),
)
```
````

