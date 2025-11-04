from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select

from promium.base import Element


class MultiSelectListBox(Element):
    @property
    def listbox(self) -> Select:
        return Select(self.lookup())

    @property
    def options(self) -> list[WebElement]:
        """Gets drop down options list"""
        return self.listbox.options

    def deselect_all(self) -> None:
        """Deselects all options"""
        for opt in self.options:
            if opt.is_selected():
                opt.click()

    def select_by_visible_text(self, text: str) -> None:
        """Selects the option by the visible_text"""
        return self.listbox.select_by_visible_text(text)
