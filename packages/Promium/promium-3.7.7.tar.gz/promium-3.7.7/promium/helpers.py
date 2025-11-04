from six.moves.urllib.parse import urlparse


class ParseUrl:
    def __init__(self, url: str) -> None:
        self.url = url

    def __repr__(self) -> str:
        return self.url

    @property
    def scheme(self) -> str:
        """
        :return: scheme, for example: http or https
        """
        parse_url = urlparse(self.url)
        return parse_url.scheme

    @property
    def hostname(self) -> str:
        """
        :return: hostname, for example: prom.ua
        """
        parse_url = urlparse(self.url)
        return parse_url.netloc.split(":")[0]

    @property
    def port(self) -> str | None:
        """
        :return: port
        """
        parse_url = urlparse(self.url)
        parse_netloc_split = parse_url.netloc.split(":")
        if len(parse_netloc_split) > 1:
            return parse_netloc_split[-1]
        return None

    @property
    def path(self) -> str | None:
        """
        :return: hierarchical path, for example: /Zhenskii-platya
        """
        parse_url = urlparse(self.url)
        if parse_url.path:
            return parse_url.path
        return None

    @property
    def params(self) -> str | None:
        """
        :return: parameters for last path element
        """
        parse_url = urlparse(self.url)
        if parse_url.params:
            return parse_url.params
        return None

    @property
    def query(self) -> dict[str, str] | None:
        """
        :return: query component
        """
        parse_url = urlparse(self.url)
        if parse_url.query:
            return dict([
                query.split("=") for query in parse_url.query.split("&")
            ])
        return None

    @property
    def fragment(self) -> str | None:
        """
        :return: fragment identifier (#)
        """
        parse_url = urlparse(self.url)
        if parse_url.fragment:
            return parse_url.fragment
        return None
