import os
from typing import Any, Never

from selenium.webdriver import DesiredCapabilities, FirefoxProfile
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.ie.options import Options as IeOptions

from promium.device_config import CHROME_DESKTOP_1024_768, CustomDevice


BASE_CAPABILITIES = {
    "loggingPrefs": {
        "performance": "ALL",
        "server": "ALL",
        "client": "ALL",
        "driver": "ALL",
        "browser": "ALL",
    }
}


def get_download_path() -> str:
    return os.environ.get("DOWNLOAD_PATH", "/tmp")


class SettingsDrivers:
    @staticmethod
    def chrome() -> "SettingsChrome":
        return SettingsChrome()

    @staticmethod
    def firefox() -> "SettingsFirefox":
        return SettingsFirefox()

    @staticmethod
    def opera() -> "SettingsOpera":
        return SettingsOpera()

    @staticmethod
    def ie() -> "SettingsIE":
        return SettingsIE()

    @staticmethod
    def edge() -> "SettingsEDGE":
        return SettingsEDGE()

    @classmethod
    def get(cls, browser_name: str) -> Any:
        name = browser_name.lower()
        if hasattr(cls, name):
            method = getattr(cls, name)
            return method()
        raise ValueError(f"Not correct browser name {name}")


class Base:
    driver_capabilities = {}
    binary_path = ""
    device = CHROME_DESKTOP_1024_768
    default_options = []
    user_options = []
    default_exp_options = {}
    user_exp_options = {}
    default_capabilities = BASE_CAPABILITIES.copy()
    user_capabilities = {}
    default_preferences = {}
    user_preferences = {}

    @classmethod
    def driver_options(cls) -> Never:
        raise NotImplementedError

    @classmethod
    def options(cls) -> list[str]:
        return cls.user_options or cls.default_options

    @classmethod
    def experimental_options(cls) -> dict[str, Any]:
        return cls.user_exp_options or cls.default_exp_options

    @classmethod
    def capabilities(cls) -> dict[str, Any]:
        return cls.user_capabilities or cls.default_capabilities

    @classmethod
    def preference(cls) -> dict[str, Any]:
        return cls.user_preferences or cls.default_preferences

    @classmethod
    def set_custom_device(
        cls,
        width: str = "",
        height: str = "",
        pixel_ratio: float = 1.0,
        user_agent: str = "",
    ) -> Any:
        """
        Set browser windows size and user agent
        :param int width: for example 1024
        :param int height: for example 768
        :param str device_name: for example Nexus 5
        :param str user_agent: not required param
        :return: namedtuple
        """
        cls.device = CustomDevice(
            width=width,
            height=height,
            pixel_ratio=pixel_ratio,
            user_agent=user_agent,
        )
        return cls.device

    @classmethod
    def set_options(cls, *args: str) -> list[str]:
        """
        set browser option, not use default
        :param args: fot example --no-sandbox, --test-type, ...,
        :return: list[str]
        """
        cls.user_options.extend(args)
        return cls.user_options

    @classmethod
    def add_option(cls, option: str) -> list[str]:
        """
        add browser options to default
        :param str option: for example --headless
        :return: list[str]
        """
        cls.default_options.append(option)
        return cls.default_options

    @classmethod
    def delete_option(cls, option: str) -> list[str]:
        """
        deleted browser options from default
        :param str option: for example --verbose
        :return: list[str]
        """
        cls.default_options.remove(option)
        return cls.default_options

    @classmethod
    def set_windows_size(
        cls, device: tuple[str, str, float, str] | None = None
    ) -> list[str]:
        if device:
            cls.set_custom_device(*device)

        if cls.device.user_agent:
            cls.add_option(f"--user-agent={cls.device.user_agent}")

        cls.add_option(f"--window-size={cls.device.width},{cls.device.height}")
        return cls.default_options

    @classmethod
    def get_options(cls) -> ChromeOptions:
        cls.set_windows_size()
        driver_options = cls.driver_options()
        for option in cls.options():
            driver_options.add_argument(option)

        for exp_key, exp_option in cls.experimental_options().items():
            driver_options.add_experimental_option(exp_key, exp_option)

        if os.getenv("HEADLESS") == "Enabled":
            driver_options.add_argument("--headless")

        return driver_options

    @classmethod
    def get_capabilities(cls) -> dict[str, Any]:
        cap = cls.driver_capabilities.copy()
        for key, value in cls.capabilities().items():
            cap[key] = value
        return cap

    @classmethod
    def set_preferences(cls, **kwargs: Any) -> dict[str, Any]:
        cls.user_preferences.update(kwargs)
        return cls.user_preferences

    @classmethod
    def update_preferences(cls, **kwargs: Any) -> dict[str, Any]:
        for key, value in kwargs.items():
            cls.default_preferences[key] = value
        return cls.default_preferences

    @classmethod
    def delete_preference(cls, key: str) -> dict[str, Any]:
        cls.default_preferences.pop(key)
        return cls.default_preferences

    @classmethod
    def get_preferences(cls) -> None:
        return None

    def __str__(self) -> str:
        return self.__class__.__name__


class SettingsChrome(Base):
    driver_capabilities = DesiredCapabilities.CHROME
    binary_path = "/usr/bin/chromedriver"
    default_options = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--no-default-browser-check",
        "--dns-prefetch-disable",
        "--no-first-run",
        "--verbose",
        "--enable-logging --v=1",
        "--test-type",
        "--ignore-certificate-errors",
        "--disable-notifications",
        "--disable-gpu",
    ]
    default_exp_options = {
        "prefs": {
            "download.default_directory": get_download_path(),
            "download.directory_upgrade": True,
            "prompt_for_download": False,
        }
    }

    @classmethod
    def driver_options(cls) -> ChromeOptions:
        return ChromeOptions()


class SettingsOpera(SettingsChrome):
    # TODO need fix
    # binary_path = '/usr/bin/operadriver'
    binary_path = "/usr/bin/opera"

    @classmethod
    def get_options(cls) -> ChromeOptions:
        cls.set_windows_size()
        driver_options = cls.driver_options()
        for option in cls.options():
            driver_options.add_argument(option)

        for exp_key, exp_option in cls.experimental_options().items():
            driver_options.add_experimental_option(exp_key, exp_option)

        if os.getenv("HEADLESS") == "Enabled":
            driver_options.add_argument("--headless")

        driver_options._binary_location = cls.binary_path
        return driver_options


class SettingsFirefox(Base):
    driver_capabilities = DesiredCapabilities.FIREFOX
    binary_path = "/usr/bin/gekodriver"
    default_options = ["-no-remote"]
    default_preferences = {
        "browser.startup.homepage": "about:blank",
        "browser.download.folderList": 2,
        "browser.download.manager.showWhenStarting": False,
        "browser.download.dir": get_download_path(),
        "browser.helperApps.neverAsk.saveToDisk": "application/zip",
        "startup.homepage_welcome_url": "about:blank",
        "startup.homepage_welcome_url.additional": "about:blank",
        "pdfjs.disabled": True,
    }

    @classmethod
    def driver_options(cls) -> FirefoxOptions:
        return FirefoxOptions()

    @classmethod
    def set_windows_size(
        cls, device: tuple[str, str, float, str] | None = None
    ) -> list[str]:
        if device:
            cls.set_custom_device(*device)

        cls.add_option(f"-width {cls.device.width}")
        cls.add_option(f"-height {cls.device.height}")
        return cls.default_options

    @classmethod
    def get_options(cls) -> FirefoxOptions:
        cls.set_windows_size()
        driver_options = cls.driver_options()
        for option in cls.options():
            driver_options.add_argument(option)

        if os.getenv("HEADLESS") == "Enabled":
            driver_options.add_argument("-headless")

        return driver_options

    @classmethod
    def get_preferences(cls) -> FirefoxProfile:
        profile = FirefoxProfile()
        for key, value in cls.preference().items():
            profile.set_preference(key=key, value=value)

        if cls.device.user_agent:
            profile.set_preference(
                key="general.useragent.override", value=cls.device.user_agent
            )
        profile.update_preferences()
        return profile


class SettingsIE(Base):
    driver_capabilities = DesiredCapabilities.INTERNETEXPLORER
    binary_path = "/usr/bin/iedriver"

    @classmethod
    def driver_options(cls) -> IeOptions:
        return IeOptions()

    @classmethod
    def get_options(cls) -> IeOptions:
        driver_options = cls.driver_options()
        for option in cls.options():
            driver_options.add_argument(option)

        return driver_options


class SettingsEDGE(Base):
    driver_capabilities = DesiredCapabilities.EDGE
    binary_path = "/usr/bin/edgedriver"

    @classmethod
    def driver_options(cls) -> EdgeOptions:
        return EdgeOptions()

    @classmethod
    def get_options(cls) -> EdgeOptions:
        return cls.driver_options()
