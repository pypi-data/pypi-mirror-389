import os
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import WebDriverException

from promium.exceptions import PromiumException
from promium.test_case import (
    RequestTestCase,
    TDPException,
    TDPHandler,
    TestCase,
    WebDriverTestCase,
    create_driver,
    timeout,
)


@pytest.fixture
def mock_driver():
    """Mock driver for testing."""
    return MagicMock(
        name="driver",
        **{
            "get.return_value": None,
            "execute_script.return_value": None,
            "session_id": "test_session",
        },
    )


@pytest.fixture
def mock_session():
    """Mock session for testing."""
    return MagicMock(
        name="session",
        **{
            "url": None,
            "status_code": None,
            "request.return_value": MagicMock(status=200),
        },
    )


@pytest.mark.unit
def test_timeout_decorator_success():
    """Test timeout decorator with successful execution."""
    @timeout(seconds=1)
    def quick_function():
        return "success"

    result = quick_function()
    assert result == "success"


@pytest.mark.unit
def test_timeout_decorator_with_custom_error_message():
    """Test timeout decorator with custom error message."""
    custom_message = "Custom timeout error"

    @timeout(seconds=1, error_message=custom_message)
    def quick_function():
        return "success"

    result = quick_function()
    assert result == "success"


@pytest.mark.unit
def test_timeout_decorator_preserves_function_metadata():
    """Test that timeout decorator preserves function metadata."""
    @timeout(seconds=1)
    def test_function(arg1, arg2=None):
        "Test function docstring."
        return f"{arg1}-{arg2}"

    assert test_function.__name__ == "test_function"
    assert test_function.__doc__ == "Test function docstring."
    assert test_function("a", "b") == "a-b"


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "chrome://", "HEADLESS": "False"})
@patch("promium.test_case.ChromeBrowser")
def test_create_driver_chrome(mock_chrome_browser, mock_driver):
    """Test create_driver with Chrome browser."""
    mock_chrome_browser.return_value = mock_driver

    result = create_driver(device="desktop")

    assert result == mock_driver
    mock_chrome_browser.assert_called_once_with(
        device="desktop",
        proxy_server=None,
        is_headless=False,
    )


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "firefox://"})
@patch("promium.test_case.FirefoxBrowser")
def test_create_driver_firefox(mock_firefox_browser, mock_driver):
    """Test create_driver with Firefox browser."""
    mock_firefox_browser.return_value = mock_driver

    result = create_driver(device="mobile")

    assert result == mock_driver
    mock_firefox_browser.assert_called_once_with(device="mobile")


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "opera://"})
@patch("promium.test_case.OperaBrowser")
def test_create_driver_opera(mock_opera_browser, mock_driver):
    """Test create_driver with Opera browser."""
    mock_opera_browser.return_value = mock_driver

    result = create_driver(device="tablet")

    assert result == mock_driver
    mock_opera_browser.assert_called_once_with(device="tablet")


@pytest.mark.unit
@patch.dict(os.environ, {
    "SE_DRIVER": "http+chrome://selenium-hub:4444/wd/hub",
    "HEADLESS": "False",
})
@patch("promium.test_case.RemoteBrowser")
def test_create_driver_remote_chrome(mock_remote_browser, mock_driver):
    """Test create_driver with remote Chrome browser."""
    mock_remote_browser.return_value = mock_driver

    result = create_driver(device="desktop")

    assert result == mock_driver
    mock_remote_browser.assert_called_once_with(
        device="desktop",
        proxy_server=None,
        is_headless=False,
        client="chrome",
        hub="http://selenium-hub:4444/wd/hub",
    )


@pytest.mark.unit
@patch.dict(os.environ, {
    "SE_DRIVER": "http+firefox://selenium-hub:4444/wd/hub",
    "HEADLESS": "False",
})
@patch("promium.test_case.RemoteBrowser")
def test_create_driver_remote_firefox(mock_remote_browser, mock_driver):
    """Test create_driver with remote Firefox browser."""
    mock_remote_browser.return_value = mock_driver

    result = create_driver(device="mobile")

    assert result == mock_driver
    mock_remote_browser.assert_called_once_with(
        device="mobile",
        proxy_server=None,
        is_headless=False,
        client="firefox",
        hub="http://selenium-hub:4444/wd/hub",
    )


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "http+chrome://selenium-hub:4444/wd/hub"})
@patch("promium.test_case.RemoteBrowser")
def test_create_driver_remote_retry_on_webdriver_exception(
        mock_remote_browser,
        mock_driver,
):
    """Test create_driver retries on WebDriverException."""
    mock_remote_browser.side_effect = [
        WebDriverException("First attempt fails"),
        mock_driver,
    ]

    result = create_driver(device="desktop")

    assert result == mock_driver
    assert mock_remote_browser.call_count == 2


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "http+chrome://selenium-hub:4444/wd/hub"})
@patch("promium.test_case.RemoteBrowser")
def test_create_driver_remote_keyerror_with_status(mock_remote_browser):
    """Test create_driver handles KeyError with status in message."""
    mock_remote_browser.side_effect = KeyError("status error")

    with pytest.raises(Exception) as exc_info:
        create_driver(device="desktop")

    assert "Session timed out" in str(exc_info.value)


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "http+chrome://selenium-hub:4444/wd/hub"})
@patch("promium.test_case.RemoteBrowser")
def test_create_driver_remote_keyerror_without_status(mock_remote_browser):
    """Test create_driver re-raises KeyError without status in message."""
    mock_remote_browser.side_effect = KeyError("other error")

    with pytest.raises(KeyError):
        create_driver(device="desktop")


@pytest.mark.unit
@patch("promium.test_case.ChromeBrowser")
def test_create_driver_no_driver_set(mock_chrome_browser, mock_driver):
    """Test create_driver uses Chrome as default when SE_DRIVER is not set."""
    # Видаляємо SE_DRIVER з середовища, якщо він там є
    with patch.dict(os.environ, {}, clear=True):
        mock_chrome_browser.return_value = mock_driver

        result = create_driver(device="desktop")

        assert result == mock_driver
        mock_chrome_browser.assert_called_once_with(
            device="desktop",
            proxy_server=None,
            is_headless=False,
        )


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "http://[invalid-url"})
def test_create_driver_invalid_url():
    """Test create_driver raises ValueError for invalid URL."""
    with pytest.raises(ValueError, match="Invalid url"):
        create_driver(device="desktop")


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "not-a-valid-url"})
def test_create_driver_unknown_driver():
    """Test create_driver raises ValueError for unknown driver."""
    with pytest.raises(ValueError, match="Unknown driver specified"):
        create_driver(device="desktop")


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "unknown://driver"})
def test_create_driver_unknown_scheme():
    """Test create_driver raises ValueError for unknown scheme."""
    with pytest.raises(ValueError, match="Unknown driver specified"):
        create_driver(device="desktop")


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "http+unknown://selenium-hub:4444/wd/hub"})
def test_create_driver_unknown_remote_client():
    """Test create_driver raises ValueError for unknown remote client."""
    with pytest.raises(ValueError, match="Unknown client specified"):
        create_driver(device="desktop")


@pytest.mark.unit
@patch.dict(os.environ, {"SE_DRIVER": "http+chrome://"})
def test_create_driver_remote_no_netloc():
    """Test create_driver raises ValueError
    when network address is not specified."""
    with pytest.raises(ValueError, match="Network address is not specified"):
        create_driver(device="desktop")


@pytest.mark.unit
@patch.dict(os.environ, {"HEADLESS": "Enabled"})
@patch.dict(os.environ, {"SE_DRIVER": "chrome://"})
@patch("promium.test_case.ChromeBrowser")
def test_create_driver_headless_mode(mock_chrome_browser, mock_driver):
    """Test create_driver with headless mode enabled."""
    mock_chrome_browser.return_value = mock_driver

    create_driver(device="desktop")

    mock_chrome_browser.assert_called_once_with(
        device="desktop",
        proxy_server=None,
        is_headless=True,
    )


@pytest.mark.unit
def test_tdp_exception():
    """Test TDPException class."""
    try:
        raise ValueError("Test error")
    except ValueError as e:
        exc_type, exc_value, exc_tb = type(e), e, e.__traceback__
        tdp_exc = TDPException(exc_type, exc_value, exc_tb)

        assert isinstance(tdp_exc, Exception)
        assert "exception caught during execution test data preparing" in str(
            tdp_exc
        )
        assert "Test error" in str(tdp_exc)


@pytest.mark.unit
def test_tdp_handler_success():
    """Test TDPHandler context manager with successful execution."""
    handler = TDPHandler()

    with handler as ctx:
        assert ctx is handler
        # No exception should be raised


@pytest.mark.unit
def test_tdp_handler_with_exception():
    """Test TDPHandler context manager with exception."""
    handler = TDPHandler()

    with pytest.raises(TDPException), handler:
        raise ValueError("Test error")


@pytest.mark.unit
def test_test_case_setup_method_no_test_case_url():
    """Test TestCase.setup_method when TEST_CASE is True
    but no test_case_url."""
    test_case = TestCase()
    test_case.test_case_url = None

    with patch.dict(os.environ, {"TEST_CASE": "True"}), pytest.raises(
        PromiumException,
        match="Test don't have a test case url",
    ):
        test_case.setup_method(None)


@pytest.mark.unit
def test_test_case_setup_method_with_test_case_url():
    """Test TestCase.setup_method when test_case_url is set."""
    test_case = TestCase()
    test_case.test_case_url = "http://example.com"

    with patch.dict(os.environ, {"TEST_CASE": "True"}):
        # Should not raise exception
        test_case.setup_method(None)


@pytest.mark.unit
def test_test_case_setup_method_test_case_false():
    """Test TestCase.setup_method when TEST_CASE is not True."""
    test_case = TestCase()
    test_case.test_case_url = None

    with patch.dict(os.environ, {"TEST_CASE": "False"}):
        # Should not raise exception
        test_case.setup_method(None)


@pytest.mark.unit
def test_test_case_tdp_handler():
    """Test TestCase.tdp_handler method."""
    test_case = TestCase()
    handler = test_case.tdp_handler()

    assert isinstance(handler, TDPHandler)


@pytest.mark.unit
def test_webdriver_test_case_get_url(mock_driver):
    """Test WebDriverTestCase.get_url method."""
    test_case = WebDriverTestCase()
    test_case.driver = mock_driver

    url = "http://example.com"
    result = test_case.get_url(url)

    assert result == url
    mock_driver.get.assert_called_once_with(url)
    mock_driver.execute_script.assert_called_once_with("localStorage.clear()")


@pytest.mark.unit
def test_webdriver_test_case_get_url_no_cleanup(mock_driver):
    """Test WebDriverTestCase.get_url method without cleanup."""
    test_case = WebDriverTestCase()
    test_case.driver = mock_driver

    url = "http://example.com"
    result = test_case.get_url(url, cleanup=False)

    assert result == url
    mock_driver.get.assert_called_once_with(url)
    mock_driver.execute_script.assert_not_called()


@pytest.mark.unit
def test_webdriver_test_case_get_url_with_exception(mock_driver):
    """Test WebDriverTestCase.get_url method when execute_script raises exc."""
    test_case = WebDriverTestCase()
    test_case.driver = mock_driver
    mock_driver.execute_script.side_effect = WebDriverException("Script error")

    url = "http://example.com"
    result = test_case.get_url(url)

    assert result == url
    mock_driver.get.assert_called_once_with(url)
    mock_driver.execute_script.assert_called_once_with("localStorage.clear()")


@pytest.mark.unit
def test_request_test_case_get_response(mock_session):
    """Test RequestTestCase.get_response method."""
    test_case = RequestTestCase()
    test_case.session = mock_session
    test_case.xrequestid = "test-request-id"

    url = "http://example.com"
    response = test_case.get_response(url)

    assert response == mock_session.request.return_value
    mock_session.request.assert_called_once()


@pytest.mark.unit
def test_request_test_case_get_response_with_cookies(mock_session):
    """Test RequestTestCase.get_response method with cookies."""
    test_case = RequestTestCase()
    test_case.session = mock_session
    test_case.xrequestid = "test-request-id"

    url = "http://example.com"
    cookies = {"session": "abc123"}
    response = test_case.get_response(url, cookies=cookies)

    assert response == mock_session.request.return_value
    mock_session.request.assert_called_once()


@pytest.mark.unit
def test_request_test_case_get_response_with_proxy(mock_session):
    """Test RequestTestCase.get_response method with proxy server."""
    test_case = RequestTestCase()
    test_case.session = mock_session
    test_case.xrequestid = "test-request-id"
    test_case.proxy_server = "proxy.example.com:8080"

    url = "http://example.com"
    response = test_case.get_response(url)

    assert response == mock_session.request.return_value
    mock_session.request.assert_called_once()


@pytest.mark.unit
def test_request_test_case_get_response_with_headers(mock_session):
    """Test RequestTestCase.get_response method with custom headers."""
    test_case = RequestTestCase()
    test_case.session = mock_session
    test_case.xrequestid = "test-request-id"

    url = "http://example.com"
    headers = {"Authorization": "Bearer token"}
    response = test_case.get_response(url, headers=headers)

    assert response == mock_session.request.return_value
    mock_session.request.assert_called_once()


@pytest.mark.unit
def test_request_test_case_get_response_retry_on_5xx_status(mock_session):
    """Test RequestTestCase.get_response method retries on 5xx status codes."""
    test_case = RequestTestCase()
    test_case.session = mock_session
    test_case.xrequestid = "test-request-id"

    mock_response1 = MagicMock(status=502)
    mock_response2 = MagicMock(status=200)
    mock_session.request.side_effect = [mock_response1, mock_response2]

    url = "http://example.com"
    response = test_case.get_response(url)

    assert response == mock_response2
    assert mock_session.request.call_count == 2


@pytest.mark.unit
def test_request_test_case_get_response_session_cookie_handling():
    """Test RequestTestCase.get_response method handles session cookies."""
    test_case = RequestTestCase()
    test_case.session = type(
        "MockSession", (), {"url": None, "status_code": None}
    )()
    test_case.xrequestid = "test-request-id"

    mock_response = MagicMock(
        status=200,
        headers={"set-cookie": "session=abc123"},
    )
    test_case.session.request = lambda *args, **kwargs: mock_response

    test_case.get_response("http://example.com")

    assert test_case.session.session_cookie == "session=abc123"


@pytest.mark.unit
def test_request_test_case_get_response_url_fix(mock_session):
    """Test RequestTestCase.get_response method fixes response URL."""
    test_case = RequestTestCase()
    test_case.session = mock_session
    test_case.xrequestid = "test-request-id"

    mock_response = MagicMock(status=200)
    mock_response.url = "/path/to/resource"
    mock_session.request.return_value = mock_response

    url = "http://example.com/path/to/resource"
    response = test_case.get_response(url)

    assert response == mock_response
    assert response.url == "http://example.com/path/to/resource"
