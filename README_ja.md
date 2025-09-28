# ComfyUI-exit

[<a href="README.md">English</a>][日本語]

ComfyUIを終了させるカスタムノードです。

## Shutdown when Last Batch

ComfyUI の実行がすべて終わったら自動で ComfyUI を終了するカスタムノードです。\
「残バッチ数が 0」に見えたタイミングで即終了せず、**一定時間後に再確認（複数回）** してから終了します。

![image](https://github.com/user-attachments/assets/2e105f4c-08f3-462c-8e5e-290870677c48)

## 特長

* グラフ末尾に置くだけで、**全バッチ完了後に自動終了**
* **再確認あり**：`confirm_delay_sec` 秒後から `confirm_attempts` 回、`confirm_interval_sec` 秒間隔で `/queue` を見直し、毎回 0 なら終了
* **強制終了/通常終了**を選択可能（`os._exit(0)` / `sys.exit(0)`）
* ComfyUI の **HTTP `/queue` API** を利用（外部拡張なしで動作）

## パラメータ

* `confirm_delay_sec` (int): **初回で「残り0」判定になった後**、再確認を始めるまでの待機秒数。保存や後処理の余裕を持たせます。
* `confirm_attempts` (int): 再確認の**試行回数**。この回数すべてで 0 が続いたときに終了します。
* `confirm_interval_sec` (int): 再確認の**各試行間隔**。
* `base_url` (str): ComfyUI のベースURL。ローカル以外で立てている場合に変更。例: `http://127.0.0.1:8188`
* `hard_exit` (bool): `True` で `os._exit(0)` による**確実な即時終了**、`False` で `sys.exit(0)`（可能な範囲で通常終了）。
* `http_timeout_sec` (int): `/queue` 取得のタイムアウト秒。

### 推奨設定の目安

* 基本はデフォルトのままでOK
* ローカル運用・単純な保存のみ：
  `confirm_delay_sec=3〜5`, `confirm_attempts=2〜3`, `confirm_interval_sec=2〜3`, `hard_exit=True`
* 後段に独自後処理があり「できるだけ通常終了したい」：
  `hard_exit=False` を検討


## Exit ComfyUI

指定秒数の経過後にComfyUIを終了させます。

![image](https://github.com/user-attachments/assets/efe0e7a6-2df0-4d68-9d5b-910b3ab5e300)

Google Colabで大量生成後に自動終了させたい場合に使います。
Google Colabのランタイムを接続解除して削除するのはNotebook側で行う必要があります。

## Fetch API

指定したURLにリクエストを送信します。

![image](https://github.com/user-attachments/assets/f7e9a497-7579-4f91-ad11-d45e2e15630b)

## 変更履歴

- V1.2.0 (2025-09-29)
  - `Shutdown when Last Batch` ノードを追加
- V1.1.0 (2024-12-31)
  - `Fetch API` ノードを追加
- v1.0.0 (2024-12-13)
  - `Exit ComfyUI` ノードをリリース
