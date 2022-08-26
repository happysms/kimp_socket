import datetime
import time
from pprint import pprint

import websockets
import asyncio
import json
import env
import pykorbit


def adapter_korbit_orderbook(orderbook_dict):
    orderbook_dict = orderbook_dict["data"]
    if orderbook_dict.get('currency_pair', None):
        new_orderbook = dict(coin=orderbook_dict['currency_pair'].replace("_krw", "").upper(),
                             time=orderbook_dict['timestamp'] / 1000,
                             asks=[], bids=[])
        new_orderbook['time'] = orderbook_dict['timestamp'] / 1000
        new_orderbook['asks'] = list(map(lambda x: [float(x['price']), float(x['price']) * float(x['amount'])], orderbook_dict['asks']))
        new_orderbook['bids'] = list(map(lambda x: [float(x['price']), float(x['price']) * float(x['amount'])], orderbook_dict['bids']))
        return new_orderbook
    else:
        return None


class Korbit:
    exchange_name = "korbit"
    url = "wss://ws.korbit.co.kr/v1/user/push"
    market_fee = 0.002
    orderbook_dict = dict()
    access_key = env.KORBIT_ACCESS_KEY
    secret_key = env.KORBIT_SECRET_KEY
    available_coin_list = []

    def __init__(self):
        pass

    async def socket_order_book(self, callback):
        korbit_ticker_list = list(map(lambda x: x.lower() + "_krw", self.available_coin_list))
        korbit_ticker_list_str = ",".join(korbit_ticker_list)
        now = datetime.datetime.now()
        timestamp = int(now.timestamp() * 1000)
        subscribe_fmt = {
                          "accessToken": None,
                          "timestamp": timestamp,
                          "event": "korbit:subscribe",
                          "data": {
                              "channels": [f"orderbook:{korbit_ticker_list_str}"]
                          }
                        }

        subscribe_data = json.dumps(subscribe_fmt)
        async with websockets.connect(self.url) as websocket:
            await websocket.send(subscribe_data)
            while True:
                await callback(await websocket.recv())

    async def process_buffer(self, *args, **kwargs):
        orderbook_dict = json.loads(args[0])
        updated_orderbook_dict = adapter_korbit_orderbook(orderbook_dict)
        if updated_orderbook_dict:
            self.orderbook_dict[updated_orderbook_dict['coin']] = updated_orderbook_dict

    @staticmethod
    async def get_subscribe_items() -> list:
        loop = asyncio.get_event_loop()
        items = await loop.run_in_executor(None, pykorbit.get_tickers)
        return items


if "__main__" == __name__:
    korbit = Korbit()
    korbit.available_coin_list = ["BTC", "ETH"]
    loop = asyncio.get_event_loop()
    items = loop.run_until_complete(Korbit.get_subscribe_items())
    loop.run_until_complete(korbit.socket_order_book(korbit.process_buffer))


