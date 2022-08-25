import asyncio
import ccxt.async_support as ccxt


def adapter_coinone_orderbook(orderbook):
    orderbook_dict = dict()
    orderbook_dict['coin'] = orderbook['symbol'].replace("/KRW", "")
    orderbook_dict['time'] = orderbook['timestamp']
    orderbook_dict['bids'] = list(map(lambda x: [float(x[0]), float(x[1]) * float(x[0])], orderbook['bids']))
    orderbook_dict['asks'] = list(map(lambda x: [float(x[0]), float(x[1]) * float(x[0])], orderbook['asks']))
    return orderbook_dict


class Coinone:
    exchange_name = "coinone"
    orderbook_dict = dict()
    available_coin_list = []
    market_fee = 0.002
    limit_fee = 0.002

    def __init__(self):
        self.coinone_obj = ccxt.coinone()

    async def update_orderbook(self):
        while True:
            for coin in self.available_coin_list:
                ticker = f"{coin}/KRW"
                orderbook = await self.get_orderbook(ticker=ticker)
                orderbook_dict = adapter_coinone_orderbook(orderbook)
                self.orderbook_dict[orderbook_dict['coin']] = orderbook_dict
            await asyncio.sleep(0.1)

    async def get_orderbook(self, ticker):
        orderbook = await self.coinone_obj.fetch_order_book(symbol=ticker, limit=10)
        return orderbook

    async def get_subscribe_items(self):
        markets = await self.coinone_obj.load_markets()
        coin_list = list(map(lambda x: x.replace("/KRW", ""), markets.keys()))
        return coin_list


if "__main__" == __name__:
    coinone = Coinone()
    loop = asyncio.get_event_loop()
    coinone.available_coin_list = loop.run_until_complete(coinone.get_subscribe_items())
    loop.run_until_complete(coinone.update_orderbook())
