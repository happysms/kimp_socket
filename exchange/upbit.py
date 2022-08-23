from pprint import pprint
import websockets
import pyupbit
import asyncio
import json
import time


class Upbit:
    exchange_name = "upbit"
    url = 'wss://api.upbit.com/websocket/v1'
    market_fee = 0.0005
    limit_fee = 0.0005
    orderbook_dict = dict()
    available_coin_list = []

    async def socket_order_book(self, callback):
        subscribe_items = await Upbit.get_subscribe_items()
        subscribe_fmt = [
            {"ticket": "test-websocket"},
            {
                "type": "orderbook",
                "codes": subscribe_items,
                "isOnlyRealtime": True
            },
            {"format": "SIMPLE"}
        ]

        subscribe_data = json.dumps(subscribe_fmt)
        async with websockets.connect(self.url) as websocket:
            await websocket.send(subscribe_data)

            while True:
                await callback(await websocket.recv())

    @staticmethod
    def adapter_orderbook(cur_orderbook):
        new_orderbook = dict(coin=cur_orderbook['cd'].replace("KRW-", ""),
                             time=cur_orderbook['tms'] / 1000, asks=[], bids=[])

        for maker_order in cur_orderbook['obu']:
            ask_price = maker_order['ap']
            ask_side = maker_order['as']
            bid_price = maker_order['bp']
            bid_side = maker_order['bs']
            new_orderbook["asks"].append([ask_price, ask_side * ask_price])
            new_orderbook["bids"].append([bid_price, bid_side * bid_price])
            new_orderbook["bids"].sort(key=lambda x: -x[0])

        return new_orderbook

    async def process_buffer(self, *args, **kwargs):
        orderbook_str = args[0].decode('utf-8')
        orderbook_dict = json.loads(orderbook_str)
        updated_orderbook_dict = Upbit.adapter_orderbook(orderbook_dict)
        self.orderbook_dict[updated_orderbook_dict['coin']] = updated_orderbook_dict

    @staticmethod
    async def get_subscribe_items() -> list:
        try:
            loop = asyncio.get_event_loop()
            items = await loop.run_in_executor(None, pyupbit.get_tickers, "KRW")
            return items
        except Exception:
            raise



if "__main__" == __name__:
    upbit_obj = Upbit()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(upbit_obj.socket_order_book(upbit_obj.process_buffer))

