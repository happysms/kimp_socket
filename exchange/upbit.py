import websockets
import pyupbit
import asyncio
import json
import jwt
import hashlib
import uuid
from urllib.parse import urlencode, unquote
import env
from aiohttp import ClientSession
import ccxt.async_support as ccxt


class Upbit:
    exchange_name = "upbit"
    url = 'wss://api.upbit.com/websocket/v1'
    market_fee = 0.0005
    limit_fee = 0.0005
    orderbook_dict = dict()
    available_coin_list = []
    access_key = env.UPBIT_ACCESS_KEY
    secret_key = env.UPBIT_SECRET_KEY
    server_url = "https://api.upbit.com"

    def __init__(self):
        self.upbit_obj = ccxt.upbit()

    async def socket_order_book(self, callback):
        subscribe_items = list(map(lambda x: "KRW-" + x, self.available_coin_list))
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

    async def get_subscribe_items(self) -> list:
        markets = await self.upbit_obj.load_markets()
        coin_list = list(map(lambda x: x.replace("/KRW", ""), markets.keys()))
        return coin_list

    async def buy_order(self, ticker, amount):
        params = {
            'market': ticker,
            'ord_type': 'price',
            'side': 'bid',
            'price': str(amount)
        }
        query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }

        async with ClientSession() as session:
            async with session.post(self.server_url + '/v1/orders', json=params, headers=headers) as response:
                r = await response.read()

        return r

    async def sell_order(self, ticker, price, amount):
        params = {
            'market': ticker,
            'ord_type': 'market',
            'side': 'ask',
            'volume': str(amount / price),
            'price': str(amount)
        }

        query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }

        async with ClientSession() as session:
            async with session.post(self.server_url + '/v1/orders', json=params, headers=headers) as response:
                r = await response.read()

        return r


if "__main__" == __name__:
    upbit_obj = Upbit()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(upbit_obj.socket_order_book(upbit_obj.process_buffer))

