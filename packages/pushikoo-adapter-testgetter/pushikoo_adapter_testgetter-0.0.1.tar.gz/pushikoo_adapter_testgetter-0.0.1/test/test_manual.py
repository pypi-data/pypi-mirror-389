import importlib.metadata as md
import tomllib
from pathlib import Path

import pytest
from pushikoo_interface import (
    Adapter,
    AdapterFrameworkContext,
    Detail,
    Getter,
    get_adapter_config_types,
)


@pytest.fixture(scope="session")
def adapter_env(tmp_path_factory):
    """
    Combined fixture: loads current adapter class and builds test context.
    Provides (UnderTestAdapterClass, ctx).

    In practice, all logic within this function is handled by the framework.
    """
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())[
        "project"
    ]["name"]

    eps = md.entry_points(group="pushikoo.adapter")
    ep = next((e for e in eps if getattr(e.dist, "name", None) == project), None)
    if not ep:
        pytest.skip(f"No entry point found for {project}")

    UnderTestAdapterClass = ep.load()
    ClassCfg, InstCfg = get_adapter_config_types(UnderTestAdapterClass)

    class MockCtx(AdapterFrameworkContext):
        storage_base_path = tmp_path_factory.mktemp("adapter_storage")

        @staticmethod
        def get_proxies():
            return {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}

        @staticmethod
        def get_class_config():
            return ClassCfg()

        @staticmethod
        def get_instance_config():
            return InstCfg()

    return UnderTestAdapterClass, MockCtx


# TODO: Edit this, or add more test cases
def test_adapter_basic_flow(adapter_env: tuple[type[Adapter], AdapterFrameworkContext]):
    """Smoke test: adapter can fetch timeline and details"""
    UnderTestAdapterClass, ctx = adapter_env
    # assert UnderTestAdapterClass.meta.name == ""
    getter: Getter = UnderTestAdapterClass.create(id_="123", ctx=ctx)

    ids = getter.timeline()
    assert isinstance(ids, list)
    assert ids, "timeline() should return non-empty list"

    detail = getter.detail(ids[0])
    assert isinstance(detail, Detail)

    agg = getter.details(ids)
    assert isinstance(agg, Detail)
