class apikey:
    """
    That class represents API key. It store api key size, prefix and
    key itself. It could be converted into string, to store it in database
    and it would be created by the apikey_factory. Do not create it by hand.
    """

    def __init__(
        self, 
        content: str, 
        size: int, 
        prefix: str, 
        prefix_separator: str
    ) -> None:
        """
        That is constructor, it would be generated only by apikey_factory
        not manual in the app. Use apikey_factory, not that function.

        Parameters
        ----------
        content : str
            Full generated API key.

        size : int
            Size of the full API key.

        prefix : str
            API key prefix.

        prefix_separator : str
            Separation character between prefix and API key.
        """
        
        self.__content = content
        self.__size = size
        self.__prefix = prefix
        self.__prefix_separator = prefix_separator

    @property
    def content(self) -> str:
        """
        Full API key, which could be used in app or store in database.

        Returns
        -------
        str
            API key to use.
        """

        return self.__content
    
    @property
    def size(self) -> int:
        """
        Size of the full API key.

        Returns
        -------
        int
            API key size.
        """

        return self.__size

    @property
    def prefix(self) -> str:    
        """
        Prefix of the API key. Static part before random characters.

        Returns
        -------
        str
            Prefix of the API key.
        """

        return self.__prefix

    @property
    def prefix_separator(self) -> str:
        """
        Separator between prefix and random part of the API key.

        Returns
        -------
        str
            Separator between prefix and random part API key.
        """

        return self.__prefix_separator

    @property
    def key(self) -> str:
        """
        API key as string. Alias of content property.

        Returns
        -------
        str 
            API key as string.
        """

        return self.__content

    def compare(self, target: str | object) -> bool:
        """
        That compare API key with second API key. The second API key could
        be given as string or apikey object.

        Parameters
        ----------
        target : str
            API key to compare with.

        Returns
        -------
        bool
            Comparation result.
        """

        return self.__content == str(target)

    def __eq__(self, target: str | object) -> bool:
        """
        That is alias of compare function.

        Parameters
        ----------
        target : str
            API key to compare with.

        Returns
        -------
        bool
            Comparation result.
        """

        return self.compare(target)

    def __str__(self) -> str:
        """
        That convert API key to string, that mean return full API key.

        Returns
        -------
        str
            Fill API key.
        """

        return self.__content

    def __repr__(self) -> str:
        """
        That return debug info about API key.
        
        Returns
        -------
        str
            API key debug info.
        """

        return "API key: \"" + self.__content + "\""
