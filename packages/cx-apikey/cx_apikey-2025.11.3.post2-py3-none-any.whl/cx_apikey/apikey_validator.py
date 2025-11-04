from .apikey import apikey

class apikey_validator:
    """
    That is API key validator. It check that API key have valid prefix,
    size and separator.
    """

    def __init__(
        self,
        size: int,
        prefix: str,
        prefix_separator: str
    ) -> None:
        """
        That is API key validator constructor, it would be used by API key 
        validator factory, not direct.

        Parameters
        ----------
        size : int
            Size of the apikey validator.
        
        prefix : str
            Prefix of the API key.

        prefix_separator : str
            Separator between random part of the API key and prefix.
        """

        self.__size = size
        self.__prefix = prefix
        self.__prefix_separator = prefix_separator

    @property
    def size(self) -> int:
        """
        Full size of the API key.

        Returns
        -------
        int
            Full lenght of the API key.
        """

        return self.__size

    @property
    def prefix(self) -> str:
        """
        Prefix of the API key.

        Returns
        -------
        str
            Prefix of the API key.
        """

        return self.__prefix

    @property
    def prefix_separator(self) -> str:
        """
        Character between prefix and random part of the API key.

        Returns
        -------
        str
            Separator character.
        """

        return self.__prefix_separator

    def validate(self, content: str | apikey) -> bool:
        """
        That validate API key, check that it prefix, prefix separator and 
        size if proof.

        Parameters
        ----------
        content : str | apikey
            Target to validate that is proof API key.

        Returns
        -------
        bool    
            Result of the validation. True when valid, False when invalid.
        """

        if type(content) is not str:
            content = str(content)

        parts = content.split(self.prefix_separator)

        if len(parts) != 2:
            return False

        prefix = parts[0]
        token = parts[1]

        if prefix != self.prefix:
            return False

        if len(content) != self.size:
            return False

        if len(token) % 2 != 0:
            token = token + "0"

        try:
            bytes_token = bytes.fromhex(token)
        except:
            return False

        return True

