import os
import re


class TranslationFileFinder(object):

    path_mapping = (
        (".", "\."),
        ("<lang>", "(?P<lang>[\w]*)"),
        ("<filename>", "(?P<filename>[\w]*)"),
        ("<directory_path>", "(?P<directory_path>[\w\/]*)"))

    def __init__(self, translation_path):
        self.translation_path = translation_path
        self.regex = re.compile(self._parse_path())

    @property
    def file_root(self):
        file_root = self.translation_path.split("<")[0]
        if not file_root.endswith("/"):
            file_root = "/".join(file_root.split("/")[:-1])
        return file_root

    def find(self):
        # TODO: make sure translation_path has no ..
        #       ..validate
        for root, dirs, files in os.walk(self.file_root):
            for filename in files:
                file_path = os.path.join(root, filename)
                match = self.regex.match(file_path)
                if match:
                    yield file_path, match.groupdict()

    def _parse_path(self):
        path = self.translation_path
        for k, v in self.path_mapping:
            path = path.replace(k, v)
        return path
