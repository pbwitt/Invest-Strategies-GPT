import pandas as pd
import yfinance as yf
from typing import Dict, List


def fetch_prices(symbols: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Fetch recent price and previous close for a list of symbols.
    Returns a dict like:
      {
        "QQQ": {"price": 123.45, "prev_close": 120.67},
        "TQQQ": {"price": 45.67, "prev_close": 44.12}
      }
    """
    uniq = sorted(set([s.strip() for s in symbols if s and isinstance(s, str)]))
    if not uniq:
        return {}

    # Try fetching all at once
    data = yf.download(
        " ".join(uniq),
        period="5d",
        interval="1d",
        auto_adjust=False,
        progress=False,
        group_by="ticker",
    )

    results = {}
    for sym in uniq:
        try:
            # Handle multi-index vs single-index DataFrames
            df = data[sym] if isinstance(data.columns, pd.MultiIndex) else data
            df = df.dropna()
            if df.empty:
                continue

            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else None

            results[sym] = {
                "price": float(last["Close"]),
                "prev_close": float(prev["Close"]) if prev is not None else float(last["Close"]),
            }

        except Exception:
            # Fallback: download symbol separately
            try:
                df = yf.download(
                    sym,
                    period="5d",
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                ).dropna()
                if not df.empty:
                    last = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) >= 2 else None
                    results[sym] = {
                        "price": float(last["Close"]),
                        "prev_close": float(prev["Close"]) if prev is not None else float(last["Close"]),
                    }
            except Exception:
                pass

    return results
