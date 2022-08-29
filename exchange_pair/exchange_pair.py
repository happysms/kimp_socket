import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import env
import json
import asyncio
from aiohttp import ClientSession
from alert.bot import TelegramBot
from utils import cal_avg_price


class ExchangePair:
    available_coin_list = []
    exchange_rate = 0
    won_orderbook_list = []   # 한국(원화 거래) 거래소
    dollar_orderbook_list = []   # 외국(달러 거래) 거래소
    kimp_status_dict = {}

    def __init__(self, won_exchange, dollar_exchange):
        self.won_exchange = won_exchange
        self.dollar_exchange = dollar_exchange


    async def set_available_coin_list(self):
        upbit_items = await Upbit.get_subscribe_items()
        upbit_items = list(map(lambda x: x.replace("KRW-", ""), upbit_items))
        binance_future_items = await self.dollar_exchange.get_subscribe_items()

        for upbit_item in upbit_items:
            for binance_future_item in binance_future_items:
                if upbit_item == binance_future_item:
                    self.available_coin_list.append(upbit_item)
                    self.kimp_status_dict[upbit_item] = {"time_diff1": None, "time_diff2": None, "kimp": None, "is_active": False}
                    continue

        self.dollar_exchange.available_coin_list = self.available_coin_list
        self.won_exchange.available_coin_list = self.available_coin_list
