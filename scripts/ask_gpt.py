
# scripts/ask_gpt.py

"""
ask_gpt.py — Send a custom analysis prompt to OpenAI with optional portfolio context.

Usage examples:
  # Free-form question (no context)
  python scripts/ask_gpt.py --prompt "What risks do you see in semis this quarter?"

  # Include latest positions + watchlist as context
  python scripts/ask_gpt.py --prompt-file prompts/ai_rotation.md --with-positions --with-watchlist --model gpt-5

  # Save output and optionally email it
  python scripts/ask_gpt.py --prompt "Summarize portfolio risk" --with-positions --email
"""
import os, argparse, datetime as dt, pandas as pd, json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception:
        return ""

def load_positions():
    p = "reports/positions_latest.csv"
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

def load_watchlist():
    p = "data/watchlist.csv"
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame(columns=["symbol","note","active"])

def build_context(include_positions: bool, include_watchlist: bool) -> dict:
    ctx = {}
    if include_positions:
        df = load_positions()
        ctx["positions"] = df.to_dict(orient="records")
    if include_watchlist:
        wl = load_watchlist()
        ctx["watchlist"] = wl.to_dict(orient="records")
    return ctx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", type=str, help="Inline prompt string")
    ap.add_argument("--prompt-file", type=str, help="Path to a prompt file (markdown or text)")
    ap.add_argument("--with-positions", action="store_true", help="Attach positions_latest.csv as JSON context")
    ap.add_argument("--with-watchlist", action="store_true", help="Attach data/watchlist.csv as JSON context")
    ap.add_argument("--model", type=str, default=os.environ.get("OPENAI_MODEL","gpt-5-mini"))
    ap.add_argument("--email", action="store_true", help="Email the output after saving")
    args = ap.parse_args()

    if not args.prompt and not args.prompt_file:
        print("Provide --prompt or --prompt-file")
        return

    user_prompt = args.prompt or read_file(args.prompt_file)
    context = build_context(args.with_positions, args.with_watchlist)
    context_str = json.dumps(context) if context else ""

    # Construct final prompt
    final_prompt = f"""You are a rigorous investment analyst.
Use the user's instruction and the JSON context (if provided) to produce a concise, bulletproof analysis with clear assumptions.
Always call out data gaps and risks.

User prompt:
{user_prompt}

JSON context:
{context_str}
"""

    client = OpenAI()
    resp = client.responses.create(
        model=args.model,
        input=[{"role":"user","content":final_prompt}],
    )
    text = resp.output_text

    # Save analysis
    os.makedirs("reports", exist_ok=True)
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_path = f"reports/analysis_{ts}.txt"
    with open(out_path, "w") as f:
        f.write(text)
    print(f"Saved analysis: {out_path}\n")
    print(text)

    if args.email:
        try:
            from scripts.email_report import send_email
            send_email(subject="Custom Analysis", body=text)
            print("Emailed analysis.")
        except Exception as e:
            print(f"Email failed: {e}")

if __name__ == "__main__":
    main()
