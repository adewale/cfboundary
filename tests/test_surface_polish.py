from __future__ import annotations

from hypothesis import example, given
from hypothesis import strategies as st

from cfboundary import ffi
from cfboundary.ffi import is_js_missing, is_js_null, js_null, to_js, to_py
from cfboundary.testing.fakes import patch_pyodide_runtime

json_scalars = st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text()
json_values = st.recursive(
    json_scalars,
    lambda children: st.lists(children, max_size=5)
    | st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=5),
    max_leaves=20,
)


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
@example({1: "int key", "nested": {2: None}})
def test_to_py_returns_plain_python_values_unchanged(value) -> None:
    assert to_py(value) == value


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

    assert d1_null(value) is value


def test_pyodide_fake_null_surface_uses_public_names() -> None:
    with patch_pyodide_runtime():
        null = js_null()
        assert is_js_null(null) is True
        assert is_js_null(None) is False
        assert is_js_missing(null) is True
        assert is_js_missing(None) is True

