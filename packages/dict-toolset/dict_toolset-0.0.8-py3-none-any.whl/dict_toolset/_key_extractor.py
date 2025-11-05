from typing import Callable


KeyExtractor = Callable[[any], dict]

class IndexKey:

    __slots__ = ("index",)

    def __init__(self, index: int) -> None:
        self.index = index

    def __repr__(self):
        return f"{self.index}"
    
    def __str__(self):
        return f"[{self.index}]"
    
    def __hash__(self):
        return self.index
    
    def __eq__(self, other):
        if isinstance(other, IndexKey):
            return self.index == other.index
        return False

class Key:
    
    __slots__ = ("key", "value", "extractor")

    def __init__(
        self,
        key: any,
        value: any,
        extractor: KeyExtractor
    ) -> None:
        self.key = key
        self.value = value
        self.extractor = extractor

    def __repr__(self):
        return f"{self.key}={self.value}"
    
    def __str__(self):
        return f"[{self.key}={self.value}]"
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        if isinstance(other, Key):
            return (
                self.key == other.key
                and self.value == other.value
            )
        return False


def get_key_name(entry, *args):
    for arg in args:
        if arg in entry:
            return f"arg:{entry[arg]}"

def default_dict_key_extractor(entry):
    if isinstance(entry, dict):
        for key in ('id', 'ID', 'uuid', 'UUID'):
            if key in entry:
                return Key(key, entry[key], default_dict_key_extractor)

def get_key(data: any, key_extractors: list[KeyExtractor]) -> any:
    """Extracts a key from the given data using the provided key extractors.
    :param any data: The data from which to extract the key.
    :param list[KeyExtractor] key_extractors: A list of key extractor functions.
    :return: The extracted key, or None if no key could be extracted.
    :rtype: any
    """
    for key_extractor in key_extractors:
        if key := key_extractor(data):
            return key