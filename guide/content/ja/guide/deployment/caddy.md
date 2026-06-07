# キャディデプロイメント

## はじめに

CaddyはHTTP/3までサポートする最先端のWebサーバーとプロキシです。 そのシンプルさは、最小限の設定と、Let's Encrypt からドメイン用の TLS 証明書を自動的に調達するための構築機能にあります。 この設定では、127.0.0でローカルで動作するようにSanicアプリケーションを設定します。 :8001, Caddy がドメインの example.com の公開サーバーの役割を果たしています。

Windows、Linux、Macでお気に入りのパッケージメニューからCaddyをインストールできます。 パッケージ名は `caddy` です。

## プロキシされたサニックアプリ

```python
from sanic import Sanic
from sanic.response import text

app = Sanic("proxied_example")

@app.get("/")
def index(request):
    # This should display external (public) addresses:
    return text(
        f"{request.remote_addr} connected to {request.url_for('index')}\n"
        f"Forwarded: {request.forwarded}\n"
    )
```

このアプリケーションを実行するには、`proxied_example.py` として保存し、sanic コマンドラインインターフェイスを以下のように使用します。

```bash
SANIC_PROXIES_COUNT=1 sanic proxied_example --port 8001
```

SANIC_PROXIES_COUNT環境変数を設定すると、SanicはCaddyから送信されたX-Forward-\*ヘッダを信頼するように命令します。 クライアントのIPアドレスやその他の情報を正しく識別できるようにします。

## キャディはシンプルです

他の Web サーバーが動作していない場合は、Caddy CLI を実行できます（Linux では `sudo` が必要です）。

```bash
caddy リバース・プロキシ --from example.com --to :8001
```

これはあなたのドメインの証明書、http-to-https リダイレクト、プロキシヘッダ、ストリーミング、WebSocketを含む完全なサーバーです。 Sanicアプリケーションは、HTTPバージョン1、2、3で指定されたドメインで利用可能になるはずです。 H3通信を有効にするには、ファイアウォールでUDP/443 を開いてください。

すべて完了しましたか？

すぐに、複数のサーバーが必要になります。または、設定ファイルが入ってくる詳細を制御する必要があります。 上記のコマンドは `Caddyfile` と同等で、インストールの良い開始点として機能します。

```
example.com {
    reverse_proxy localhost:8001
}
```

Linuxディストリビューションによっては、`/etc/caddy/Caddy/Caddy/Caddyfile` から設定を読み込むようにインストールされているものもあります。これは `import /etc/caddy/conf.d/*` です。 そうでない場合は、 `caddy run` をシステムサービスとして手動で実行し、適切な設定ファイルを指す必要があります。 もしくは、永続的な設定変更には、 `caddy run --resume` を使用して Caddy API モードを使用してください。 Caddyfile の読み込みはすべての設定を置き換えるため、 `caddy-api` は従来の方法では設定できません。

## 高度な構成

時には、静的なファイルとハンドラをサイトルートで混在させ、よりクリーンな URL を得る必要があるかもしれません。 Sanicでは、\`app.static("/", "static", index="index.html")を使用します。 ただし、パフォーマンスを向上させるために、静的ファイルをCaddyにオフロードすることができます。

```
app.example.com {
    # Look for static files first, proxy to Sanic if not found
    route {
        file_server {
            root /srv/sanicexample/static
            precompress br                     # brotli your large scripts and styles
            pass_thru
        }
        reverse_proxy unix//tmp/sanic.socket   # sanic --unix /tmp/sanic.socket
    }
}
```

詳細については、format@@0(https://caddyserver.com/docs/)を参照してください。
