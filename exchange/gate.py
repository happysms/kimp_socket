import ccxt.async_support as ccxt
from pprint import pprint
import websockets
import asyncio
import json
import time


class GateFuture:
    exchange_name = "gate-future"
    market_fee = 0.05
    orderbook_dict = dict()
    available_coin_list = []

    def __init__(self):
        self.gate_obj = ccxt.gate(config={
            'enableRateLimit': True,
            'options': {
                'defaultType': "future"}})

    async def get_subscribe_items(self):
        try:
            markets = await self.gate_obj.fetch_markets()
            coin_list = []
            for coin in markets:
                if coin['id'].find("USDT") != -1:
                    coin_list.append(coin['id']
                                     .replace("_USDT", "")
                                     .replace("_20221230", "")
                                     .replace("_20220909", "")
                                     .replace("_20220902", ""))
            coin_list = list(set(coin_list))
            await self.gate_obj.close()
            return coin_list

        except Exception:
            raise

    async def socket_order_book(self, callback):
        subscribe_items = list(map(lambda x: x + "_USDT", self.available_coin_list))
        uri = f"wss://fx-ws.gateio.ws/v4/ws/usdt"

        async with websockets.connect(uri) as websocket:
            subscribe_fmt = {"time": int(time.time()), "channel": "futures.order_book", "event": "subscribe", "payload": ["BTC_USDT", "20", "0"]}
            subscribe_data = json.dumps(subscribe_fmt)
            await websocket.send(subscribe_data)

            while True:
                async for recv in self.generator_call(subscribe_items, websocket):
                    await callback(recv)

    async def generator_call(self, subscribe_items, websocket):
        for item in subscribe_items:
            subscribe_fmt = {"time": int(time.time()), "channel": "futures.order_book", "event": "subscribe", "payload": [item, "20", "0"]}
            subscribe_data = json.dumps(subscribe_fmt)
            await websocket.send(subscribe_data)
            yield websocket.recv()

    async def process_buffer(self, *args, **kwargs):
        pprint(args[0])
        # orderbook_str = args[0].decode('utf-8')


if "__main__" == __name__:
    gate_future_obj = GateFuture()
    loop = asyncio.get_event_loop()
    coin_list = loop.run_until_complete(gate_future_obj.socket_order_book(gate_future_obj.process_buffer))
    print(coin_list)
    # loop.run_until_complete(gate_future_obj.socket_order_book(gate_future_obj.process_buffer))
