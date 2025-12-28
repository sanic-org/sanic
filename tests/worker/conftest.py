import pytest


def pytest_collection_modifyitems(items):
    """Group all worker tests to run on same xdist worker.

    These tests spawn processes and can conflict with parallel execution.
    """
    for item in items:
        if "/worker/" in str(item.fspath):
            item.add_marker(pytest.mark.xdist_group(name="process_spawning"))
