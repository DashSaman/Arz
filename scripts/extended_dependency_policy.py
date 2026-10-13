"""Narrow optional Parquet-reader declaration; unknown imports fail closed."""
import sys


def classify_imports(origins, optional_data_dependencies):
    external = set(origins) - sys.stdlib_module_names - {'arz', 'arz_extended'}
    if (optional_data_dependencies == ['pyarrow==21.0.0']
            and origins.get('pyarrow') == {'src/arz_extended/sources.py'}):
        external.discard('pyarrow')
    return sorted(external)
