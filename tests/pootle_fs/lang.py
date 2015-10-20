
import pytest

from pootle_fs.language import LANG_MAP_PRESETS, LanguageMapper


CUSTOM_LANG_MAP_PRESETS = {
    "foo": (
        ("testfoo1", "en"),
        ("testfoo2", "es"),
        ("testfoo3", "zu"),
        ("testfoo4", "foo")),
    "bar": (
        ("testbar1", "en"),
        ("testbar2", "es"),
        ("testbar3", "zu"),
        ("testbar4", "bar")),
    "baz": (
        ("testbaz1", "en"),
        ("testbaz2", "es"),
        ("testbaz3", "zu"),
        ("testbaz4", "baz"))}


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


@pytest.mark.django
def test_lang_mapper_custom_presets(english, spanish, zulu):
    mapper = LanguageMapper([], presets=CUSTOM_LANG_MAP_PRESETS)
    assert mapper.presets == CUSTOM_LANG_MAP_PRESETS
    assert mapper.lang_mappings == {}


@pytest.mark.django
def test_lang_mapper_bad_preset(english, spanish, zulu):
    mapper = LanguageMapper(["$PRESET_DOES_NOT_EXIST"])
    assert mapper.lang_mappings == {}

    mapper = LanguageMapper(["$PRESET_DOES_NOT_EXIST", "foo en"])
    assert mapper["foo"] == english
    assert mapper.lang_mappings == {"foo": "en"}

    mapper = LanguageMapper(["foo en", "$PRESET_DOES_NOT_EXIST"])
    assert mapper["foo"] == english
    assert mapper.lang_mappings == {"foo": "en"}


@pytest.mark.django
def test_lang_mapper_preset_mappings(english, spanish, zulu):
    mapper = LanguageMapper(["$foo"], presets=CUSTOM_LANG_MAP_PRESETS)
    assert (
        sorted(mapper.lang_mappings.items())
        == sorted(CUSTOM_LANG_MAP_PRESETS["foo"]))

    # in this case all of the foo entries are overridden by the bar ones
    # if they appear in both
    mapper = LanguageMapper(["$foo", "$bar"], presets=CUSTOM_LANG_MAP_PRESETS)
    expected = (
        [CUSTOM_LANG_MAP_PRESETS["foo"][3]]
        + list(CUSTOM_LANG_MAP_PRESETS["bar"]))
    assert mapper.lang_mappings.items() == expected
    assert mapper["testfoo1"] is None
    assert "testfoo1" not in mapper
    assert mapper["testbar1"] == english
    assert "testbar1" in mapper

    # any mapping can be overridden
    mapper = LanguageMapper(
        ["$foo", "$bar", "custom_code en"],
        presets=CUSTOM_LANG_MAP_PRESETS)
    expected = (
        [CUSTOM_LANG_MAP_PRESETS["foo"][3]]
        + [x for x in CUSTOM_LANG_MAP_PRESETS["bar"] if x[1] != "en"]
        + [("custom_code", "en")])
    assert mapper.lang_mappings.items() == expected
    assert mapper["testfoo1"] is None
    assert "testfoo1" not in mapper
    assert mapper["testbar1"] is None
    assert "testbar1" not in mapper
    assert "custom_code" in mapper
    assert mapper["custom_code"] == english

    # but order is important
    mapper = LanguageMapper(
        ["$foo", "custom_code en", "$bar"],
        presets=CUSTOM_LANG_MAP_PRESETS)
    expected = (
        [CUSTOM_LANG_MAP_PRESETS["foo"][3]]
        + [x for x in CUSTOM_LANG_MAP_PRESETS["bar"]])
    assert mapper.lang_mappings.items() == expected
    assert mapper["testfoo1"] is None
    assert "testfoo1" not in mapper
    assert "custom_code" not in mapper
    assert mapper["custom_code"] is None
    assert mapper["testbar1"] == english
    assert "testbar1" in mapper
