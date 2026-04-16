from app.utils import utils

def test_split_name():
    assert utils.split_name("") == ["", ""]
    assert utils.split_name("test") == ["test", ""]
    assert utils.split_name("test#euw") == ["test", "euw"]
    assert utils.split_name("test#euw#extra") == ["test", "euw#extra"]