class apikey_syntax_error(Exception):
    """
    That exception had been raised when API key is not valid.
    """

    def __init__(self) -> None:
        super().__init__("That is not valid API key.")
