import logging

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle_language.models import Language


LANG_MAP_PRESETS = {}

logger = logging.getLogger(__name__)


class LanguageMapper(object):
    """For a given code find the relevant pootle lang taking account of any
    lang mapping configuration

    """

    def __init__(self, mapping):
        self.mapping = mapping

    @cached_property
    def lang_mappings(self):
        return self._parse_lang_mappings(self.mapping)

    def get_lang_code(self, lang_code):
        return self.lang_mappings.get(lang_code, lang_code)

    @lru_cache(maxsize=None)
    def get_lang(self, lang_code):
        try:
            return Language.objects.get(
                code=self.get_lang_code(lang_code))
        except Language.DoesNotExist:
            return None

    def _parse_lang_mappings(self, config):
        try:
            mapping = config.get("default", "lang_mappings")
        except:
            return {}

        _mapping = {}
        for line in mapping.split("\n"):
            if line.strip().startswith("$"):
                preset = LANG_MAP_PRESETS.get(line.strip()[1:], None)
                if not preset:
                    logger.warning(
                        "Unrecognised lang mapping preset: %s" % preset)
                else:
                    for k, v in preset:
                        _mapping[k] = v
            else:
                try:
                    k, v = line.strip().split(":")
                    _mapping[k] = [x.strip() for x in v.split(",")]
                except ValueError:
                    logger.warning("Misconfigured lang mapping: %s" % line)
        return _mapping
