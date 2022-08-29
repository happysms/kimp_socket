import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import env
import json
from exchange.binance import BinanceFuture
from exchange.upbit import Upbit
import asyncio
from aiohttp import ClientSession
from alert.bot import TelegramBot
from utils import cal_avg_price


class UpbitBinanceFuture:
    available_coin_list = []
    exchange_rate = 0
    upbit_orderbook_list = []
    binance_future_orderbook_list = []
    kimp_status_dict = {}

    # {"BTC": {"time_diff": 1.4, "kimp": 4.2, "is_active": False}}
    # action: 4퍼 이상 상승 시 is_updated 를 True 로 바꿈 -> 다시 4퍼 아래로 내려갈 때 is_updated 를 False 로 변경

    def __init__(self, upbit: Upbit, binance_future: BinanceFuture):
        self.upbit = upbit
        self.binance_future = binance_future
        self.telegram_bot = TelegramBot(chat_id=env.UPBIT_CHAT_ID)

    def alert_info(self, coin, kimp, time_diff1, time_diff2):
        coin_info = self.kimp_status_dict[coin]
        if coin_info["is_active"]:
            if 0 < kimp < 4:
                self.kimp_status_dict[coin]["is_active"] = False
                self.kimp_status_dict[coin]["kimp"] = kimp
                self.kimp_status_dict[coin]["time_diff1"] = time_diff1
                self.kimp_status_dict[coin]["time_diff2"] = time_diff2
        else:
            if kimp <= 0 or kimp >= 4:
                self.kimp_status_dict[coin]["is_active"] = True
                self.kimp_status_dict[coin]["kimp"] = kimp
                self.kimp_status_dict[coin]["time_diff1"] = time_diff1
                self.kimp_status_dict[coin]["time_diff2"] = time_diff2
                log = f"종목: {coin}\t  김프: {kimp:.2f}%\t  환율:{self.exchange_rate}\t  time_delay: ({time_diff1:.2f},{time_diff2:.2f})"
                self.telegram_bot.log(log)
                self.telegram_bot.send_logs()

    async def set_available_coin_list(self):
        upbit_items = await Upbit.get_subscribe_items()
        upbit_items = list(map(lambda x: x.replace("KRW-", ""), upbit_items))
        binance_future_items = await self.binance_future.get_subscribe_items()

        for upbit_item in upbit_items:
            for binance_future_item in binance_future_items:
                if upbit_item == binance_future_item:
                    self.available_coin_list.append(upbit_item)
                    self.kimp_status_dict[upbit_item] = {"time_diff1": None, "time_diff2": None, "kimp": None, "is_active": False}
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
                print(self.kimp_status_dict)
                for trade_size in [1000000]:
                    print("\n\n\n\n\ntrading size(won): ", format(trade_size, ','))
                    cur_time = time.time()
                    for binance_key in self.binance_future.orderbook_dict.keys():
                        if self.binance_future.orderbook_dict.get(binance_key) and self.upbit.orderbook_dict.get(binance_key):
                            binance_orderbook = self.binance_future.orderbook_dict[binance_key]
                            upbit_orderbook = self.upbit.orderbook_dict[binance_key]
                            binance_time_diff = cur_time - binance_orderbook['time']
                            upbit_time_diff = cur_time - upbit_orderbook['time']

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
                                self.alert_info(binance_key, upbit_premium, binance_time_diff, upbit_time_diff)
                                pass
                            elif 4 < binance_premium < 10:
                                self.alert_info(binance_key, binance_premium, binance_time_diff, upbit_time_diff)
                await asyncio.sleep(2)
            except Exception as e:
                print(e)
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

