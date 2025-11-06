#---------- Imports ----------

from snaplit._rust_snaplit import CircularBuffer as _RustCircularBuffer

from typing import Any, Optional, List, Iterable

#---------- CircularBuffer Shim ----------

class CircularBuffer():
    """
    A fixed-szie standard Circular Buffer data structure implemented in Rust.

    Once full, the CircularBuffer raises a ValueError if the new elements are enqueued without dequeueing first.
    Provides constanct time O(1) enqueue & dequeue operations, and alos supports indexing, searching and copying.

    ----- Parameters -----

    size: int
        The maximum number of elements available in the internal array.

    ----- Methods -----

    enqueue(value: Any) -> None:
        Adds and element to the head (front) of the internal array.
        Throws ValueError if the internal array is full.

    dequeue() -> Any: 
        Removes an element from the tail (back) of the internal array.

    peek() -> Optional[Any]:
        Returns the head element without removing it from the internal array.

    size() -> int:
        Returns the current number of elements present in the internal array.

    capacity() -> int:
        Returns the maximum capacity of elements available in the internal array.

    extend(elements: Iterable) -> None:
        Adds each element of a Python Iterable to the head of the internal array.
        Throws ValueError if the number of available slots in the internal array,
        is less than elements.

    contains(value: Any) -> bool:
        Returns True if the specified value is present in the internal array, else False.

    search(value: Any) -> Optional[int]:
        Returns the index where the specified value is located in the internal array.
        If not present returns None.

    update(value: Any, index: int) -> None:
        Updates the internal value of the element at the specified index.

    is_empty() -> bool:
        Returns True if the current internal array holds no values, else False.

    is_full() -> bool:
        Returns True if the current internal array is at capacity, else False.

    to_list() -> List[Any]:
        Returns an iterable Python list consisting of all the CircularBuffer elements.

    copy() -> CircularBuffer:
        Copies the elements of the current CircularBuffer and returns a new CircularBuffer instance.

    subarray() -> List[Any]:
        Returns the current subarray of available values fromm the CircularBuffer.

    clear() -> None:
        Removes all elements from the internal array and resets all general values.

    ----- Example -----

    >>> buffer = CircularBuffer(size=10)
    >>> buffer.enqueue('Squirtle')
    >>> buffer.enqueue('Wartortle')
    >>> buffer.enqueue('Blastoise')
    >>> print(buffer.to_list())
    ['Squirtle', 'Wartortle', 'Blastoise']

    >>> print(buffer.dequeue())
    'Squirtle'

    >>> buffer.enqueue('Totodile')
    >>> buffer.enqueue('Croconaw')
    >>> buffer.enqueue('feraligatr')
    >>> print(buffer.to_list())
    ['Wartortle', 'Blastoise', 'Totodile', 'Croconaw', 'Feraligatr']

    >>> print(buffer.peek())
    'Wartortle'

    >>> print(buffer.search('Totodile'))
    2

    >>> buffer.update(value='Cyndaquil', index=0)
    >>> print(buffer.to_list())
    ['Cyndaquil', 'Blastoise', 'Totodile', 'Croconaw', 'Feraligatr']

    >>> 'Totodile' in buffer
    True
    >>> 'Celebi' in buffer
    False

    >>> buffer.clear()
    >>> print(buffer.is_empty())
    True
    """

    def __init__(self, size: int):
        self._inner = _RustCircularBuffer(size=size)

    def enqueue(self, value: Any) -> None:
        self._inner.enqueue(value)

    def dequeue(self) -> Any:
        return self._inner.dequeue()
    
    def peek(self) -> Optional[Any]:
        return self._inner.peek()
    
    def size(self) -> int:
        return self._inner.size()
    
    def capacity(self) -> int:
        return self._inner.capacity()
    
    def extend(self, elements: Iterable) -> None:
        self._inner.extend(elements)

    def contains(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def search(self, value: Any) -> Optional[int]:
        return self._inner.search(value)
    
    def update(self, value: Any, index: int) -> None:
        self._inner.update(index, value)

    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def is_full(self) -> bool:
        return self._inner.is_full()
    
    def to_list(self) -> List[Any]:
        return self._inner.to_list()
    
    def copy(self) -> "CircularBuffer":
        return self._inner.copy()
    
    def subarray(self) -> List[Any]:
        return self._inner.subarray()
    
    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.size()
    
    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __getitem__(self, value: Any) -> Any:
        return self._inner.__getitem__(value)
    
    def __contains__(self, value: Any) -> bool:
        return self._inner.__contains__(value)

    def __copy__(self) -> "CircularBuffer":
        return self._inner.copy()