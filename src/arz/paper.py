"""Bounded prospective paper journal, atomic storage and fail-closed restarts."""
from contextlib import contextmanager
from pathlib import Path
import hashlib,json,os,tempfile,time
from .data import validate_bars
from .engine import Engine


def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

@contextmanager
def locked(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    lock=path.with_suffix(path.suffix+".lock")
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as e:raise ValueError("Paper journal locked; concurrent writer or stale lock needs review") from e
    try:
        os.write(fd,str(os.getpid()).encode());os.close(fd);yield
    finally:lock.unlink(missing_ok=True)


def atomic_write(path,obj):
    raw=json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)
    temp=None
    try:
        with tempfile.NamedTemporaryFile("w",dir=path.parent,delete=False,encoding="utf-8") as f:
            temp=Path(f.name);f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp is not None and temp.exists():temp.unlink()


def paper_step(path,bars,config,strategy,now=None):
    if config.mode!="paper":raise ValueError("Paper command requires paper configuration")
    path=Path(path);now=time.time() if now is None else now
    validate_bars(bars,config.interval_s,now)
    with locked(path):
        if path.exists():
            if path.stat().st_size>20_000_000:raise ValueError("Journal size requires review")
            envelope=json.loads(path.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError("Invalid state JSON")))
            state=envelope["engine"]
            if envelope.get("state_sha256")!=digest(state):raise ValueError("Corrupt or modified journal")
            engine=Engine.restore(config,strategy,state)
            fault=envelope.get("fault");started=envelope["started_at"]
        else:
            engine=Engine(config,strategy);fault=None;started=now;envelope=None
        if fault:status="HALTED_REQUIRES_REVIEW"
        elif now-(bars[-1].ts+config.interval_s)>min(90,config.interval_s):
            status="HALTED_DATA_STALE";fault=status;engine.risk.halt_reason="data_stale"
        elif envelope is None:
            for bar in bars:engine.step(bar,trading=False)
            status="WARMED_NO_HISTORICAL_TRADES"
        else:
            previous=engine.history[-1].ts
            shared={b.ts:b for b in bars}
            if previous in shared and shared[previous]!=engine.history[-1]:raise ValueError("Historical source revision detected")
            new=[b for b in bars if b.ts>previous]
            if not new:status="NO_NEW_COMPLETED_BAR"
            elif len(new)!=1 or new[0].ts!=previous+config.interval_s:
                status="HALTED_MISSED_BARS";fault=status;engine.risk.halt_reason="missed_bars"
            else:
                # A paper observer cannot claim the bar's earlier open as its fill.
                engine.step(new[0],execution_price=new[0].close,observed_at=now)
                status="PROCESSED_PROSPECTIVE_BAR"
        state=engine.state()
        output={"version":1,"started_at":started,"observed_at":now,"status":status,"fault":fault,"engine":state,"state_sha256":digest(state)}
        atomic_write(path,output)
        return {"status":status,"observed_at":now,"source_last_close":bars[-1].ts+config.interval_s,"started_at":started,"fault":fault,"result":engine.result()}
