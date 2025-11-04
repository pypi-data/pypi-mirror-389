import os
import json
from types import SimpleNamespace

import requests
import websocket
from urllib.parse import parse_qs
from tpds.app.vars import get_url_base


class Messages:
    op_codes = {
        "loopback": 0,
        "get_mplab_path": 1,
        "open_notebook": 2,
        "open_link": 3,
        "file_upload": 11,
        "text_box": 12,
        "dropdown": 13,
        "open_explorer": 14,
        "messagebox": 18,
        "symm_auth_inputs": 40,
        "wpc_user_inputs": 41,
        "sha10x_symm_auth_inputs": 42,
        "provision_inputs": 50,
    }

    # msg_schema = {"msg_id": "int", "parameters": ["string"]}
    def encode(self, op_code: str, args: list):
        qs = parse_qs(os.environ.get('QUERY_STRING', ''))
        message = {"msg_id": self.op_codes.get(op_code, "loopback"), "parameters": args, "app_id": qs.get("id", [""])[0]}
        return json.dumps(message)


class Client:
    def __init__(self, parent, recv_handler=None):
        self.client = websocket.WebSocket(on_error=self.error, on_close=self.close)
        self.client.connect(f"{get_url_base().replace('http', 'ws')}/websocket")

    def error(self, error_code):
        print("error code: {}".format(error_code))
        print(self.client.errorString())

    def close(self):
        print("close - exiting")
        self.client.close()

    def send_message(self, op_code, args: list):
        msg = Messages()
        message = msg.encode(op_code, args)
        self.client.send(message)


def tpdsAPI_get(url_suffix):
    response = requests.get(url=f"{get_url_base()}/{url_suffix}")
    return json.loads(response.content.decode("utf-8"), object_hook=lambda d: SimpleNamespace(**d))


if __name__ == "__main__":
    # Server must be running before this application starts sending
    # requests
    pass
