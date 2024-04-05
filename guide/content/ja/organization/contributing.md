# コントリビューション

ご興味をお持ちいただきありがとうございます! Sanicは常に貢献者を探しています。 貢献するコードが不快であれば、ソース・ファイルにdocstringを追加したり、[Sanic User Guide](https://github) を手伝ってください。 om/sanic-org/sanic-guide: ドキュメントまたは実装例を提供することにより、当然のことです!

我々は,性別,性的指向,障害,民族性,宗教その他の個人的特性にかかわらず,すべての人に友好的で安全で歓迎的な環境を提供することにコミットしている。 format@@0(https://github.com/sanic-org/sanic/blob/master/CONDUCT.md) は行動の標準を設定します。

## インストール

Sanicで開発する(主にテストを実行する)には、ソースからインストールすることを強くお勧めします。

そのため、既にリポジトリをクローンし、すでに設定されている仮想環境が作業ディレクトリにあると仮定してから、以下を実行します。

```sh
pip install -e " .[dev]"
```

## 依存関係の変更

`Sanic` は `requirements*.txt` ファイルを使用して、依存関係の管理に必要な作業を簡素化するために、依存関係に関連するあらゆる種類の依存関係を管理しません。 `setup.py`ファイル内で`sanic`が依存関係を管理する方法を説明する以下のセクションを読んで理解していることを確認してください。

| 依存関係の種類                                                                                                                              | 使用法                              | インストール                      |
| ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------- | --------------------------- |
| 要件                                                                                                                                   | sanic が機能するために必要な最小の依存関係を事前に確認する | `pip3 install -e .`         |
| tests_require / extras_require['test'] | `sanic`のユニットテストを実行するために必要な依存関係   | `pip3 install -e '.[test]'` |
| extras_require['dev']                                       | 貢献を追加するための追加開発要件                 | `pip3 install -e '.[dev]'`  |
| extras_require['docs']                                      | サニック文書の構築と強化に必要な依存関係             | `pip3 install -e '.[docs]'` |

## すべてのテストを実行中

Sanicのテストを実行するには、以下のようにtoxを使用することをお勧めします。

```sh
tox
```

それは簡単です参照してください!

`tox.ini` には異なる環境が含まれています。 Running `tox` without any arguments will
run all unittests, perform lint and other checks.

## Unittestsを実行

`tox` 環境 -> `[testenv]`

unittestsのみを実行するには、次のような環境で`tox`を実行します。

```sh

tox -e py37 -v -- tests/test_config.py
# or
tox -e py310 -v -- tests/test_config.py
```

## lint のチェックを実行

`tox` 環境 -> `[testenv:lint]`

`flake8`\ , `black` と `isort` のチェックを実行します。

```sh
tox -e lint
```

## 型アノテーションチェックを実行

`tox` 環境 -> `[testenv:type-checking]`

`mypy`チェックを実行します。

```sh
tox -e タイプチェック
```

## 他のチェックを実行

`tox` 環境 -> `[testenv:check]`

他のチェックを実行します。

```sh
tox -e check
```

## 静的解析を実行

`tox` 環境 -> `[testenv:security]`

静的解析セキュリティスキャンを実行

```sh
tox -e セキュリティ
```

## ドキュメントの健全性チェックを実行

`tox` 環境 -> `[testenv:docs]`

ドキュメント上で健全性チェックを行う

```sh
tox -e ドキュメント
```

## コードスタイル

Sanicはコードの一貫性を維持するために、以下のツールを使用します。

1. [isort](https://github.com/timothycrossley/isort)
2. [black](https://github.com/python/black)
3. [flake8](https://github.com/PyCQA/flake8)
4. [slotscheck](https://github.com/ariebovenberg/slotscheck)

### isort

`isort` は Python インポートをソートします。 これは、インポートをアルファベット順にソートされた3つのカテゴリに分割します。

1. ビルトイン
2. サードパーティーの
3. プロジェクト固有の

### ブラック

`black` はPythonのコードフォーマッタです。

### flake8

`flake8` は次のツールを一つにまとめるPythonスタイルガイドです。

1. PyFlakes
2. pycodestyle
3. Ned BatchelderのMcCabeスクリプト

### slotscheck

`slotscheck` は、`__slots__` に問題がないことを保証します (基本クラスの重複や欠落など)。

`isort` 、 `black` 、 `flake8` 、 `slotscheck` のチェックは `tox` lintチェック中に行われます。

**最も簡単**な方法は、コミットする前に以下を実行することです。

```bash
きれいにする
```

詳細については、format@@0(https://tox.readthedocs.io/en/latest/index.html)を参照してください。

## プルリクエスト

したがって、プルリクエストの承認ルールは非常に簡単です。

1. すべてのプルリクエストは単体テストに合格しなければなりません。
2. すべてのプルリクエストは、コア開発チームの少なくとも1人の現在のメンバーによって審査および承認されなければなりません。
3. すべてのプルリクエストは flake8 チェックを渡す必要があります。
4. すべてのプルリクエストは `isort` と `black` 要件に一致する必要があります。
5. 免除が与えられない限り、全てのプルリクエストは **PROPERLY** 型に注釈を付ける必要があります。
6. すべてのプルリクエストは、既存のコードと一致している必要があります。
7. 任意の一般的なインターフェイスから何かを削除/変更することにした場合、非推奨メッセージは format@@0(https://sanicframework.org/ja/guide/project/polices.html#deprecation )に従って同行する必要があります。
8. 新しい機能を実装する場合は、少なくとも1つの単位テストが必要です。
9. 例は次のいずれかでなければなりません:
   - Sanicの使い方の例
   - Sanic extensions の使用例
   - Sanicライブラリと非同期ライブラリの使用例

## ドキュメント

戻って確認(_C) 変更されるようにドキュメントを再作業しています。_
