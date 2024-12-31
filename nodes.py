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
        # 別スレッドで実行
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


NODE_CLASS_MAPPINGS = {
    "ExitComfyUI": ExitComfyUINode,
    "FetchApi": FetchApiNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExitComfyUI": "Exit ComfyUI",
    "FetchApi": "Fetch API",
}
