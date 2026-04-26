from __future__ import annotations

import importlib

from hypothesis import given
from hypothesis import strategies as st

import cfboundary.ffi as ffi
from cfboundary.ffi import R2ListResult, SafeVectorize, is_js_missing, is_js_null, js_null, to_js, to_py
from cfboundary.testing.fakes import patch_pyodide_runtime

json_scalars = st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text()
json_values = st.recursive(
    json_scalars,
    lambda children: st.lists(children, max_size=5)
    | st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=5),
    max_leaves=20,
)


def test_preferred_public_names_are_exported_from_ffi() -> None:
    assert callable(ffi.to_py)
    assert callable(ffi.to_js)
    assert callable(ffi.js_null)
    assert callable(ffi.is_js_missing)


def test_star_import_surface_has_no_private_or_compat_names() -> None:
    assert "to_py" in ffi.__all__
    assert "to_js" in ffi.__all__
    assert "js_null" in ffi.__all__
    assert "is_js_missing" in ffi.__all__
    assert not any(name.startswith("_") for name in ffi.__all__)
    assert "get_js_null" not in ffi.__all__
    assert "is_js_null_or_undefined" not in ffi.__all__
    assert "to_js_value" not in ffi.__all__
    assert "HttpResponse" not in ffi.__all__
    assert "http_fetch" not in ffi.__all__


@given(json_values)
def test_to_py_is_idempotent_for_python_values(value) -> None:
    assert to_py(to_py(value)) == to_py(value)


@given(json_values)
def test_to_js_is_identity_in_cpython(value) -> None:
    assert to_js(value) == value


@given(
    st.one_of(
        st.booleans(),
        st.integers(),
        st.text(),
        st.lists(json_scalars),
        st.dictionaries(st.text(), json_scalars),
    )
)
def test_d1_null_only_changes_none(value) -> None:
    from cfboundary.ffi import d1_null

    if value is not None:
        assert d1_null(value) == value


def test_pyodide_fake_null_surface_uses_public_names() -> None:
    with patch_pyodide_runtime():
        null = js_null()
        assert is_js_null(null) is True
        assert is_js_null(None) is False
        assert is_js_missing(null) is True
        assert is_js_missing(None) is True


class VectorizeDeleteByIdsOnly:
    async def deleteByIds(self, ids):
        return {"deleted": ids}


class VectorizeDeleteOnly:
    async def delete(self, ids):
        return {"deleted": ids}


def run(coro):
    import asyncio

    return asyncio.run(coro)


def test_vectorize_uses_pythonic_delete_by_ids() -> None:
    assert run(SafeVectorize(VectorizeDeleteByIdsOnly()).delete_by_ids(["a"])) == {"deleted": ["a"]}
    assert run(SafeVectorize(VectorizeDeleteOnly()).delete_by_ids(["b"])) == {"deleted": ["b"]}
    assert not hasattr(SafeVectorize(VectorizeDeleteOnly()), "deleteByIds")


def test_result_aliases_are_available_for_pythonic_docs() -> None:
    safe_env = importlib.import_module("cfboundary.ffi.safe_env")
    assert safe_env.R2ListResult is R2ListResult
