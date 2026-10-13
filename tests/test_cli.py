import unittest,subprocess,sys,tempfile,json
from pathlib import Path

class CLITests(unittest.TestCase):
    def test_help_and_live_rejection(self):
        help_run=subprocess.run([sys.executable,"-m","arz","--help"],capture_output=True,text=True)
        self.assertEqual(help_run.returncode,0,help_run.stderr)
        live=subprocess.run([sys.executable,"-m","arz","live"],capture_output=True,text=True)
        self.assertNotEqual(live.returncode,0)

    def test_backtest_cli_with_known_flat_synthetic_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=root/"synthetic.csv";out=root/"result.json"
            data.write_text("ts,open,high,low,close,volume\n"+"".join(f"{i*14400},10,10,10,10,100000\n" for i in range(60)))
            run=subprocess.run([sys.executable,"-m","arz","backtest","--data",str(data),"--strategy","trend","--output",str(out)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            result=json.loads(out.read_text());self.assertEqual(result["live_trading"],"DISABLED")
            self.assertEqual(result["metrics"]["ending_equity"],100)

if __name__=="__main__":unittest.main()
