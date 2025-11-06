"""consdata sample routines"""

import random
import string
import itertools

import pandas as pd


def ticker_generator(length=3):
    alpha = string.ascii_uppercase
    memory = set()
    while True:
        ticker = "".join(random.choice(alpha) for i in range(length))
        if ticker not in memory:
            memory.add(ticker)
            yield ticker


def sample_tickers(count=10, *, ticker_length=3):
    """sample tickers"""
    tickers = ticker_generator(ticker_length)

    return list(itertools.islice(tickers, count))


def sample_portfolio(count=500, **kwargs):
    """sample portfolio"""

    SUFFIXES = "Co. Ltd. Inc. Intl. Tech Researh Lab Global Power".split()
    EXCHANGES = "ALPHA BRAVO CHARLIE DELTA".split()

    tickers = ticker_generator()

    records = []
    for i in range(count):
        record = dict(kwargs)
        ticker = next(tickers)

        description = ticker + " " + random.choice(SUFFIXES)
        exchange = random.choice(EXCHANGES)

        tick = random.choice((1, 10, 25, 50, 100)) / 100
        price = random.randint(100, 5000) * tick
        shares = random.randint(10, 50) * int(100 / tick)

        record["ticker"] = ticker
        record["description"] = description
        record["exchange"] = exchange
        record["shares"] = shares
        record["price"] = price

        records.append(record)

    result = pd.DataFrame.from_records(records, index="ticker")

    return result
