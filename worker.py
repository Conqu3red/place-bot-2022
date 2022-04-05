from typing import *

import requests
import requests.auth
from dataclasses import dataclass
import time

@dataclass
class Worker:
    username: str
    password: str
    client_auth: requests.auth.HTTPBasicAuth
    offset: List[int]

    token: str = None
    token_invalid_at: float = 0
    cooldown: float = 0

    def get_token(self):
        post_data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "duration": "permanent",
        }
        headers = {
            "User-Agent": "PlaceClient By Conqu3red",
        }

        r = requests.post("https://www.reddit.com/api/v1/access_token", auth=self.client_auth, data=post_data, headers=headers)
        if r.ok:
            data = r.json()
            if "access_token" in data:
                self.token = data["access_token"]
                self.token_invalid_at = time.time() + data["expires_in"]
            else:
                print(f"FAILED to get token for {self.username}")
                print(data)
                self.token_invalid_at = 0
    
    def get_cooldown(self):
        headers = {
            "origin": "https://hot-potato.reddit.com",
            "referer": "https://hot-potato.reddit.com/",
            "apollographql-client-name": "mona-lisa",
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }

        json_data = {
            'operationName': 'getUserCooldown',
            'variables': {
                'input': {
                    'actionName': 'r/replace:get_user_cooldown',
                },
            },
            'query': 'mutation getUserCooldown($input: ActInput!) {\n  act(input: $input) {\n    data {\n      ... on BasicMessage {\n        id\n        data {\n          ... on GetUserCooldownResponseMessageData {\n            nextAvailablePixelTimestamp\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n',
        }

        r = requests.post('https://gql-realtime-2.reddit.com/query', headers=headers, json=json_data).json()
        print(r)

        if r["data"] is not None:
            for d in r["data"]["act"]["data"]:
                if d["data"]["__typename"] == "GetUserCooldownResponseMessageData":
                    self.cooldown = (d["data"]["nextAvailablePixelTimestamp"] or 0) / 1000
                    return self.cooldown
        
        print("ERROR - couldn't get time to next available!")
        self.cooldown = 0
        return 0