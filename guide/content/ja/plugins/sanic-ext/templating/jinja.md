---
title: Sanic Extensions - Jinja
---

# テンプレート設定

Sanic Extensions は、テンプレートをルートハンドラに簡単に統合するのに役立ちます。

## 依存関係

**現在、 [Jinja](https://github.com/pallets/jinja/)のみサポートしています。**

format@@0(https\://jinja.palletsprojects.com/en/3.1.x/) テンプレートを作成する方法に慣れていない場合は、format@@1を参照してください。

Sanic Extensionsは、環境にインストールされている場合、自動的にJinjaをセットアップしてロードします。 したがって、必要なセットアップはJinjaのインストールだけです。

```
pip install Jinja2
```

## ファイルからテンプレートをレンダリングする

あなたには3つの方法があります:

1. テンプレートファイルを事前にロードするデコレータを使用する
2. レンダリングされた `HTTPResponse` オブジェクトを返す
3. `LazyResponse`を作るハイブリッドパターン。

`./templates/foo.html`というファイルがあるとしましょう。

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

Sanic + Jinjaでどのようにレンダリングできるか見てみましょう。

### Option 1 - as a decorator

.. 列::

```
このアプローチの利点は、起動時にテンプレートをあらかじめ定義できることです。 これは、より少ないフェッチがハンドラで起こる必要があることを意味し、したがって最速のオプションであるべきです。
```

.. 列::

````
```python
@app.get("/")
@app.ext.template("foo.html")
async def handler(request: Request):
    return {"seq": ["one", "two"]}
```
````

### Option 2 - 戻り値オブジェクトとして

.. 列::

```
これはSanicの`text`、`json`、`html`、`file`などのパターンを模倣するものです。 それはそれを直接制御しているので、レスポンスオブジェクトにほとんどのカスタマイズを可能にする。 他の `HTTPResponse` オブジェクトと同様に、ヘッダー、クッキーなどを制御できます。
```

.. 列::

````
```python
from sanic_ext import render

@app.get("/alt")
async def handler(request: Request):
    return await render(
        "foo.html", context={"seq": ["three", "four"]}, status=400
    )
```
````

### Option 3 - hybrid/lazy

.. 列::

```
このアプローチでは、テンプレートはハンドラ内ではなく前面で定義されます(パフォーマンスのため)。 次に、`render` 関数はデコレータ内で適切な `HTTPResponse` を構築するために使用できる `LazyResponse` を返します。
```

.. 列::

````
```python
from sanic_ext import render

@app.get("/")
@app.ext.template("foo.html")
async def handler(request: Request):
    return await render(context={"seq": ["five", "six"]}, status=400)
```
````

## 文字列からテンプレートをレンダリング

.. 列::

```
Pythonコードの中でテンプレートを書く(または生成する)ことを望むことがあり、HTMLファイルから_not_読み込みを望むことがあります。 この場合でも、上記で見た「render」関数を使うことができます。`template_source` を使うだけです。
```

.. 列::

````
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
````

.. note::

```
この例では、複数行の文字列の先頭にある空白を削除するために `textwrap.dedent` を使用します。 それは必要ありませんが、コードと生成されたソースの両方をきれいに保つためにちょうどいいタッチです。
```

## 開発と自動再読み込み

自動再読み込みがオンになっている場合、テンプレートファイルへの変更によりサーバーの再読み込みが実行されます。

## 設定

[settings](./configuration.md#settings) の `templating_enable_async` と `templating_path_to_templates` を参照してください。
