import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import env
import json
from exchange.binance import BinanceFuture
from exchange.korbit import Korbit
import asyncio
from aiohttp import ClientSession
from alert.bot import TelegramBot
from utils import cal_avg_price


class KorbitBinanceFuture:
    available_coin_list = []
    exchange_rate = 0
    upbit_orderbook_list = []
    binance_future_orderbook_list = []

    def __init__(self, korbit: Korbit, binance_future: BinanceFuture):
        self.korbit = korbit
        self.binance_future = binance_future
        self.telegram_bot = TelegramBot(chat_id=env.KORBIT_CHAT_ID)

    async def set_available_coin_list(self):
        korbit_items = await Korbit.get_subscribe_items()
        korbit_items = list(map(lambda x: x.replace("KRW-", ""), korbit_items))
        binance_future_items = await self.binance_future.get_subscribe_items()

        for korbit_item in korbit_items:
            for binance_future_item in binance_future_items:
                if korbit_item == binance_future_item:
                    self.available_coin_list.append(korbit_item)
                    continue

        self.binance_future.available_coin_list = self.available_coin_list
        self.korbit.available_coin_list = self.available_coin_list

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
                for trade_size in [100000, 1000000, 10000000]:
                    print("\n\n\n\n\ntrading size(won): ", format(trade_size, ','))
                    for binance_key in self.binance_future.orderbook_dict.keys():
                        if self.binance_future.orderbook_dict.get(binance_key) and self.korbit.orderbook_dict.get(binance_key):

                            binance_orderbook = self.binance_future.orderbook_dict[binance_key]
                            korbit_orderbook = self.korbit.orderbook_dict[binance_key]
                            korbit_long, korbit_short = cal_avg_price(korbit_orderbook, trade_size)
                            if korbit_long > 1e10 or korbit_short < -1e10:
                                continue

                            korbit_long = korbit_long / self.exchange_rate * (1 + Korbit.market_fee)
                            korbit_short = korbit_short / self.exchange_rate * (1 - Korbit.market_fee)
                            binance_long, binance_short = cal_avg_price(binance_orderbook, trade_size / self.exchange_rate)
                            if binance_long > 1e10 or binance_short < -1e10:
                                continue

                            binance_long = binance_long * (1 + BinanceFuture.market_fee)
                            binance_short = binance_short * (1 - BinanceFuture.market_fee)
                            korbit_premium = round((binance_short / korbit_long - 1) * 100, 3)
                            binance_premium = round((korbit_short / binance_long - 1) * 100, 3)
                            print("korbit_long - binance_short: ", binance_key, korbit_premium)
                            print("korbit_short - binance_long: ", binance_key, binance_premium)

                            if 0 < korbit_premium < 10:
                                self.telegram_bot.log(f"{binance_key} 거래액: {format(trade_size, ',')}won\t 역김프: {korbit_premium}%")
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
        korbit = Korbit()
        korbit_binance_future_obj = KorbitBinanceFuture(korbit=korbit, binance_future=binance_future)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(korbit_binance_future_obj.set_available_coin_list())

        tasks = [asyncio.ensure_future(korbit.socket_order_book(korbit.process_buffer)),
                 asyncio.ensure_future(binance_future.socket_order_book(binance_future.process_buffer)),
                 asyncio.ensure_future(korbit_binance_future_obj.cal_kimp()),
                 asyncio.ensure_future(korbit_binance_future_obj.update_exchange_rate()),
                 asyncio.ensure_future(korbit_binance_future_obj.health_check())
                 ]
        loop.run_until_complete(asyncio.wait(tasks))

    except Exception:
        exit(0)

