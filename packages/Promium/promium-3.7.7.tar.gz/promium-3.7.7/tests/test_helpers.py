import pytest

from promium.helpers import ParseUrl


@pytest.mark.unit
def test_parse_url_init_and_repr():
    """Test ParseUrl initialization and string representation."""
    url = "https://example.com/path"
    parse_url = ParseUrl(url)

    assert parse_url.url == url
    assert repr(parse_url) == url
    assert str(parse_url) == url


@pytest.mark.unit
@pytest.mark.parametrize(("url", "expected_scheme"), [
    ("https://example.com", "https"),
    ("http://example.com", "http"),
    ("ftp://files.example.com", "ftp"),
    ("file:///local/path", "file"),
    ("//example.com", ""),  # No scheme
])
def test_scheme_property(url, expected_scheme):
    """Test ParseUrl.scheme property with various URLs."""
    parse_url = ParseUrl(url)
    assert parse_url.scheme == expected_scheme


@pytest.mark.unit
@pytest.mark.parametrize(("url", "expected_hostname"), [
    ("https://example.com", "example.com"),
    ("https://sub.example.com", "sub.example.com"),
    ("https://example.com:8080", "example.com"),
    ("http://localhost", "localhost"),
    ("https://192.168.1.1:3000", "192.168.1.1"),
    ("//example.com:8080", "example.com"),
])
def test_hostname_property(url, expected_hostname):
    """Test ParseUrl.hostname property with and without ports."""
    parse_url = ParseUrl(url)
    assert parse_url.hostname == expected_hostname


@pytest.mark.unit
@pytest.mark.parametrize(("url", "expected_port"), [
    ("https://example.com", None),
    ("https://example.com:8080", "8080"),
    ("http://localhost:3000", "3000"),
    ("https://192.168.1.1:22", "22"),
    ("//example.com:8080", "8080"),
    ("https://example.com:80/path", "80"),
])
def test_port_property(url, expected_port):
    """Test ParseUrl.port property with various port scenarios."""
    parse_url = ParseUrl(url)
    assert parse_url.port == expected_port


@pytest.mark.unit
@pytest.mark.parametrize(("url", "expected_path"), [
    ("https://example.com", None),
    ("https://example.com/", "/"),
    ("https://example.com/path", "/path"),
    ("https://example.com/path/to/resource", "/path/to/resource"),
    ("https://example.com/path/to/resource/", "/path/to/resource/"),
    ("file:///local/path", "/local/path"),
    ("https://example.com/path;param", "/path"),
])
def test_path_property(url, expected_path):
    """Test ParseUrl.path property with various paths."""
    parse_url = ParseUrl(url)
    assert parse_url.path == expected_path


@pytest.mark.unit
@pytest.mark.parametrize(("url", "expected_params"), [
    ("https://example.com", None),
    ("https://example.com/path", None),
    ("https://example.com/path;param=value", "param=value"),
    (
        "https://example.com/path;param1=value1;param2=value2",
        "param1=value1;param2=value2"
    ),
])
def test_params_property(url, expected_params):
    """Test ParseUrl.params property."""
    parse_url = ParseUrl(url)
    assert parse_url.params == expected_params


@pytest.mark.unit
@pytest.mark.parametrize(("url", "expected_query"), [
    ("https://example.com", None),
    ("https://example.com?", None),
    ("https://example.com?key=value", {"key": "value"}),
    (
        "https://example.com?key1=value1&key2=value2",
        {"key1": "value1", "key2": "value2"}
    ),
    ("https://example.com?empty=", {"empty": ""}),
])
def test_query_property(url, expected_query):
    """Test ParseUrl.query property with various query strings."""
    parse_url = ParseUrl(url)
    assert parse_url.query == expected_query


@pytest.mark.unit
@pytest.mark.parametrize(("url", "expected_fragment"), [
    ("https://example.com", None),
    ("https://example.com#", None),
    ("https://example.com#fragment", "fragment"),
    ("https://example.com/path#section1", "section1"),
    ("https://example.com?key=value#anchor", "anchor"),
    ("https://example.com/path;param#fragment", "fragment"),
])
def test_fragment_property(url, expected_fragment):
    """Test ParseUrl.fragment property."""
    parse_url = ParseUrl(url)
    assert parse_url.fragment == expected_fragment


@pytest.mark.unit
def test_complete_url_parsing():
    """Test parsing of a complete URL with all components."""
    url = "https://example.com:8080/path/to/resource;param1=value1?key1=value1&key2=value2#fragment"
    parse_url = ParseUrl(url)

    assert parse_url.scheme == "https"
    assert parse_url.hostname == "example.com"
    assert parse_url.port == "8080"
    assert parse_url.path == "/path/to/resource"
    assert parse_url.params == "param1=value1"
    assert parse_url.query == {"key1": "value1", "key2": "value2"}
    assert parse_url.fragment == "fragment"


@pytest.mark.unit
def test_edge_cases():
    """Test edge cases and unusual URLs."""
    # Empty URL
    parse_url = ParseUrl("")
    assert not parse_url.scheme
    assert not parse_url.hostname
    assert parse_url.port is None
    assert parse_url.path is None
    assert parse_url.params is None
    assert parse_url.query is None
    assert parse_url.fragment is None

    # URL with only scheme
    parse_url = ParseUrl("https:")
    assert parse_url.scheme == "https"
    assert not parse_url.hostname
