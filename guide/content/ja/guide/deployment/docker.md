# Docker Deployment

## はじめに

長い間、環境はデプロイにとって困難な問題でした。 プロジェクトに矛盾する構成がある場合は、それらの解決に多くの時間を費やす必要があります。 幸いなことに、仮想化は私たちに良い解決策を提供します。 Dockerはその一つです。 Dockerを知らない場合は、format@@0(https://www.docker.com/)をご覧ください。

## ビルド画像

簡単なプロジェクトから始めましょう 例として、Sanicプロジェクトを使用します。 プロジェクトのパスは `/path/to/SanicDocker` であるとします。

.. 列::

```
ディレクトリ構造は以下のようになります:
```

.. 列::

````
```text
# /path/to/SanicDocker
SanicDocker
├── requirements.txt
├── dockerfile
├── server.py
```
````

.. 列::

```
`server.py`のコードは次のようになります。
```

.. 列::

````
```python
app = Sanic("MySanicApp")

@app.get('/')
async def hello(request):
    return text("OK!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```
````

.. note::

```
ホストは 127.0.0.1 ではありません。docker container, 127.0.0. は、コンテナのデフォルトのネットワークインターフェイスです。コンテナだけが他のコンテナと通信できます。 詳細はformat@@0(https://docs.docker.com/engine/reference/commandline/network/)をご覧ください。
```

コードの準備ができました。`Dockerfile`を書きましょう。

```Dockerfile

FROM sanicframework/sanic:3.8-latest

WORKDIR /sanic

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "server.py"]
```

次のコマンドを実行してイメージをビルドします。

```shell
docker build -t my-sanic-image .
```

## コンテナを起動

.. 列::

```
イメージ構築後、コンテナは `my-sanic-image` を使用します。
```

.. 列::

````
```shell
docker run --name mysanic -p 8000:8000 -d my-sanic-image
```
````

.. 列::

```
`http://localhost:8000`で結果を確認できます。
```

.. 列::

````
```text
OK!
```
````

## docker-compose を使用

プロジェクトが複数のサービスで構成されている場合は、 [docker-compose](https://docs.docker.com/compose/) を使用して管理できます。

例えば、`my-sanic-image` と `nginx` をデプロイし、nginx アクセスの sanic サーバーを使用して実現します。

.. 列::

```
まず、nginxの設定ファイルを準備する必要があります。`mysanic.conf`という名前のファイルを作成します。
```

.. 列::

````
```nginx
server {
    listen 80;
    listen [::]:80;
    location / {
      proxy_pass http://mysanic:8000/;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection upgrade;
      proxy_set_header Accept-Encoding gzip;
    }
}
```
````

.. 列::

```
次に、`docker-compose.yml` ファイルを準備する必要があります。内容は以下のとおりです:
```

.. 列::

````
```yaml
version: "3"

services:
  mysanic:
    image: my-sanic-image
    ports:
      - "8000:8000"
    restart: always

  mynginx:
    image: nginx:1.13.6-alpine
    ports:
      - "80:80"
    depends_on:
      - mysanic
    volumes:
      - ./mysanic.conf:/etc/nginx/conf.d/mysanic.conf
    restart: always

networks:
  default:
    driver: bridge
```
````

.. 列::

```
その後、次のように開始できます。
```

.. 列::

````
```shell
docker-compose up -d
```
````

.. 列::

```
`http://localhost:80`で結果を確認できます。
```

.. 列::

````
```text
OK!
```
````

