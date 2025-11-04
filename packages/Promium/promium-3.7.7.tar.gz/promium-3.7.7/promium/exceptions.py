class PromiumException(Exception):
    pass


class PromiumTimeout(PromiumException):
    def __init__(
        self,
        message: str = "no error message",
        seconds: int = 10,
        screen: str | None = None,
    ) -> None:
        self.message = f"{message} (waited {seconds} seconds)"
        if screen:
            self.message += "Screenshot: available via screen\n"
        super().__init__(self.message)


class ElementLocationException(PromiumException):
    pass


class LocatorException(PromiumException):
    pass


class BrowserConsoleException(PromiumException):
    pass
