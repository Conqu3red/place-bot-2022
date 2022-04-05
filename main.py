import time
from worker import Worker
import json
import requests
import requests.auth
from websocket import create_connection
from typing import *
from io import BytesIO
from PIL import Image
import math

COLOR_TO_ID = {
    (0x6D, 0x00, 0x1A): 0,
    (0xBE, 0x00, 0x39): 1,
    (0xFF, 0x45, 0x00): 2,
    (0xFF, 0xA8, 0x00): 3,
    (0xFF, 0xD6, 0x35): 4,
    (0xFF, 0xF8, 0xB8): 5,
    (0x00, 0xA3, 0x68): 6,
    (0x00, 0xCC, 0x78): 7,
    (0x7E, 0xED, 0x56): 8,
    (0x00, 0x75, 0x6F): 9,
    (0x00, 0x9E, 0xAA): 10,
    (0x00, 0xCC, 0xC0): 11,
    (0x24, 0x50, 0xA4): 12,
    (0x36, 0x90, 0xEA): 13,
    (0x51, 0xE9, 0xF4): 14,
    (0x49, 0x3A, 0xC1): 15,
    (0x6A, 0x5C, 0xFF): 16,
    (0x94, 0xB3, 0xFF): 17,
    (0x81, 0x1E, 0x9F): 18,
    (0xB4, 0x4A, 0xC0): 19,
    (0xE4, 0xAB, 0xFF): 20,
    (0xDE, 0x10, 0x7F): 21,
    (0xFF, 0x38, 0x81): 22,
    (0xFF, 0x99, 0xAA): 23,
    (0x6D, 0x48, 0x2F): 24,
    (0x9C, 0x69, 0x26): 25,
    (0xFF, 0xB4, 0x70): 26,
    (0x00, 0x00, 0x00): 27,
    (0x51, 0x52, 0x52): 28,
    (0x89, 0x8D, 0x90): 29,
    (0xD4, 0xD7, 0xD9): 30,
    (0xFF, 0xFF, 0xFF): 31,
}

names = [
    "Burgundy",
    "Dark Red",
    "Red",
    "Orange",
    "Yellow",
    "Pale Yellow",
    "Dark Green",
    "Green",
    "Light Green",
    "Dark Teal",
    "Teal",
    "Light Teal",
    "Dark Blue",
    "Blue",
    "Light Blue",
    "Indigo",
    "Periwinkle",
    "Lavender",
    "Dark Purple",
    "Purple",
    "Pale Purple",
    "Magenta",
    "Pink",
    "Light Pink",
    "Dark Brown",
    "Brown",
    "Beige",
    "Black",
    "Dark Grey",
    "Grey",
    "Light Grey",
    "White",
]

COLOR_TO_NAME = {
    k: v for k, v in zip(COLOR_TO_ID.keys(), names)
}

COLORS = list(COLOR_TO_ID.keys())

IGNORE = (80, 20, 60)

class Manager:
    def __init__(self) -> None:
        with open("config.json") as f:
            data = json.load(f)
        
        self.auths = [requests.auth.HTTPBasicAuth(app["app_id"], app["app_secret"]) for app in data["apps"]]
        
        self.image = data["image"]
        
        self.workers: List[Worker] = []
        for w in data["accounts"]:
            worker =  Worker(w["username"], w["password"], self.auths[w["app"]], w["offset"])
            self.workers.append(worker)
        
        self.board_id = data["board"]
        self.offset = data["offset"]
        
        self.boardx = 2
        self.boardy = 1
        self.width = 1000
        self.height = 1000
        self.board: Image.Image = None
    
    def load_board(self, i):
        worker = self.workers[0]
        if time.time() > worker.token_invalid_at:
            worker.get_token()

        ws = create_connection(
            "wss://gql-realtime-2.reddit.com/query", origin="https://hot-potato.reddit.com"
        )

        #ws.timeout = 2

        ws.send(json.dumps({
            "type": "connection_init",
            "payload": {
                "Authorization": f"Bearer {worker.token}"
            }
        }))
        ws.recv()
        print("init")

        ws.send(json.dumps({
            "id": "1",
            "type": "start",
            "payload": {
                "variables": {
                    "input": {
                        "channel": {
                            "teamOwner": "AFD2022",
                            "category": "CONFIG"
                        }
                    }
                },
                "extensions": {},
                "operationName": "configuration",
                "query": "subscription configuration($input: SubscribeInput!) {\n  subscribe(input: $input) {\n    id\n    ... on BasicMessage {\n      data {\n        __typename\n        ... on ConfigurationMessageData {\n          colorPalette {\n            colors {\n              hex\n              index\n              __typename\n            }\n            __typename\n          }\n          canvasConfigurations {\n            index\n            dx\n            dy\n            __typename\n          }\n          canvasWidth\n          canvasHeight\n          __typename\n        }\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
            }
        }))
        ws.recv()
        print("start 1")



        ws.send(json.dumps({
            "id": str(1 + i),
            "type": "start",
            "payload": {
                "variables": {
                    "input": {
                        "channel": {
                            "teamOwner": "AFD2022",
                            "category": "CANVAS",
                            "tag": str(i)
                        }
                    }
                },
                "extensions": {},
                "operationName": "replace",
                "query": "subscription replace($input: SubscribeInput!) {\n  subscribe(input: $input) {\n    id\n    ... on BasicMessage {\n      data {\n        __typename\n        ... on FullFrameMessageData {\n          __typename\n          name\n          timestamp\n        }\n        ... on DiffFrameMessageData {\n          __typename\n          name\n          currentTimestamp\n          previousTimestamp\n        }\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
            }
        }))
        
        while True:
            t = json.loads(ws.recv())
            print(f"type: {t['type']}")
            if t["type"] == "data":
                msg = t["payload"]["data"]["subscribe"]
                print("   ", msg["data"]["__typename"])
                if msg["data"]["__typename"] == "FullFrameMessageData":
                    url = msg["data"]["name"]
                    #print("    Found full board url...")
                    #print(f"   -- URL: {url} --")
                    board = Image.open(
                        BytesIO(
                            requests.get(
                                url,
                                stream=True
                            ).content
                        )
                    ).convert("RGB")
                    
                    print(f"Loaded board {i}")
                    break
        
        ws.send(json.dumps({"id": str(1 + i), "type": "stop"}))
        
        self.board = board
        return board
    
    @staticmethod
    def closest_color(rgb: Tuple[int, int, int]):
        r, g, b = rgb
        color_diffs = []
        for color in COLORS:
            cr, cg, cb = color
            color_diff = math.sqrt((r - cr)**2 + (g - cg)**2 + (b - cb)**2)
            color_diffs.append((color_diff, color))
        return min(color_diffs)[1]
    
    @staticmethod
    def format_rgb(rgb: Tuple[int, int, int]):
        return f"#{rgb[0]:x}{rgb[1]:x]}{rgb[2]:x}"
    
    def maybe_place(self, worker: Worker):
        # TODO: might be reloading too much?
        print("Reloading Board")
        self.load_board(self.board_id)


        with Image.open(self.image) as f:
            target = f.convert("RGB")

            for y in range(worker.offset[1], target.height):
                for x in range(worker.offset[0], target.width):
                    target_pixel = self.closest_color(target.getpixel((x, y)))
                    current_pixel = self.board.getpixel((self.offset[0] + x, self.offset[1] + y))
                    
                    if target_pixel != current_pixel and target.getpixel((x, y)) != IGNORE:
                        print(f"TRYING PIXEL AT {x}, {y}")
                        print(f"Color is {COLOR_TO_NAME[current_pixel]}, target is {COLOR_TO_NAME[target_pixel]}")
                        self.place_pixel(self.offset[0] + x, self.offset[1] + y, target_pixel, worker)
                        # TODO: update cached board with new pixel
                        return 1
            
        print("No incorrect pixels")
        return -1
    
    def place_pixel(self, x: int, y: int, color: Tuple[int, int, int], worker: Worker):
        headers = {
            "origin": "https://hot-potato.reddit.com",
            "referer": "https://hot-potato.reddit.com/",
            "apollographql-client-name": "mona-lisa",
            "Authorization": "Bearer " + worker.token,
            "Content-Type": "application/json",
        }
        json_data = {
            'operationName': 'setPixel',
            'variables': {
                'input': {
                    'actionName': 'r/replace:set_pixel',
                    'PixelMessageData': {
                        'coordinate': {
                            'x': x,
                            'y': y,
                        },
                        'colorIndex': COLOR_TO_ID[color],
                        'canvasIndex': self.board_id,
                    },
                },
            },
            'query': 'mutation setPixel($input: ActInput!) {\n  act(input: $input) {\n    data {\n      ... on BasicMessage {\n        id\n        data {\n          ... on GetUserCooldownResponseMessageData {\n            nextAvailablePixelTimestamp\n            __typename\n          }\n          ... on SetPixelResponseMessageData {\n            timestamp\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n',
        }

        r = requests.post('https://gql-realtime-2.reddit.com/query', headers=headers, json=json_data)
        d = r.json()
        if d["data"] is not None:
            for packet in d["data"]["act"]["data"]:
                if packet["data"]["__typename"] == "GetUserCooldownResponseMessageData":
                    worker.cooldown = packet["data"]["nextAvailablePixelTimestamp"] / 1000
                    print(f"PIXEL DRAWN AT {x}, {y}")
                    print(f"Cooldown for {worker.cooldown - time.time():.0f}s")
                    return
        
        print(d["data"])
        print("FAILED TO DRAW PIXEL.")
        # probably on cooldown
        worker.get_cooldown()
        print("COOLDOWN:", worker.cooldown)
        if worker.cooldown == 0:
            worker.cooldown = -1
    
    def mainloop(self):
        while True:
            for worker in self.workers:
                if time.time() > worker.token_invalid_at:
                    print("Refreshing worker token")
                    worker.get_token()
            
            for worker in self.workers:
                if worker.cooldown == -1:
                    print(f"Account {worker.username} maybe ratelimited")
                
                if worker.cooldown <= 0:
                    worker.get_cooldown()
                
                if time.time() > worker.cooldown and worker.cooldown != -1:
                    if self.maybe_place(worker) == -1:
                        break
                        # BUG: this will break when there are offsets not [0, 0], too bad!
            cooldowns = [w.cooldown for w in self.workers if w.cooldown > 0]
            if not cooldowns:
                cooldowns.append(time.time())
            next_pixel_time = min(cooldowns)
            print(f"Sleep 10... Next in {next_pixel_time - time.time():.0f}s")
            time.sleep(10)

m = Manager()
m.mainloop()

# TODO: remove your password from the config bozo