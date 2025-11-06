"""
Core i18n functionality for Flower
"""

import json
import os
from typing import Dict, Optional
from pathlib import Path


class I18n:
    """Internationalization handler for Flower"""

    def __init__(self, default_locale: str = "en_US"):
        self.default_locale = default_locale
        self.current_locale = default_locale
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """Load all translation files"""
        locales_dir = Path(__file__).parent / "locales"

        for locale_dir in locales_dir.iterdir():
            if locale_dir.is_dir():
                locale_name = locale_dir.name
                translation_file = locale_dir / "messages.json"

                if translation_file.exists():
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[locale_name] = json.load(f)

    def set_locale(self, locale: str):
        """Set current locale"""
        if locale in self.translations:
            self.current_locale = locale
        else:
            print(f"Warning: Locale '{locale}' not found, using default '{self.default_locale}'")

    def get(self, key: str, locale: Optional[str] = None) -> str:
        """Get translation for a key"""
        target_locale = locale or self.current_locale

        # Try to get translation for target locale
        if target_locale in self.translations:
            translation = self.translations[target_locale].get(key)
            if translation:
                return translation

        # Fallback to default locale
        if self.default_locale in self.translations:
            translation = self.translations[self.default_locale].get(key)
            if translation:
                return translation

        # Return key if no translation found
        return key

    def get_available_locales(self) -> list:
        """Get list of available locales"""
        return list(self.translations.keys())


# Global i18n instance
_i18n_instance = None


def get_i18n() -> I18n:
    """Get global i18n instance"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


class I18nHandler:
    """Mixin for Tornado handlers to support i18n"""

    def get_user_locale(self):
        """Get user's preferred locale from cookie or browser"""
        # Check cookie first
        locale = self.get_cookie("flower_locale")
        if locale:
            return locale

        # Check Accept-Language header
        accept_language = self.request.headers.get("Accept-Language", "")
        if accept_language:
            # Parse Accept-Language header (simple implementation)
            languages = accept_language.split(",")
            if languages:
                primary_lang = languages[0].split(";")[0].strip()
                # Convert en-US to en_US
                primary_lang = primary_lang.replace("-", "_")

                # Check if we support this locale
                i18n = get_i18n()
                if primary_lang in i18n.get_available_locales():
                    return primary_lang

                # Try just the language code
                lang_code = primary_lang.split("_")[0]
                for locale in i18n.get_available_locales():
                    if locale.startswith(lang_code):
                        return locale

        return "en_US"

    def set_user_locale(self, locale: str):
        """Set user's locale preference"""
        self.set_cookie("flower_locale", locale, expires_days=365)

    def _(self, key: str) -> str:
        """Translate a key to current locale"""
        i18n = get_i18n()
        locale = self.get_user_locale()
        return i18n.get(key, locale)


def setup_i18n(app):
    """Setup i18n for Flower application"""
    # Initialize global i18n instance
    i18n = get_i18n()

    # Add i18n helper to template namespace
    def translate_helper(key: str) -> str:
        """Template helper for translation"""
        return i18n.get(key)

    # This will be used in templates
    return {
        '_': translate_helper,
        'i18n': i18n
    }