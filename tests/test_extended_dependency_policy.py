"""Synthetic dependency-boundary tests; this is not a vulnerability audit."""
import importlib.util
from pathlib import Path
import unittest

class DependencyPolicy(unittest.TestCase):
    def load(self):
        p=Path(__file__).resolve().parents[1]/'scripts/extended_dependency_policy.py'
        spec=importlib.util.spec_from_file_location('arz_dep_policy',p)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        return m.classify_imports
    def test_pinned_reader_allowed_only_in_its_adapter(self):
        self.assertEqual(self.load()({'pyarrow':{'src/arz_extended/sources.py'}},['pyarrow==21.0.0']),[])
    def test_reader_in_another_module_is_rejected(self):
        self.assertEqual(self.load()({'pyarrow':{'src/arz/accounting.py'}},['pyarrow==21.0.0']),['pyarrow'])
    def test_missing_or_loose_declaration_rejected(self):
        for dep in [[],['pyarrow'],['pyarrow>=21']]:
            self.assertEqual(self.load()({'pyarrow':{'src/arz_extended/sources.py'}},dep),['pyarrow'])
    def test_other_external_modules_remain_rejected(self):
        self.assertEqual(self.load()({'numpy':{'src/arz_extended/sources.py'},'math':{'src/arz_extended/data.py'}},['pyarrow==21.0.0']),['numpy'])

if __name__=='__main__':unittest.main()
