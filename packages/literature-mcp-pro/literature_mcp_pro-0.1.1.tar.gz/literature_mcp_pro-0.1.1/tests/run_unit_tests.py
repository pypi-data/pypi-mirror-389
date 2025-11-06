"""Lightweight test runner to execute async test functions without pytest.

Updated to import modules from project root (no src layer).
"""
import sys
import os
import asyncio
import inspect

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ensure any stray 'src' entries do not shadow the root package
new_sys = []
for p in sys.path:
    if not p:
        continue
    np = p.replace('/', os.path.sep).replace('\\', os.path.sep)
    # filter paths that contain a /src/ segment or end with /src
    if os.path.sep + 'src' + os.path.sep in np or np.endswith(os.path.sep + 'src'):
        continue
    new_sys.append(p)
sys.path = new_sys
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TEST_MODULES = [
    'tests.test_services',
    'tests.test_ai',
    'tests.test_tools'
]

results = []

for mod_name in TEST_MODULES:
    try:
        mod = __import__(mod_name, fromlist=['*'])
    except Exception as e:
        results.append((mod_name, False, f'ImportError: {e}'))
        continue

    for name, obj in inspect.getmembers(mod, inspect.iscoroutinefunction):
        if name.startswith('test_'):
            try:
                asyncio.run(obj())
                results.append((f'{mod_name}.{name}', True, ''))
            except AssertionError as ae:
                results.append((f'{mod_name}.{name}', False, f'AssertionError: {ae}'))
            except Exception as e:
                results.append((f'{mod_name}.{name}', False, f'Error: {e}'))

# Also handle sync test functions
for mod_name in TEST_MODULES:
    try:
        mod = __import__(mod_name, fromlist=['*'])
    except Exception:
        continue
    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith('test_'):
            try:
                # skip coroutine functions (already handled)
                if inspect.iscoroutinefunction(obj):
                    continue
                obj()
                results.append((f'{mod_name}.{name}', True, ''))
            except AssertionError as ae:
                results.append((f'{mod_name}.{name}', False, f'AssertionError: {ae}'))
            except Exception as e:
                results.append((f'{mod_name}.{name}', False, f'Error: {e}'))

# Report
passed = sum(1 for r in results if r[1])
failed = [r for r in results if not r[1]]

print('\nTest results:')
for name, ok, msg in results:
    status = 'PASS' if ok else 'FAIL'
    print(f'{status}: {name} {msg}')

print(f'\nSummary: {passed} passed, {len(failed)} failed, total {len(results)}')

if failed:
    sys.exit(2)
else:
    sys.exit(0)
