from api.exchange.upbit_exchange import Upbit
from api.exchange.binance_future_excahnge import Binance


class Service:
    def __init__(self, upbit: Upbit, binance: Binance, repository):
        self.upbit = upbit
        self.binance = binance

    def execute(self):
        pass


