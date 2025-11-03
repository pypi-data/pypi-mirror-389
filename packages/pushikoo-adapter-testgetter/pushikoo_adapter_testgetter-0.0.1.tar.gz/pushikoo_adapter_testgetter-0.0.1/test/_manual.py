from pathlib import Path

from pushikoo_interface import AdapterFrameworkContext, Detail, get_adapter_config_types
from pydantic import BaseModel

from pushikoo_adapter_testgetter import TestGetter

TestAdapterClass = TestGetter
TestAdapterClassConfig, TestAdapterInstanceConfig = get_adapter_config_types(
    TestAdapterClass
)


class MockCtx(AdapterFrameworkContext):
    """Simulated framework context"""

    @staticmethod
    def get_class_config():
        return TestAdapterClassConfig()

    @staticmethod
    def get_instance_config():
        return TestAdapterInstanceConfig()


class FrameworkSimulator:
    """Simulated framework runtime environment"""

    def __init__(self):
        # Create configuration and context
        self.ctx = MockCtx()
        self.ctx.proxies = {
            "http": "http://127.0.0.1:7890",
            "https": "http://127.0.0.1:7890",
        }
        self.ctx.storage_base_path = Path(f".cache/adapter/storage")

    def run(self):
        print("=== Framework Booting Adapter ===")
        getter = TestAdapterClass.create(id_="123", ctx=self.ctx)
        print(getter)
        print(repr(getter))

        # Call timeline
        print("\n=== Fetching timeline ===")
        ids = getter.timeline()
        print("IDs:", ids)

        # Call detail
        print("\n=== Fetching detail (first post) ===")
        d = getter.detail(ids[0])
        print("Detail Result:")
        print("  Title:", d.title)
        print("  Author:", d.author_name)
        print("  Content: |\n")
        print(d.content[:60], "...")

        # Call details (aggregate)
        print("\n=== Fetching details (aggregate) ===")
        agg = getter.details(ids)
        print("Aggregated Result:")
        print("  Title:", agg.title)
        print("  Authors:", agg.author_name)
        print("  Content (joined): |\n")
        print(agg.content[:60], "...")
        print("  URL count:", len(agg.url))
        print("  Image count:", len(agg.image))
        print("  Timestamp:", agg.ts)


if __name__ == "__main__":
    FrameworkSimulator().run()
