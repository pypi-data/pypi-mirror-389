#---------- Imports ----------

from snaplit._rust_snaplit import Flatlist as _RustFlatlist

from typing import Any, Optional, Iterable, List, Iterator

#---------- Flatlist (Flattened Skiplist) Shim ----------

class Flatlist():
    """
    An optimized, Rust-powered ordered collection for Python operations.

    'Flatlist' provides a high-performance, memory-efficient data structure based on a flattened Skiplist,
    implemented in Rust. This hybrid design combines Rust's low-level speed and memory safety guarantess 
    with a clean Pythonic API. The result is a deterministic, lock-free ordered listthat supports fast 
    insertions, deletion and lookups - Ideal for workloads requiring predictable ordering and high output.

    ----- Parameters -----

    levels: Optional[int] = None
        Maximum skiplist height - The number of levels that the Flatlist include.
        Must be represented by a positive, unsigned integer.
        Rust backend ensures that default 'levels' value is 4.

    probability: Optional[float] = None
        Probability controlling level management.
        Must be represented by a floating-point number betwee 0.00 - 1.00.
        Rust backend ensures that default 'probability' value is 0.5.

    ----- Methods -----

    insert(payload: Any) -> bool:
        Inserts a new element into the internal Flatlist.

    remove(key: Any) -> Any:
        Remove and return an element by unique key.

    contains(key: Any) -> bool:
        Checks whether an element is currently present in internal Flatlist.

    get(key: Any) -> Optional[Any]:
        Retrieves an element by unique key - returns 'None' if value wasn't present.

    update(key: Any, new_value: Any) -> bool:
        Updates the internal payload of the specified element.
    
    extend(elements: Iterable[Any]) -> bool:
        Bulk inserts multiple new elements.

    index_of(key: Any) -> int:
        Returns the index position of the specified value.

    to_list() -> List[Any]:
        Returns a list representation of all internally stored values.

    peek_first() -> Any:
        Returns the first element from the internal list without removing it.

    peek_last() -> Any:
        Returns the last element from the internal list without removing it.

    pop_first() -> Any:
        Remove and return the first element from the internal list.

    pop_last() -> Any:
        Remove and return the last element from the internal list.

    merge(other: Flatlist) -> Flatlist:
        Merge the current Flatlist with specified list to return a new combined Flatlist.

    size() -> int:
        Returns the current size of the internal Flatlist.

    is_empty() -> bool:
        Returns True if the internal Flatlist at lvl. 0 is completely empty.

    clear() -> None:
        Removes all current elements from internal lists and then resets all related instances.

    __len__() -> 
    
    """

    def __init__(self, levels: Optional[int] = None, probability: Optional[float] = None):
        if levels is not None:
            if not isinstance(levels, int):
                raise TypeError(f"Levels must be of Type: int - Current type {type(levels)}")
            if levels <= 0:
                raise ValueError(f"Levels must be represented by a positive integer")
            
        if probability is not None:
            if not isinstance(probability, float):
                raise TypeError(f"Probability must be of Type: float - Current type {type(probability)}")
            if not 0 < probability <= 1.0:
                raise ValueError(f"Probability must be represented by a floating point between 0.00 - 1.00")
        
        self._inner = _RustFlatlist(levels, probability)

    def insert(self, payload: Any) -> bool:
        return self._inner.insert(payload)
    
    def remove(self, key: Any) -> Any:
        return self._inner.remove(key)
    
    def contains(self, key: Any) -> bool:
        return self._inner.contains(key)
    
    def get(self, key: Any) -> Optional[Any]:
        return self._inner.get(key)
    
    def update(self, key: Any, new_value: Any) -> bool:
        return self._inner.update(key, new_value)
    
    def extend(self, elements: Iterable[Any]) -> bool:
        return self._inner.extend(elements)
    
    def index_of(self, key: Any) -> int:
        return self._inner.index_of(key)
    
    def to_list(self) -> List[Any]:
        return self._inner.to_list()
    
    def peek_first(self) -> Any:
        return self._inner.peek_first()
    
    def peek_last(self) -> Any:
        return self._inner.peek_last()
    
    def pop_first(self) -> Any:
        return self._inner.pop_first()
    
    def pop_last(self) -> Any:
        return self._inner.pop_last()
    
    def merge(self, other: "Flatlist") -> "Flatlist":
        if not isinstance(other, Flatlist):
            raise TypeError(f"Other must be of Type: Flatlist - Current type {type(other)}")
        
        merged_inner = self._inner.merge(other._inner)
        new_flatlist = Flatlist.__new__(Flatlist)
        new_flatlist._inner = merged_inner
        return new_flatlist
    
    def size(self) -> int:
        return self._inner.size()
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.size()
    
    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __contains__(self, elements: Iterable[Any]) -> bool:
        return self._inner.contains(elements)
    
    def __iter__(self) -> Iterator[Any]:
        return iter(self._inner.to_list())