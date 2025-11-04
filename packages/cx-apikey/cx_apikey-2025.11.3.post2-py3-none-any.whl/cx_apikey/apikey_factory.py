import os
import functools 

from .apikey import apikey
from .apikey_validator import apikey_validator
from .apikey_exceptions import apikey_syntax_error

class apikey_factory:
    """
    Factory for the API keys. That is useable to generating new random API
    keys, importing API keys from string, with validation, generating 
    validators, and much more.
    """

    def __init__(self, prefix: str = "key") -> None:
        """
        That create new API keys factory, it require prefix, that mean static
        string which is pushed always before random part of the string. It 
        also set API keys size, which is default 256.

        Parameters
        ----------
        prefix : str (default: "key")
            Prefix for the API keys.
        """

        self.__size = 256
        self.__prefix = prefix

    def set_size(self, size: int) -> object:
        """
        That change size of the API keys. Default API key size is 256, but
        it could be changed to other custom size. Size must be greater than
        prefix with prefix separator.

        Parameters
        ----------
        size : int
            Size of the API keys.

        Raises
        ------
        RuntimeError
            When new size is too small.

        Returns
        -------
        apikey_factory
            Self for chain loading.
        """

        if size <= len(self.prefix + self.prefix_separator):
            raise RuntimeError("Size of the API keys must be bigger.")

        self.__size = size
        return self

    def set_prefix(self, prefix: str) -> object:
        """
        That change prefix of the API keys generating by the factory.
        It could not countain any white space, and cound not being empty.
        Size of the API key also must being greater than prefix with 
        separator character.

        Parameters
        ----------
        prefix : str
            New prefix to set.

        Raises
        ------
        ValueError
            When prefix is empty.

        ValueError
            When prefix contain white characters.
        
        RuntimeError
            When prefix is too long.


        Returns
        -------
        apikey_factory
            Self to chain loading.
        """

        prefix = prefix.strip()

        if len(prefix) == 0:
            raise ValueError("Prefix can not being empty.")
        
        for letter in prefix:
            if letter.isspace():
                raise ValueError("Prefix can not contain space.")
       
        if len(prefix + self.prefix_separator) >= self.size:
            raise RuntimeError("Prefix must be shorten")

        self.__prefix = prefix
        return self

    @property
    def prefix_separator(self) -> str: 
        """
        That return prefix separator.
        
        Returns
        -------
        str
            Prefix separator.
        """

        return "_"

    @property
    def prefix(self) -> str:
        """
        That return current prefix separator.

        Returns
        -------
        str
            Current prefix separator.
        """

        return self.__prefix

    @property
    def size(self) -> int:
        """
        That return current API key size.

        Returns 
        -------
        int
            Current API key size.
        """

        return self.__size

    @functools.lru_cache
    def __get_random_token_size(self, token_size: int) -> int:
        """
        That return size in bytes of random part of the API key.

        Parameters
        ----------
        token_size : int
            How much character have token.

        Returns
        -------
        int
            Size of the random token in bytes.
        """

        random_size = token_size / 2 + token_size % 2
        random_size = int(random_size)

        return random_size

    @functools.lru_cache
    def __get_token_size(self, full_size: int, prefix_size: int) -> int: 
        """
        That return how much characters would have token.

        Parameters
        ----------
        full_size : int
            Full size of the API key.
        
        prefix_size : int
            Size of the API key prefix.
        
        Returns
        -------
        int
            Random token size.
        """

        return full_size - prefix_size - len(self.prefix_separator)

    def __get_random(self) -> str:
        """
        That return new random part of the API key.

        Returns
        -------
        str
            New random part of the API key.
        """

        token_size = self.__get_token_size(self.size, len(self.prefix))
        random_size = self.__get_random_token_size(token_size)

        return os.urandom(random_size).hex()[0:token_size]
    
    def __get_new_token(self) -> str:
        """
        That return new API key token.

        Returns
        -------
        str
            That return new API key token string.
        """

        return self.prefix + self.prefix_separator + self.__get_random()

    def generate(self) -> apikey:
        """
        That generate new random API key. Result is API key object, with 
        parameters like size, prefix etc from the factory.

        Returns
        -------
        apikey 
            New random API key.
        """

        return apikey(
            self.__get_new_token(),
            self.size,
            self.prefix,
            self.prefix_separator
        )
    
    def load(self, token: str) -> apikey:
        """
        That import API key from its string form to the API key object. It
        also validate it, and raise error when API key is not valid.

        Parameters
        ----------
        token : str
            API key as string to import.

        Raises
        ------
        apikey_syntax_error
            When API key is not valid.
        
        Returns
        -------
        apikey
            API key in its object form.
        """

        if not self.get_validator().validate(token):
            raise apikey_syntax_error()

        return apikey(
            token,
            self.size,
            self.prefix,
            self.prefix_separator
        )

    def get_validator(self) -> apikey_validator:
        """
        That generate API keys validator.

        Returns
        -------
        apikey_validator
            New API key validator with parameters from factory.
        """

        return self.__get_validator_cache(
            self.size,
            self.prefix,
            self.prefix_separator
        )

    @functools.lru_cache
    def __get_validator_cache(
        self, 
        size: int, 
        prefix: str, 
        prefix_separator: str
    ) -> apikey_validator:
        """
        That is cache for API keys validator.
        
        Parameters
        ----------
        size : int
            Size of the API keys.

        prefix : str
            Prefix of the API keys.

        prefix_separator : str
            Prefix separator character.

        Returns
        -------
        apikey_validator
            New API key validator.
        """

        return apikey_validator(
            size,
            prefix,
            prefix_separator
        )
