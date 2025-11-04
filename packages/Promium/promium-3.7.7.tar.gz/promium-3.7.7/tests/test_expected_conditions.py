from unittest.mock import MagicMock

import pytest

from promium.exceptions import PromiumException
from promium.expected_conditions import (
    BaseElementConditionWithRefresh,
    ElementIsDisplay,
    ElementNotDisplay,
    ElementNotPresent,
    ElementPresent,
    ElementText,
    ElementTextContain,
    ElementTextNotContain,
    is_display,
    is_not_display,
    is_not_present,
    is_present,
    is_text,
    is_text_contain,
    is_text_not_contain,
)


@pytest.fixture
def mock_element():
    """Mock element for testing."""
    return MagicMock(
        name="element",
        spec=[
            "is_present",
            "is_displayed",
            "text",
            "_find_elements",
        ],
    )


@pytest.fixture
def mock_driver():
    """Mock driver for testing."""
    return MagicMock(name="driver", **{"refresh.return_value": None})


@pytest.mark.unit
def test_base_element_condition_with_refresh_init(mock_element):
    """Test BaseElementConditionWithRefresh initialization."""
    condition = BaseElementConditionWithRefresh(mock_element)

    assert condition.element == mock_element
    assert condition.with_refresh is False


@pytest.mark.unit
def test_base_element_condition_with_refresh_true_init(mock_element):
    """Test BaseElementConditionWithRefresh initialization with refresh."""
    condition = BaseElementConditionWithRefresh(mock_element, with_refresh=True)

    assert condition.element == mock_element
    assert condition.with_refresh is True


@pytest.mark.unit
def test_base_element_condition_call_method_not_implemented():
    """Test BaseElementConditionWithRefresh.call_method raises exception."""
    condition = BaseElementConditionWithRefresh(MagicMock())

    with pytest.raises(PromiumException, match="Not implemented"):
        condition.call_method()


@pytest.mark.unit
def test_base_element_condition_call_without_refresh(mock_driver, mock_element):
    """Test BaseElementConditionWithRefresh __call__ without refresh."""
    class TestCondition(BaseElementConditionWithRefresh):
        def call_method(self):
            return True

    condition = TestCondition(mock_element)
    result = condition(mock_driver)

    assert result is True
    mock_driver.refresh.assert_not_called()


@pytest.mark.unit
def test_base_element_condition_call_with_refresh(mock_driver, mock_element):
    """Test BaseElementConditionWithRefresh __call__ with refresh."""
    class TestCondition(BaseElementConditionWithRefresh):
        def call_method(self):
            return True

    condition = TestCondition(mock_element, with_refresh=True)
    result = condition(mock_driver)

    assert result is True
    mock_driver.refresh.assert_called_once()


@pytest.mark.unit
@pytest.mark.parametrize(("is_present_value", "expected"), [
    (True, True),
    (False, False),
])
def test_element_present_call_method(mock_element, is_present_value, expected):
    """Test ElementPresent.call_method."""
    mock_element.is_present.return_value = is_present_value
    condition = ElementPresent(mock_element)

    result = condition.call_method()

    assert result == expected
    mock_element.is_present.assert_called_once()


@pytest.mark.unit
def test_element_present_returns_bool(mock_element):
    """Test ElementPresent always returns bool."""
    mock_element.is_present.return_value = None
    condition = ElementPresent(mock_element)

    result = condition.call_method()

    assert result is False
    assert isinstance(result, bool)


@pytest.mark.unit
def test_is_present_alias():
    """Test is_present is an alias for ElementPresent."""
    assert is_present is ElementPresent


@pytest.mark.unit
@pytest.mark.parametrize(("is_present_value", "expected"), [
    (True, False),
    (False, True),
])
def test_element_not_present_call_method(
    mock_element: MagicMock,
    is_present_value: bool,
    expected: bool,
):
    """Test ElementNotPresent.call_method."""
    mock_element.is_present.return_value = is_present_value
    condition = ElementNotPresent(mock_element)

    result = condition.call_method()

    assert result == expected
    mock_element.is_present.assert_called_once()


@pytest.mark.unit
def test_is_not_present_alias():
    """Test is_not_present is an alias for ElementNotPresent."""
    assert is_not_present is ElementNotPresent


@pytest.mark.unit
@pytest.mark.parametrize(("is_displayed_value", "expected"), [
    (True, True),
    (False, False),
])
def test_element_is_display_call_method(
    mock_element: MagicMock,
    is_displayed_value: bool,
    expected: bool,
):
    """Test ElementIsDisplay.call_method."""
    mock_element.is_displayed.return_value = is_displayed_value
    condition = ElementIsDisplay(mock_element)

    result = condition.call_method()

    assert result == expected
    mock_element.is_displayed.assert_called_once()


@pytest.mark.unit
def test_element_is_display_returns_bool(mock_element):
    """Test ElementIsDisplay always returns bool."""
    mock_element.is_displayed.return_value = None
    condition = ElementIsDisplay(mock_element)

    result = condition.call_method()

    assert result is False
    assert isinstance(result, bool)


@pytest.mark.unit
def test_is_display_alias():
    """Test is_display is an alias for ElementIsDisplay."""
    assert is_display is ElementIsDisplay


@pytest.mark.unit
@pytest.mark.parametrize(("is_displayed_value", "expected"), [
    (True, False),
    (False, True),
])
def test_element_not_display_call_method(
    mock_element: MagicMock,
    is_displayed_value: bool,
    expected: bool,
):
    """Test ElementNotDisplay.call_method."""
    mock_element.is_displayed.return_value = is_displayed_value
    condition = ElementNotDisplay(mock_element)

    result = condition.call_method()

    assert result == expected
    mock_element.is_displayed.assert_called_once()


@pytest.mark.unit
def test_is_not_display_alias():
    """Test is_not_display is an alias for ElementNotDisplay."""
    assert is_not_display is ElementNotDisplay


@pytest.mark.unit
@pytest.mark.parametrize(("element_text", "expected_text", "expected"), [
    ("Hello", "Hello", True),
    ("Hello", "World", False),
    ("", "", True),
])
def test_element_text_call_method(
    mock_element: MagicMock,
    element_text: str,
    expected_text: str,
    expected: bool,
):
    """Test ElementText.call_method."""
    mock_element.text = element_text
    condition = ElementText(mock_element, expected_text)

    result = condition.call_method()

    assert result == expected


@pytest.mark.unit
def test_element_text_init(mock_element):
    """Test ElementText initialization."""
    condition = ElementText(mock_element, "test text")

    assert condition.element == mock_element
    assert condition.text == "test text"
    assert condition.with_refresh is False


@pytest.mark.unit
def test_element_text_init_with_refresh(mock_element):
    """Test ElementText initialization with refresh."""
    condition = ElementText(mock_element, "test text", with_refresh=True)

    assert condition.element == mock_element
    assert condition.text == "test text"
    assert condition.with_refresh is True


@pytest.mark.unit
def test_is_text_alias():
    """Test is_text is an alias for ElementText."""
    assert is_text is ElementText


@pytest.mark.unit
@pytest.mark.parametrize(("element_text", "search_text", "expected"), [
    ("Hello World", "Hello", True),
    ("Hello World", "Hi", False),
    ("Hello", "Hello World", False),
    ("", "Hello", False),
    ("Hello", "", True),
])
def test_element_text_contain_call_method(
    mock_element: MagicMock,
    element_text: str,
    search_text: str,
    expected: bool,
):
    """Test ElementTextContain.call_method."""
    mock_element.text = element_text
    condition = ElementTextContain(mock_element, search_text)

    result = condition.call_method()

    assert result == expected


@pytest.mark.unit
def test_is_text_contain_alias():
    """Test is_text_contain is an alias for ElementTextContain."""
    assert is_text_contain is ElementTextContain


@pytest.mark.unit
@pytest.mark.parametrize(("element_text", "search_text", "expected"), [
    ("Hello World", "Hello", False),
    ("Hello World", "Hi", True),
    ("Hello", "Hello World", True),
    ("", "Hello", True),
    ("Hello", "", False),
])
def test_element_text_not_contain_call_method(
    mock_element: MagicMock,
    element_text: str,
    search_text: str,
    expected: bool,
):
    """Test ElementTextNotContain.call_method."""
    mock_element.text = element_text
    condition = ElementTextNotContain(mock_element, search_text)

    result = condition.call_method()

    assert result == expected


@pytest.mark.unit
def test_is_text_not_contain_alias():
    """Test is_text_not_contain is an alias for ElementTextNotContain."""
    assert is_text_not_contain is ElementTextNotContain


@pytest.mark.unit
def test_element_present_with_refresh(mock_driver, mock_element):
    """Test ElementPresent with refresh flag."""
    mock_element.is_present.return_value = True
    condition = ElementPresent(mock_element, with_refresh=True)

    result = condition(mock_driver)

    assert result is True
    mock_element.is_present.assert_called_once()
    mock_driver.refresh.assert_called_once()


@pytest.mark.unit
def test_element_text_inheritance():
    """Test ElementTextContain and ElementTextNotContain
    inherit from ElementText."""
    assert issubclass(ElementTextContain, ElementText)
    assert issubclass(ElementTextNotContain, ElementText)


@pytest.mark.unit
def test_element_text_contain_inherits_text_attribute(mock_element):
    """Test ElementTextContain inherits text attribute."""
    condition = ElementTextContain(mock_element, "test")

    assert condition.text == "test"
    assert condition.element == mock_element


@pytest.mark.unit
def test_element_text_not_contain_inherits_text_attribute(mock_element):
    """Test ElementTextNotContain inherits text attribute."""
    condition = ElementTextNotContain(mock_element, "test")

    assert condition.text == "test"
    assert condition.element == mock_element
