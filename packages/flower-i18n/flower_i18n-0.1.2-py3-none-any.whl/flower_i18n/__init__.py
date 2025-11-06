"""
Flower i18n - Internationalization support for Flower Celery monitoring tool
"""

__version__ = "0.1.2"
__author__ = "邹长林 (Zou Changlin)"
__email__ = "zchanglin@163.com"

from .i18n import I18nHandler, setup_i18n

__all__ = ['I18nHandler', 'setup_i18n', '__version__']