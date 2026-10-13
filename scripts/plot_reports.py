"""Optional standalone research figures from already-generated derived CSVs."""
from pathlib import Path
import csv
import datetime


def rows(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def create_plots(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(out)
    summary = rows(out/"summary.csv")
    names = list(dict.fromkeys(r["strategy"] for r in summary))
    holdout = [r for r in summary if r["case"] == "final_holdout"]
    utc = datetime.timezone.utc
    fig, ax = plt.subplots(figsize=(10, 5))
    for name in names:
        points = rows(out/f"full_exploratory_{name}_equity.csv")
        ax.plot([datetime.datetime.fromtimestamp(int(x["ts"]), utc) for x in points],
                [float(x["equity"]) for x in points], label=name.replace("_", " "))
    ax.axhline(100, color="#475569", ls="--", label="cash reference")
    ax.axvspan(datetime.datetime.fromtimestamp(int(holdout[0]["first_candle"]), utc),
               datetime.datetime.fromtimestamp(int(holdout[0]["last_candle"]), utc),
               alpha=.08, color="navy", label="holdout dates within full sample")
    ax.set(title="Historical simulation: USD 100 account / USD 20 entry", ylabel="Marked equity (USD)")
    ax.legend(fontsize=9)
    ax.grid(alpha=.2)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out/"equity_overview.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for k, case in enumerate(("final_holdout", "holdout_double_cost")):
        vals = [float(next(r["net_profit"] for r in summary if r["case"] == case and r["strategy"] == s)) for s in names]
        ax.bar([i + (.18 if k else -.18) for i in range(len(names))], vals, width=.36,
               label="Base costs" if k == 0 else "Doubled costs")
    ax.set_xticks(range(len(names)), [x.replace("_", " ") for x in names])
    ax.axhline(0, color="black", lw=.8)
    ax.set(ylabel="Modeled net profit (USD)", title="Final holdout and cost stress: no live trading")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out/"holdout_cost_stress.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    create_plots(Path(__file__).resolve().parents[1]/"reports/backtests")
