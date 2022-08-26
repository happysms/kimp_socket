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
