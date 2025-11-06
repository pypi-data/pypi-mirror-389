#---------- Imports ----------

from snaplit._rust_snaplit import RhoodMap as _RustRhoodMap

from typing import Any, Optional, List, Iterable, Iterator, Dict

#---------- RhoodMap (Robin Hood Hashing Map) Shim ----------

class RhoodMap():
    """
    A Python-friendly HashMap implementation powered by Rust for exceptional performance.

    RhoodMap is engineered for workloads that demand both **speed** and **memory efficiency**, delivering
    superior performance compared to Python's native 'dict' sstructure in large-scale or high-frequency
    access patterns.
    The core implementation, written in **Rust**, employs **Robin Hood Hashing** - A a collision-resolution
    strategy that minimizes variance in probe chain length by allowing elements with longer probe distances
    to "steal" slots from those with lesser ones.

    ----- Parameters -----

    capacity: Optional[int] = 1024
        The initial number of key-value slots allocated in memory. Defaults to '1024'.
        Larger capacities reduce internal entry collisions, but increase memory usage.

    ----- Methods -----

    insert(key: Any, value: Any) -> bool:
        Inserts a key-value pair into internal hashmap. Returns 'True' is insertion is successfull.

    remove(key: Any) -> Optional[Any]:
        Removes and returns the key-value pair from internal hashmap. Returns 'None' is the value is not found.

    get(key: Any) -> Any:
        Retrieves the value associated with the specified key without mutating the internal hashmap.

    update(key: Any, new_value: Any) -> bool:
        Updates the value associated with the specified key. Returns 'True' is update is successfull.

    contains(key: Any) -> bool:
        Returns 'True' if the key is present in the internal hashmap.

    from_keys(iterable: Iterable[Any]) -> List[Any]:
        Returns a list of values corresponding to the list of provided keys.

    keys() -> List[Any]:
        Returns all keys currently stored in the internal hashmap.

    values() -> List[Any]:
        Returns all values currently stored in the internal hashmap.

    items() -> List[Any]:
        Returns all items (keys + values) currently stored in the internal hashmap.

    copy() -> RhoodMap:
        Creates a deep copy of internal RhoodMap, preserving internal capacity and bucket_size.
        Returns a fully independent clone of original RhoodMap.

    info() -> Dict[str, Any]:
        Returns internal statistics regarding the current RhoodMap.

    capacity() -> int:
        Returns the total capacity of the internal hashmap

    size() -> int:
        Returns the current number of elements stored in internal hashmap.

    percentage() -> float:
        Returns the current load factor (the percentage of used capacity)

    is_empty() -> bool:
        Returns 'True' is the internal hashmap contains no elements.

    clear() -> None:
        Removes all entries from internal hashmap and resets internal metrics.

    __len__() -> int:
        Enables the use of Python's native 'len()' to return current map size.

    __bool__() -> bool:
        Enables the use of Python's native 'if map' to return 'True' if the map is not empty.

    __contains__(key: Any) -> bool:
        Enables the use of Python's native 'x in map' to return 'True' if the map contains specified value.

    __getitem__(key: Any) -> Any:
        Enables the use of Python's native 'map[key]' to return the specified value.

    __setitem__(key: Any, value: Any) -> None:
        Enables the use of Python's native 'map[key] = value' to update the internal value associated with key.

    __delitem__(key: Any) -> None:
        Enables the use of Python's native 'del map[key]' to delete internal key-value pair.

    __iter__() -> Iterator:
        Enables the use of Python's native 'for x in map' to iterate over map's internal keys.

    __copy__() -> RhoodMap:
        Enables the use of Python's native 'copy()' to create a new instance of map object.

    ----- Example -----

    >>> map = RhoodMap(capacity=1024)
    >>> map.insert(key=1, value="Bulbasaur")
    >>> map.insert(key=2, value="Ivysaur")
    >>> map.insert(key=3, value="Venusaur")

    >>> print(map.contains(1))
    True
    >>> print(map.get(2))
    "Ivysaur"
    >>> map.update(key=3, new_value="Squirtle")

    >>> print(map.keys())
    [1, 2, 3]
    >>> print(map.values())
    ["Bulbasaur", "Ivysaur", "Squirtle"]
    """

    def __init__(self, capacity: Optional[int] = 1024):
        if not isinstance(capacity, int):
            return TypeError(f"Capacity must be of Type: int - Current type {type(capacity)}")
        if capacity <= 0:
            return ValueError("Capacity must be represented by a positive integer")
        
        self._inner = _RustRhoodMap(capacity)

    def insert(self, key: Any, value: Any) -> bool:
        return self._inner.insert(key, value)
    
    def remove(self, key: Any) -> Any:
        return self._inner.remove(key)
    
    def get(self, key: Any) -> Optional[Any]:
        return self._inner.get(key)
    
    def update(self, key: Any, new_value: Any) -> bool:
        return self._inner.update(key, new_value)
    
    def contains(self, key: Any) -> bool:
        return self._inner.contains(key)
    
    def from_keys(self, iterable: Iterable[Any]) -> List[Any]:
        return self._inner.from_keys(iterable)
    
    def keys(self) -> List[Any]:
        return self._inner.keys()
    
    def values(self) -> List[Any]:
        return self._inner.values()
    
    def items(self) -> List[Any]:
        return self._inner.items()
    
    def copy(self) -> "RhoodMap":
        new_map = RhoodMap(capacity=self.capacity())
        new_map._inner = self._inner.copy()
        return new_map

    def info(self) -> Dict[str, Any]:
        return self._inner.info()
    
    def capacity(self) -> int:
        return self._inner.capacity()
    
    def size(self) -> int:
        return self._inner.size()
    
    def percentage(self) -> float:
        return self._inner.precentage()
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.size()

    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __contains__(self, key: Any) -> bool:
        return self._inner.contains(key)
    
    def __getitem__(self, key: Any) -> Any:
        gotten_item = self._inner.get(key)
        if gotten_item is None:
            raise ValueError(f"Key {key} not found in RhoodMap")
        else:
            return gotten_item
        
    def __setitem__(self, key: Any, value: Any) -> None:
        self._inner.insert(key, value)

    def __delitem__(self, key: Any) -> None:
        deleted_value = self._inner.remove(key)
        if deleted_value is None:
            raise ValueError(f"Key {key} not found in RhoodMap")
        else:
            return deleted_value
        
    def __iter__(self) -> Iterator[Any]:
        return iter(self._inner.keys())
    
    def __copy__(self) -> "RhoodMap":
        new_map = RhoodMap(capacity=self.capacity())
        new_map._inner = self._inner.copy()
        return new_map