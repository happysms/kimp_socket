import os
import sys
from pprint import pprint

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import json
from exchange.binance import BinanceFuture
from exchange.upbit import Upbit
import asyncio
from aiohttp import ClientSession
from alert.bot import TelegramBot


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

        if idx == len(asks) - 1 and ask_amount <= trade_size:
            long_avg_price = 1e12

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

        if idx == len(bids) - 1 and bid_amount <= trade_size:
            short_avg_price = -1e12

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
        self.telegram_bot = TelegramBot()

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
            try:
                async with ClientSession() as session:
                    async with session.get("https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD") as response:
                        r = await response.read()
                        self.exchange_rate = json.loads(r.decode('utf-8'))[0]['basePrice']
                await asyncio.sleep(5)
            except Exception:
                exit(0)

    async def cal_kimp(self):
        while True:
            try:
                for trade_size in [1000000, 10000000]:
                    print("\n\n\n\n\ntrading size(won): ", format(trade_size, ','))
                    for binance_key in self.binance_future.orderbook_dict.keys():
                        if self.binance_future.orderbook_dict.get(binance_key) and self.upbit.orderbook_dict.get(binance_key):

                            binance_orderbook = self.binance_future.orderbook_dict[binance_key]
                            upbit_orderbook = self.upbit.orderbook_dict[binance_key]
                            upbit_long, upbit_short = cal_avg_price(upbit_orderbook, trade_size)
                            if upbit_long > 1e10 or upbit_short < -1e10:
                                continue

                            upbit_long = upbit_long / self.exchange_rate * (1 + Upbit.market_fee)
                            upbit_short = upbit_short / self.exchange_rate * (1 - Upbit.market_fee)
                            binance_long, binance_short = cal_avg_price(binance_orderbook, trade_size / self.exchange_rate)
                            if binance_long > 1e10 or binance_short < -1e10:
                                continue

                            binance_long = binance_long * (1 + BinanceFuture.market_fee)
                            binance_short = binance_short * (1 - BinanceFuture.market_fee)
                            upbit_premium = round((binance_short / upbit_long - 1) * 100, 3)
                            binance_premium = round((upbit_short / binance_long - 1) * 100, 3)
                            print("upbit_long - binance_short: ", binance_key, upbit_premium)
                            print("upbit_short - binance_long: ", binance_key, binance_premium)

                            if 0 < upbit_premium < 10:
                                self.telegram_bot.log(f"{binance_key} 거래액: {format(trade_size, ',')}won\t 역김프: {upbit_premium}%")
                            elif 4 < binance_premium < 10:
                                self.telegram_bot.log(f"{binance_key} 거래액: {format(trade_size, ',')}\t 김프: {binance_premium}%")

                loop.run_in_executor(None, self.telegram_bot.send_logs)
                await asyncio.sleep(2)
            except Exception:
                exit(0)

    async def health_check(self):
        while True:
            self.telegram_bot.log("health_check")
            loop.run_in_executor(None, self.telegram_bot.send_logs)
            await asyncio.sleep(10800)  # 3 hour


if "__main__" == __name__:
    try:
        binance_future = BinanceFuture()
        upbit = Upbit()
        upbit_binance_future_obj = UpbitBinanceFuture(upbit=upbit, binance_future=binance_future)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(upbit_binance_future_obj.set_available_coin_list())

        tasks = [asyncio.ensure_future(upbit.socket_order_book(upbit.process_buffer)),
                 asyncio.ensure_future(binance_future.socket_order_book(binance_future.process_buffer)),
                 asyncio.ensure_future(upbit_binance_future_obj.cal_kimp()),
                 asyncio.ensure_future(upbit_binance_future_obj.update_exchange_rate()),
                 asyncio.ensure_future(upbit_binance_future_obj.health_check())]
        loop.run_until_complete(asyncio.wait(tasks))

    except Exception:
        exit(0)

