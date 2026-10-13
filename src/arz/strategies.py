"""Three pre-registered, fixed-parameter, long-only hypotheses. No fitting."""
import statistics

PARAMETERS = {
    "trend": {"fast":12,"slow":48},
    "momentum": {"lookback":12,"entry_return":0.02,"exit_return":0.0},
    "mean_reversion": {"window":24,"entry_z":-1.5,"exit_z":0.0},
}

class Strategy:
    def __init__(self,name):
        if name not in PARAMETERS:raise ValueError("Unknown pre-registered strategy")
        self.name=name

    def signal(self,history,holding):
        c=[b.close for b in history]
        p=PARAMETERS[self.name]
        if self.name=="trend":
            if len(c)<p["slow"]:return False
            return statistics.fmean(c[-p["fast"]:])>statistics.fmean(c[-p["slow"]:])
        if self.name=="momentum":
            if len(c)<=p["lookback"]:return False
            ret=c[-1]/c[-1-p["lookback"]]-1
            return ret> (p["exit_return"] if holding else p["entry_return"])
        if len(c)<p["window"]:return False
        window=c[-p["window"]:];sd=statistics.pstdev(window)
        if sd<=0:return False
        z=(c[-1]-statistics.fmean(window))/sd
        return z<p["exit_z"] if holding else z<=p["entry_z"]
