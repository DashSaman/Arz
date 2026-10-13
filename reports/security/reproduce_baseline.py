"""Independent, offline adversarial review repros; writes only beside this file."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from dataclasses import replace
from unittest.mock import patch

from arz.config import Config
from arz.data import Bar
from arz.engine import Engine, run_backtest
from arz.paper import paper_step, digest
from arz.strategies import Strategy, PARAMETERS
from arz.__main__ import main
from arz.connectors import fetch_bars

HERE = Path(__file__).resolve().parent
REPO = HERE.parent / "Arz"


class Sequence:
    name = "literal_review_fixture"

    def __init__(self, signals=None):
        self.signals = signals or {}

    def signal(self, history, holding):
        return self.signals.get(len(history), False)


def bar(ts, price=10):
    return Bar(ts, price, price, price, price, 100000)


def config(**kw):
    return Config(interval_s=60, fee_bps=0, slippage_bps=0, gas_usd=0, **kw)


def failed_exit_trade_pnl():
    c = replace(config(), gas_usd=0.1)
    r = run_backtest([bar(0), bar(60), bar(120, 10.125), bar(180, 10.125)],
                     c, Sequence({1: True}), fail_on={120})
    return {"account_net_profit": r["metrics"]["net_profit"],
            "realized_pnl": r["metrics"]["realized_pnl"],
            "closed_trade_net_pnl": r["closed_trades"][0]["net_pnl"],
            "win_rate": r["metrics"]["win_rate"],
            "failed_attempts": r["metrics"]["failed_attempts"],
            "total_gas": r["portfolio"]["total_gas"]}


def observed_day_caps():
    c = config(mode="paper", max_trades_day=1)
    bs = [bar(86280)]
    with tempfile.TemporaryDirectory(dir=HERE) as d:
        p = Path(d) / "state.json"
        paper_step(p, bs, c, Sequence({1: True}), now=86341)
        bs.append(bar(86340))
        paper_step(p, bs, c, Sequence({1: True}), now=86401)
        risk_after_first = json.loads(p.read_text())["engine"]["risk"]
        bs.append(bar(86400))
        r = paper_step(p, bs, c, Sequence({1: True}), now=86461)
        return {"max_trades_day": c.max_trades_day,
                "risk_after_first_fill": risk_after_first,
                "fills": [{k: f[k] for k in ("ts", "side", "observed_at")}
                          for f in r["result"]["fills"]],
                "fills_on_observed_UTC_day_1": sum(
                    int(f["observed_at"] // 86400 == 1) for f in r["result"]["fills"])}


def invalid_restore():
    c = config(mode="paper")
    e = Engine(c, Strategy("trend"))
    e.step(bar(0), trading=False)
    cases = {}
    for name, mutation in (
            ("unfunded_cash", lambda s: s["portfolio"].update(cash=101)),
            ("negative_risk_counters", lambda s: s["risk"].update(count=-100, fees=-100)),
            ("string_pending_false", lambda s: s.update(pending="false")),
            ("boolean_state_version", lambda s: s.update(version=True))):
        s = copy.deepcopy(e.state())
        mutation(s)
        try:
            restored = Engine.restore(c, Strategy("trend"), s)
            restored.step(bar(60), execution_price=10, observed_at=121)
            cases[name] = {"accepted": True, "cash": restored.portfolio.cash,
                           "units": restored.portfolio.units,
                           "fills": len(restored.fills), "risk": restored.risk.snapshot()}
        except Exception as exc:
            cases[name] = {"accepted": False, "error": type(exc).__name__ + ": " + str(exc)}
    return cases


def older_source_revision():
    c = config(mode="paper")
    bs = [bar(0), bar(60), bar(120)]
    with tempfile.TemporaryDirectory(dir=HERE) as d:
        p = Path(d) / "state.json"
        paper_step(p, bs, c, Sequence(), now=181)
        revised = [bar(0, 11), bs[1], bs[2], bar(180)]
        r = paper_step(p, revised, c, Sequence(), now=241)
        return {"status": r["status"], "fault": r["fault"],
                "incoming_first_close": revised[0].close,
                "journal_first_close": json.loads(p.read_text())["engine"]["history"][0]["close"]}


def halted_valuation():
    c = config(mode="paper")
    bs = [bar(0)]
    with tempfile.TemporaryDirectory(dir=HERE) as d:
        p = Path(d) / "state.json"
        paper_step(p, bs, c, Sequence({1: True, 2: True}), now=61)
        bs.append(bar(60))
        paper_step(p, bs, c, Sequence({1: True, 2: True}), now=121)
        paper_step(p, bs, c, Sequence({1: True, 2: True}), now=181)
        bs.append(bar(120, 1))
        r = paper_step(p, bs, c, Sequence({1: True, 2: True}), now=181)
        pstate = r["result"]["portfolio"]
        return {"status": r["status"], "source_last_close": r["source_last_close"],
                "reported_ending_equity": r["result"]["metrics"]["ending_equity"],
                "actual_mark_at_current_valid_close": pstate["cash"] + pstate["units"] * bs[-1].close,
                "units": pstate["units"],
                "last_recorded_equity_ts": r["result"]["equity_curve"][-1]["ts"]}


def malformed_data_fault_not_sticky():
    c = config(mode="paper")
    bs = [bar(0)]
    with tempfile.TemporaryDirectory(dir=HERE) as d:
        p = Path(d) / "state.json"
        paper_step(p, bs, c, Sequence({1: True}), now=61)
        try:
            paper_step(p, [bs[0], bar(60, float("nan"))], c, Sequence({1: True}), now=121)
        except ValueError as exc:
            error = str(exc)
        r = paper_step(p, bs + [bar(60)], c, Sequence({1: True}), now=121)
        return {"initial_error": error, "resumed_status": r["status"],
                "resumed_fault": r["fault"], "fills_after_fault": r["result"]["metrics"]["fills"]}


def changed_strategy_restores():
    c = config(mode="paper")
    e = Engine(c, Strategy("trend"))
    for i in range(60):
        e.step(bar(i * 60, 10 + i / 100), trading=False)
    old = copy.deepcopy(PARAMETERS["trend"])
    s = e.state()
    try:
        PARAMETERS["trend"]["fast"] = 2
        restored = Engine.restore(c, Strategy("trend"), s)
        return {"accepted": True, "before": old, "after": PARAMETERS["trend"].copy(),
                "stored_identity_fields": [k for k in s if "version" in k or "hash" in k or "strategy" in k],
                "restored_strategy": restored.strategy.name}
    finally:
        PARAMETERS["trend"] = old


def cli_state_output_collision():
    c = config(mode="paper")
    with tempfile.TemporaryDirectory(dir=HERE) as d:
        p = Path(d) / "state.json"
        cfg = Path(d) / "config.json"
        from dataclasses import asdict
        cfg.write_text(json.dumps(asdict(c)))
        with patch("arz.__main__.fetch_bars", return_value=([bar(0)], {"observed_at": 61}, b"{}")):
            code = main(["paper", "--config", str(cfg), "--state", str(p), "--output", str(p)])
        saved = json.loads(p.read_text())
        return {"return_code": code, "saved_keys": sorted(saved),
                "valid_engine_journal_retained": "engine" in saved}


def four_hour_valid_feed_halted():
    c = replace(config(mode="paper"), interval_s=14400)
    with tempfile.TemporaryDirectory(dir=HERE) as d:
        p = Path(d) / "state.json"
        a = paper_step(p, [bar(0)], c, Sequence(), now=14401)
        b = paper_step(p, [bar(0)], c, Sequence(), now=14500)
        return {"first": a["status"], "next": b["status"],
                "seconds_since_last_close": 100, "next_bar_close": 28800,
                "observation_time": 14500}


def historical_completion_boundaries():
    c = config()
    payload = {
        "data": {"attributes": {"ohlcv_list": [
            [i, 10, 10, 10, 10, 100000] for i in (0, 60, 120)]}},
        "meta": {"base": {"address": c.token},
                 "quote": {"address": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"}}}
    bars, _, _ = fetch_bars(c, before=120, now=180,
                            transport=lambda url: (payload, b"{}"))
    future = [bar(4102444800 + i * 60) for i in range(60)]
    result = run_backtest(future, c, Strategy("trend"))
    return {"requested_as_of": 120, "returned_starts": [b.ts for b in bars],
            "last_returned_completion": bars[-1].ts + c.interval_s,
            "year_2100_backtest_accepted": result["metrics"]["ending_equity"] == 100}


def historical_mode_mislabeled():
    c = config(mode="paper")
    result = run_backtest([bar(i * 60) for i in range(60)], c, Strategy("trend"))
    return {"historical_backtest_mode": result["mode"]}


if __name__ == "__main__":
    funcs = [failed_exit_trade_pnl, observed_day_caps, invalid_restore, older_source_revision,
             halted_valuation, malformed_data_fault_not_sticky, changed_strategy_restores,
             cli_state_output_collision, four_hour_valid_feed_halted,
             historical_completion_boundaries, historical_mode_mislabeled]
    out = {"source_hashes": {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted((REPO / "src" / "arz").glob("*.py"))}}
    for func in funcs:
        try:
            out[func.__name__] = func()
        except Exception as exc:
            out[func.__name__] = {"repro_error": type(exc).__name__ + ": " + str(exc)}
    (HERE / "repro_results.json").write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True, allow_nan=False))
