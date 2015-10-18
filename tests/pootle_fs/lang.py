
import pytest

from pootle_fs.language import LANG_MAP_PRESETS, LanguageMapper


@pytest.mark.django
def test_lang_mapper(english, spanish, zulu):
    mapper = LanguageMapper([])
    assert mapper.presets == LANG_MAP_PRESETS
    assert mapper.lang_mappings == {}

    # if there is no mapping you get back what you gave
    assert mapper.get_pootle_code("DOESNT_EXIST") == "DOESNT_EXIST"
    assert mapper.get_fs_code("DOESNT_EXIST") == "DOESNT_EXIST"

    # You can always get any langs that exist even if they are not
    # specifically mapped
    assert "zu" not in mapper
    assert mapper['zu'] == zulu

    mapper = LanguageMapper([("foo en")])
    assert mapper.lang_mappings == {"foo": "en"}
    assert mapper["foo"] == english
    assert "foo" in mapper
    assert mapper.get_fs_code("en") == "foo"
    assert mapper.get_pootle_code("foo") == "en"

    mapper = LanguageMapper([("foo en"), ("foo es")])
    assert mapper.lang_mappings == {"foo": "es"}
    assert mapper["foo"] == spanish
    assert "foo" in mapper
    assert mapper.get_fs_code("es") == "foo"
    assert mapper.get_pootle_code("foo") == "es"

    # mappings are 1-2-1 - so if you set another mapping with same
    # value it overrides
    mapper = LanguageMapper([("foo en"), ("foo2 en")])
    assert mapper.lang_mappings == {"foo2": "en"}
    assert mapper["foo"] is None
    assert "foo" not in mapper
    assert mapper["foo2"] == english
    assert "foo2" in mapper
    assert mapper.get_fs_code("en") == "foo2"
    assert mapper.get_pootle_code("foo2") == "en"
    assert mapper.get_pootle_code("foo") == "foo"

    # You can create a mapping to a non-existent lang - but it
    # wont return a language
    mapper = LanguageMapper([("foo bar")])
    assert mapper.lang_mappings == {"foo": "bar"}
    assert "foo" in mapper
    assert mapper['foo'] is None
    assert mapper['foo73'] is None
