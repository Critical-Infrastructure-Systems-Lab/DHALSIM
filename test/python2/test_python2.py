import sys


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7
