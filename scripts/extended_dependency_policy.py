"""Narrow optional Parquet-reader declaration; unknown imports fail closed."""
import sys


def classify_imports(origins, optional_data_dependencies):
    external = set(origins) - sys.stdlib_module_names - {'arz', 'arz_extended'}
    if (optional_data_dependencies == ['pyarrow==21.0.0']
            and origins.get('pyarrow') == {'src/arz_extended/sources.py'}):
        external.discard('pyarrow')
    local_origins = {
        'arz_phase4': {'src/arz_phase4_scope.py', 'src/arz_phase4_audit.py'},
        'arz_phase4_scope': {'src/arz_phase4_audit.py'},
    }
    for name, allowed in local_origins.items():
        actual = origins.get(name, set())
        if actual and actual <= allowed:
            external.discard(name)
    return sorted(external)
