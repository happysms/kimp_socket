import json
import time

from exchange.binance import BinanceFuture
from exchange.upbit import Upbit
import asyncio
from aiohttp import ClientSession


def cal_avg_price(orderbook, trade_size):
    """
    :param orderbook:
    :param trade_size:
    :return: avg_price 평단가
    """
    asks = orderbook['asks']
    ask_amount = 0
    long_avg_price = 0
    trade_size = trade_size

    for idx, (price, amount) in enumerate(asks):
        ask_amount += amount
        if ask_amount >= trade_size:
            alloc_size = trade_size - (ask_amount - amount)
            if idx == 0:
                long_avg_price += price
            else:
                long_avg_price += (alloc_size / trade_size) * price
            break
        else:
            long_avg_price += (amount / trade_size) * price

    bids = orderbook['bids']
    bid_amount = 0
    short_avg_price = 0

    for idx, (price, amount) in enumerate(bids):
        bid_amount += amount
        if bid_amount >= trade_size:
            alloc_size = trade_size - (bid_amount - amount)
            if idx == 0:
                short_avg_price += price
            else:
                short_avg_price += (alloc_size / trade_size) * price
            break
        else:
            short_avg_price += (amount / trade_size) * price

    return long_avg_price, short_avg_price


class UpbitBinanceFuture:
    available_coin_list = []
    exchange_rate = 0
    upbit_orderbook_list = []
    binance_future_orderbook_list = []
    trade_size = 10000000

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
        """5초에 한번 환율 갱신"""
        while True:
            async with ClientSession() as session:
                async with session.get("https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD") as response:
                    r = await response.read()
                    self.exchange_rate = json.loads(r.decode('utf-8'))[0]['basePrice']
            await asyncio.sleep(5)

    async def cal_spread(self):
        while True:
            for trade_size in [100000, 1000000, 10000000]:
                print("\n\n\n\n\ntrading size(won): ", format(trade_size, ','))
                for binance_key in self.binance_future.orderbook_dict.keys():
                    if self.binance_future.orderbook_dict.get(binance_key) and self.upbit.orderbook_dict.get(binance_key):
                        binance_orderbook = self.binance_future.orderbook_dict[binance_key]
                        upbit_orderbook = self.upbit.orderbook_dict[binance_key]
                        upbit_long, upbit_short = cal_avg_price(upbit_orderbook, trade_size)
                        upbit_long = upbit_long / self.exchange_rate * (1 + Upbit.market_fee)
                        upbit_short = upbit_short / self.exchange_rate * (1 - Upbit.market_fee)

                        binance_long, binance_short = cal_avg_price(binance_orderbook, trade_size / self.exchange_rate)
                        binance_long = binance_long * (1 + BinanceFuture.market_fee)
                        binance_short = binance_short * (1 - BinanceFuture.market_fee)

                        # print("upbit: ", binance_key, upbit_long, upbit_short)
                        # print("binance: ", binance_key, binance_long, binance_short)
                        print("upbit_long - binance_short: ", binance_key, round((binance_short / upbit_long - 1) * 100, 3))
                        print("upbit_short - binance_long: ", binance_key, round((upbit_short / binance_long - 1) * 100, 3))

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

