import time
import os
import threading
import requests

class ComfyAnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


class ExitComfyUINode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any": (ComfyAnyType("*"), {}),
                "wait_seconds": ("INT", {"default": 5}),
            }
        }

    OUTPUT_NODE = True
    FUNCTION = 'exit_comfyui'
    RETURN_TYPES = ()
    CATEGORY = "utils"


    def sleep_and_exit(self, wait_seconds):
        for i in range(wait_seconds):
            print(f"Exit ComfyUI in {wait_seconds - i} seconds...")
            time.sleep(1)

        print("Exit ComfyUI!")
        os._exit(0)


    def exit_comfyui(self, any, wait_seconds):
        # 別スレッドで実行
        threading.Thread(target=self.sleep_and_exit, args=(wait_seconds,)).start()
        return (0, )


class FetchApiNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any": (ComfyAnyType("*"), {}),
                "url": ("STRING",),
            }
        }

    RETURN_TYPES = ("STRING",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "execute"
    CATEGORY = "api"

    def execute(self, any, url):
        return (requests.get(url).content, )    



class ExitWhenLastBatchConfirm:
    """
    キューの残り件数を確認し、残バッチ数が0なら (再確認のうえ) ComfyUI を終了するノード。

    推奨配置:
      - グラフの末端（保存ノードなどの直後）

    仕組み:
      - ノード実行時に /queue を取得し、(pending + running - 1) を「この実行後に残る件数」とみなす
      - 0 なら終了予約を入れる（confirm_delay 後に再チェック）
      - 再チェックで 0 が N回連続で確認できたら終了
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 終端ノードにするためのダミー入力
                "any": (ComfyAnyType("*"), {}),
                # 初回判定が0のとき、何秒後に再確認を開始するか
                "confirm_delay_sec": ("INT", {"default": 5, "min": 0, "max": 120}),
                # 再確認の試行回数（連続で0ならOK）
                "confirm_attempts": ("INT", {"default": 2, "min": 1, "max": 10}),
                # 再確認の各試行の間隔
                "confirm_interval_sec": ("INT", {"default": 2, "min": 1, "max": 60}),
                # /queue のベースURL
                "base_url": ("STRING", {"default": "http://127.0.0.1:8188"}),
                # 強制終了を使うか（True: os._exit(0), False: sys.exit(0)）
                "hard_exit": ("BOOLEAN", {"default": True}),
                # /queue タイムアウト
                "http_timeout_sec": ("INT", {"default": 2, "min": 1, "max": 10}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "maybe_shutdown"
    OUTPUT_NODE = True
    CATEGORY = "utils"

    # ---- 内部ユーティリティ ----
    def _get_remaining_after_this(self, base, timeout):
        """
        /queue を見て「この実行が終わった時点での残り」を推定して返す。
        running の1件は「今まさに実行中の自分」とみなして引く。
        """
        try:
            resp = requests.get(f"{base}/queue", timeout=timeout)
            resp.raise_for_status()
            r = resp.json()

            # 代表的なキーをフォールバックしながら読む
            pending_list = r.get("queue", r.get("queue_pending", [])) or []
            running_list = r.get("queue_running", []) or []
            pending = len(pending_list)
            running = len(running_list)

            remaining = max(pending + running - 1, 0)
            print(f"[ExitWhen] queue: pending={pending}, running={running}, remaining(after this)={remaining}")
            return remaining
        except Exception as e:
            print(f"[ExitWhen] queue check failed: {e}")
            return None

    def _exit_process(self, hard=True):
        print("[ExitWhen] Exiting ComfyUI (requested by node).")
        if hard:
            print("[ExitWhen] hard exit (os._exit(0))")
            os._exit(0)
        else:
            import sys
            print("[ExitWhen] soft exit (sys.exit(0))")
            sys.exit(0)

    def _confirm_and_exit(self, base_url, http_timeout, confirm_attempts, confirm_interval_sec, hard_exit):
        """
        再確認を所定回数行い、毎回 0 であれば終了。
        一度でも 0 以外になったら中止。
        """
        for i in range(1, confirm_attempts + 1):
            remaining = self._get_remaining_after_this(base_url, http_timeout)
            # 取得失敗時は保守的に中止（終了しない）
            if remaining is None:
                print(f"[ExitWhen] confirm #{i}: could not determine, abort shutdown.")
                return
            if remaining != 0:
                print(f"[ExitWhen] confirm #{i}: remaining={remaining} -> abort shutdown.")
                return
            print(f"[ExitWhen] confirm #{i}: remaining=0 OK")
            # 最後の確認以外は待ってから次ループ
            if i < confirm_attempts:
                time.sleep(confirm_interval_sec)

        # すべて 0 → 終了
        self._exit_process(hard_exit)

    def _schedule_confirm(self, delay_sec, base_url, http_timeout, confirm_attempts, confirm_interval_sec, hard_exit):
        def runner():
            # 遅延してから再確認ループ
            if delay_sec > 0:
                time.sleep(delay_sec)
            self._confirm_and_exit(
                base_url=base_url,
                http_timeout=http_timeout,
                confirm_attempts=confirm_attempts,
                confirm_interval_sec=confirm_interval_sec,
                hard_exit=hard_exit,
            )
        t = threading.Thread(target=runner, daemon=True)
        t.start()

    # ---- メイン ----
    def maybe_shutdown(
        self,
        any,
        confirm_delay_sec=3,
        confirm_attempts=2,
        confirm_interval_sec=2,
        base_url="http://127.0.0.1:8188",
        hard_exit=True,
        http_timeout_sec=2,
    ):
        print("[ExitWhen] checking if this is the last batch...")

        remaining = self._get_remaining_after_this(base_url, http_timeout_sec)

        # None: /queue 取得失敗 → 安全側で終了しない
        if remaining is None:
            print("[ExitWhen] initial check failed; skip shutdown.")
            return ()

        # “この実行後に残り0”なら確認フェーズへ
        if remaining == 0:
            print(f"[ExitWhen] schedule confirm in {confirm_delay_sec}s "
                  f"(attempts={confirm_attempts}, interval={confirm_interval_sec}s)")
            self._schedule_confirm(
                delay_sec=confirm_delay_sec,
                base_url=base_url,
                http_timeout=http_timeout_sec,
                confirm_attempts=confirm_attempts,
                confirm_interval_sec=confirm_interval_sec,
                hard_exit=hard_exit,
            )
        else:
            print(f"[ExitWhen] not last; remaining(after this)={remaining}, keep running.")
        return ()


NODE_CLASS_MAPPINGS = {
    "ExitComfyUI": ExitComfyUINode,
    "FetchApi": FetchApiNode,
    "ExitWhenLastBatchConfirm": ExitWhenLastBatchConfirm,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExitComfyUI": "Exit ComfyUI",
    "FetchApi": "Fetch API",
    "ExitWhenLastBatchConfirm": "Exit when Last Batch (Confirm)",
}
