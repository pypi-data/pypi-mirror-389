import os
import codecs

# Python 3.4+ compatibility
if 'unicode' not in dir():
    unicode = str


__version__ = '0.2.2'


class NonExistentLanguageError(RuntimeError):
    pass


def find(whatever=None, language=None, iso639_1=None, iso639_2=None,
        iso639_3=None, native=None, spanish=None, french=None,
        russian=None, arabic=None, chinese=None, english=None):
    """Find data row with the language.

    :param whatever: key to search in any of the following fields
    :param language: key to search in English language name
    :param iso639_1: key to search in ISO 639-1 code (2 digits)
    :param iso639_2: key to search in ISO 639-2 code (3 digits,
                     bibliographic & terminological)
    :param iso639_3: key to search in ISO 639-3 code (3 digits)
    :param native: key to search in native language name
    :param native: key to search in Spanish language name
    :param native: key to search in French language name
    :param native: key to search in Russian language name
    :param native: key to search in Arabic language name
    :param native: key to search in Chinese language name
    :return: a dict with keys (u'name', u'iso639_1', u'iso639_2_b',
                     u'iso639_2_t', u'iso639_3', u'native', u'spanish',
                     u'french', u'russian', u'arabic', u'chinese')

    All arguments can be both string or unicode (Python 2).
    If there are multiple names defined, any of these can be looked for.
    """
    if whatever:
        keys = [u'name', u'iso639_1', u'iso639_2_b', u'iso639_2_t', \
                u'iso639_3', u'native', u'spanish', u'french', \
                u'russian', u'arabic', u'chinese', u'english']
        val = whatever
    elif language:
        keys = [u'name']
        val = language
    elif iso639_1:
        keys = [u'iso639_1']
        val = iso639_1
    elif iso639_2:
        keys = [u'iso639_2_b', u'iso639_2_t']
        val = iso639_2
    elif iso639_3:
        keys = [u'iso639_3']
        val = iso639_3
    elif native:
        keys = [u'native']
        val = native
    elif native:
        keys = [u'spanish']
        val = spanish
    elif native:
        keys = [u'french']
        val = french
    elif native:
        keys = [u'russian']
        val = russian
    elif native:
        keys = [u'arabic']
        val = arabic
    elif native:
        keys = [u'chinese']
        val = chinese
    elif native:
        keys = [u'english']
        val = language
    else:
        raise ValueError('Invalid search criteria.')
    val = unicode(val).lower()
    return next((item for item in data if any(
        val in item[key].lower().split("; ") for key in keys)), None)


def is_valid639_1(code):
    """Whether code exists as ISO 639-1 code.

    >>> is_valid639_1("swe")
    False
    >>> is_valid639_1("sv")
    True
    """
    if len(code) != 2:
        return False
    return find(iso639_1=code) is not None


def is_valid639_2(code):
    """Whether code exists as ISO 639-2 code.

    >>> is_valid639_2("swe")
    True
    >>> is_valid639_2("sv")
    False
    """
    if len(code) != 3:
        return False
    return find(iso639_2=code) is not None


def is_valid639_3(code):
    """Whether code exists as ISO 639-3 code.

    >>> is_valid639_3("swe")
    True
    >>> is_valid639_3("sv")
    False
    """
    if len(code) != 3:
        return False
    return find(iso639_3=code) is not None


def to_iso639_1(key):
    """Find ISO 639-1 code for language specified by key.

    >>> to_iso639_1("swe")
    u'sv'
    >>> to_iso639_1("English")
    u'en'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'iso639_1']


def to_iso639_2(key, type='B'):
    """Find ISO 639-2 code for language specified by key.

    :param type: "B" - bibliographical (default), "T" - terminological

    >>> to_iso639_2("German")
    u'ger'
    >>> to_iso639_2("German", "T")
    u'deu'
    """
    if type not in ('B', 'T'):
        raise ValueError('Type must be either "B" or "T".')
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    if type == 'T' and item[u'iso639_2_t']:
        return item[u'iso639_2_t']
    return item[u'iso639_2_b']


def to_iso639_3(key):
    """Find ISO 639-3 code for language specified by key.

    >>> to_iso639_3("sv")
    u'swe'
    >>> to_iso639_3("English")
    u'eng'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'iso639_3']


def to_name(key):
    """Find the English name for the language specified by key.

    >>> to_name('br')
    u'Breton'
    >>> to_name('sw')
    u'Swahili'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'name']


def to_english(key):
    """Find the English name for the language specified by key.

    >>> to_name('br')
    u'Breton'
    >>> to_name('sw')
    u'Swahili'
    """
    return to_name(key)


def to_spanish(key):
    """Find the Spanish name for the language specified by key.

    >>> to_spanish('eng')
    u'Inglés'
    >>> to_spanish('deu')
    u'Alemán'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'spanish']


def to_french(key):
    """Find the French name for the language specified by key.

    >>> to_french('eng')
    u'Anglais'
    >>> to_french('deu')
    u'Allemand'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'french']


def to_russian(key):
    """Find the Russian name for the language specified by key.

    >>> to_russian('eng')
    u'Английский'
    >>> to_russian('deu')
    u'Немецкий'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'russian']


def to_chinese(key):
    """Find the Chinese name for the language specified by key.

    >>> to_chinese('eng')
    u'英语'
    >>> to_chinese('deu')
    u'德语'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'chinese']


def to_arabic(key):
    """Find the Arabic name for the language specified by key.

    >>> to_chinese('eng')
    u'إنجليزي'
    >>> to_chinese('deu')
    u'ألمانية'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'arabic']


def to_native(key):
    """Find the native name for the language specified by key.

    >>> to_native('br')
    u'brezhoneg'
    >>> to_native('sw')
    u'Kiswahili'
    """
    item = find(whatever=key)
    if not item:
        raise NonExistentLanguageError('Language does not exist.')
    return item[u'native']


def _load_data():
    def parse_line(line):
        data = line.strip().split('|')
        return {
            u'iso639_2_b': data[0],
            u'iso639_2_t': data[1],
            u'iso639_3': data[2],
            u'iso639_1': data[3],
            u'name': data[4],
            u'english': data[4],
            u'native': data[5],
            u'spanish': data[6],
            u'french': data[7],
            u'russian': data[8],
            u'arabic': data[9],
            u'chinese': data[10],
        }

    data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'languages_utf-8.txt')
    with codecs.open(data_file, 'r', 'UTF-8') as f:
        data = [parse_line(line) for line in f]
    return data


data = _load_data()
