import json
import time

from exchange.binance import BinanceFuture
from exchange.upbit import Upbit
import asyncio
from aiohttp import ClientSession


class UpbitBinanceFuture:
    available_coin_list = []
    exchange_rate = 0
    upbit_orderbook_list = []
    binance_future_orderbook_list = []

    def __init__(self, upbit: Upbit, binance_future: BinanceFuture):
        self.upbit = upbit
        self.binance_future = binance_future

    async def set_available_coin_list(self):
        upbit_items = await Upbit.get_subscribe_items()
        upbit_items = list(map(lambda x: x.replace("KRW-", ""), upbit_items))
        binance_future_items = await BinanceFuture.get_subscribe_items()

        for upbit_item in upbit_items:
            for binance_future_item in binance_future_items:
                if upbit_item == binance_future_item:
                    self.available_coin_list.append(upbit_item)
                    continue

        self.binance_future.available_coin_list = self.available_coin_list
        self.upbit.available_coin_list = self.available_coin_list

    async def update_exchange_rate(self):
        while True:
            async with ClientSession() as session:
                async with session.get("https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD") as response:
                    r = await response.read()
                    self.exchange_rate = json.loads(r.decode('utf-8'))[0]['basePrice']
                    print(self.exchange_rate)
            await asyncio.sleep(5)

    async def cal_spread(self):
        while True:
            print("---")

            print(self.binance_future.orderbook_dict)
            print(self.upbit.orderbook_dict)
            print(self.exchange_rate)
            start_time = time.time()

            if self.binance_future.orderbook_dict.get("BTC"):
                print("time delay: ", self.binance_future.orderbook_dict['BTC']['time'] / 1000 - start_time)
                print("---")

            await asyncio.sleep(2)


if "__main__" == __name__:
    binance_future = BinanceFuture()
    upbit = Upbit()
    upbit_binance_future_obj = UpbitBinanceFuture(upbit=upbit, binance_future=binance_future)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(upbit_binance_future_obj.set_available_coin_list())

    tasks = [asyncio.ensure_future(upbit.socket_order_book(upbit.process_buffer)),
             asyncio.ensure_future(binance_future.socket_order_book(binance_future.process_buffer)),
             asyncio.ensure_future(upbit_binance_future_obj.cal_spread()),
             asyncio.ensure_future(upbit_binance_future_obj.update_exchange_rate())]

    loop.run_until_complete(asyncio.wait(tasks))

