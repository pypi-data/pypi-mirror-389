#---------- Imports ----------

from snaplit._rust_snaplit import SnapMap as _RustSnapMap

from typing import Any, Optional, List, Iterable, Iterator

#---------- SnapMap (Cuckoo Hashing Map) Shim ----------

class SnapMap():
    """
    A high-performance HashMap implementation powered by Rust and with a comprehensive Pythonic interface.

    SnapMap is designed for scenarios requiring both **speed** and **memory efficiency**, outperforming 
    Python's native 'dict' data structure for large or high-frequency workloads. The underlying Rust 
    implementation uses **Cuckoo Hashing** to guarantee near-constant-time operations for insertion, deletiong,
    and lookup, while also maintaining a predictable memory footprint.

    ----- Parameters -----

    capacity: Optional[int] = 1024
        The initial number of key-value slots allocated in memory. Defaults to '1024'.
        Larger capacities reduce internal entry collisions, but increase memory usage.

    bucket_size: Optional[int] = 4
        The number of entries per internal hash buckets. Defaults to '4'.
        Larger buckets sizes reduce hashing frequency, but increase lookup time.

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

    copy() -> SnapMap:
        Creates a deep copy of internal SnapMap, preserving internal capacity and bucket_size.
        Returns a fully independent clone of original SnapMap.

    info() -> Dict[str, Any]:
        Returns internal statistics regarding the current SnapMap.

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

    __copy__() -> SnapMap:
        Enables the use of Python's native 'copy()' to create a new instance of map object.

    ----- Example -----

    >>> map = SnapMap(capacity=1024, bucket_size=4)
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

    def __init__(self, capacity: Optional[int] = 1024, bucket_size: Optional[int] = 4):
        if not isinstance(capacity, int):
            raise TypeError(f"Capacity must be of Type: int - current type {type(capacity)}")
        if not isinstance(bucket_size, int):
            raise TypeError(f"Bucket size must be of Type: int - current type {type(bucket_size)}")
        self._inner = _RustSnapMap(capacity, bucket_size)

    def insert(self, key: Any, value: Any) -> bool:
        return self._inner.insert(key, value)
    
    def remove(self, key: Any) -> Optional[Any]:
        return self._inner.remove(key)
    
    def get(self, key: Any) -> Any:
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
    
    def copy(self) -> "SnapMap":
        new_map = SnapMap(self.capacity(), self.bucket_size())
        new_map._inner = self._inner.copy()
        return new_map
    
    def info(self) -> dict[str, Any]:
        return self._inner.info()
    
    def capacity(self) -> int:
        return self._inner.capacity()
    
    def size(self) -> int:
        return self._inner.size()
    
    def percentage(self) -> float:
        return self._inner.percentage()
    
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
        gotten_value = self._inner.get(key)
        if gotten_value is None:
            raise ValueError(f"Key {key} not found in SnapMap")
        else:
            return gotten_value
        
    def __setitem__(self, key: Any, value: Any) -> None:
        self._inner.insert(key, value)

    def __delitem__(self, key: Any) -> None:
        deleted_value = self._inner.remove(key)
        if deleted_value is None:
            raise ValueError(f"Key {key} not found in SnapMap")
        else:
            return deleted_value
        
    def __iter__(self) -> Iterator:
        return iter(self._inner.keys())
    
    def __copy__(self) -> "SnapMap":
        new_map = SnapMap(self.capacity(), self.bucket_size())
        new_map._inner = self._inner.copy()
        return new_map
