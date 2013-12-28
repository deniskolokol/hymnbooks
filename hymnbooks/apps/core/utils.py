# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

import re
import random
import string
import collections

"""
Custom validators and exceptions.
"""
class MissingDataError(Exception):
    message = _(u'The following fields cannot be empty: %s')
    
    def __init__(self, fields):
        self.message = self.message % ', '.join(fields)
        Exception.__init__(self, self.message)


class WrongTypeError(Exception):
    message = _(u'Wrong type: %s')
    
    def __init__(self, field):
        self.message = self.message % field
        Exception.__init__(self, self.message)


class WrongDesctinationError(Exception):
    message = _(u'Wrong destination: %s')
    
    def __init__(self, field):
        self.message = self.message % field
        Exception.__init__(self, self.message)

        
class FieldValidator(object):
    """
    Validates if fields are None or empty with given conditions.
    """
    @classmethod
    def _check_if_empty(self, val):
        if hasattr(val, '__getitem__'):
            try:
                if val.strip() == '':
                    return True
            except AttributeError:
                if len(val) == 0:
                    return True
        else:
            if len(str(val)) == 0:
                return True
        return False

    @classmethod
    def validate(self, obj, fields, **kwargs):
        """
        Conditions are defined by kwargs {fieldname: value}.
        There should be at least one condition: {status: active}.
        Errors in conditions ignored.
        """
        if (not kwargs) or ('status' not in kwargs):
            kwargs.update({'status': 'active'})

        # Validate only if conditions set up right.
        for k, v in kwargs.iteritems():
            try:
                if getattr(obj, k) != v:
                    return
            except AttributeError:
                continue

        empty = []
        for field in fields:
            value = getattr(obj, field)
            if value is None:
                empty.append(field)
                continue

            # Assume field can be empty, try different field types.
            if self._check_if_empty(value):
                empty.append(field)

        if empty:
            raise MissingDataError(empty)


class UserMessage():
    statuses = ('info', 'warning', 'success', 'danger')
    status = 'info'
    message = ''

    def __init__(self, message=None, status=None):
        self.set_message(message)
        self.set_status(status)

    def __str__(self):
        return "%s: %s" % (self.status, self.message)

    def __unicode__(self):
        return unicode(self.__str__())

    def _status(self, status=None):
        if status in self.statuses:
            return status
        else:
            return 'info' # default

    def set_status(self, status=None):
        self.status = self._status(status)

    def set_message(self, message=None):
        if (message is not None) and (message.strip() != ''):
            self.message = message

    def serialize(self):
        return {'status': self.status, 'message': self.message}

    def info(self, message=None):
        self.set_message(message)
        self.set_status()
        return self.serialize()

    def warning(self, message=None):
        self.set_message(message)
        self.set_status('warning')
        return self.serialize()

    def danger(self, message=None):
        self.set_message(message)
        self.set_status('danger')
        return self.serialize()

    def success(self, message=None):
        self.set_message(message)
        self.set_status('success')
        return self.serialize()


def id_generator(size=6, chars=string.ascii_lowercase+string.digits):
    """
    Generates quazi-unique sequence from random digits and letters.
    """
    return ''.join(random.choice(chars) for x in range(size))


def sizify(value):
    """
    File size pretty printing.
    """
    if value < 512000:
        value /= 1024.0
        ext = 'KB'
    elif value < 4194304000:
        value /= 1048576.0
        ext = 'MB'
    else:
        value /= 1073741824.0
        ext = 'GB'
    return '%s %s' % (str(round(value, 2)), ext)


"""
Custom procedure for unique slug depending on the document type.
See slugify_unique
"""

LATIN_MAP = {
    u'À': 'A', u'Á': 'A', u'Â': 'A', u'Ã': 'A', u'Ä': 'A', u'Å': 'A', u'Æ': 'AE', u'Ç':'C', 
    u'È': 'E', u'É': 'E', u'Ê': 'E', u'Ë': 'E', u'Ì': 'I', u'Í': 'I', u'Î': 'I',
    u'Ï': 'I', u'Ð': 'D', u'Ñ': 'N', u'Ò': 'O', u'Ó': 'O', u'Ô': 'O', u'Õ': 'O', u'Ö':'O', 
    u'Ő': 'O', u'Ø': 'O', u'Ù': 'U', u'Ú': 'U', u'Û': 'U', u'Ü': 'U', u'Ű': 'U',
    u'Ý': 'Y', u'Þ': 'TH', u'ß': 'ss', u'à':'a', u'á':'a', u'â': 'a', u'ã': 'a', u'ä':'a', 
    u'å': 'a', u'æ': 'ae', u'ç': 'c', u'è': 'e', u'é': 'e', u'ê': 'e', u'ë': 'e',
    u'ì': 'i', u'í': 'i', u'î': 'i', u'ï': 'i', u'ð': 'd', u'ñ': 'n', u'ò': 'o', u'ó':'o', 
    u'ô': 'o', u'õ': 'o', u'ö': 'o', u'ő': 'o', u'ø': 'o', u'ù': 'u', u'ú': 'u',
    u'û': 'u', u'ü': 'u', u'ű': 'u', u'ý': 'y', u'þ': 'th', u'ÿ': 'y'
}
LATIN_SYMBOLS_MAP = {
    u'©':'(c)'
}
GREEK_MAP = {
    u'α':'a', u'β':'b', u'γ':'g', u'δ':'d', u'ε':'e', u'ζ':'z', u'η':'h', u'θ':'8',
    u'ι':'i', u'κ':'k', u'λ':'l', u'μ':'m', u'ν':'n', u'ξ':'3', u'ο':'o', u'π':'p',
    u'ρ':'r', u'σ':'s', u'τ':'t', u'υ':'y', u'φ':'f', u'χ':'x', u'ψ':'ps', u'ω':'w',
    u'ά':'a', u'έ':'e', u'ί':'i', u'ό':'o', u'ύ':'y', u'ή':'h', u'ώ':'w', u'ς':'s',
    u'ϊ':'i', u'ΰ':'y', u'ϋ':'y', u'ΐ':'i',
    u'Α':'A', u'Β':'B', u'Γ':'G', u'Δ':'D', u'Ε':'E', u'Ζ':'Z', u'Η':'H', u'Θ':'8',
    u'Ι':'I', u'Κ':'K', u'Λ':'L', u'Μ':'M', u'Ν':'N', u'Ξ':'3', u'Ο':'O', u'Π':'P',
    u'Ρ':'R', u'Σ':'S', u'Τ':'T', u'Υ':'Y', u'Φ':'F', u'Χ':'X', u'Ψ':'PS', u'Ω':'W',
    u'Ά':'A', u'Έ':'E', u'Ί':'I', u'Ό':'O', u'Ύ':'Y', u'Ή':'H', u'Ώ':'W', u'Ϊ':'I',
    u'Ϋ':'Y'
}
TURKISH_MAP = {
    u'ş':'s', u'Ş':'S', u'ı':'i', u'İ':'I', u'ç':'c', u'Ç':'C', u'ü':'u', u'Ü':'U',
    u'ö':'o', u'Ö':'O', u'ğ':'g', u'Ğ':'G'
}
RUSSIAN_MAP = {
    u'а':'a', u'б':'b', u'в':'v', u'г':'g', u'д':'d', u'е':'e', u'ё':'yo', u'ж':'zh',
    u'з':'z', u'и':'i', u'й':'j', u'к':'k', u'л':'l', u'м':'m', u'н':'n', u'о':'o',
    u'п':'p', u'р':'r', u'с':'s', u'т':'t', u'у':'u', u'ф':'f', u'х':'h', u'ц':'c',
    u'ч':'ch', u'ш':'sh', u'щ':'sh', u'ъ':'', u'ы':'y', u'ь':'', u'э':'e', u'ю':'yu',
    u'я':'ya',
    u'А':'A', u'Б':'B', u'В':'V', u'Г':'G', u'Д':'D', u'Е':'E', u'Ё':'Yo', u'Ж':'Zh',
    u'З':'Z', u'И':'I', u'Й':'J', u'К':'K', u'Л':'L', u'М':'M', u'Н':'N', u'О':'O',
    u'П':'P', u'Р':'R', u'С':'S', u'Т':'T', u'У':'U', u'Ф':'F', u'Х':'H', u'Ц':'C',
    u'Ч':'Ch', u'Ш':'Sh', u'Щ':'Sh', u'Ъ':'', u'Ы':'Y', u'Ь':'', u'Э':'E', u'Ю':'Yu',
    u'Я':'Ya'
}
UKRAINIAN_MAP = {
    u'Є':'Ye', u'І':'I', u'Ї':'Yi', u'Ґ':'G', u'є':'ye', u'і':'i', u'ї':'yi', u'ґ':'g'
}
CZECH_MAP = {
    u'č':'c', u'ď':'d', u'ě':'e', u'ň':'n', u'ř':'r', u'š':'s', u'ť':'t', u'ů':'u',
    u'ž':'z', u'Č':'C', u'Ď':'D', u'Ě':'E', u'Ň':'N', u'Ř':'R', u'Š':'S', u'Ť':'T',
    u'Ů':'U', u'Ž':'Z'
}

POLISH_MAP = {
    u'ą':'a', u'ć':'c', u'ę':'e', u'ł':'l', u'ń':'n', u'ó':'o', u'ś':'s', u'ź':'z',
    u'ż':'z', u'Ą':'A', u'Ć':'C', u'Ę':'e', u'Ł':'L', u'Ń':'N', u'Ó':'o', u'Ś':'S',
    u'Ź':'Z', u'Ż':'Z'
}

LATVIAN_MAP = {
    u'ā':'a', u'č':'c', u'ē':'e', u'ģ':'g', u'ī':'i', u'ķ':'k', u'ļ':'l', u'ņ':'n',
    u'š':'s', u'ū':'u', u'ž':'z', u'Ā':'A', u'Č':'C', u'Ē':'E', u'Ģ':'G', u'Ī':'i',
    u'Ķ':'k', u'Ļ':'L', u'Ņ':'N', u'Š':'S', u'Ū':'u', u'Ž':'Z'
}

def _makeRegex():
    ALL_DOWNCODE_MAPS = {}
    ALL_DOWNCODE_MAPS.update(LATIN_MAP)
    ALL_DOWNCODE_MAPS.update(LATIN_SYMBOLS_MAP)
    ALL_DOWNCODE_MAPS.update(GREEK_MAP)
    ALL_DOWNCODE_MAPS.update(TURKISH_MAP)
    ALL_DOWNCODE_MAPS.update(RUSSIAN_MAP)
    ALL_DOWNCODE_MAPS.update(UKRAINIAN_MAP)
    ALL_DOWNCODE_MAPS.update(CZECH_MAP)
    ALL_DOWNCODE_MAPS.update(POLISH_MAP)
    ALL_DOWNCODE_MAPS.update(LATVIAN_MAP)
    
    s = u"".join(ALL_DOWNCODE_MAPS.keys())
    regex = re.compile(u"[%s]|[^%s]+" % (s,s))
    
    return ALL_DOWNCODE_MAPS, regex


_MAPINGS = None
_regex = None
def downcode(s):
    """
    This function is 'downcode' the string pass in the parameter s. This is useful 
    in cases we want the closest representation, of a multilingual string, in simple
    latin chars. The most probable use is before calling slugify.
    """
    global _MAPINGS, _regex

    if not _regex:
        _MAPINGS, _regex = _makeRegex()    

    downcoded = ""
    for piece in _regex.findall(s):
        if _MAPINGS.has_key(piece):
            downcoded += _MAPINGS[piece]
        else:
            downcoded += piece
    return downcoded


def slugify_downcode(value):
    return slugify(downcode(value))


def slugify_unique(value, doc, slugfield="slug"):
    potential = base = slugify_downcode(value)
    suffix = 0
    while True:
        if suffix:
            potential = "-".join([base, str(suffix)])
        if not doc.objects.filter(**{slugfield: potential}).count():
            return potential
        suffix += 1
"""
slugify_unique - end
"""

# VARIOUS UTILS

def flatten(lst):
    # WARNING! Finish it so that it would be real flatten (for dictionaries - not just keys)
    for element in lst:
        if isinstance(element, collections.Iterable) and \
          not isinstance(element, basestring):
            for sub in flatten(element):
                yield sub
        else:
            yield element


def ensure_list(val, flat=False):
    """
    Convert strings, floats, etc. to list.
    """
    try:
        return [float(val)]
    except TypeError, ValueError:
        if hasattr(val, '__getitem__') and (not hasattr(val, '__iter__')):
            return [val] # string
        elif hasattr(val, '__getitem__') and hasattr(val, '__iter__'):
            if isinstance(val, dict):
                if flat:
                    return [l for l in flatten(val)]
                return [val]
            return list(val)
    except Exception as e: # unsuccessfull!
        return []
