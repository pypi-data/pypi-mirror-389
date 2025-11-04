import pytest

from promium.exceptions import (
    BrowserConsoleException,
    ElementLocationException,
    LocatorException,
    PromiumException,
    PromiumTimeout,
)


@pytest.mark.unit
def test_promium_exception():
    """Test PromiumException base class."""
    exc = PromiumException()
    assert isinstance(exc, Exception)
    assert isinstance(exc, PromiumException)

    message = "Test error message"
    exc = PromiumException(message)
    assert str(exc) == message
    assert exc.args == (message,)


@pytest.mark.unit
def test_promium_timeout_with_default_parameters():
    """Test PromiumTimeout with default parameters."""
    exc = PromiumTimeout()

    assert isinstance(exc, PromiumException)
    assert isinstance(exc, PromiumTimeout)
    assert exc.message == "no error message (waited 10 seconds)"
    assert str(exc) == "no error message (waited 10 seconds)"


@pytest.mark.unit
def test_promium_timeout_with_screenshot():
    """Test PromiumTimeout with screenshot parameter."""
    exc = PromiumTimeout(
        message="Timeout occurred",
        seconds=20,
        screen="screenshot_data"
    )

    expected_message = (
        "Timeout occurred (waited 20 seconds)"
        "Screenshot: available via screen\n"
    )
    assert exc.message == expected_message
    assert str(exc) == expected_message


@pytest.mark.unit
def test_promium_timeout_with_screenshot_none():
    """Test PromiumTimeout with screenshot parameter set to None."""
    exc = PromiumTimeout(
        message="Timeout occurred",
        seconds=20,
        screen=None
    )

    expected_message = "Timeout occurred (waited 20 seconds)"
    assert exc.message == expected_message
    assert str(exc) == expected_message


@pytest.mark.unit
def test_promium_timeout_with_empty_screenshot():
    """Test PromiumTimeout with empty screenshot parameter."""
    exc = PromiumTimeout(
        message="Timeout occurred",
        seconds=20,
        screen=""
    )

    expected_message = "Timeout occurred (waited 20 seconds)"
    assert exc.message == expected_message
    assert str(exc) == expected_message


@pytest.mark.unit
def test_element_location_exception():
    """Test ElementLocationException."""
    exc = ElementLocationException()
    assert isinstance(exc, Exception)
    assert isinstance(exc, PromiumException)
    assert isinstance(exc, ElementLocationException)

    message = "Element not found"
    exc = ElementLocationException(message)
    assert str(exc) == message
    assert exc.args == (message,)


@pytest.mark.unit
def test_locator_exception():
    """Test LocatorException."""
    exc = LocatorException()
    assert isinstance(exc, Exception)
    assert isinstance(exc, PromiumException)
    assert isinstance(exc, LocatorException)

    message = "Invalid locator"
    exc = LocatorException(message)
    assert str(exc) == message
    assert exc.args == (message,)


@pytest.mark.unit
def test_browser_console_exception():
    """Test BrowserConsoleException."""
    exc = BrowserConsoleException()
    assert isinstance(exc, Exception)
    assert isinstance(exc, PromiumException)
    assert isinstance(exc, BrowserConsoleException)

    message = "Browser console error"
    exc = BrowserConsoleException(message)
    assert str(exc) == message
    assert exc.args == (message,)


@pytest.mark.unit
def test_exception_inheritance_hierarchy():
    """Test that all custom exceptions inherit from PromiumException."""
    exceptions = [
        PromiumTimeout,
        ElementLocationException,
        LocatorException,
        BrowserConsoleException,
    ]

    for exc_class in exceptions:
        exc = exc_class("test message")
        assert isinstance(exc, PromiumException)
        assert isinstance(exc, Exception)


@pytest.mark.unit
def test_promium_timeout_exception_attributes():
    """Test PromiumTimeout specific attributes and behavior."""
    message = "Custom timeout message"
    seconds = 25
    screen = "base64_screenshot_data"

    exc = PromiumTimeout(message=message, seconds=seconds, screen=screen)

    assert hasattr(exc, "message")
    expected_msg = (
        f"{message} (waited {seconds} seconds)"
        "Screenshot: available via screen\n"
    )
    assert exc.message == expected_msg

    assert str(exc) == exc.message

    with pytest.raises(PromiumTimeout) as exc_info:
        raise exc
    assert exc_info.value.message == exc.message
    assert str(exc_info.value) == exc.message
