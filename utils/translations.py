import copy
from typing import Union

import loguru
import yaml
import os


__path__ = os.getcwd()
logger = loguru.logger


class LanguagePackage(dict):
    name: str
    _english_dict: "LanguagePackage"

    def __init__(self, *args):
        args = list(args)
        if len(args) == 1:
            if type(args[0]) is dict:
                a = LanguagePackage()
                for key, value in args[0].items():
                    if type(value) is dict:
                        value = LanguagePackage(value)
                    a[key] = value
                args[0] = a
        super().__init__(*args)

    def test(self):
        print(self.__dict__)

    def __or__(self, other: Union[dict, "LanguagePackage"]):
        if type(other) is dict:
            other = LanguagePackage(other)
        if type(other) is LanguagePackage:
            new_value = copy.copy(self)
            for key, value in other.items():
                if type(value) is LanguagePackage:
                    tmp = new_value.get(key, None) | value
                else:
                    tmp = value
                new_value[key] = tmp
            return new_value
        return super().__or__(other)

    @classmethod
    def set_english(cls, package: "LanguagePackage") -> None:
        cls._english_dict = package

    def __missing__(self, key) -> None:
        return None


class LanguageLoader:
    allow_languages: list = []
    _languages = {}
    _language: str

    def __init__(self, lang: str):
        lang = lang.upper()
        if lang not in self.allow_languages:
            lang = 'EN'
        if self._languages.get(lang, None) is None:
            lang = 'EN'
        self._language = lang

    def get(self):
        pass

    @classmethod
    def add_localization_file(cls, lang: str, filename: str, path: str = None) -> None:
        if path is None:
            path = __path__
        data: LanguagePackage = cls.load_data_from_file(filename, path=path)
        if lang == 'EN':
            cls._languages[lang] = data
        else:
            cls._languages[lang] = cls._languages.get('EN') | data

    @staticmethod
    def load_data_from_file(filename: str, path: str = None) -> LanguagePackage:
        if path is None:
            path = __path__
        os.chdir(path)
        try:
            with open(filename, 'r', encoding='utf8') as file:
                result = LanguagePackage(yaml.load(file, Loader=yaml.FullLoader))
        except FileExistsError:
            os.chdir(__path__)
            raise ValueError(f'Невозможно загрузить языковой файл {filename!r}: Файл не найден')
        os.chdir(__path__)
        return result

    @classmethod
    def load(cls, path: str = None) -> None:
        if path is None:
            path = __path__ + r'\translations'
        os.chdir(path)
        files = os.listdir()
        cls.add_localization_file(lang="EN", filename='Locale_EN.yml', path=path)
        for file in files:
            if file.startswith('Locale_') and file.endswith('.yml'):
                lang = file.split("_")[1][:2].upper()
                cls.allow_languages.append(lang)
                cls.add_localization_file(lang=lang, filename=file, path=path)
        os.chdir(__path__)

    @classmethod
    async def reload(cls, path: str = None) -> None:
        cls._languages = {}
        cls.allow_languages = []
        cls.load(path=path)
