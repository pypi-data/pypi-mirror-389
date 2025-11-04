from typing import Any, NoReturn

from promium.exceptions import PromiumException


class BaseElementConditionWithRefresh:
    def __init__(self, element: Any, with_refresh: bool = False) -> None:
        self.element = element
        self.with_refresh = with_refresh

    def call_method(self) -> NoReturn:
        raise PromiumException("Not implemented")

    def __call__(self, driver: Any) -> bool:
        if self.with_refresh:
            driver.refresh()
        return self.call_method()


class ElementPresent(BaseElementConditionWithRefresh):
    def call_method(self) -> bool:
        return bool(self.element.is_present())


is_present = ElementPresent


class ElementNotPresent(BaseElementConditionWithRefresh):
    def call_method(self) -> bool:
        return not self.element.is_present()


is_not_present = ElementNotPresent


class ElementIsDisplay(BaseElementConditionWithRefresh):
    def call_method(self) -> bool:
        return bool(self.element.is_displayed())


is_display = ElementIsDisplay


class ElementNotDisplay(BaseElementConditionWithRefresh):
    def call_method(self) -> bool:
        return not self.element.is_displayed()


is_not_display = ElementNotDisplay


class ElementText(BaseElementConditionWithRefresh):
    def __init__(
        self,
        element: Any,
        text: str,
        with_refresh: bool = False,
    ) -> None:
        super().__init__(element, with_refresh)
        self.text = text

    def call_method(self) -> bool:
        return self.element.text == self.text


is_text = ElementText


class ElementTextContain(ElementText):
    def call_method(self) -> bool:
        return self.text in self.element.text


is_text_contain = ElementTextContain


class ElementTextNotContain(ElementText):
    def call_method(self) -> bool:
        return self.text not in self.element.text


is_text_not_contain = ElementTextNotContain
