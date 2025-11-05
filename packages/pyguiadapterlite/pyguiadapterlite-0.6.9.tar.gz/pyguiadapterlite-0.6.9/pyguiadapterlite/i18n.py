import gettext
import locale
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from pyguiadapterlite.assets import locales_dir

_DEFAULT_LOCALE_DIR = locales_dir().as_posix()
_DEFAULT_DOMAIN = "pyguiadapterlite"
_DEFAULT_LOCALE = "en_US"

ENV_AUTO_EXPORT = "PYGUIADAPTERLITE_EXPORT_LOCALES"
ENV_LOCALE = "PYGUIADAPTERLITE_LOCALE"
ENV_LOCALE_DIR = "PYGUIADAPTERLITE_LOCALE_DIR"
ENV_DOMAIN = "PYGUIADAPTERLITE_DOMAIN"


class SystemLocaleDetector(object):
    def __init__(self):
        self._system = platform.system().lower()

    def detect(self, default: str = _DEFAULT_LOCALE) -> str:
        if self._system == "linux":
            return self._detect_linux() or default
        elif self._system == "darwin":
            return self._detect_macos() or default
        elif self._system == "windows":
            return self._detect_windows() or default
        else:
            return self._detect_other() or default

    def detect_language_code(
        self, fallback_locale: str = _DEFAULT_LOCALE
    ) -> Optional[str]:
        locale_str = self.detect(fallback_locale).strip()
        if locale_str and "_" in locale_str:
            return locale_str.split("_")[0]
        return locale_str or None

    def detect_country_code(
        self, fallback_locale: str = _DEFAULT_LOCALE
    ) -> Optional[str]:
        locale_str = self.detect(fallback_locale)
        if locale_str and "_" in locale_str:
            return locale_str.split("_")[1]
        return None

    @staticmethod
    def _detect_linux() -> Optional[str]:
        # 检查多个环境变量
        env_vars = ["LC_ALL", "LC_CTYPE", "LANG", "LANGUAGE"]
        for var in env_vars:
            value = os.environ.get(var)
            if value and value != "C" and value != "POSIX":
                return value
        # 使用locale命令
        try:
            result = subprocess.run(["locale"], capture_output=True, text=True)
            if result.returncode != 0:
                return None
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("LANG=") or line.startswith("LC_CTYPE="):
                    return line.split("=")[1].strip().strip('"')
            return None
        except BaseException as e:
            print("failed to detect system locale on Linux")
            print(e)
            return None

    @staticmethod
    def _detect_macos() -> Optional[str]:
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleLocale"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except BaseException as e:
            print("failed to detect system locale on macOS")
            print(e)
            return None

    @staticmethod
    def _detect_windows() -> Optional[str]:
        try:
            import ctypes

            # noinspection PyUnresolvedReferences
            lcid = ctypes.windll.kernel32.GetUserDefaultLCID()
            return locale.windows_locale.get(lcid, None)
        except BaseException as e:
            print("failed to detect system locale on Windows")
            print(e)
            return None

    @staticmethod
    def _detect_other() -> Optional[str]:
        try:
            return locale.getdefaultlocale()[0] or None
        except BaseException as e:
            print("failed to detect system locale on other system")
            print(e)


_default_detector = SystemLocaleDetector()


def export_locale_dir(target_dir: str, overwrite: bool = False) -> None:
    """导出翻译文件到指定目录"""
    target_dir = Path(target_dir)
    if target_dir.is_dir() and not overwrite:
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(locales_dir(), target_dir, dirs_exist_ok=True)


class I18N:
    def __init__(
        self,
        domain: Optional[str] = None,
        localedir: Optional[str] = None,
        locale_code: Optional[str] = None,
    ):

        self._domain: str = ""
        self._localedir: str = ""
        self._current_locale: str = ""
        self._translation: Optional[gettext.NullTranslations] = None

        self.set_locale(locale_code, domain, localedir)

    def set_locale_dir(self, localedir: str) -> None:
        if not os.path.exists(localedir):
            os.makedirs(localedir, exist_ok=True)
        self._localedir = localedir

    def get_locale_dir(self) -> str:
        return self._localedir

    def set_locale(
        self,
        locale_code: Optional[str] = None,
        domain: Optional[str] = None,
        localedir: Optional[str] = None,
    ) -> None:
        if not (domain and domain.strip()):
            domain = os.environ.get(ENV_DOMAIN, _DEFAULT_DOMAIN)
        self._domain = domain

        if not (localedir and localedir.strip()):
            localedir = os.environ.get(ENV_LOCALE_DIR, _DEFAULT_LOCALE_DIR)
        if not os.path.isdir(localedir):
            # 如果翻译文件目录不存在，则创建目录
            os.makedirs(localedir, exist_ok=True)
        # 如果翻译文件目录不为空，且环境变量要求自动导出，则导出内置翻译文件
        export_locales = os.environ.get(ENV_AUTO_EXPORT, "false").lower() == "true"
        if export_locales and not os.listdir(localedir):
            export_locale_dir(localedir, overwrite=True)
            print(f"exporting built-in locales to {localedir}")
        self._localedir = localedir

        locale_code = os.environ.get(ENV_LOCALE, locale_code)
        locale_code = (locale_code or "").strip()
        if locale_code.lower() == "auto" or locale_code == "":
            locale_code = _default_detector.detect()
        self._current_locale = locale_code

        try:
            self._translation = gettext.translation(
                self._domain,
                localedir=self._localedir,
                languages=[self._current_locale],
                fallback=True,
            )
            # self._translation.install()
        except FileNotFoundError:
            # 如果找不到翻译文件，使用空翻译
            self._translation = gettext.NullTranslations()
            # self._translation.install()
        # print(f"setlocale: {self._localedir}, {self._domain}, {locale_code}")

    def gettext(self, message: str) -> str:
        if self._translation:
            return self._translation.gettext(message)
        return message

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        if self._translation:
            return self._translation.ngettext(singular, plural, n)
        return singular if n == 1 else plural

    # 简化方法别名
    def _(self, message: str) -> str:
        """gettext 的简写形式"""
        return self.gettext(message)

    def _n(self, singular: str, plural: str, n: int) -> str:
        """ngettext 的简写形式"""
        return self.ngettext(singular, plural, n)


# 创建全局实例
_default_i18n = I18N()


def detect_system_locale(fallback: str = _DEFAULT_LOCALE) -> str:
    return _default_detector.detect(fallback)


def detect_system_language_code(
    fallback_locale: str = _DEFAULT_LOCALE,
) -> Optional[str]:
    return _default_detector.detect_language_code(fallback_locale)


def detect_system_country_code(fallback_locale: str = _DEFAULT_LOCALE) -> Optional[str]:
    return _default_detector.detect_country_code(fallback_locale)


def tr_(message: str) -> str:
    """翻译字符串"""
    return _default_i18n.gettext(message)


def ntr_(singular: str, plural: str, n: int) -> str:
    """翻译单复数字符串"""
    return _default_i18n.ngettext(singular, plural, n)
