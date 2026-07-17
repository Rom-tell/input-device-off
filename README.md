# 入力デバイスオフ

⚠️ **Notice / 注意事項**  
このリポジトリはオープンソースとして公開していますが、個人利用目的で管理しているため、バグ報告、機能要望、プルリクエストなどのサポートやコミュニケーションは一切受け付けておりません。  
This repository is public, but I do not accept any issues, pull requests, or personal inquiries. Thank you for understanding.

---

掃除中などにキーボードやマウスを一時的に無効化するWindowsアプリです。

## 特徴

- キーボードだけ、またはマウスだけを選んで無効化できます
- マウスが使える状態ではボタンで簡単に復帰できます
- インストール不要の1ファイル exe です

## ダウンロード

[Releases](https://github.com/Rom-tell/input-device-off/releases) から `input-device-off.exe` をダウンロードして実行してください。

## 使い方

1. `input-device-off.exe` を起動します
2. 無効化するデバイスを選択します（キーボード or マウス）
3. マウスを選ぶ場合は復帰用ショートカットを確認します（デフォルト: `Ctrl+Shift+F12`）
4. 「無効化する」ボタンを押します
5. 掃除が終わったら復帰操作を行います

| 無効化したデバイス | 復帰方法 |
|---|---|
| キーボード | 画面の「解除する」ボタンをクリック |
| マウス | ショートカットキーを押す |

## 注意事項

- 管理者権限が必要な場合があります
- `Ctrl+Alt+Del` などのシステムキーはブロックできない場合があります
