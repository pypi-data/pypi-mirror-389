#---------- Imports ----------

from snaplit._rust_snaplit import CuckooFilter as _RustCuckooFilter

from typing import Any, Optional

#---------- Cuckoo Filter Shim ----------

class CuckooFilter():
    """
    A high-performance, space-efficient Cuckoo Filter for approximate membership checking.

    This CuckooFilter-class is a comprehensive probabilisitc data structure, similar in function to
    ordinary Bloom Filters, but offering the opportunity for entry deletion and better space efficiency.
    Powered by a Rust backend, the filter offers fast insertions, efficient lookups, and entry deletions.

    ----- Parameters -----

    size: Optional[int] = 100:
        The number of individual storage buckets implemented in the internal filter.
        Must be a positive integer.
    bucket_size: Optional[int] = 4:
        The number individual slots per bucket. higher values reduce false positivity rates but increase
        memory usage.
        Must be a positive integer.
    retries: Optional[int] = 5:
        The maximum number of displacemnt attempts made during insertions before giving up.
        Must be a positive integer.

    ----- Methods -----

    insert(item: Any) -> bool:
        Inserts an item into the filter. Returns True if the insertion in successfull,
        or False if the filter is full.

    contains(item: Any) -> bool:
        Checks whether the specified item is *possibly* present in the filter.

    delete(item: Any) -> bool:
        Removes the specified item from the filter. Returns True if the deletion in successfull,
        or False if not.

    is_empty() -> bool:
        Returns True if the current filter has 0 entries, else False.

    load_factor() -> float:
        Returns the current filter's load factor - A floating-point representation of how full the filter is.

    clear() -> None:
        Clears all entries from the current filter.

    __len__() -> int:
        Returns the number of elements currently stored in the filter.

    __bool__() -> bool:
        Returns True if the current filter is not empty, else False.

    __contains__(item: Any) -> bool:
        Enables Python's native 'in' operation:
        'item in cuckoo_filter'.

    ----- Example -----

    >>> test_filter = CuckooFilter(size=50, bucket_size=2, retries=4)
    >>> test_filter.insert("Abra")
    >>> test_filter.insert("Kadabra")
    >>> test_filter.insert("Alakazam")

    >>> print(test_filter.contains("Abra"))
    True
    >>> print(test_filter.contains("Magikarp"))
    False

    >>> test_filter.delete("Alakazam")
    >>> print(test_filter.contains("Alakazam"))
    False
    """

    def __init__(
        self,
        size: Optional[int]=100,
        bucket_size: Optional[int]=4,
        retries: Optional[int]=5
    ):
        if not isinstance(size, int):
            raise TypeError("Size must be of Type: int")
        if not isinstance(bucket_size, int):
            raise TypeError("Bucket size must be of Type: int")
        if not isinstance(retries, int):
            raise TypeError("Retries must be of Type: int")
        if size <= 0:
            raise ValueError("Size must be represented by a positive integer")
        if bucket_size <= 0:
            raise ValueError("Bucket size must be represented by a positive integer")
        if retries <= 0:
            raise ValueError("Retries must be represented by a positive integer")
        
        self._inner = _RustCuckooFilter(size=size, bucket_size=bucket_size, retries=retries)

    def insert(self, item: Any) -> bool:
        return self._inner.insert(item)
    
    def contains(self, item: Any) -> bool:
        return self._inner.contains(item)
    
    def delete(self, item: Any) -> bool:
        return self._inner.delete(item)
    
    def is_empty(self) -> int:
        return self._inner.is_empty()
    
    def load_factor(self) -> float:
        return self._inner.load_factor()
    
    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.len()
    
    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __contains__(self, item: Any) -> bool:
        return self._inner.contains(item)