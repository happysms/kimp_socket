import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from exchange_pair_object.exchange_pair import ExchangePair
import env
from exchange.binance import BinanceFuture
from exchange.korbit import Korbit
import asyncio
from alert.bot import TelegramBot


class KorbitBinanceFuture(ExchangePair):
    def __init__(self, korbit: Korbit, binance_future: BinanceFuture):
        super().__init__(korbit, binance_future)
        self.telegram_bot = TelegramBot(chat_id=env.UPBIT_CHAT_ID)
        self.won_exchange_fee = korbit.market_fee
        self.dollar_exchange_fee = binance_future.market_fee

    async def health_check(self):
        while True:
            self.telegram_bot.log("health_check")
            loop.run_in_executor(None, self.telegram_bot.send_logs)
            await asyncio.sleep(10800)  # 3 hour

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


if "__main__" == __name__:
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
