#---------- Imports ----------

from snaplit._rust_snaplit import Trie as _RustTrie

from typing import List, Iterable, Iterator

#---------- Prefix Tree/Trie Shim ----------

class Trie():
    """
    A high-performance prefix tree (Trie) implementation with a efficient Rust backend.

    This class provides a fast, memory-efficient and type safe implementation of a Trie data structure
    idea for operations involving prefix-based lookups, autocompletion systems, dictionaries and other
    large-scale language-processing tasks.

    ----- Methods -----

    insert(word: str) -> None:
        Insert a single word into the Trie structure.
        Word parameter must be of Type: str.

    remove(word: str) -> None:
        Removes a single word form the Trie structure, if it exists.
        Word parameter must be of Type: str.

    contains(word: str) -> bool:
        Checks whether the specified word is contained in the Trie structure.
        Word parameter must be of Type: str.

    starts_with(prefix: str) -> bool:
        Returns True is any stored words start with the specified prefix.
        Prefix parameter must be of Type: str.

    prefixed(prefix: str) -> List[str]:
        Returns a list of all the words that begin with the specified prefix.
        Prefix parameter must be of Type: str.

    extend(elements: Iterable[str]) -> None:
        Inserts multiple word elements into the Trie structure.
        Iterable must consist of String types.

    get_prefixes(word: str) -> List[str]:
        Returns all valid prefixes of the input wordthat exists in the Trie structure.
        Word parameter must be of Type: str.

    prefix_count(prefix: str) -> int:
        Returns the number of words that share the specified prefix.
        Prefix parameter must be of Type: str.

    base_keys() -> List[str]:
        Returns a list of all base-level characters present in the Trie structure.

    node_size() -> int:
        Returns the total number of nodes currently stored in the Trie structure.

    word_size() -> int:
        Returns the total number of words currently stored in the Trie structure.

    is_empty() -> bool:
        Returns True if the Trie structure currently contains no words, else False.

    copy() -> Trie:
        Returns a deep copy of the current Trie structure.

    clear() -> None:
        Removes all current words from the Trie structure.

    __len__() -> int:
        Enables the use of Python's internal 'len()' functionality. 
        Returns the current number of words present in the Trie structure.

    __bool__() -> bool:
        Enables the use of Python's internal 'if Trie' functionality.
        Returns True if the current Trie structure contains at least one word.

    __contains__(word: str) -> bool:
        Enables the use of Python's internal 'value in Trie' functionality.
        Returns True if the curent Trie contains the specified word, else False.

    __iter__() -> Iterator:
        Enables the use of Python's internal iteration operations ('for x in Trie').
        Returns aPython list of stored words that allows for iteration.

    __copy__() -> Trie:
        Enables the use of Python's internal 'copy()' functionality.
        Returns a new instance of the current Trie structure.

    ----- Example -----

    >>> trie = Trie()
    >>> trie.insert("apple")
    >>> trie.insert("app")
    >>> trie.insert("banana")
    >>> print(trie.contains("app"))
    True
    >>> print(trie.starts_with("ap"))
    True
    >>> print(trie.prefixed("ap"))
    ['app', 'apple']
    >>> print(trie.words())
    ['app', 'apple', 'banana']
    >>> trie.clear()
    >>> print(trie.is_empty())
    True
    """

    def __init__(self):
        self._inner = _RustTrie()

    def insert(self, word: str) -> None:
        if not isinstance(word, str):
            raise ValueError("Word must be of Type: str")
        self._inner.insert(word)

    def remove(self, word: str) -> None:
        if not isinstance(word, str):
            raise ValueError("Word must be of Type: str")
        self._inner.remove(word)

    def contains(self, word: str) -> bool:
        if not isinstance(word, str):
            raise ValueError("Word must be of Type: str")
        return self._inner.contains(word)
    
    def starts_with(self, prefix: str) -> bool:
        if not isinstance(prefix, str):
            raise ValueError("Prefix must be of Type: str")
        return self._inner.starts_with(prefix)
    
    def prefixed(self, prefix: str) -> List[str]:
        if not isinstance(prefix, str):
            raise ValueError("Prefix must be of Type: str")
        return self._inner.prefixed(prefix)
    
    def words(self) -> List[str]:
        return self._inner.words()
    
    def extend(self, elements: Iterable[str]) -> None:
        self._inner.extend()

    def get_prefixes(self, word: str) -> List[str]:
        if not isinstance(word, str):
            raise ValueError("Word must be of Type: str")
        return self._inner.get_prefixes(word)
    
    def prefix_count(self, prefix: str) -> int:
        if not isinstance(prefix, str):
            raise ValueError("Prefix must be of Type: str")
        return self._inner.prefix_count(prefix)
    
    def base_keys(self) -> List[chr]:
        return self._inner.base_keys()
    
    def node_size(self) -> int:
        return self._inner.node_size()
    
    def word_size(self) -> int:
        return self._inner.word_size()
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def copy(self) -> "Trie":
        return self._inner.copy()
    
    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.word_size()
    
    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __contains__(self, word: str) -> bool:
        if not isinstance(word, str):
            raise ValueError("Word must be of Type: str")
        return self._inner.contains(word)
    
    def __iter__(self) -> Iterator:
        return self._inner.words()
    
    def __copy__(self) -> "Trie":
        return self._inner.copy()