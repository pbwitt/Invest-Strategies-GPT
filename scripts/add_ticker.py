
# scripts/add_ticker.py
import sys, pandas as pd, os

WATCHLIST_PATH = "data/watchlist.csv"

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/add_ticker.py SYMBOL "note about this stock" [active]")
        sys.exit(1)
    symbol = sys.argv[1].upper()
    note = sys.argv[2]
    active = True
    if len(sys.argv) >= 4:
        val = sys.argv[3].strip().lower()
        active = val in ("1","true","yes","y")
    if os.path.exists(WATCHLIST_PATH):
        df = pd.read_csv(WATCHLIST_PATH)
    else:
        df = pd.DataFrame(columns=["symbol","note","active"])
    if symbol in df["symbol"].values:
        df.loc[df["symbol"]==symbol, ["note","active"]] = [note, active]
        print(f"Updated {symbol} in watchlist.")
    else:
        df.loc[len(df)] = [symbol, note, active]
        print(f"Added {symbol} to watchlist.")
    df.to_csv(WATCHLIST_PATH, index=False)

if __name__ == "__main__":
    main()
