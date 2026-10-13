"""CLI commands are all research or simulated. There is no live command."""
import argparse
from dataclasses import replace
import hashlib,json,sys,time
from pathlib import Path
from .config import Config
from .data import read_csv,write_csv
from .strategies import Strategy,PARAMETERS
from .engine import run_backtest
from .connectors import fetch_bars
from .paper import paper_step,atomic_write,record_fault


def config_from_file(path):
    return Config.from_dict(json.loads(Path(path).read_text())) if path else Config()


def output_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    atomic_write(path,data)


def reject_path_collisions(paths):
    entries=[Path(p).resolve() for p in paths if p]
    for i,left in enumerate(entries):
        for right in entries[i+1:]:
            if left==right or (left.exists() and right.exists() and left.samefile(right)):
                raise ValueError("Configuration, input data, journal and output paths must be distinct")


def main(argv=None):
    parser=argparse.ArgumentParser(description="Arz research / simulation only; live DISABLED")
    sub=parser.add_subparsers(dest="command",required=True)
    for name in ("fetch","backtest","paper"):
        p=sub.add_parser(name);p.add_argument("--config")
        p.add_argument("--output",required=True)
        if name=="backtest":
            p.add_argument("--data",required=True);p.add_argument("--strategy",choices=PARAMETERS,required=True)
        elif name=="fetch":p.add_argument("--before",type=int);p.add_argument("--limit",type=int,default=1000)
        else:
            p.add_argument("--state",required=True);p.add_argument("--strategy",choices=PARAMETERS,default="trend")
            p.add_argument("--samples",type=int,default=1);p.add_argument("--sleep",type=float,default=20)
    args=parser.parse_args(argv)
    reject_path_collisions([args.config,args.output,getattr(args,"data",None),getattr(args,"state",None)])
    c=config_from_file(args.config)
    if args.command=="fetch":
        bars,meta,raw=fetch_bars(c,before=args.before,limit=args.limit)
        target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
        write_csv(target,bars)
        meta.update({"normalized_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"first_ts":bars[0].ts,"last_ts":bars[-1].ts,"interval_s":c.interval_s,"network":c.network,"pool":c.pool,"token":c.token,"config_hash":c.fingerprint(),"redistribution_status":"PENDING; raw data retained only in ignored local runtime for analysis"})
        target.with_suffix(".raw.json").write_bytes(raw)
        output_json(target.with_suffix(".provenance.json"),meta)
        print(json.dumps(meta))
    elif args.command=="backtest":
        bars=read_csv(args.data,c.interval_s,now=time.time())
        result=run_backtest(bars,c,Strategy(args.strategy));result["input_sha256"]=hashlib.sha256(Path(args.data).read_bytes()).hexdigest()
        output_json(args.output,result);print(json.dumps({"output":args.output,"strategy":args.strategy,"metrics":result["metrics"]}))
    else:
        if not 1<=args.samples<=20 or not 1<=args.sleep<=60:raise ValueError("Paper collection must be bounded: 1..20 samples, 1..60 seconds")
        c=replace(c,mode="paper")
        records=[]
        for i in range(args.samples):
            try:
                bars,meta,_=fetch_bars(c,limit=100)
                record=paper_step(args.state,bars,c,Strategy(args.strategy),now=meta["observed_at"])
                record["source"]=meta;records.append(record)
            except Exception as exc:
                # No retry can silently clear the recorded paper fault.
                record_fault(args.state,c,Strategy(args.strategy))
                records.append({"status":"HALTED_NETWORK_OR_DATA_ERROR","error_type":type(exc).__name__,"observed_at":time.time()})
                output_json(args.output,{"live_trading":"DISABLED","observations":records,"continuous_service":False})
                return 1
            output_json(args.output,{"live_trading":"DISABLED","observations":records,"continuous_service":False})
            print(json.dumps({"observation":i+1,"status":record["status"],"observed_at":record["observed_at"],"fills":record["result"]["metrics"]["fills"]}),flush=True)
            if record["fault"]:return 1
            if i+1<args.samples:time.sleep(args.sleep)
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"Arz halted: {type(exc).__name__}: {exc}",file=sys.stderr);raise SystemExit(2)
