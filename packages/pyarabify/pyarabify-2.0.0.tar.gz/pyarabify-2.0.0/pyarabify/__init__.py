__version__ = "2.0.0"
__author__ = "MERO"
__telegram__ = "QP4RM"
__github__ = "https://github.com/6x-u"

from .src.prs import ArabicParser
from .src.exe import execute, execute_file
from .src.cvt import to_english, to_arabic
from .src.err import ArabicError

from .src import git
from .src import web
from .src.pkg import تحميل, حمل, ثبت, نزل

__all__ = [
    'ArabicParser',
    'execute',
    'execute_file',
    'to_english',
    'to_arabic',
    'ArabicError',
    'git',
    'web',
    'تحميل',
    'حمل',
    'ثبت',
    'نزل'
]
