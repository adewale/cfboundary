// Runs tests/pyodide/real_runtime_checks.py inside real Pyodide (the pinned
// `pyodide` npm package), one node:test case per `check_*` function.
// Usage: npm ci --prefix tests/pyodide && npm test --prefix tests/pyodide
import assert from "node:assert/strict";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { loadPyodide } from "pyodide";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..", "..");

const pyodide = await loadPyodide();
pyodide.mountNodeFS("/repo", repoRoot);
pyodide.runPython(`
import sys
sys.dont_write_bytecode = True  # keep the mounted checkout free of __pycache__
sys.path[:0] = ["/repo", "/repo/tests/pyodide"]
import real_runtime_checks
`);

const checkNames = pyodide
  .runPython("[name for name in dir(real_runtime_checks) if name.startswith('check_')]")
  .toJs();

test("discovers the real-Pyodide checks", () => {
  // Guards against a vacuous pass if discovery or the module import breaks.
  assert.ok(checkNames.length >= 10, `only found ${checkNames.length} checks`);
  assert.match(pyodide.version, /^0\.28\./);
});

for (const name of checkNames) {
  test(name, async () => {
    await pyodide.runPythonAsync(`
import inspect
result = real_runtime_checks.${name}()
if inspect.isawaitable(result):
    await result
`);
  });
}
