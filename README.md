# AIウミガメのスープ

出題者を Jev (TypeSafe AI) が担当するウミガメのスープ。プレイヤーの質問に「はい / いいえ / 関係ありません」で答え、真相に到達したかを確率で判定する。

デモ: https://umigame-soup-three.vercel.app

## 構成

- `public/index.html` : 画面 (静的 HTML)
- `api/ask.py` : Vercel Python 関数。問題と真相を持ち、Jev の System One API に Choice / Noul で判定を投げる
- `vercel.json` : 関数のタイムアウト設定

## 動かし方

Vercel の環境変数に `TYPESAFE_API_KEY` を設定して `vercel --prod` でデプロイする。問題を足すときは `api/ask.py` の `PUZZLES` に追記する。
