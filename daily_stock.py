import datetime
from dataclasses import dataclass
from typing import Optional

import yfinance as yf

@dataclass
class DailyStock:
    symbol: str
    close: float
    date: datetime.date


def fetch_latest_close(symbol: str, date: Optional[datetime.date] = None) -> DailyStock:
    """Fetch the latest closing price for the given stock symbol."""
    if date is None:
        date = datetime.date.today()
    data = yf.download(symbol, period="5d", interval="1d")
    if data.empty:
        raise ValueError(f"No data returned for symbol {symbol}")
    last_row = data.tail(1).iloc[0]
    close_price = float(last_row["Close"])
    return DailyStock(symbol=symbol, close=close_price, date=last_row.name.date())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch daily closing stock price.")
    parser.add_argument("symbol", help="Ticker symbol, e.g. AAPL")
    args = parser.parse_args()
    stock = fetch_latest_close(args.symbol)
    print(f"{stock.symbol} closing price on {stock.date}: ${stock.close:.2f}")
