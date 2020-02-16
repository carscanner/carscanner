import pytest

print('configuring pytest')


def pytest_addoption(parser):
    print('adding option')
    parser.addoption(
        "--runweb", action="store_true", default=False, help="run web tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "web: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runweb"):
        # --runweb given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runweb option to run")
    for item in items:
        if "web" in item.keywords:
            item.add_marker(skip_slow)
