#---------- Imports ----------

from snaplit._rust_snaplit import RingBuffer as _RustRingBuffer

from typing import Any, Optional, List, Iterable

#---------- RingBuffer Shim ----------

class RingBuffer():
    """
    A high-performance overwriting Ring Buffer (Circular) data structure powered by Rust.

    The RingBuffer supports general Circular Buffer functionality as enqueue, dequeue, peek, capacity, to_list
    and subarray management. 
    Built utilizing Rust's extensive type safety, memory optimization and speef efficiency, the ringBuffer offers
    significantly recuded execution time and lessened memory overhead, compared to ordinary Python Buffers.

    ----- Parameters -----

    size: int
        The bounded size of the available elements present in the RingBuffer at initialization.

    ----- Methods -----

    enqueue(value: Any) -> None:
        Adds and element to the head (front) of the RingBuffer's internal array.

    dequeue() -> Any:
        Removes an element from the tail (back) of the RingBuffer's internal array.

    peek() -> Optional[Any]:
        Returns the head element without removing it from the internal array.

    size() -> int:
        Returns the current number of elements present in the internal array.

    capacity() -> int:
        Returns the maximum capacity of elements available in the internal array.

    extend(elements: Iterable) -> None:
        Adds each element of a Python Iterable to the head of the internal array.

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

    to_list() -> Lisst[Any]:
        Returns an iterable Python list consisting of all the RingBuffer elements.

    copy() -> RingBuffer:
        Copies the elements of the current RingBuffer and returns a new RingBuffer instance.

    subarray() -> List[Any]:
        Returns the current subarray of available values fromm the RingBuffer.

    clear() -> None:
        Removes all elements from the internal array and resets all general values.

    ----- Example -----

    >>> buffer = RingBuffer()
    >>> buffer.enqueue('Bulbasaur')
    >>> buffer.enqueue('Ivysaur')
    >>> buffer.enqueue('Venusaur')
    >>> print(buffer.size())
    3

    >>> buffer.dequeue()
    >>> print(buffer.to_list())
    ['Ivysaur', 'Venusaur']
    """

    def __init__(self, size: int):
        self._inner = _RustRingBuffer(size=size)

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
    
    def copy(self) -> "RingBuffer":
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
        self._inner.__contains__(value)

    def __copy__(self) -> "RingBuffer":
        return self._inner.copy()