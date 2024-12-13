import time
import os
import threading

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


NODE_CLASS_MAPPINGS = {
    "ExitComfyUI": ExitComfyUINode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExitComfyUI": "Exit ComfyUI",
}