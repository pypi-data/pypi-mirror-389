#---------- Imports ----------

from snaplit._rust_snaplit import BloomFilter as _RustBloomFilter

from typing import Any

#---------- Bloom Filter Shim ----------

class BloomFilter():
    """
    A space-efficient probabilistic data structure for optimized membership checking.

    This Bloom Filter class implements a Rust-powered backend to enable fast insertion and membership
    checks with configurable false-positive probability and compact memory usage.

    Bloom filters are specifically useful when needing to check whether an element *possibly* exists in 
    a give set with minimal memory overhead. Filters allow for false positives but never false negatives.

    ----- Parameters -----

    size: int
        Expected number of elements to be stored in the Bloom Filter.
        Must be a positive integer.

    probability: float
        Desired false-positive probability for the filter.
        Must be a float betwee 0.00 - 1.00.

    ----- Methods -----

    add(item: Any) -> None:
        Inserts an element into the internal Bloom Filter.

    contains(item: Any) -> bool:
        Returns True if an element *might* be present in the internal Bloom Filter.
        Returns False if the element is *definitely* not present in the internal Bloom Filter.

    clear() -> None:
        Resets the internal Bloom Filter, removing all stored values.

    ----- Example -----

    >>> test_filter = BloomFilter(size=10000, probability=0.1)

    >>> test_filter.add("Greninja")

    >>> print(test_filter.contains("Greninja"))
    True
    >>> print(test_filter.contains("Chesnaught"))
    False
    """

    def __init__(self, size: int, probability: float):
        if not isinstance(size, int):
            raise TypeError("Size must be of Type: int")
        if not isinstance(size, int):
            raise TypeError("Probability must be of Type: float")
        if size <= 0:
            raise ValueError("Size must be represented by a positive integer")
        if not (0.00 < probability <= 1.00):
            raise ValueError("Probability must be betweenn 0.00 - 1.00")
        
        self._inner = _RustBloomFilter(size=size, probability=probability)

    def add(self, item: Any) -> None:
        self._inner.add(item)

    def contains(self, item: Any) -> bool:
        return self._inner.contains(item)
    
    def clear(self) -> None:
        self._inner.clear()

    