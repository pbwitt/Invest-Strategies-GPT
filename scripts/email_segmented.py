# scripts/email_segmented.py
import os
import re
import glob
import pandas as pd
from dotenv import load_dotenv

# Make the project root importable when running this file directly
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.fetcher import fetch_prices
from scripts.email_report import send_email

load_dotenv()


def load_positions():
    path = "reports/positions_latest.csv"
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


def load_trades():
    path = "reports/trades.csv"
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


def load_summary_text():
    path = "reports/daily_summary.txt"
    return open(path).read() if os.path.exists(path) else "(No daily_summary.txt found — run your daily step first.)"


def load_latest_analysis():
    files = sorted(glob.glob("reports/analysis_*.txt"))
    return open(files[-1]).read() if files else "(No custom analysis found — run scripts/ask_gpt.py to create one.)"


def load_watchlist():
    p = "data/watchlist.csv"
    if not os.path.exists(p):
        return pd.DataFrame(columns=["symbol", "note", "active"])
    df = pd.read_csv(p)
    if "active" in df.columns:
        # Only include active tickers
        df = df[df["active"].astype(str).str.lower().isin(["true", "1", "yes", "y"])]
    return df


def filter_positions(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    if df.empty or not filters:
        return df
    out = df.copy()

    st = filters.get("strategy_tag") or []
    ac = filters.get("account") or []
    sy = filters.get("symbols") or []

    if st:
        out = out[out["strategy_tag"].astype(str).isin(st)]
    if ac:
        out = out[out["account"].astype(str).isin(ac)]
    if sy:
        def match_symbol(s):
            s = str(s)
            for pat in sy:
                try:
                    if re.search(pat, s):
                        return True
                except re.error:
                    if s == pat:
                        return True
            return s in sy
        out = out[out["symbol"].apply(match_symbol)]

    return out


def watchlist_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["symbol", "price", "prev_close", "change", "change_pct", "note"])
    syms = df["symbol"].astype(str).tolist()
    prices = fetch_prices(syms)
    rows = []
    for s in syms:
        px = prices.get(s, {})
        price = px.get("price")
        prev = px.get("prev_close")
        chg = (price - prev) if (price is not None and prev is not None) else None
        chg_pct = (chg / prev * 100.0) if (chg is not None and prev not in (None, 0)) else None
        note = df.loc[df["symbol"] == s, "note"].iloc[0] if "note" in df.columns and (df["symbol"] == s).any() else ""
        rows.append({
            "symbol": s,
            "price": price,
            "prev_close": prev,
            "change": chg,
            "change_pct": chg_pct,
            "note": note
        })
    return pd.DataFrame(rows)


def fmt_table(df: pd.DataFrame, cols: list) -> str:
    if df.empty:
        return "(no rows)"
    out = df.copy()
    out = out[[c for c in cols if c in out.columns]]

    # Pretty formatting
    money_cols = [c for c in ["price", "prev_close", "change", "market_value", "today_pnl", "total_pnl"] if c in out.columns]
    for c in money_cols:
        out[c] = out[c].map(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
    if "change_pct" in out.columns:
        out["change_pct"] = out["change_pct"].map(lambda x: f"{x:.2f}%" if pd.notnull(x) else "")

    return out.to_string(index=False)


def build_body(group: dict,
               positions_df: pd.DataFrame,
               trades_df: pd.DataFrame,
               summary_text: str,
               watch_df: pd.DataFrame) -> str:
    parts = []
    includes = group.get("include", ["summary"])

    if "summary" in includes:
        parts.append("=== Daily Summary ===\n" + summary_text.strip())

    if "analysis" in includes:
        parts.append("\n=== Custom Analysis ===\n" + load_latest_analysis())

    if "trades_latest" in includes:
        tail = trades_df.tail(1)
        parts.append("\n=== Latest Signal ===\n" + (tail.to_string(index=False) if not tail.empty else "(no trades yet)"))

    if "positions" in includes:
        filt = filter_positions(positions_df, group.get("filters"))
        parts.append(
            "\n=== Positions (filtered) ===\n" +
            (fmt_table(
                filt,
                ["symbol", "shares", "price", "market_value", "today_pnl", "total_pnl", "strategy_tag", "account"]
            ) if not filt.empty else "(no matching positions)")
        )

    if "watchlist" in includes:
        snap = watchlist_snapshot(watch_df)
        parts.append(
            "\n=== Watchlist Movers ===\n" +
            fmt_table(snap, ["symbol", "price", "change", "change_pct", "note"])
        )

    return "\n\n".join(parts).strip() + "\n"


def main():
    # Load config
    import yaml
    cfg_path = "notify.yaml"
    if not os.path.exists(cfg_path):
        raise FileNotFoundError("notify.yaml not found in project root.")

    cfg = yaml.safe_load(open(cfg_path))

    # Load data
    positions_df = load_positions()
    trades_df = load_trades()
    summary_text = load_summary_text()
    watch_df = load_watchlist()

    # Send to each group
    for g in cfg.get("groups", []):
        body = build_body(g, positions_df, trades_df, summary_text, watch_df)
        attachments = g.get("attachments", [])
        # Set EMAIL_TO dynamically per group (so send_email can use it)
        os.environ["EMAIL_TO"] = ",".join(g.get("to", []))
        send_email(subject=g.get("subject", "Daily Update"), body=body, attachments=attachments)
        print(f"Sent: {g.get('name', '(unnamed group)')} -> {', '.join(g.get('to', []))}")


if __name__ == "__main__":
    main()
