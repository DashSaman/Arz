# Frozen slower-rule and later-window check

Research only. Source license: AGPL-3.0-or-later as in the prior isolated experiment; see `../upstream_benchmark/NOTICE.md`. No financial authority or network code is present in fresh_check.py.

Read `research/fresh_window_protocol_20261017.json` first. Install the existing exact package pins in an isolated venv only if not already available. Then, from repo root:

```sh
PYTHONPATH=experiments/fresh_window_check:experiments/crossmarket_repeatability:experiments/upstream_benchmark python3 -m unittest discover -s experiments/fresh_window_check -v
PYTHONPATH=experiments/fresh_window_check:experiments/crossmarket_repeatability:experiments/upstream_benchmark python3 experiments/fresh_window_check/fresh_check.py --old-data PATH_TO_OLD_NATIVE4H --new-data PATH_TO_NEW_NATIVE4H --output NEW_RESULT_DIRECTORY
```

Old input hashes come from `reports/crossmarket_20261016/data_provenance.json`. New input files are `<pair_id>.jsonl`, with manifest.json containing pair_id/sha256 entries. Exact request parameters and original hash values are in `reports/fresh_window_20261017/data_provenance.json`. Use only permitted source access and do not retry denials or overwrite old samples. Hashes are not a substitute for access to the matching data. No raw provider data are distributed here.

The fresh interval has only15days; old6/12/18month periods overlap previously seen data. Eight cbBTC18month cases fail the warmup gate. Results CSV retains all96case statuses, not only winners. Cash inactivity is not income. Costs are sensitivity assumptions, not complete real DEX expenses. No deployment, signing or persistent service.

فارسی: ابتدا پروتکل ثابت را بخوانید. کد روی داده محلی هم‌هش اجرا می‌شود و هیچ شبکه/کلید/معامله واقعی ندارد. داده قدیمی و تازه جدا هستند و مرز زمانی در پروتکل است. نتایج مثبت، منفی و ناقص همگی ثبت‌اند؛۱۵روز بی‌معاملگی سود محسوب نمی‌شود. هیچ مجوز مالی از این آزمایش نتیجه نمی‌شود.
