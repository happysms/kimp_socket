import ccxt.async_support as ccxt
from pprint import pprint
import websockets
import asyncio
import json



async def adapter_binance_orderbook(orderbook):
    coin = orderbook['stream'][: orderbook['stream'].find("usdt")].upper()
    orderbook = orderbook['data']
    orderbook_dict = dict()
    orderbook_dict['coin'] = coin
    orderbook_dict['time'] = orderbook['T'] / 1000
    orderbook_dict['asks'] = list(map(lambda x: [float(x[0]), float(x[1]) * float(x[0])], orderbook['a']))
    orderbook_dict['bids'] = list(map(lambda x: [float(x[0]), float(x[1]) * float(x[0])], orderbook['b']))
    return orderbook_dict


class BinanceFuture:
    exchange_name = "binance-future"
    url = 'wss://fstream.binance.com/stream'
    market_fee = 0.0004
    limit_fee = 0.0004
    orderbook_dict = dict()
    available_coin_list = []

    @staticmethod
    async def get_subscribe_items():
        try:
            exchange_obj = ccxt.binance(config={'enableRateLimit': True,
                                                'options': {
                                                            'defaultType': "future"}
                                                })
            markets = await exchange_obj.fetch_markets()
            coin_list = []

            for coin in markets:
                if coin['id'].find("USDT") != -1:
                    coin_list.append(coin['id'].replace("USDT", "").replace("_220930", ""))
            coin_list = list(set(coin_list))
            await exchange_obj.close()
            return coin_list

        except Exception:
            raise

    async def socket_order_book(self, callback):
        for coin in self.available_coin_list:
            self.orderbook_dict[coin] = None

        coin_list = await BinanceFuture.get_subscribe_items()
        params_list = [f"{coin.lower()}usdt@depth10@500ms" for coin in coin_list]
        subscribe_fmt = {
                            "method": "SUBSCRIBE",
                            "params": params_list,
                            "id": 1
                            }

        subscribe_data = json.dumps(subscribe_fmt)
        async with websockets.connect(self.url) as websocket:
            await websocket.send(subscribe_data)

            while True:
                await callback(await websocket.recv())

    async def process_buffer(self, *args, **kwargs):
        orderbook_str = json.loads(args[0])
        if "id" not in orderbook_str.keys():
            orderbook_dict = await adapter_binance_orderbook(orderbook_str)
            self.orderbook_dict[orderbook_dict['coin']] = orderbook_dict


class BinanceSpot:
    pass


if "__main__" == __name__:
    binance_future_obj = BinanceFuture()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(binance_future_obj.socket_order_book(binance_future_obj.process_buffer))


