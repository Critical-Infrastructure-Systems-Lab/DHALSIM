import pytest

from dhalsim.parser.config_parser import ConfigParser


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        ConfigParser("non_existing_path.yaml")

def test_imp_path_1(tmpdir):
    c = tmpdir.join("config.yaml")
    tmpdir.join("test.inp")
    c.write("inp_file: test.inp")
    print(str(c))
    parser = ConfigParser(str(c))
    assert parser.inp_path == str(tmpdir.join("test.inp"))