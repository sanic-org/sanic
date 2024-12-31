---
content_class: 更新履歴
---

# 更新履歴

🔶 現在のリリース\
🔷 LTS リリース

## バージョン24.12.0 🔶🔷

_現在のバージョン_

### 特徴

- [#3019](https://github.com/sanic-org/sanic/pull/3019) `sanic` CLI にカスタムコマンドを追加する

### バグ修正

- [#2992](https://github.com/sanic-org/sanic/pull/2992) `mixins.startup.serve` UnboundLocalError を修正
- [#3000](https://github.com/sanic-org/sanic/pull/3000) `dumps`呼び出し可能な戻り値タイプの`bytes`に対する`JSONResponse`メソッドの型迷惑を修正しました
- [#3009](https://github.com/sanic-org/sanic/pull/3009) `False`に設定すると、`SanicException.quiet`属性の処理を修正します。
- [#3014](https://github.com/sanic-org/sanic/pull/3014) 入力内容をクリーンアップする
- [#3015](https://github.com/sanic-org/sanic/pull/3015) 該当する場合、プロセスグループ全体を倒す
- [#3016](https://github.com/sanic-org/sanic/pull/3016) HTTPMethodView クラスで get メソッドの互換性のない型注釈を修正しました

### 非推奨と削除

- [#3020](https://github.com/sanic-org/sanic/pull/3020) Python 3.8 サポートを削除

### 開発者のインフラストラクチャ

- [#3017](https://github.com/sanic-org/sanic/pull/3017) Cleanup setup.cfg

### ドキュメントの改善

- [#3007](https://github.com/sanic-org/sanic/pull/3007) `sanic-ext`のドキュメントでtypoを修正する

## バージョン 24.6.0

### 特徴

- [#2838](https://github.com/sanic-org/sanic/pull/2838) リクエストクッキー「getlist」を簡素化する
- [#2850](https://github.com/sanic-org/sanic/pull/2850) Unix ソケットは `pathlib.Path` を使用できるようになりました
- [#2931](https://github.com/sanic-org/sanic/pull/2931) [#2958](https://github.com/sanic-org/sanic/pull/2958) ログの改善点
- [#2947](https://github.com/sanic-org/sanic/pull/2947) .message フィールドを空ではない例外にする
- [#2961](https://github.com/sanic-org/sanic/pull/2961) [#2964](https://github.com/sanic-org/sanic/pull/2964) カスタム名生成を許可する

### バグ修正

- [#2919](https://github.com/sanic-org/sanic/pull/2919) websockets で非推奨の通知を削除する
- [#2937](https://github.com/sanic-org/sanic/pull/2937) ASGIモードで応答ストリーミングエラーを解決する
- [#2959](https://github.com/sanic-org/sanic/pull/2959) Python 3.12 deprecation notic を解決する
- [#2960](https://github.com/sanic-org/sanic/pull/2960) 騒々しい例外に対する適切な意図を確認する
- [#2970](https://github.com/sanic-org/sanic/pull/2970) [#2978](https://github.com/sanic-org/sanic/pull/2978) 3.12 の不足している依存関係を修正します。
- [#2971](https://github.com/sanic-org/sanic/pull/2971) ミドルウェアの例外が見つからないルートでエラーが発生した問題を修正しました。
- [#2973](https://github.com/sanic-org/sanic/pull/2973) `transport.close`と`transport.abort`のchedulingロジックを解決します。
- [#2976](https://github.com/sanic-org/sanic/pull/2976) `secure=False`で作成されたクッキーの削除を修正
- [#2979](https://github.com/sanic-org/sanic/pull/2979) 体長が悪い場合にエラーを投げます
- [#2980](https://github.com/sanic-org/sanic/pull/2980) ボディエンコーディングの不良時にエラーを投げる。

### 非推奨と削除

- [#2899](https://github.com/sanic-org/sanic/pull/2899) HTTPX が影響を受けない環境の REPL から誤った行を削除します
- [#2962](https://github.com/sanic-org/sanic/pull/2962) マージエンティティヘッダーの削除

### 開発者のインフラストラクチャ

- [#2882](https://github.com/sanic-org/sanic/pull/2882) [#2896](https://github.com/sanic-org/sanic/pull/2896) ポート選択によるテストを改善するために動的なポートフィクスチャーを適用する
- [#2887](https://github.com/sanic-org/sanic/pull/2887) docker image builds の更新
- [#2932](https://github.com/sanic-org/sanic/pull/2932) Ruff を使ってコードベースをクリーンアップする

### ドキュメントの改善

- [#2924](https://github.com/sanic-org/sanic/pull/2924) html5tagger page
- [#2930](https://github.com/sanic-org/sanic/pull/2930) Sanic Extensions README.md
- [#2934](https://github.com/sanic-org/sanic/pull/2934) ヘルスチェック文書に文脈を追加する
- [#2936](https://github.com/sanic-org/sanic/pull/2936) ワーカーマネージャーのドキュメントを改善する
- [#2955](https://github.com/sanic-org/sanic/pull/2955) `request.md`のフォーマットが間違っているのを修正しました

## バージョン23.12.0 🔷

### 特徴

- [#2775](https://github.com/sanic-org/sanic/pull/2775) 任意のプロセスを開始して再起動する
- [#2811](https://github.com/sanic-org/sanic/pull/2811) シャットダウン時のクリーナープロセス管理
- [#2812](https://github.com/sanic-org/sanic/pull/2812) オープンなウェブソケットでタスクのトレースバックを抑制する
- [#2822](https://github.com/sanic-org/sanic/pull/2822) リスナーとシグナルの優先順位付け
- [#2831](https://github.com/sanic-org/sanic/pull/2831) メモリ消費量を削減
- [#2837](https://github.com/sanic-org/sanic/pull/2837) ベアクッキーを受け入れます
- [#2841](https://github.com/sanic-org/sanic/pull/2841) `websocket.handler.<before/after/exception>` signers を追加する
- [#2805](https://github.com/sanic-org/sanic/pull/2805) 変更されたファイルを追加してトリガーリスナーをリロードする
- [#2813](https://github.com/sanic-org/sanic/pull/2813) シンプルなシグナルを許可する
- [#2827](https://github.com/sanic-org/sanic/pull/2827) `Sanic.event()`の機能性と一貫性を向上させます
- [#2851](https://github.com/sanic-org/sanic/pull/2851) 1 バイトの範囲リクエストを許可する
- [#2854](https://github.com/sanic-org/sanic/pull/2854) ウェブソケットリクエストに適した`Request.scheme` を改善
- [#2858](https://github.com/sanic-org/sanic/pull/2858) Sanic `Request`をWebsockets `Request`にハンドシェイク変換する
- [#2859](https://github.com/sanic-org/sanic/pull/2859) `sanic` CLI に REPL を追加します
- [#2870](https://github.com/sanic-org/sanic/pull/2870) Python 3.12 サポートを追加
- [#2875](https://github.com/sanic-org/sanic/pull/2875) マルチプロセッシングコンテキストの競合時の例外の改善

### バグ修正

- [#2803](https://github.com/sanic-org/sanic/pull/2803) MOTD の追加データ表示を修正する

### 開発者のインフラストラクチャ

- [#2796](https://github.com/sanic-org/sanic/pull/2796) ユニットテストケースをリファクタリングする
- [#2801](https://github.com/sanic-org/sanic/pull/2801) CPUが1つだけの場合、`test_fast`を修正する
- [#2807](https://github.com/sanic-org/sanic/pull/2807) autocsum の制約を追加する (lint issum in old package version)
- [#2808](https://github.com/sanic-org/sanic/pull/2808) GitHubアクションをリファクタリングする
- [#2814](https://github.com/sanic-org/sanic/pull/2814) git push で CI パイプラインを実行
- [#2846](https://github.com/sanic-org/sanic/pull/2846) 古いパフォーマンステスト/ベンチマーク
- [#2848](https://github.com/sanic-org/sanic/pull/2848) Makefile cleanup
- [#2865](https://github.com/sanic-org/sanic/pull/2865)
  [#2869](https://github.com/sanic-org/sanic/pull/2869)
  [#2872](https://github.com/sanic-org/sanic/pull/2872)
  [#2879](https://github.com/sanic-org/sanic/pull/2879)
  ツールチェーンにラフを追加
- [#2866](https://github.com/sanic-org/sanic/pull/2866) alt svc テストが明示的なバッファnbytes でローカルで実行されるように修正する
- [#2877](https://github.com/sanic-org/sanic/pull/2877) Pythonの信頼できるパブリッシャーをデプロイに使用する
- [#2882](https://github.com/sanic-org/sanic/pull/2882) テストスイート内の対象となる場所に動的ポートフィクスチャーを導入する

### ドキュメントの改善

- [#2781](https://github.com/sanic-org/sanic/pull/2781)
  [#2821](https://github.com/sanic-org/sanic/pull/2821)
  [#2861](https://github.com/sanic-org/sanic/pull/2863)
  [#2863](https://github.com/sanic-org/sanic-pull/pull/2781)
  User Guide to SHH (Sanic, html5tagger, HTMX) stack
- [#2810](https://github.com/sanic-org/sanic/pull/2810) README を更新
- [#2855](https://github.com/sanic-org/sanic/pull/2855) Discordバッジを編集する
- [#2864](https://github.com/sanic-org/sanic/pull/2864) http/https リダイレクションドキュメント内で state プロパティを使用するためのドキュメントを調整する

## バージョン 23.9.0

_当時の状況により、v.23.9はスキップされました。 _

## バージョン 23.6.0

### 特徴

- [#2670](https://github.com/sanic-org/sanic/pull/2670) `KEEP_ALIVE_TIMEOUT`のデフォルトを120秒に増やします
- [#2716](https://github.com/sanic-org/sanic/pull/2716) ブループリントにルート上書きオプションを追加する
- [#2724](https://github.com/sanic-org/sanic/pull/2724) および [#2792](https://github.com/sanic-org/sanic/pull/2792) アプリケーションのどこでも発生するすべての例外に新しい例外信号を追加します。
- [#2727](https://github.com/sanic-org/sanic/pull/2727) BPグループの前に名前を追加
- [#2754](https://github.com/sanic-org/sanic/pull/2754) ミドルウェアタイプのリクエストタイプを更新
- [#2770](https://github.com/sanic-org/sanic/pull/2770) 起動時にエラーが発生した場合の例外メッセージの改善
- [#2776](https://github.com/sanic-org/sanic/pull/2776) マルチプロセッシングスタートメソッドを早期に設定する
- [#2785](https://github.com/sanic-org/sanic/pull/2785) 設定とctxオブジェクトにカスタム入力を追加
- [#2790](https://github.com/sanic-org/sanic/pull/2790) `request.client_ip` を追加する

### バグ修正

- [#2728](https://github.com/sanic-org/sanic/pull/2728) 意図した結果のトラバーサルを修正
- [#2729](https://github.com/sanic-org/sanic/pull/2729) ResponseStream コンストラクターの引数が None の場合に処理する
- [#2737](https://github.com/sanic-org/sanic/pull/2737) デフォルトのコンテンツ型の型アノテーションを修正
- [#2740](https://github.com/sanic-org/sanic/pull/2740) SanicのシリアライザをインスペクターでJSONレスポンスに使用する
- [#2760](https://github.com/sanic-org/sanic/pull/2760) ASGI モードでの `Request.get_current` のサポート
- [#2773](https://github.com/sanic-org/sanic/pull/2773) 明示的にerror_format を定義するためのブループリントルートを無視する
- [#2774](https://github.com/sanic-org/sanic/pull/2774) さまざまなレンダラーでヘッダーを解決する
- [#2782](https://github.com/sanic-org/sanic/pull/2782) pypy の互換性の問題を解決する

### 非推奨と削除

- [#2777](https://github.com/sanic-org/sanic/pull/2777) Python 3.7 サポートを削除

### 開発者のインフラストラクチャ

- [#2766](https://github.com/sanic-org/sanic/pull/2766) Unpin setuptools version
- [#2779](https://github.com/sanic-org/sanic/pull/2779) 有効なポートを取得するために、ループ内のテストを実行してください

### ドキュメントの改善

- [#2741](https://github.com/sanic-org/sanic/pull/2741) Better documentation examples about running Sanic
  From that list, the items to highlight in the release notes:

## バージョン 23.3.0

### 特徴

- [#2545](https://github.com/sanic-org/sanic/pull/2545) 例外の init を標準化して、例外を使用してHTTPレスポンスの一貫性を高めます。
- [#2606](https://github.com/sanic-org/sanic/pull/2606) ASGIでもUTF-8としてデコードヘッダーを解読する
- [#2646](https://github.com/sanic-org/sanic/pull/2646) ASGIリクエストと寿命の呼び出しを分離する
- [#2659](https://github.com/sanic-org/sanic/pull/2659) `empty()` を返すハンドラには `FALLBACK_ERROR_FORMAT` を使用してください。
- [#2662](https://github.com/sanic-org/sanic/pull/2662) 基本的なファイルブラウザー (HTMLページ) と自動インデックスサービス
- [#2667](https://github.com/sanic-org/sanic/pull/2667) Nice traceback formatting (HTML page)
- [#2668](https://github.com/sanic-org/sanic/pull/2668) よりスマートなエラーページレンダリングフォーマットの選択。ヘッダーと「常識」のデフォルトに依存する
- [#2680](https://github.com/sanic-org/sanic/pull/2680) `SHUT_RDWR` でシャットダウンする前にソケットの状態を確認してください。
- [#2687](https://github.com/sanic-org/sanic/pull/2687) `Request.accept` 機能をよりパフォーマンスと仕様に準拠するように更新します。
- [#2696](https://github.com/sanic-org/sanic/pull/2696) ヘッダーアクセサをプロパティとして追加
  ```
  Example-Field: Foo, Bar
  Example-Field: Baz
  ```
  ```python
  request.headers.example_field == "Foo, Bar,Baz"
  ```
- [#2700](https://github.com/sanic-org/sanic/pull/2700) Simpler CLI target

  ```sh
  $ sanic path.to.module:app # global app instance
  $ sanic path.to.module:create_app # factory pattern
  $ sanic ./path/to/directory/ # simple serve
  ```
- [#2701](https://github.com/sanic-org/sanic/pull/2701) 管理されたプロセスの多くのワーカーを定義する API
- [#2704](https://github.com/sanic-org/sanic/pull/2704) ルーティングの動的変更に便利な機能を追加
- [#2706](https://github.com/sanic-org/sanic/pull/2706) クッキーの作成と削除に便利なメソッドを追加する

  ```python
  response = text("...")
  response.add_cookie("test", "It worked!", domain=".yummy-yummy-cookie.com")
  ```
- [#2707](https://github.com/sanic-org/sanic/pull/2707) `parse_content_header` エスケープを簡素化し、RFCに準拠し、古いFFハックを削除する
- [#2710](https://github.com/sanic-org/sanic/pull/2710) リクエストURLの厳密な文字セットの扱いとescaping
- [#2711](https://github.com/sanic-org/sanic/pull/2711) デフォルトでは `DELETE` の本文を消費します
- [#2719](https://github.com/sanic-org/sanic/pull/2719) `password` を TLS コンテキストに渡すことを許可する
- [#2720](https://github.com/sanic-org/sanic/pull/2720) `RequestCancelled` でミドルウェアをスキップする
- [#2721](https://github.com/sanic-org/sanic/pull/2721) アクセスログのフォーマットを \`%s\`\` に変更する
- [#2722](https://github.com/sanic-org/sanic/pull/2722) `SSLContext` オブジェクトを直接制御するためのアプリケーションオプションとして `CertLoader` を追加します
- [#2725](https://github.com/sanic-org/sanic/pull/2725) レース状態におけるワーカー同期状態

### バグ修正

- [#2651](https://github.com/sanic-org/sanic/pull/2651) ASGI のウェブソケットをそのままバイトを渡します
- [#2697](https://github.com/sanic-org/sanic/pull/2697) `If-Modified-Since` を使用した場合、datetime aware と naive の比較を`file` で修正しました

### 非推奨と削除

- [#2666](https://github.com/sanic-org/sanic/pull/2666) 非推奨の「**blueprintname**」プロパティを削除します

### ドキュメントの改善

- [#2712](https://github.com/sanic-org/sanic/pull/2712) リダイレクトを作成するために `'https'` を使用した例を改善しました

## バージョン 22.12.0

現在のLTSバージョン_

### 特徴

- [#2569](https://github.com/sanic-org/sanic/pull/2569) レスポンスオブジェクトを更新する際に便利なメソッドで `JSONResponse` クラスを追加する
- [#2598](https://github.com/sanic-org/sanic/pull/2598) `uvloop`の要件を`>=0.15.0`に変更します
- [#2609](https://github.com/sanic-org/sanic/pull/2609) `websockets` v11.0 との互換性を追加
- [#2610](https://github.com/sanic-org/sanic/pull/2610) ワーカーエラー時にサーバーを早期にキルする
  - デッドロックのタイムアウトを30秒に上げる
- [#2617](https://github.com/sanic-org/sanic/pull/2617) 実行中のサーバーワーカーの数
- [#2621](https://github.com/sanic-org/sanic/pull/2621) [#2634](https://github.com/sanic-org/sanic/pull/2634) 次の`ctrl+c`に`SIGKILL`を送信してワーカーの出口を強制する
- [#2622](https://github.com/sanic-org/sanic/pull/2622) APIを追加してマルチプレクサからすべてのワーカーを再起動する
- [#2624](https://github.com/sanic-org/sanic/pull/2624) 特別に設定しない限り、全てのサブプロセスの `spawn` をデフォルトに設定します。
  ```python
  from sanic import Sanic

  Sanic.start_method = "fork"
  ```
- [#2625](https://github.com/sanic-org/sanic/pull/2625) フォームデータ/マルチパートファイルアップロードの正規化
- [#2626](https://github.com/sanic-org/sanic/pull/2626) HTTP インスペクタに移動:
  - 実行中の Sanic インスタンスを検査するリモートアクセス
  - TLSはインスペクターへの暗号化コールに対応しています
  - API キーを使用したインスペクタの認証
  - カスタムコマンドでインスペクターを拡張できる機能
- [#2632](https://github.com/sanic-org/sanic/pull/2632) 再起動操作の順序を制御する
- [#2633](https://github.com/sanic-org/sanic/pull/2633) リロード間隔をクラス変数に移動する
- [#2636](https://github.com/sanic-org/sanic/pull/2636) `register_middleware`メソッドに`priority`を追加します
- [#2639](https://github.com/sanic-org/sanic/pull/2639) `add_route`メソッドに`unquote`を追加します
- [#2640](https://github.com/sanic-org/sanic/pull/2640) ASGI websockets to receive `text` or `bytes`

### バグ修正

- [#2607](https://github.com/sanic-org/sanic/pull/2607) ソケットの再結合を許可する前に強制的にシャットダウンする
- [#2590](https://github.com/sanic-org/sanic/pull/2590) Python 3.11以降では実際の`StrEnum`を使用してください
- [#2615](https://github.com/sanic-org/sanic/pull/2615) ミドルウェアがリクエストタイムアウトごとに1回だけ実行されることを確認する
- [#2627](https://github.com/sanic-org/sanic/pull/2627) 寿命エラーに関するクラッシュASGIアプリケーション
- [#2635](https://github.com/sanic-org/sanic/pull/2635) Windowsで低レベルのサーバー作成でエラーを解決する

### 非推奨と削除

- [#2608](https://github.com/sanic-org/sanic/pull/2608) [#2630](https://github.com/sanic-org/sanic/pull/2630) シグナル条件とトリガーは `signal.extra` に保存されます。
- [#2626](https://github.com/sanic-org/sanic/pull/2626) HTTPインスペクタに移動
  - 🚨 _BREAKING CHANGE_: インスペクターをカスタムプロトコルを持つシンプルなTCPソケットからSanicアプリに移動します。
  - _DEPRECATE_: `--inspect*` コマンドは非推奨になりました。
- [#2628](https://github.com/sanic-org/sanic/pull/2628) 非推奨の `distutils.strtobool` を置き換え

### 開発者のインフラストラクチャ

- [#2612](https://github.com/sanic-org/sanic/pull/2612) CI testing for Python 3.11

## バージョン 22.9.1

### 特徴

- [#2585](https://github.com/sanic-org/sanic/pull/2585) アプリケーションが登録されていない場合のエラーメッセージを改善しました

### バグ修正

- [#2578](https://github.com/sanic-org/sanic/pull/2578) プロセス証明書作成に証明書ローダーを追加する
- [#2591](https://github.com/sanic-org/sanic/pull/2591) `spawn`互換性のためにsentinel identityを使用しないでください
- [#2592](https://github.com/sanic-org/sanic/pull/2592) 入れ子になったブループリントグループのプロパティを修正
- [#2595](https://github.com/sanic-org/sanic/pull/2595) 新しいワーカーの再ローダーで睡眠間隔を導入する

### 非推奨と削除

### 開発者のインフラストラクチャ

- [#2588](https://github.com/sanic-org/sanic/pull/2588) Issue フォームの Markdown テンプレート

### ドキュメントの改善

- [#2556](https://github.com/sanic-org/sanic/pull/2556) v22.9 documentation
- [#2582](https://github.com/sanic-org/sanic/pull/2582) Windows 対応のドキュメントをクリーンアップする

## バージョン 22.9.0

### 特徴

- [#2445](https://github.com/sanic-org/sanic/pull/2445) カスタムロード関数を追加
- [#2490](https://github.com/sanic-org/sanic/pull/2490) `WebsocketImpletocol` async iterable
- [#2499](https://github.com/sanic-org/sanic/pull/2499) Sanic Server WorkerManager のリファクタリング機能
- [#2506](https://github.com/sanic-org/sanic/pull/2506) パス解像度には`pathlib`を使用してください (静的なファイルを提供する場合)
- [#2508](https://github.com/sanic-org/sanic/pull/2508) `match` の代わりに `path.parts` を使ってください (静的なファイルを提供する場合)
- [#2513](https://github.com/sanic-org/sanic/pull/2513) リクエスト処理をキャンセルする
- [#2516](https://github.com/sanic-org/sanic/pull/2516) HTTP メソッドのリクエストプロパティを追加:
  - `request.is_safe`
  - `request.is_idempotent`
  - `request.is_cacheable`
  - _参照_ format@@0(https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) _これらが適用される時の詳細_
- [#2522](https://github.com/sanic-org/sanic/pull/2522) ASGIに常にサーバーの場所を表示する
- [#2526](https://github.com/sanic-org/sanic/pull/2526) 適切な場合に304を返すための静的ファイルのキャッシュ管理のサポート
- [#2533](https://github.com/sanic-org/sanic/pull/2533) リファクタリング`_static_request_handler`
- [#2540](https://github.com/sanic-org/sanic/pull/2540) ハンドラ実行の前後に信号を追加する
  - `http.handler.before`
  - `http.handler.after`
- [#2542](https://github.com/sanic-org/sanic/pull/2542) _[redacted]_ to CLI :)
- [#2546](https://github.com/sanic-org/sanic/pull/2546) 非推奨警告フィルタを追加する
- [#2550](https://github.com/sanic-org/sanic/pull/2550) Middleware の優先度とパフォーマンスの強化

### バグ修正

- [#2495](https://github.com/sanic-org/sanic/pull/2495) 静的なファイルでディレクトリのtraversionを防止する
- [#2515](https://github.com/sanic-org/sanic/pull/2515) ブループリントの特定の静的dirsに二重スラッシュを適用しないでください

### 非推奨と削除

- [#2525](https://github.com/sanic-org/sanic/pull/2525) 重複したルート名の警告はv23.3で完全に防止されます
- [#2537](https://github.com/sanic-org/sanic/pull/2537) 重複した例外に対する警告と非推奨通知はv23.3で完全に防止されます。

### 開発者のインフラストラクチャ

- [#2504](https://github.com/sanic-org/sanic/pull/2504) Cleanup test suite
- [#2505](https://github.com/sanic-org/sanic/pull/2505) コントリビューションドキュメントからサポートされていないPythonバージョン番号を置き換え
- [#2530](https://github.com/sanic-org/sanic/pull/2530) インストールされたパッケージリゾルバーにtestsフォルダを含めないでください

### ドキュメントの改善

- [#2502](https://github.com/sanic-org/sanic/pull/2502) いくつかのタイプミスを修正
- [#2517](https://github.com/sanic-org/sanic/pull/2517) [#2536](https://github.com/sanic-org/sanic/pull/2536) いくつかのタイプヒントを追加する

## バージョン 22.6.2

### バグ修正

- [#2522](https://github.com/sanic-org/sanic/pull/2522) ASGIに常にサーバーの場所を表示する

## バージョン 22.6.1

### バグ修正

- [#2477](https://github.com/sanic-org/sanic/pull/2477) フォルダ名が ".." で終わると、Sanic static ディレクトリに失敗します。

## バージョン 22.6.0

### 特徴

- [#2378](https://github.com/sanic-org/sanic/pull/2378) `DEBUG`モードでHTTP/3とTLS証明書の自動生成を導入する
  - 👶 _早期にリリースされる機能_: HTTP/3 を超えてサニックにサービスを提供することは早期リリース機能です。 まだHTTP/3 の仕様を完全にカバーしているわけではありませんが、代わりに、Sanic の既存の HTTP/1.1 サーバーとの機能準拠を目指しています。 Websocket、WebTransport、プッシュ応答は、まだ実装されていないいくつかの機能の例です。
  - 📦 _EXTRA要求_: すべてのHTTPクライアントがHTTP/3サーバーとインターフェースできるわけではありません。 [HTTP/3 対応クライアント](https://curl.se/docs/http3.html) をインストールする必要があります。
  - 📦 _EXTRA REQUIREMENT_: TLS の自己生成を使用するには、 [mkcert](https://github.com/FiloSottile/mkcert) または [trustme](https://github.com/python-trio/trustme)のいずれかをインストールする必要があります。
- [#2416](https://github.com/sanic-org/sanic/pull/2416) `task.cancel`にメッセージを追加する
- [#2420](https://github.com/sanic-org/sanic/pull/2420) 標準のHTTPレスポンスタイプ(`BadRequest`, `MethodNotAllowed`, `RangeNotSatisfiable`)でより一貫した命名をするための例外エイリアスを追加します。
- [#2432](https://github.com/sanic-org/sanic/pull/2432) `Request`オブジェクトのプロパティとしてASGI `scope`を公開します
- [#2438](https://github.com/sanic-org/sanic/pull/2438) 注釈のWebSocketクラスへの簡単なアクセス: `from sanic import Websocket`
- [#2439](https://github.com/sanic-org/sanic/pull/2439) フォームの値を読み取るための新しいAPI: `Request.get_form`
- [#2445](https://github.com/sanic-org/sanic/pull/2445) カスタムの `loads` 関数を追加する
- [#2447](https://github.com/sanic-org/sanic/pull/2447), [#2486](https://github.com/sanic-org/sanic/pull/2486) キャッシュコントロールヘッダーの設定をサポートする API を改善しました。
- [#2453](https://github.com/sanic-org/sanic/pull/2453) 詳細フィルタリングをロガーに移動する
- [#2475](https://github.com/sanic-org/sanic/pull/2475) `Request.get_current()` を使って現在のリクエストの取得を行います。

### バグ修正

- [#2448](https://github.com/sanic-org/sanic/pull/2448) `pythonw.exe`または`sys.stdout`がない場所で実行できるように修正しました
- [#2451](https://github.com/sanic-org/sanic/pull/2451) ASGI モードで `http.lifycle.request` シグナルをトリガーします
- [#2455](https://github.com/sanic-org/sanic/pull/2455) 積み上げられたルート定義のタイピングを解決する
- [#2463](https://github.com/sanic-org/sanic/pull/2463) Python 3.7 の websocket ハンドラーの CancelledError を適切にキャッチします。

### 非推奨と削除

- [#2487](https://github.com/sanic-org/sanic/pull/2487) v22.6の非推奨と変更
  1. オプションのアプリケーションレジストリ
  2. 応答の一部が送信された後のカスタムハンドラの実行
  3. `ErrorHandler`でフォールバックハンドラを設定する
  4. カスタム `LOGO` 設定
  5. `sanic.response.stream`
  6. `AsyncioServer.init`

### 開発者のインフラストラクチャ

- [#2449](https://github.com/sanic-org/sanic/pull/2449) `black`と`isort`の設定をクリーンアップする
- [#2479](https://github.com/sanic-org/sanic/pull/2479) フラッピーテストを修正する

### ドキュメントの改善

- [#2461](https://github.com/sanic-org/sanic/pull/2461) アプリケーションの命名規格に合わせてサンプルを更新する
- [#2466](https://github.com/sanic-org/sanic/pull/2466) `Extend` の型注釈を改善しました
- [#2485](https://github.com/sanic-org/sanic/pull/2485) CLI のヘルプメッセージを改善

## バージョン 22.3.0

### 特徴

- [#2347](https://github.com/sanic-org/sanic/pull/2347) マルチアプリケーション・サーバー用 API
  - 🚨 _BREAKING CHANGE_: 古い `sanic.worker.GunicornWorker` が \*\*削除されました。 Sanic を `gunicorn` で実行するには、`uvicorn` format@@0(https://www.uvicorn.org/#running-with-gunicorn) で実行する必要があります。
  - 🧁 _SIDE EFFECT_: 名前付きバックグラウンドタスクがPython 3.7 でもサポートされるようになりました
- [#2357](https://github.com/sanic-org/sanic/pull/2357) `Request.credentials` として `Authorization` ヘッダーを解析
- [#2361](https://github.com/sanic-org/sanic/pull/2361) 設定オプションを追加して、アプリケーションの起動時に`Touchup`ステップをスキップします
- [#2372](https://github.com/sanic-org/sanic/pull/2372) CLIヘルプメッセージングへのアップデート
- [#2382](https://github.com/sanic-org/sanic/pull/2382) バックウォーターデバッグメッセージに警告をダウングレードする
- [#2396](https://github.com/sanic-org/sanic/pull/2396) `multidict` v0.6を許可する
- [#2401](https://github.com/sanic-org/sanic/pull/2401) アプリケーションの実行タイプに応じてCLIをアップグレード
- [#2402](https://github.com/sanic-org/sanic/pull/2402) CLI引数を工場に条件付きで注入する
- [#2413](https://github.com/sanic-org/sanic/pull/2413) 新しい開始と停止のイベントリスナを再ローダープロセスに追加します
- [#2414](https://github.com/sanic-org/sanic/pull/2414) 必要に応じてループを削除
- [#2415](https://github.com/sanic-org/sanic/pull/2415) 不正なURL解析に対する例外の改善
- [sanic-routing#47](https://github.com/sanic-org/sanic-routing/pull/47) Add a new extention parameter type: `<file:ext>`, `<file:ext=jpg>`, `<file:ext=jpg|png|gif|svg>`, `<file=int:ext>`, `<file=int:ext=jpg|png|gif|svg>`, `<file=float:ext=tar.gz>`
  - 👶 _ベータ機能_: この機能は `path` タイプのマッチングでは動作せず、ベータ機能としてのみリリースされています。
- [sanic-routing#57](https://github.com/sanic-org/sanic-routing/pull/57) `register_pattern`を`str`または`Pattern`に変更します。
- [sanic-routing#58](https://github.com/sanic-org/sanic-routing/pull/58) 空でない文字列のみのデフォルトのマッチングと、新しい `strorempty` パターンタイプ
  - 🚨 _BREAKING CHANGE_: 以前は動的な文字列パラメータ (`/<foo>` または `/<foo:str>`) を持つルートが任意の文字列にマッチします。 空の文字列も含めてね 空でない文字列と**のみ**が一致します。 古い動作を保持するには、新しいパラメータ `/<foo:strorempty> ` を使用します。

### バグ修正

- [#2373](https://github.com/sanic-org/sanic/pull/2373) websockets の `error_logger` を削除する
- [#2381](https://github.com/sanic-org/sanic/pull/2381) 新たに割り当てられた `None` をタスクレジストリに修正する
- [sanic-routing#52](https://github.com/sanic-org/sanic-routing/pull/52) regex route matchに型キャストを追加
- [sanic-routing#60](https://github.com/sanic-org/sanic-routing/pull/60) regex route (ホスト値が異なる複数の静的ディレクトリなど)の要件を追加します。

### 非推奨と削除

- [#2362](https://github.com/sanic-org/sanic/pull/2362) 22.3 廃止と変更
  1. `debug=True` と `--debug` do _NOT_ は自動的に `auto_reload` を実行します
  2. デフォルトのエラーレンダリングはプレーンテキストで行われます（ブラウザーは `auto` がヘッダを参照するため、HTML をデフォルトで取得します）
  3. `ErrorHandler.finalize`には`config`が必要です
  4. `ErrorHandler.lookup` には2つの位置引数が必要です
  5. 未使用の websocket プロトコル引数を削除しました
- [#2344](https://github.com/sanic-org/sanic/pull/2344) 小文字の環境変数のロードを非推奨にする

### 開発者のインフラストラクチャ

- [#2363](https://github.com/sanic-org/sanic/pull/2363) コードカバレッジをCodecovに戻す
- [#2405](https://github.com/sanic-org/sanic/pull/2405) `sanic-routing`の変更のためのテストのアップグレード
- [sanic-testing#35](https://github.com/sanic-org/sanic-testing/pull/35) Allow for httpx v0.22

### ドキュメントの改善

- [#2350](https://github.com/sanic-org/sanic/pull/2350) READMEのリンクを修正する
- [#2398](https://github.com/sanic-org/sanic/pull/2398) ドキュメントミドルウェアon_requestとon_response
- [#2409](https://github.com/sanic-org/sanic/pull/2409) `Request.respond`に不足しているドキュメントを追加する

### その他

- [#2376](https://github.com/sanic-org/sanic/pull/2376) `ListenerMixin.listener` の入力を修正
- [#2383](https://github.com/sanic-org/sanic/pull/2383) `asyncio.wait` で非推奨の警告をクリアする
- [#2387](https://github.com/sanic-org/sanic/pull/2387) Cleanup `__slots__` 実装
- [#2390](https://github.com/sanic-org/sanic/pull/2390) `asyncio.get_event_loop`で非推奨の警告をクリアする

## バージョン21.12.1

- [#2349](https://github.com/sanic-org/sanic/pull/2349) スタートアップ時にMOTD のみ表示する
- [#2354](https://github.com/sanic-org/sanic/pull/2354) Python 3.7 の名前引数を無視する
- [#2355](https://github.com/sanic-org/sanic/pull/2355) config.update サポートをすべての設定値に追加しました。

## バージョン 21.12.0

### 特徴

- [#2260](https://github.com/sanic-org/sanic/pull/2260) 初期のブループリント登録を許可して、後で追加されたオブジェクトを適用する
- [#2262](https://github.com/sanic-org/sanic/pull/2262) ノイズ例外 - すべての例外を強制的にログ収集する
- [#2264](https://github.com/sanic-org/sanic/pull/2264) オプションの `uvloop` 設定で
- [#2270](https://github.com/sanic-org/sanic/pull/2270) 複数の TLS 証明書を使用した Vhost サポート
- [#2277](https://github.com/sanic-org/sanic/pull/2277) シグナルルーティングを変更して一貫性を高めます。
  - _BREAKING CHANGE_:手動でルーティングしていた場合は、改ざんの変更があります。 シグナルルーターの「get」は100%決定的なものではなくなりました。 返される信号をループさせて、要件を適切にマッチングするための追加のステップが追加されました。 `app.dispatch` や `bp.dispatch` を使ってシグナルがディスパッチされている場合、変更はありません。
- [#2290](https://github.com/sanic-org/sanic/pull/2290) 文脈例外を追加する
- [#2291](https://github.com/sanic-org/sanic/pull/2291) 参加コンキャットのパフォーマンスを向上させる
- [#2295](https://github.com/sanic-org/sanic/pull/2295), [#2316](https://github.com/sanic-org/sanic/pull/2331), [#2331](https://github.com/sanic-org/sanic/pull/2331) CLIとアプリケーションの状態を再構築し、`app.run`を使用するとコマンドパリティを強化します。
- [#2302](https://github.com/sanic-org/sanic/pull/2302) 定義時にルートコンテキストを追加
- [#2304](https://github.com/sanic-org/sanic/pull/2304) バックグラウンドタスクを管理するための名前付きタスクと新しい API
- [#2307](https://github.com/sanic-org/sanic/pull/2307) アプリの自動再読み込みで、変更されたファイルの洞察を提供する
- [#2308](https://github.com/sanic-org/sanic/pull/2308) インストールされている場合は[Sanic Extensions](https://sanicframework.org/en/plugins/sanic-ext/getting-started.html)でアプリケーションを自動的に拡張し、拡張機能にアクセスするためのファーストクラスをサポートします。
- [#2309](https://github.com/sanic-org/sanic/pull/2309) 組み込み信号が`Enum`に変更されました
- [#2313](https://github.com/sanic-org/sanic/pull/2313) 追加の設定実装ユースケースに対応
- [#2321](https://github.com/sanic-org/sanic/pull/2321) 環境変数水和ロジックをリファクタリングする
- [#2327](https://github.com/sanic-org/sanic/pull/2327) 単一のリクエストで複数の反応や混合反応を防ぎます
- [#2330](https://github.com/sanic-org/sanic/pull/2330) 環境変数のカスタム型キャスト。
- [#2332](https://github.com/sanic-org/sanic/pull/2332) すべての非推奨通知を一貫性のあるものにする
- [#2335](https://github.com/sanic-org/sanic/pull/2335) アンダースコアのインスタンス名の開始を許可する

### バグ修正

- [#2273](https://github.com/sanic-org/sanic/pull/2273) `websocket_handshake`を入力して割り当てを変更する
- [#2285](https://github.com/sanic-org/sanic/pull/2285) スタートアップログのIPv6表示を修正
- [#2299](https://github.com/sanic-org/sanic/pull/2299) 例外ハンドラから `http.lifyle.response` を送信する

### 非推奨と削除

- [#2306](https://github.com/sanic-org/sanic/pull/2306) 非推奨アイテムの削除
  - `Sanic` と `Blueprint` に任意のプロパティが付いていない可能性があります
  - `Sanic` と `Blueprint` に準拠した名前が強制されました
    - alphanumeric + `_` + `-`
    - は文字または`_`で始まる必要があります
  - `Sanic`の`load_env`キーワード引数
  - `sanic.exceptions.abort`
  - `sanic.views.CompositionView`
  - `sanic.response.StreamingHTTPResponse`
    - _注意:_ `stream()` レスポンスメソッド (呼び出し可能なストリーミング関数を渡す) は廃止され、v22.6 で削除されます。 新しいスタイルのすべてのストリーミング応答をアップグレードする必要があります: https://sanicframework.org/ja/guide/advanced/streaming.html#response-stream
- [#2320](https://github.com/sanic-org/sanic/pull/2320) Configからエラーハンドラ設定用アプリインスタンスを削除します

### 開発者のインフラストラクチャ

- [#2251](https://github.com/sanic-org/sanic/pull/2251) dev install コマンドを変更する
- [#2286](https://github.com/sanic-org/sanic/pull/2286) コード化のしきい値を5から10に変更する
- [#2287](https://github.com/sanic-org/sanic/pull/2287) ホストテスト関数名を上書きしないように更新する
- [#2292](https://github.com/sanic-org/sanic/pull/2292) エラー時に失敗する CI
- [#2311](https://github.com/sanic-org/sanic/pull/2311), [#2324](https://github.com/sanic-org/sanic/pull/2324) PRsのドラフトテストを実行しないでください
- [#2336](https://github.com/sanic-org/sanic/pull/2336) カバレッジチェックからパスを削除
- [#2338](https://github.com/sanic-org/sanic/pull/2338) テストのポートをクリーンアップする

### ドキュメントの改善

- [#2269](https://github.com/sanic-org/sanic/pull/2269), [#2329](https://github.com/sanic-org/sanic/pull/2333) 型のクリーンアップと言語の修正

### その他

- [#2257](https://github.com/sanic-org/sanic/pull/2257), [#2294](https://github.com/sanic-org/sanic/pull/22941) [#2341](https://github.com/sanic-org/sanic/pull/2341) Python 3.10 サポートを追加
- [#2279](https://github.com/sanic-org/sanic/pull/2279), [#2317](https://github.com/sanic-org/sanic/pull/2322) 不足している型の注釈を追加/修正する
- [#2305](https://github.com/sanic-org/sanic/pull/2305) モダンな実装を使用する例を修正しました。

## バージョン 21.9.3

_クリーンアップされた v21.9.2 の再リリース_

## バージョン 21.9.2

- [#2268](https://github.com/sanic-org/sanic/pull/2268) HTTP接続をIDLEステージで開始し、遅延やエラーメッセージを回避する
- [#2310](https://github.com/sanic-org/sanic/pull/2310) Post-FALLBACK_ERROR_FORMAT が適用されます。

## バージョン21.9.1

- [#2259](https://github.com/sanic-org/sanic/pull/2259) 非準拠ErrorHandlers を許可する

## バージョン 21.9.0

### 特徴

- [#2158](https://github.com/sanic-org/sanic/pull/2158), [#2248](https://github.com/sanic-org/sanic/pull/2248) I/Oをwebsocketに完全にオーバーホールする
- [#2160](https://github.com/sanic-org/sanic/pull/2160) サーバーに17の新しい信号を追加し、ライフサイクルをリクエストする
- [#2162](https://github.com/sanic-org/sanic/pull/2162) 例外が発生した場合、よりスマートな `auto` フォールバックの書式設定
- [#2184](https://github.com/sanic-org/sanic/pull/2184) ブループリントをコピーするための実装を導入する
- [#2200](https://github.com/sanic-org/sanic/pull/2200) ヘッダーの解析を許可
- [#2207](https://github.com/sanic-org/sanic/pull/2207) 利用可能な場合はリモートアドレスを記録する
- [#2209](https://github.com/sanic-org/sanic/pull/2209) BPグループに便利な方法を追加
- [#2216](https://github.com/sanic-org/sanic/pull/2216) SanicExceptionsにデフォルトのメッセージを追加する
- [#2225](https://github.com/sanic-org/sanic/pull/2225) パスパラメータを持つアノテーションハンドラのタイプアノテーションの利便性。
- [#2236](https://github.com/sanic-org/sanic/pull/2236) ルートハンドラーからのFalsey(ただしNoneではない)応答を許可する
- [#2238](https://github.com/sanic-org/sanic/pull/2238) ブループリントグループに`exception`デコレータを追加する
- [#2244](https://github.com/sanic-org/sanic/pull/2244) ファイルまたはdir (例: `static(..., resource_type="file")`)
- [#2245](https://github.com/sanic-org/sanic/pull/2245) 接続タスクがキャンセルされたらHTTPループを閉じます。

### バグ修正

- [#2188](https://github.com/sanic-org/sanic/pull/2188) チャンクされたリクエストの終了を修正する
- [#2195](https://github.com/sanic-org/sanic/pull/2195) 静的リクエスト時の予期しないエラー処理を解決する
- [#2208](https://github.com/sanic-org/sanic/pull/2208) ブループリントベースの例外をより直感的にアタッチしてトリガーさせる。
- [#2211](https://github.com/sanic-org/sanic/pull/2211) asgi アプリ呼び出しの例外処理を修正。
- [#2213](https://github.com/sanic-org/sanic/pull/2213) 例外が記録されないバグを修正しました。
- [#2231](https://github.com/sanic-org/sanic/pull/2231) 戦略的な場所で `abort()` を使用してタスクを終了させ、ダングルソケットを避けます。
- [#2247](https://github.com/sanic-org/sanic/pull/2247) デバッグモードでの自動リロード状態のロギングを修正する
- [#2246](https://github.com/sanic-org/sanic/pull/2246) BPアカウントの例外ハンドラーですがルートはありません

### 開発者のインフラストラクチャ

- [#2194](https://github.com/sanic-org/sanic/pull/2194) 生クライアントのHTTPユニットテスト
- [#2199](https://github.com/sanic-org/sanic/pull/2199) codeclimate に切り替える
- [#2214](https://github.com/sanic-org/sanic/pull/2214) Windows テストを再開してみてください
- [#2229](https://github.com/sanic-org/sanic/pull/2229) `HttpProtocol`をベースクラスにリファクタリングします
- [#2230](https://github.com/sanic-org/sanic/pull/2230) `server.py`をマルチファイルモジュールにリファクタリングします。

### その他

- [#2173](https://github.com/sanic-org/sanic/pull/2173) 重複した依存関係とPEP 517のサポート
- [#2193](https://github.com/sanic-org/sanic/pull/2193), [#2196](https://github.com/sanic-org/sanic/pull/2196), [#2217](https://github.com/sanic-org/sanic/pull/2217) 型注釈の変更

## バージョン 21.6.1

**バグ修正**

- [#2178](https://github.com/sanic-org/sanic/pull/2178) Update
  sanic-routing to allow for better splitting of complex URI
  templates
- [#2183](https://github.com/sanic-org/sanic/pull/2183) ブロックされたリクエストボディの適切な
  処理でログ内のファントム503を解決する
- [#2181](https://github.com/sanic-org/sanic/pull/2181) 例外ロギングで
  回帰を解決する
- [#2201](https://github.com/sanic-org/sanic/pull/2201) パイプライン化リクエストの
  リクエスト情報

## バージョン 21.6.0

**機能**

- [#2094](https://github.com/sanic-org/sanic/pull/2094) ハンドラ内でストリームを閉じるために
  `response.eof()` メソッドを追加する

- [#2097](https://github.com/sanic-org/sanic/pull/2097)
  大文字小文字を区別しない HTTP アップグレードヘッダー

- [#2104](https://github.com/sanic-org/sanic/pull/2104) 明示
  CIMultDictゲッターの使用

- [#2109](https://github.com/sanic-org/sanic/pull/2109) 一貫性のある
  エラーロガーの使用

- [#21114](https://github.com/sanic-org/sanic/pull/2114) 新しい
  `client_ip` 接続情報インスタンスへのアクセス

- [#2119](https://github.com/sanic-org/sanic/pull/2119) `Config` と `Sanic.ctx` のインスタンス化時の代替
  クラス

- [#2133](https://github.com/sanic-org/sanic/pull/2133) Implement
  new version of AST router

  - `alpha` と `string` param
    型を適切に区別します
  - `slug` param typeを追加します。例: `<foo:slug>`
  - 非推奨の`<foo:string>`は`<foo:str>`
  - 非推奨の`<foo:number>`は`<foo:float>`
  - Adds a `route.uri` accessor

- [#2136](https://github.com/sanic-org/sanic/pull/2136) CLI
  の改善と新しいオプションのパラメータ

- [#2137](https://github.com/sanic-org/sanic/pull/2137) URLビルダーに
  `version_prefix` を追加する

- [#2140](https://github.com/sanic-org/sanic/pull/2140) Event
  autoregistration with `EVENT_AUTOREGISTER`

- [#2146](https://github.com/sanic-org/sanic/pull/2146),
  [#2147](https://github.com/sanic-org/sanic/pull/2147) Require
  stricter names on `Sanic()` and `Blueprint()`

- [#2150](https://github.com/sanic-org/sanic/pull/2150) Infinitely
  reuseable and nestable `Blueprint` and `BlueprintGroup`

- [#2154](https://github.com/sanic-org/sanic/pull/2154)
  `websockets` の依存関係をminバージョンにアップグレード

- [#2155](https://github.com/sanic-org/sanic/pull/2155)
  の最大ヘッダーサイズを増加させる: `REQUEST_MAX_HEADER_SIZE`

- [#2157](https://github.com/sanic-org/sanic/pull/2157) CLI でアプリ
  ファクトリパターンを許可する

- [#2165](https://github.com/sanic-org/sanic/pull/2165) HTTP
  メソッドを列挙に変更する

- [#2167](https://github.com/sanic-org/sanic/pull/2167)
  追加ディレクトリの自動再読み込みを許可する

- [#2168](https://github.com/sanic-org/sanic/pull/2168) シンプルな
  HTTPサーバーをCLIに追加

- [#2170](https://github.com/sanic-org/sanic/pull/2170) 追加の
  メソッドで `HTTPMethodView` をアタッチする

**バグ修正**

- [#2091](https://github.com/sanic-org/sanic/pull/2091) Fix
  `UserWarning` in ASGI mode for missing `__slots__`
- [#2099](https://github.com/sanic-org/sanic/pull/2099) スタティック
  リクエストハンドラーのログ例外を404で修正
- [#2110](https://github.com/sanic-org/sanic/pull/2110)
  request.args.pop パラメータを不整合に削除する
- [#2107](https://github.com/sanic-org/sanic/pull/2107) Fix type
  hinting for load_env
- [#2127](https://github.com/sanic-org/sanic/pull/2127)
  ASGI ws サブプロトコルがリストであることを確認してください
- [#2128](https://github.com/sanic-org/sanic/pull/2128) 問題
  ブループリントの例外ハンドラーが一貫して
  適切なハンドラーにルートされない問題を修正

**非推奨と削除**

- [#2156](https://github.com/sanic-org/sanic/pull/2156)
  設定値 `REQUE_SIZE` を削除する
- [#2170](https://github.com/sanic-org/sanic/pull/2170)
  `CompositionView` は非推奨となり、21.12 で削除されるようになりました。
- [#2172](https://github.com/sanic-org/sanic/pull/2170)
  StreamingHTTPResponse

**開発者のインフラストラクチャ**

- [#2149](https://github.com/sanic-org/sanic/pull/2149) GitHub Actions を支持する
  Travis CI を削除する

**ドキュメントの改善**

- [#2164](https://github.com/sanic-org/sanic/pull/2164)
  ドキュメントのtypoを修正
- [#2100](https://github.com/sanic-org/sanic/pull/2100) 存在しない引数の
  ドキュメントを削除する

## バージョン 21.3.2

**バグ修正**

- [#2081](https://github.com/sanic-org/sanic/pull/2081) WebSocket接続で
  応答タイムアウトを無効にする
- [#2085](https://github.com/sanic-org/sanic/pull/2085) Make sure
  that blueprints with no slash is maintained when applied

## バージョン 21.3.1

**バグ修正**

- [#2076](https://github.com/sanic-org/sanic/pull/2076) サブフォルダー内の静的ファイル
  にアクセスできません (404)

## バージョン 21.3.0

Release
Notes

**機能**

- [#1876](https://github.com/sanic-org/sanic/pull/1876) Unified
  ストリーミングサーバー
- [#2005](https://github.com/sanic-org/sanic/pull/2005) 新しい
  `Request.id` プロパティ
- [#2008](https://github.com/sanic-org/sanic/pull/2008)
  Pathlib Path オブジェクトを `app.static()` helper に渡すことを許可する
- [#2010](https://github.com/sanic-org/sanic/pull/2010),
  [#2031](https://github.com/sanic-org/sanic/pull/2031) New
  startup-optimized router
- [#2018](https://github.com/sanic-org/sanic/pull/2018)
  [#2064](https://github.com/sanic-org/sanic/pull/2064) メインサーバープロセスのリスナー
- [#2032](https://github.com/sanic-org/sanic/pull/2032) オブジェクトをリクエストするために生の
  ヘッダー情報を追加する
- [#2042](https://github.com/sanic-org/sanic/pull/2042)
  [#2060](https://github.com/sanic-org/sanic/pull/2060)
  [#2061](https://github.com/sanic-org/sanic/pull/2061)
  Signals API
- [#2043](https://github.com/sanic-org/sanic/pull/2043) SanicとBlueprintに
  `__str__` と \`__repr__を追加する
- [#2047](https://github.com/sanic-org/sanic/pull/2047) ブループリントグループで
  バージョン管理と厳密なスラッシュを有効にする
- [#2053](https://github.com/sanic-org/sanic/pull/2053)
  `get_app` name 引数は省略可能にする
- [#2055](https://github.com/sanic-org/sanic/pull/2055) JSONエンコーダー
  をアプリ経由で変更
- [#2063](https://github.com/sanic-org/sanic/pull/2063) App と
  コネクションレベルのコンテキストオブジェクト

**バグ修正**

- 解決する [#1420](https://github.com/sanic-org/sanic/pull/1420)
  `url_for` ここで `strict_slashes` は`/`で終わるパスに対して有効です
- 解決[#1525](https://github.com/sanic-org/sanic/pull/1525)
  ルーティングは特殊文字で正しくありません
- Resolve [#1653](https://github.com/sanic-org/sanic/pull/1653) ASGI
  headers
- 解決する [#1722](https://github.com/sanic-org/sanic/pull/1722)
  チャンクモードで curl を使う
- 解決[#1730](https://github.com/sanic-org/sanic/pull/1730)
  ASGIストリーミング応答の追加コンテンツ
- 解決[#1749](https://github.com/sanic-org/sanic/pull/1749)
  壊れたミドルウェアのエッジケースを復元する
- 解決[#1785](https://github.com/sanic-org/sanic/pull/1785)
  [#1804](https://github.com/sanic-org/sanic/pull/1804) Synchronous
  error handler
- 解決 [#1790](https://github.com/sanic-org/sanic/pull/1790)
  プロトコルエラーは非同期エラーハンドラをサポートしていません #1790
- 解決[#1824](https://github.com/sanic-org/sanic/pull/1824)
  特定のメソッドのタイムアウト
- 解決[#1875](https://github.com/sanic-org/sanic/pull/1875)
  特定のルートから複数の
  タイムアウトを返した後のすべてのルートからの応答タイムアウトエラー。
- 解決する [#1988](https://github.com/sanic-org/sanic/pull/1988)
  ボディで安全なメソッドを処理する
- [#2001](https://github.com/sanic-org/sanic/pull/2001) Cookie max-age が整数でない場合の
  ValueError

**非推奨と削除**

- [#2007](https://github.com/sanic-org/sanic/pull/2007) \* Config
  `from_envar` \* 設定で
  `from_object` を使用する
- [#2009](https://github.com/sanic-org/sanic/pull/2009) Sanic
  テストクライアントを独自のパッケージに削除
- [#2036](https://github.com/sanic-org/sanic/pull/2036),
  [#2037](https://github.com/sanic-org/sanic/pull/2037) Python
  3.6 のサポート
- `Request.endpoint` は `Request.name` を支持しています。
- handler 型名プレフィックスが削除されました (静的、websocketなど)

**開発者のインフラストラクチャ**

- [#1995](https://github.com/sanic-org/sanic/pull/1995)
  FUNDING.yml を作成
- [#2013](https://github.com/sanic-org/sanic/pull/2013) CIパイプラインにcodeql
  を追加
- [#2038](https://github.com/sanic-org/sanic/pull/2038) Codecov
  設定の更新
- [#2049](https://github.com/sanic-org/sanic/pull/2049) `find_packages`を使用するように
  setup.pyを更新しました

**ドキュメントの改善**

- [#1218](https://github.com/sanic-org/sanic/pull/1218)
  sanic.log.\* のドキュメントがありません
- [#1608](https://github.com/sanic-org/sanic/pull/1608) Add
  documentation on calver and LTS
- [#1731](https://github.com/sanic-org/sanic/pull/1731) Support
  mounting application elsewhere than at root path
- [#2006](https://github.com/sanic-org/sanic/pull/2006)
  型の注釈とdocstrings と API ドキュメンテーションの改善
- [#2052](https://github.com/sanic-org/sanic/pull/2052) いくつかの
  例とドキュメントを修正する

**その他**

- `Request.route` プロパティ
- より優れた websocket サブプロトコルのサポート
- Resolve bug with middleware in Blueprint Group when passed
  callable
- ブループリントとサニックの間で共通のロジックをミックスインに移動します。
- ルート名をより一貫性のあるものに変更しました
  - 要求エンドポイントはルート名です
  - route names are fully namespaced
- いくつかの新しいコンビニエンスデコレータ:
  - `@app.main_process_start`
  - `@app.main_process_stop`
  - `@app.before_server_start`
  - `@app.after_server_start`
  - `@app.before_server_stop`
  - `@app.after_server_stop`
  - `@app.on_request`
  - `@app.on_response`
- `HEAD`を含まない`Allow`ヘッダーを修正しました。
- ```
  名が存在しない\"静的\"ルートに`url_for`で\"name\" キーワードを使用する
  ```
- 名前付きの param を使用せずに複数の `app.static()` を持つことはできません
- ファイルルート上で`url_for`の\"filename\" キーワードを使用する
- ルートデフの`unquote` (自動ではありません)
- `routes_all`はタプルです
- ハンドラの引数はkwargのみです
- `request.match_info` はキャッシュされた(計算されていない)プロパティになりました
- 不明な静的ファイル mimetype が `application/octet-stream` として送信されます。
- `url_for`の`_host` キーワード
- ```
  が指定されていない場合はテキストとjsコンテンツタイプのデフォルトの文字セットを`utf-8`に追加します
  ```
- ルートのバージョンはstr、float、int にすることができます。
- ルートは ctx プロパティを持ちます
- アプリには`routes_static`、`routes_dynamic`、`routes_regex`があります
- [#2044](https://github.com/sanic-org/sanic/pull/2044) コードクリーンアップ
  とリファクタリングを行う
- [#2072](https://github.com/sanic-org/sanic/pull/2072) Remove
  `BaseSanic` metaclass
- [#2074](https://github.com/sanic-org/sanic/pull/2074) パフォーマンス
  `handle_request_` の調整

## バージョン 20.12.3

**バグ修正**

- [#2021](https://github.com/sanic-org/sanic/pull/2021) ウェブソケットハンドラ名から
  プレフィックスを削除

## バージョン 20.12.2

**依存**

- [#2026](https://github.com/sanic-org/sanic/pull/2026) uvloop
  を0.15 は Python 3.6 のサポートをドロップするため0.14 に修正しました。
- [#2029](https://github.com/sanic-org/sanic/pull/2029) 古い
  チャード要件を削除し、ハードマルチディクト要件を追加

## バージョン 19.12.5

**依存**

- [#2025](https://github.com/sanic-org/sanic/pull/2025) uvloop
  を0.15 は Python 3.6 のサポートをドロップするため0.14 に修正
- [#2027](https://github.com/sanic-org/sanic/pull/2027) 古い
  チャード要件を削除し、ハードマルチディクト要件を追加

## バージョン 20.12.0

**機能**

- [#1993](https://github.com/sanic-org/sanic/pull/1993)
  アプリレジストリを無効にする
- [#1945](https://github.com/sanic-org/sanic/pull/1945) 静的ルート
  より詳細なファイルが見つからない場合
- [#1954](https://github.com/sanic-org/sanic/pull/1954)静的
  ルートのブループリントへの登録を修正する
- [#1961](https://github.com/sanic-org/sanic/pull/1961) Python
  3.9 のサポート
- [#1962](https://github.com/sanic-org/sanic/pull/1962) Sanic CLI
  upgrade
- [#1967](https://github.com/sanic-org/sanic/pull/1967) Update
  aiofile version requirements
- [#1969](https://github.com/sanic-org/sanic/pull/1969)
  のバージョン要件
- [#1970](https://github.com/sanic-org/sanic/pull/1970) py.typed
  ファイルを追加
- [#1972](https://github.com/sanic-org/sanic/pull/1972) Speed
  optimization in request handler
- [#1979](https://github.com/sanic-org/sanic/pull/1979) アプリ
  レジストリとサニッククラスレベルのアプリ検索を追加

**バグ修正**

- [#1965](https://github.com/sanic-org/sanic/pull/1965) ASGIストリーミング応答でチャンクされた
  トランスポートエンコード

**非推奨と削除**

- [#1981](https://github.com/sanic-org/sanic/pull/1981) Cleanup and
  remove deprecated code

**開発者のインフラストラクチャ**

- [#1956](https://github.com/sanic-org/sanic/pull/1956) load
  モジュールテストを修正
- [#1973](https://github.com/sanic-org/sanic/pull/1973) トランジション
  Travisを.orgから.comへ。
- [#1986](https://github.com/sanic-org/sanic/pull/1986) Update tox
  requirements

**ドキュメントの改善**

- [#1951](https://github.com/sanic-org/sanic/pull/1951)
  ドキュメントの改善
- [#1983](https://github.com/sanic-org/sanic/pull/1983) testing.rst で内容が重複する
  を削除
- [#1984](https://github.com/sanic-org/sanic/pull/1984)
  routing.rst のtypoを修正

## バージョン 20.9.1

**バグ修正**

- [#1954](https://github.com/sanic-org/sanic/pull/1954) 青写真の静的
  ルート登録を修正
- [#1957](https://github.com/sanic-org/sanic/pull/1957) ASGI ストリーミングボディの
  重複ヘッダーを削除

## バージョン 19.12.3

**バグ修正**

- [#1959](https://github.com/sanic-org/sanic/pull/1959) ASGI ストリーミングボディの
  重複ヘッダーを削除

## バージョン 20.9.0

**機能**

- [#1887](https://github.com/sanic-org/sanic/pull/1887) WebSocketsの
  サブプロトコルを渡します (両方のsanic serverとASGI)。
- [#1894](https://github.com/sanic-org/sanic/pull/1894)
  アプリインスタンスに `test_mode` フラグを自動的に設定
- [#1903](https://github.com/sanic-org/sanic/pull/1903) アプリの値を更新するための新しい
  ユニファイドメソッドを追加する
- [#1906](https://github.com/sanic-org/sanic/pull/1906),
  [#1909](https://github.com/sanic-org/sanic/pull/1909)
  WEBSOCKET_PING_TIMEOUTとWEBSOCKET_PING_INTERVAL 設定
  値
- [#1935](https://github.com/sanic-org/sanic/pull/1935) httpx
  バージョンの依存関係が更新されました。v20.12 で
  依存関係が削除される予定です。
- [#1937](https://github.com/sanic-org/sanic/pull/1937) auto、
  text、json fallback エラーハンドラを追加しました (v21.3では、デフォルトは
  フォームの html を autoに変更します)

**バグ修正**

- [#1897](https://github.com/sanic-org/sanic/pull/1897) Resolves
  exception from unread bytes in stream

**非推奨と削除**

- [#1903](https://github.com/sanic-org/sanic/pull/1903)
  config.from_envar, config.from_pyfile, config.from_object は
  非推奨であり、v21.3 で削除されるように設定されています。

**開発者のインフラストラクチャ**

- [#1890](https://github.com/sanic-org/sanic/pull/1890),
  [#1891](https://github.com/sanic-org/sanic/pull/1891) isort
  呼び出しを新しいAPIと互換性があるように更新する
- [#1893](https://github.com/sanic-org/sanic/pull/1893) setup.cfg から
  バージョンセクションを削除
- [#1924](https://github.com/sanic-org/sanic/pull/1924)
  \--strict-marker を pytest に追加する

**ドキュメントの改善**

- [#1922](https://github.com/sanic-org/sanic/pull/1922) 明示的な
  ASGI準拠をREADMEに追加する

## バージョン 20.6.3

**バグ修正**

- [#1884](https://github.com/sanic-org/sanic/pull/1884) Revert
  change to multiprocessing mode

## バージョン 20.6.2

**機能**

- [#1641](https://github.com/sanic-org/sanic/pull/1641) IPv6 および UNIX ソケットに適切に実装された Socket
  バインディング。

## バージョン 20.6.1

**機能**

- [#1760](https://github.com/sanic-org/sanic/pull/1760) ウェブソケットルートにバージョン
  パラメータを追加する
- [#1866](https://github.com/sanic-org/sanic/pull/1866) エントリポイントコマンドとして `sanic`
  を追加する
- [#1880](https://github.com/sanic-org/sanic/pull/1880) url_for usage 用ウェブソケットのハンドラ
  名を追加する

**バグ修正**

- [#1776](https://github.com/sanic-org/sanic/pull/1776)
  ホストパラメータのリストに関するバグ修正
- [#1842](https://github.com/sanic-org/sanic/pull/1842) Fix static
  \_handler pickling error
- [#1827](https://github.com/sanic-org/sanic/pull/1827) OSX py38 と Windows のリローダー
  を修正
- [#1848](https://github.com/sanic-org/sanic/pull/1848) Reverse
  named_response_middlware execution order, to match normal response
  middleware execution order
- [#1853](https://github.com/sanic-org/sanic/pull/1853) Pickle
  エラーを修正
  websocket routes を含むアプリケーションをpickle しようとするとエラーが発生します

**非推奨と削除**

- [#1739](https://github.com/sanic-org/sanic/pull/1739)
  body_bytes を本体にマージする

**開発者のインフラストラクチャ**

- [#1852](https://github.com/sanic-org/sanic/pull/1852) PythonナイトリーのCI test envの
  命名を修正
- [#1857](https://github.com/sanic-org/sanic/pull/1857) Adjust
  websockets version to setup.py
- [#1869](https://github.com/sanic-org/sanic/pull/1869) Wrap
  run()の\"protocol\" 型アノテーションオプション\[\]

**ドキュメントの改善**

- [#1846](https://github.com/sanic-org/sanic/pull/1846) docs
  を更新してミドルウェアの実行順序を明確にする
- [#1865](https://github.com/sanic-org/sanic/pull/1865) 文書を隠していたrst
  フォーマットの問題を修正しました

## バージョン 20.6.0

_リリースされましたが、意図せずPR #1880を省略したため、
20.6.1_ に置き換えられました

## バージョン 20.3.0

**機能**

- [#1762](https://github.com/sanic-org/sanic/pull/1762)
  `srv.start_serving()` と `srv.serve_forever()` を `AsyncioServer` に追加します
- [#1767](https://github.com/sanic-org/sanic/pull/1767) `hypercorn -k trio myweb.app` で Sanic
  を使えるようにする
- [#1768](https://github.com/sanic-org/sanic/pull/1768) No
  tracebacks on normal errors and prettier error pages
- [#1769](https://github.com/sanic-org/sanic/pull/1769) ファイル応答のコードクリーンアップ
- [#1793](https://github.com/sanic-org/sanic/pull/1793) and
  [#1819](https://github.com/sanic-org/sanic/pull/1819) Upgrade
  `str.format()` to f-strings
- [#1798](https://github.com/sanic-org/sanic/pull/1798)
  Python 3.8 を搭載した MacOS の複数のワーカーを許可する
- [#1820](https://github.com/sanic-org/sanic/pull/1820)
  content-type と content-length ヘッダーを例外で設定しないでください。

**バグ修正**

- [#1748](https://github.com/sanic-org/sanic/pull/1748) Python 3.8 の `asyncio.Event` の loop
  引数を削除します
- [#1764](https://github.com/sanic-org/sanic/pull/1764) ルート
  デコレータが再びスタックできるようにする
- [#1789](https://github.com/sanic-org/sanic/pull/1789) Fix tests
  using hosts yielding incorrect `url_for`
- [#1808](https://github.com/sanic-org/sanic/pull/1808) Ctrl+C
  とWindowsでのテスト

**非推奨と削除**

- [#1800](https://github.com/sanic-org/sanic/pull/1800) Begin
  deprecation in way of first-class streaming, removal of
  `body_init`, `body_push`, and `body_finish`
- [#1801](https://github.com/sanic-org/sanic/pull/1801) Complete
  deprecation from
  [#1666](https://github.com/sanic-org/sanic/pull/1666) of
  dictionary context on `request` objects.
- [#1807](https://github.com/sanic-org/sanic/pull/1807) アプリから直接読み込むことのできる
  サーバー設定の引数を削除する
- [#1818](https://github.com/sanic-org/sanic/pull/1818) Complete
  deprecation of `app.remove_route` and `request.raw_args`

**依存**

- [#1794](https://github.com/sanic-org/sanic/pull/1794) `httpx`
  を0.11.1
- [#1806](https://github.com/sanic-org/sanic/pull/1806) Import
  `ASGIDispatch` from top-level `httpx` (from third-party
  deprecation)

**開発者のインフラストラクチャ**

- [#1833](https://github.com/sanic-org/sanic/pull/1833)
  壊れたドキュメントのビルドを解決する

**ドキュメントの改善**

- [#1755](https://github.com/sanic-org/sanic/pull/1755)
  `response.empty()` の使用法
- [#1778](https://github.com/sanic-org/sanic/pull/1778) Update
  README
- [#1783](https://github.com/sanic-org/sanic/pull/1783) Fix typo
- [#1784](https://github.com/sanic-org/sanic/pull/1784) Corrected
  changelog for docs move of MD to RST
  ([#1691](https://github.com/sanic-org/sanic/pull/1691))
- [#1803](https://github.com/sanic-org/sanic/pull/1803)
  設定ドキュメントをDEFAULT_CONFIGに一致させるように更新する
- [#1814](https://github.com/sanic-org/sanic/pull/1814) 更新
  getting_started.rst
- [#1821](https://github.com/sanic-org/sanic/pull/1821) Update to
  deployment
- [#1822](https://github.com/sanic-org/sanic/pull/1822) ドキュメント
  を20.3で変更を加えて更新する
- [#1834](https://github.com/sanic-org/sanic/pull/1834)
  リスナーの順序

## バージョン 19.12.0

**バグ修正**

- ブループリントミドルウェアアプリケーションを修正

  Currently, any blueprint middleware registered, irrespective of
  which blueprint was used to do so, was being applied to all of the
  routes created by the `@app` and `@blueprint` alike.

  この変更の一環として、ブループリントベースのミドルウェアアプリケーション
  は登録場所に基づいて施行されます。

  - `@blueprint.middleware`を介してミドルウェアを登録する場合、
    はblueprintで定義されたルートにのみ適用されます。
  - If you register a middleware via `@blueprint_group.middleware`
    then it will apply to all blueprint based routes that are part
    of the group.
  - If you define a middleware via `@app.middleware` then it will be
    applied on all available routes
    ([#37](https://github.com/sanic-org/sanic/issues/37))

- SERVER_NAME がない場合の [url_for]{.title-ref} の動作を修正

  If the [SERVER_NAME]{.title-ref} was missing in the
  [app.config]{.title-ref} entity, the [url_for]{.title-ref} on the
  [request]{.title-ref} and [app]{.title-ref} were failing due to an
  [AttributeError]{.title-ref}. This fix makes the availability of
  [SERVER_NAME]{.title-ref} on our [app.config]{.title-ref} an
  optional behavior.
  ([#1707](https://github.com/sanic-org/sanic/issues/1707))

**ドキュメントの改善**

- MDからRSTへドキュメントを移動

  Moved all docs from markdown to restructured text like the rest of
  the docs to unify the scheme and make it easier in the future to
  update documentation.
  ([#1691](https://github.com/sanic-org/sanic/issues/1691))

- [get]{.title-ref} と [getlist]{.title-ref} の
  [request.args]{.title-ref} のドキュメントを修正

  ```
  [getlist]{.title-ref} の使用例を追加し、
  [request.args]{.title-ref} ビヘイビア
  ([#1704](https://github.com/sanic-org/sanic/issues/1704)) のドキュメント文字列を修正します。
  ```

## バージョン 19.6.3

**機能**

- タウンクリエのサポートを有効にする

  この機能の一環として、 [towncrier]{.title-ref} は、各プルリクエストの一部として、変更ログを生成するプロセスと
  管理するメカニズムとして、
  が導入されています。
  ([#1631](https://github.com/sanic-org/sanic/issues/1631))

**ドキュメントの改善**

- ドキュメンテーションインフラストラクチャの変更
  - Enable having a single common [CHANGELOG]{.title-ref} file for
    both GitHub page and documentation
  - Sphinix非推奨の警告を修正
  - 無効な [rst]{.title-ref}
    インデントによるドキュメント警告の修正
  - Enable common contribution guidelines file across GitHub and
    documentation via [CONTRIBUTING.rst]{.title-ref}
    ([#1631](https://github.com/sanic-org/sanic/issues/1631))

## バージョン 19.6.2

**機能**

- [#1562](https://github.com/sanic-org/sanic/pull/1562) Remove
  `aiohttp` dependency and create new `SanicTestClient` based upon
  [requests-async](https://github.com/encode/requests-async)
- [#1475](https://github.com/sanic-org/sanic/pull/1475) ASGI
  サポートを追加しました (ベータ)
- [#1436](https://github.com/sanic-org/sanic/pull/1436) Add
  Configure support from object string

**バグ修正**

- [#1587](https://github.com/sanic-org/sanic/pull/1587) Expect ヘッダーの
  ハンドルを追加します。
- [#1560](https://github.com/sanic-org/sanic/pull/1560) Allow to
  disable Transfer-Encoding: chunked.
- [#1558](https://github.com/sanic-org/sanic/pull/1558) 優雅な
  シャットダウンを修正。
- [#1594](https://github.com/sanic-org/sanic/pull/1594) Strict
  スラッシュ動作修正

**非推奨と削除**

- [#1544](https://github.com/sanic-org/sanic/pull/1544) Drop
  dependency on distutil
- [#1562](https://github.com/sanic-org/sanic/pull/1562) Python 3.5 の
  サポートを終了する
- [#1568](https://github.com/sanic-org/sanic/pull/1568)
  のルート削除が非推奨です。

.. 警告::

```
Sanic will not support Python 3.5 from version 19.6 and forward. 
However, version 18.12LTS will have its support period extended thru
December 2020, and therefore passing Python\'s official support version
3.5, which is set to expire in September 2020.
```

## バージョン 19.3

**機能**

- [#1497](https://github.com/sanic-org/sanic/pull/1497) Add support
  for zero-length and RFC 5987 encoded filename for
  multipart/form-data requests.

- [#1484](https://github.com/sanic-org/sanic/pull/1484) `sanic.cookies.Cookie` の
  `expires` 属性の型は `datetime` 型の
  に適用されます。

- [#1482](https://github.com/sanic-org/sanic/pull/1482) Add support
  for the `stream` parameter of `sanic.Sanic.add_route()` available
  to `sanic.Blueprint.add_route()`.

- [#1481](https://github.com/sanic-org/sanic/pull/1481) `int`または`number`型のルートパラメータの
  負の値を受け入れます。

- [#1476](https://github.com/sanic-org/sanic/pull/1476) Deprecated
  the use of `sanic.request.Request.raw_args` - it has a fundamental
  flaw in which is drops repeated query string parameters.
  `sanic.request.Request.query_args` が
  元のユースケースの置き換えとして追加されました。

- [#1472](https://github.com/sanic-org/sanic/pull/1472) Request class `repr` 実装の
  不要な `None` チェックを削除します。 この
  は、`<Request>`からリクエストのデフォルトの`repr`を
  `<Request: None />`に変更します。

- [#1470](https://github.com/sanic-org/sanic/pull/1470) `sanic.app.create_server`に2つの新しい
  パラメータを追加:

  - `return_asyncio_server` -
    asyncio.Serverを返すかどうか。
  - `asyncio_server_kwargs` - kwargs は、sanic が使用しているイベントループの
    `loop.create_server` に渡します。

  >

  これは、破損した変化です。

- [#1499](https://github.com/sanic-org/sanic/pull/1499) ルート解像度をテストとベンチマークするテストケースのセット
  を追加しました。

- [#1457](https://github.com/sanic-org/sanic/pull/1457) `sanic.cookies.Cookie` 内の `"max-age"`値の
  型が整数になるようになりました。
  整数でない値は `0` に置き換えられます。

- [#1445](https://github.com/sanic-org/sanic/pull/1445) Added the
  `endpoint` attribute to an incoming `request`, containing the name
  of the handler function.

- [#1423](https://github.com/sanic-org/sanic/pull/1423)
  リクエストストリーミングを改善しました。 `request.stream` はバインドされていないキューの代わりに、バインドされたサイズのバッファ
  になりました。 呼び出し側は
  `await request.stream.get()` の代わりに
  `await request.stream.read()` を呼び出し、本文の各部分を読み取る必要があります。

  これは、破損した変化です。

**バグ修正**

- [#1502](https://github.com/sanic-org/sanic/pull/1502) Sanicは、
  `time.time()`の先頭に追加し、毎秒1回更新して、
  過剰な`time.time()`の呼び出しを回避します。 実装が
  に観察され、メモリリークが発生する場合がありました。 プリフェッチ
  の利点は無視できるように見えたため、これが削除されました。 Fixes
  [#1500](https://github.com/sanic-org/sanic/pull/1500)
- [#1501](https://github.com/sanic-org/sanic/pull/1501) Fix a bug in
  the auto-reloader when the process was launched as a module i.e.
  `python -m init0.mod1` where the sanic server is started in
  `init0/mod1.py` with `debug` enabled and imports another module in
  `init0`.
- [#1376](https://github.com/sanic-org/sanic/pull/1376) `SanicTestClient` を構築する際に `port=None`
  を指定することで、sanic
  テストクライアントがランダムなポートにバインドできるようにします。
- [#1399](https://github.com/sanic-org/sanic/pull/1399) Added the
  ability to specify middleware on a blueprint group, so that all
  routes produced from the blueprints in the group have the
  middleware applied.
- [#1442](https://github.com/sanic-org/sanic/pull/1442) Allow the
  the use the `SANIC_ACCESS_LOG` environment variable to
  enable/disable the access log when not explicitly passed to
  `app.run()`. This allows the access log to be disabled for example
  when running via gunicorn.

**開発者のインフラストラクチャ**

- [#1529](https://github.com/sanic-org/sanic/pull/1529) Update
  project PyPI credentials
- [#1515](https://github.com/sanic-org/sanic/pull/1515) linter
  の問題を修正する (#1514を修正)
- [#1490](https://github.com/sanic-org/sanic/pull/1490) doc build で python
  のバージョンを修正
- [#1478](https://github.com/sanic-org/sanic/pull/1478)
  setuptools のバージョンをアップグレードし、doc ビルドでネイティブの docutils を使用する
- [#1464](https://github.com/sanic-org/sanic/pull/1464)
  pytestをアップグレードし、caplog 単体テストを修正する

**ドキュメントの改善**

- [#1516](https://github.com/sanic-org/sanic/pull/1516) Fix typo at
  the exception documentation
- [#1510](https://github.com/sanic-org/sanic/pull/1510) fix typo in
  Asyncio example
- [#1486](https://github.com/sanic-org/sanic/pull/1486)
  ドキュメント typo
- [#1477](https://github.com/sanic-org/sanic/pull/1477) README.md で文法
  を修正
- [#1489](https://github.com/sanic-org/sanic/pull/1489) Added
  \"databases\" to the extensions list
- [#1483](https://github.com/sanic-org/sanic/pull/1483) 拡張リストに
  sanic-zipkinを追加する
- [#1487](https://github.com/sanic-org/sanic/pull/1487)
  リンクを削除しました。拡張機能リストからリポジトリ、Sanic-OAuthを削除しました。
- [#1460](https://github.com/sanic-org/sanic/pull/1460) 18.12
  changelog
- [#1449](https://github.com/sanic-org/sanic/pull/1449) リクエストオブジェクトを修正する例
  を追加
- [#1446](https://github.com/sanic-org/sanic/pull/1446) Update
  README
- [#1444](https://github.com/sanic-org/sanic/pull/1444) Update
  README
- [#1443](https://github.com/sanic-org/sanic/pull/1443) 新しいロゴを含む
  READMEを更新
- [#1440](https://github.com/sanic-org/sanic/pull/1440) マイナー
  型とpipインストール命令の不一致を修正
- [#1424](https://github.com/sanic-org/sanic/pull/1424)
  ドキュメントの拡張

注: 19.3.0 はパッケージ化目的でスキップされ、
PyPI ではリリースされません。

## バージョン 18.12

### 18.12.0

- 変更点:

  - コードベースのテストカバレッジが81named@@0に向上しました。
  - Added stream_large_files and host examples in static_file
    document
  - Added methods to append and finish body content on Request
    (#1379)
  - windows ci サポート用 .appveyor.yml と統合されました
  - AF_INET6 と AF_UNIX ソケットの使用に関するドキュメントを追加しました
  - コードスタイルに黒/isortを採用
  - 接続失敗時にタスクをキャンセルする
  - リクエストIPとポート取得ロジックを簡素化する
  - load設定ファイルのconfigエラーを処理します。
  - CI用のcodecovと統合
  - 設定セクションに不足しているドキュメントを追加します。
  - Handler.log を非推奨にする
  - バージョン 0.0.0.10 + の httptools 要件をピン留めしました

- 修正:

  - `remove_entity_headers` ヘルパー関数を修正 (#1415)
  - Fix TypeError when use Blueprint.group() to group blueprint
    with default url_prefix, Use os.path.normpath to avoid invalid
    url_prefix like api//v1 f8a6af1 Rename the `http` module to
    `helpers` to prevent conflicts with the built-in Python http
    library (fixes #1323)
  - WindowsのUnittestsを修正
  - 健全なロガーの名前空間を修正
  - デコレータの例で不足している引用符を修正
  - 引用符で囲まれたパラメータでリダイレクトを修正
  - 最新の建設計画コードのドキュメントを修正します。
  - マークダウンリストに関するラテックス文書の構築を修正
  - app.pyでループ例外処理を修正
  - Windowsや他のプラットフォームでコンテンツの長さが一致しない問題を修正
  - 固定ファイルの範囲ヘッダーの処理を修正 (#1402)
  - ロガーを修正して動作させます(#1397)
  - マルチプロセッシングテストでpikcle-\>pickle型を修正
  - ブループリント内の名前付きタプルの
    \"name\" セクションで渡された文字列をブループリントモジュール属性名の
    名に合わせて変更します。 This allows
    blueprints to be pickled and unpickled, without errors, which
    is a requirement of running Sanic in multiprocessing mode in
    Windows. Added a test for pickling and unpickling blueprints
    Added a test for pickling and unpickling sanic itself Added a
    test for enabling multiprocessing on an app with a blueprint
    (only useful to catch this bug if the tests are run on
    Windows).
  - ログのドキュメントを修正

## バージョン 0.8

**0.8.3**

- 変更点:
  - 所有権を組織に変更しました \'sanic-org\'

**0.8.0**

- 変更点:
  - サーバー送信済みイベント拡張を追加 (Innokenty Lebedev)
  - request_handler_task キャンセルの優美な処理 (Ashley
    Sommer)
  - リダイレクト前の URL をサニタイズします（保存）
  - リクエストに url_bytes を追加 (johndoe46)
  - py37 は travisci (ユンスタンフォード) のサポート
  - OSX (garyo) への自動リローダーのサポート
  - UUID ルートサポートを追加 (Volodymyr Maksymiv)
  - 一時停止可能な応答ストリームを追加 (Ashley Sommer)
  - スロットを要求するために弱点を追加する (vopankov)
  - 廃止予定の
    (yunstanford) のためにテストフィクスチャーから ubuntu 12.04 を削除します
  - add_route (kinware) でストリーミングハンドラを許可する
  - tox(Raphael Deem)にtravis_retryを使う
  - テストクライアント用の aiohttp バージョンの更新 (yunstanford)
  - 明瞭度のためのリダイレクトインポートを追加 (yingshaoxo)
  - HTTP エンティティヘッダーを更新 (Arnulfo Soli's)
  - register_listenerメソッドを追加 (Stephan Fitzpatrick)
  - Windows用のuvloop/ujson依存関係の削除 (abuckenheimer)
  - Content-length header on 204/304 responses (Arnulfo Soli's)
  - WebSocketProtocol引数の拡張とドキュメントの追加 (Bob Olde
    Hampsink, yunstanford)
  - アルファ前からベータ版への開発状況を更新 (Maksim
    Anisenkov)
  - KeepAlive タイムアウトのログレベルがデバッグに変更されました (Arnulfo Soli's)
  - pytest-dev/pytest#3170 (Maksim
    Aniskenov) により pytest を3.3.2 にピンします
  - テスト用のdocker container に Python 3.5 と 3.6 をインストールします (Shahin
    Azad)
  - 建設計画グループとネスト（Alias Tarhini）のサポートを追加する
  - Windows用のuvloopを削除します(Aleksandr Kurlov)
  - Auto Reload (Yaser Amari)
  - ドキュメントの更新/修正 (複数の投稿者)
- 修正:
  - 修正: Linux で auto_reload (Ashley Sommer)
  - 修正:aiohttp \>= 3.3.0 (Ashley Sommer)
  - 修正: windows ではデフォルトで auto_reload を無効にする (abuckenheimer)
  - 修正 (1143): gunicorn (hqy) でアクセスログをオフにする
  - Fix (1268): ファイル応答のステータスコードをサポート (Cosmo Borsky)
  - Fix (1266): Sanic.static (Cosmo Borsky) にcontent_type フラグを追加
  - 修正: add_websocket_route
    (ciscorn) からサブプロトコルパラメータがありません
  - Fix (1242): CI ヘッダーのレスポンス (yunstanford)
  - Fix (1237): websockets (yunstanford) のバージョン制約を追加
  - 修正 (1231): メモリリーク - 常にリソースをリリース (フィリップXu)
  - Fix (1221): トランスポートが存在する場合はリクエストを真にする (Raphael
    Deem)
  - aiohttp\>=3.1.0（Ashley Sommer）のテストに失敗する問題を修正
  - try_everything の例を修正 (PyManiacGR, kot83)
  - Fix (1158): デバッグモードで auto_reload がデフォルト(Raphel Deem)
  - Fix (11136): ErrorHandler.response ハンドラの呼び出しが制限されています
    (Julien Castiaux)
  - 修正: raw requires bytes-like object (cloudship)
  - Fix (1120): passing a list in to a route decorator\'s host arg
    (Timothy Ebiuwhe)
  - 修正: マルチパート/フォームデータパーサのバグ(DirkGuijt)
  - Fix: Exception for missing parameter when value is null
    (NyanKiyoshi)
  - 修正:パラメータチェック(Howie Hu)
  - Fix (1089): 名前付きパラメータと異なる
    メソッドでルーティングの問題 (yunstanford)
  - Fix (1085): マルチワーカーモードでの信号処理 (yunstanford)
  - 修正: readme.rst (Cosven) のシングルクォート
  - 修正: メソッドの誤植(Dmitry Dygalo)
  - Fix: ipとポートのlog_response正しい出力 (Wiboo
    Arindrarto)
  - 修正 (1042): 例外処理 (Raphael Deem)
  - 修正:中国語URI (Howie Hu)
  - Fix (1079): self.transportが None の場合のタイムアウトバグ (Raphael
    Deem)
  - Fix (1074): route has slash (Raphael
    Deem) がスラッシュの場合の strict_slash の修正
  - Fix (1050): Cookie キーに samesite Cookie を追加する (Raphel Deem)
  - 修正 (1065): サーバ起動後に add_task を許可する (Raphael Deem)
  - 修正 (1061): 許可されていない例外のダブルクォート (Raphael
    Deem)
  - 修正 (1062): add_task メソッドに アプリを注入する (Raphael Deem)
  - Fix: update environment.yml for readthedocs (Eli Uriegas)
  - Fix: Cancel request task when response timeout is triggered
    (Jeong YunWon)
  - Fix (1052): Method not allowed response for RFC7231 compliance
    (Raphael Deem)
  - 修正:IPv6 アドレスとソケットデータフォーマット(ダン・パーマー)

注: 更新履歴は0.1から0.7の間は維持されませんでした

## バージョン 0.1

**0.1.7**

- 仕様を満たすために静的URLとディレクトリ引数を逆にしました

**0.1.6**

- 静的ファイル
- 遅延クッキーの読み込み中

**0.1.5**

- Cookie
- 設計図のリスナーと注文
- より速いルータを使用する
- 修正:不完全なファイルは、中程度の大きさのポストリクエストで読み込まれます
- Breaking: after_start and before_stop now pass sanic as their
  first argument

**0.1.4**

- マルチ処理

**0.1.3**

- ブループリントのサポート
- 迅速な応答処理

**0.1.1 - 0.1.2**

- CI経由でピピを更新するのに苦労しています

**0.1.0**

- 公開
