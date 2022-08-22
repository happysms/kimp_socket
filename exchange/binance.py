import ccxt.async_support as ccxt
from pprint import pprint
import websockets
import asyncio
import json
import time


class BinanceFuture:
    exchange_name = "binance-future"
    url = 'wss://api.upbit.com'
    market_fee = 0.04


    @staticmethod
    async def get_subscribe_items():
        try:
            exchange_obj = ccxt.binance(config={'enableRateLimit': True,
                                                'options': {
                                                            'defaultType': "future"}
                                                })

            markets = await exchange_obj.fetch_markets()
            pprint(markets)

        except Exception:
            raise


class BinanceSpot:
    pass


if "__main__" == __name__:
    upbit_obj = BinanceFuture()
    loop = asyncio.get_event_loop()
    # loop.run_until_complete(upbit_obj.socket_order_book(upbit_obj.process_buffer))

