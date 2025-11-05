from typing import Callable
from ._key_extractor import get_key, KeyExtractor, Key, IndexKey

def list_to_dict(
    input: list,
    key_extractors: list[KeyExtractor] = [],
    non_primitive_types: tuple[type, ...] = [],
) -> tuple[dict[Key, any], list[any], dict[IndexKey, any]]:
    """
    Converts a list into a dictionary based on extracted keys. Entries without keys
    are categorized into primitives and rest.
    :param list input: The input list to be converted.
    :param list key_extractors: A list of key extractor functions to extract keys from entries.
    :param tuple[type, ...] non_primitive_types: A tuple of types considered non-primitive.
    :return: A tuple containing:
        - A dictionary mapping extracted keys to their corresponding entries.
        - A list of primitive entries (entries without keys and of primitive types).
        - A dictionary mapping IndexKey to non-primitive entries without keys.
    :rtype: tuple[dict[Key, any], list[any], dict[IndexKey, any]]
    """
    rtn = {}
    rest = []
    primitives = []
    
    for entry in input:
        key = get_key(entry, key_extractors)
        if key:
            rtn[key] = entry
        else:
            entry_type = type(entry)
            if entry_type in non_primitive_types:
                rest.append(entry)
            else:
                primitives.append(entry)

    return (
        rtn, 
        primitives,
        {IndexKey(index): entry for index, entry in enumerate(rest)}
    )

def extend_list(input: list, index: int):
    """
    Extends the given list to ensure it has at least 'index + 1' elements.

    Any additional elements are filled with 'None'.

    Parameters:
    :param list input: The list to be extended.
    :param int index: The index of the element to retrieve from the extended list.

    Returns:
    :return: The value at the specified 'index' in the extended list.
    :rtype: Any

    Example:
    >>> extend_list([1, 2, 3], 5)
    [1, 2, 3, None, None, None]

    >>> extend_list(['a', 'b', 'c'], 2)
    'c'
    """
    if (diff := (index + 1) - len(input)) > 0:
        input.extend([None for i in range(diff)])
    return input[index]
