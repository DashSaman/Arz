import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from extended_dependency_policy import classify_imports

class Phase4ImportScopeTests(unittest.TestCase):
    def test_owned_numerics_allowed_only_in_registered_scope(self):
        self.assertEqual(classify_imports({'arz_phase4':{'src/arz_phase4_scope.py'}},[]),[])

    def test_owned_offline_auditor_imports_allowed(self):
        origins={'arz_phase4':{'src/arz_phase4_audit.py'},'arz_phase4_scope':{'src/arz_phase4_audit.py'}}
        self.assertEqual(classify_imports(origins,[]),[])

    def test_unknown_import_or_other_origin_not_silenced(self):
        self.assertEqual(classify_imports({'arz_phase4':{'src/arz/engine.py'}},[]),['arz_phase4'])
        self.assertEqual(classify_imports({'arz_phase4_unknown':{'src/arz_phase4_scope.py'}},[]),['arz_phase4_unknown'])
