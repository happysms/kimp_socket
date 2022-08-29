import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import json
import asyncio
from aiohttp import ClientSession
from utils import cal_avg_price


class ExchangePair:
    available_coin_list = []
    exchange_rate = 0
    won_orderbook_list = []   # 한국(원화 거래) 거래소
    dollar_orderbook_list = []   # 외국(달러 거래) 거래소
    kimp_status_dict = {}
    won_exchange_fee = 0
    dollar_exchange_fee = 0

    def __init__(self, won_exchange, dollar_exchange):
        self.won_exchange = won_exchange
        self.dollar_exchange = dollar_exchange

    async def set_available_coin_list(self):
        won_exchange_items = await self.won_exchange.get_subscribe_items()
        won_exchange_items = list(map(lambda x: x.replace("KRW-", ""), won_exchange_items))
        dollar_exchange_items = await self.dollar_exchange.get_subscribe_items()

        for won_exchange_item in won_exchange_items:
            for dollar_exchange_item in dollar_exchange_items:
                if won_exchange_item == dollar_exchange_item:
                    self.available_coin_list.append(won_exchange_item)
                    self.kimp_status_dict[won_exchange_item] = {"time_diff1": None, "time_diff2": None, "kimp": None, "is_active": False}
                    continue

        self.dollar_exchange.available_coin_list = self.available_coin_list
        self.won_exchange.available_coin_list = self.available_coin_list

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
                for trade_size in [1000000]:
                    print("\n\n\n\n\ntrading size(won): ", format(trade_size, ','))
                    cur_time = time.time()
                    for dollar_key in self.dollar_exchange.orderbook_dict.keys():
                        if self.dollar_exchange.orderbook_dict.get(dollar_key) and self.won_exchange.orderbook_dict.get(dollar_key):
                            dollar_orderbook = self.dollar_exchange.orderbook_dict[dollar_key]
                            won_orderbook = self.won_exchange.orderbook_dict[dollar_key]
                            dollar_time_diff = cur_time - dollar_orderbook['time']
                            one_time_diff = cur_time - won_orderbook['time']

                            won_long, won_short = cal_avg_price(won_orderbook, trade_size)
                            if won_long > 1e10 or won_short < -1e10:
                                continue

                            won_long = won_long / self.exchange_rate * (1 + self.won_exchange_fee)
                            won_short = won_short / self.exchange_rate * (1 - self.won_exchange_fee)
                            dollar_long, dollar_short = cal_avg_price(dollar_orderbook, trade_size / self.exchange_rate)
                            if dollar_long > 1e10 or dollar_short < -1e10:
                                continue

                            dollar_long = dollar_long * (1 + self.dollar_exchange_fee)
                            dollar_short = dollar_short * (1 - self.dollar_exchange_fee)
                            won_premium = round((dollar_short / won_long - 1) * 100, 3)
                            dollar_premium = round((won_short / dollar_long - 1) * 100, 3)
                            print("won_long - dollar_short: ", dollar_key, won_premium)
                            print("won_short - dollar_long: ", dollar_key, dollar_premium)

                            if 0 < won_premium < 10:
                                self.alert_info(dollar_key, won_premium, dollar_time_diff, one_time_diff)

                            elif 4 < dollar_premium < 10:
                                self.alert_info(dollar_key, dollar_premium, dollar_time_diff, one_time_diff)

                await asyncio.sleep(2)
            except Exception as e:
                print(e)
                exit(0)

    def alert_info(self, coin, kimp, time_diff1, time_diff2):
        raise NotImplementedError
