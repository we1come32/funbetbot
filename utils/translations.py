import yaml
import os

__path__ = os.getcwd()

languages = ['ru', 'en']


class Language:
    data: dict
    _languages = {}

    def __init__(self, lang: str):
        lang = lang.lower()
        if lang not in languages:
            lang = 'en'
        if (data := self._languages.get(lang, None)) is None:
            try:
                os.chdir(__path__ + r'\translations')
                with open(f'Locale_{lang.upper()}.yml', 'r', encoding='utf8') as file:
                    data = self._languages[lang] = yaml.load(file, Loader=yaml.FullLoader)
                os.chdir(__path__)
            except FileExistsError:
                raise ValueError(f'Невозможно загрузить языковой файл {"Locale_" + lang.upper() + ".yml"!r}: '
                                 f'Файл не найден')
        self.data = data

    @classmethod
    async def reload(cls):
        pass

