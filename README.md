

## Multiple recipients & segmented emails
- **Simple multi-send:** put a comma-separated list in `.env`
  ```
  EMAIL_TO=paul@example.com, partner@example.com
  EMAIL_CC=ally@example.com
  EMAIL_BCC=archive@example.com
  ```
  Then run `python scripts/email_report.py`.

- **Segmented emails (different content per user):**
  Edit `notify.yaml` and run:
  ```
  python scripts/email_segmented.py
  ```
  Each group chooses sections: `summary` (daily GPT note) and/or `trades_latest` (latest strategy order intent).


## Multi-user emails & filters

- Edit `notify.yaml` to define groups, sections, and filters:
  - `include`: any of `summary`, `trades_latest`, `positions`, `watchlist`
  - `filters`: `strategy_tag`, `account`, `symbols` (regex or exact values)
- Run segmented sender:
```
python scripts/email_segmented.py
```
- Maintain a simple watchlist in `data/watchlist.csv` (columns: symbol, note, active).

### Quick examples
- Add a ticker to watchlist: open `data/watchlist.csv`, add a row `NVDA, AI leader, TRUE`.
- Only send AI/Semis to a teammate: set `filters.strategy_tag: ["AI-Semis"]` in their group.
