#---------- Imports ----------

from snaplit._rust_snaplit import PriorityQueue as _RustPriorityQueue

from typing import Any, List, Union, Tuple, Iterable

#---------- Priority Queue Shim ----------

class PriorityQueue():
    """
    A High-performance, Rust-backed Priority Queue (heap) for Python.

    The PriorityQueue provides efficient priority-based task handling using either a **min-heap**
    or **max-heap** strategy. Built on a Rust implementation via Py03, it offers optimized performance,
    memory safety, and low overhead - making it suitable for real-time, large-scale, computationally
    intensive operations.

    Elements are enqueued with an ingeter priority and dequeued based on their priority value respecting
    the selected heap type ('min' or 'max').

    ----- Parameters -----

    heap_type: str = 'max':
        The type of heap to utilize behind the scene - 'min' or 'max'.
        Defaults to 'max'.

    ----- Methods -----

    enqueue(value: Any, priority: int) -> None:
        Add an element with the specified priority to the internal array.

    dequeue() -> Any:
        Removes and returns the element with the highest or lowest priority,
        dependant on heap type.

    peek(return_priority: bool = false) -> Any | Tuple[Any, int]:
        Returns the top element without removing it. If 'return_priority = True', 
        returns a Tuple of (value, priority).

    is_empty() -> bool:
        Returns True if the queue is currently empty, else False.

    size() -> int:
        Returns the number of elements currently in the internal array.

    is_min_heap() -> bool:
        Returns True if the heap-type is 'min', else False.

    is_max_heap() -> bool:
        Returns True if the heap-type is 'max', else False.

    contains(value: Any) -> bool:
        Checks whether a value currently exists in the internal array.

    update_priority(index: int, priority: int) -> None:
        Updates the current priority of the element at the specified index.

    search(value: Any) -> int:
        Returns the index of the specified value if present, else throw ValueError.

    remove(index: int, return_priority: bool = False) -> Any | Tuple[Any, int]:
        Removes and returns the element at the specified index.
        Optionally also returns the related priority.

    extend(elements: Iterable[Tuple[Any, int]]) -> None:
        Adds multiple '(value, priority)' pairs to the internal array.

    to_list() -> List[Any]:
        Returns a list of all given elements in heap order.

    copy() -> PriorityQueue:
        Returns a deep copy of the internal array.

    clear() -> None:
        Removes all elements from the current queue.

    __len__() -> int:
        Enables Python's 'len()' functionality to retrieve queue size.

    __bool__() -> bool:
        Enables truthiness checks on queue instance - 'if queue'.

    __contains__(value: Any) -> bool:
        Enables use of 'value in queue' functionality.

    __copy__() -> PriorityQueue:
        Enables use of Python's '.copy()' functionality.

    ----- Example -----

    >>> queue = PriorityQueue(heap_type = 'min')
    >>> queue.enqueue('Turtwig', priority=5)
    >>> queue.enqueue('Grotle', priority=2)
    >>> queue.enqueue('Torterra', priority=8)
    >>> print(queue.peek())
    Grotle

    >>> queue.dequeue()
    >>> print(queue.to_list())
    ['Turtwig', 'Torterra']

    >>> print(queue.size())
    2
    """
    def __init__(self, heap_type: str="max"):
        self._inner = _RustPriorityQueue(priority_type=heap_type)

    def enqueue(self, value: Any, priority: int) -> None:
        self._inner.enqueue(value, priority)

    def dequeue(self) -> Any:
        return self._inner.dequeue()
    
    def peek(self, return_priority: bool=False) -> Union[Any, Tuple[Any, int]]:
        return self._inner.peek(return_priority)
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()

    def size(self) -> int:
        return self._inner.size()

    def is_min_heap(self) -> bool:
        return self._inner.is_min_heap()

    def is_max_heap(self) -> bool:
        return self._inner.is_max_heap()

    def contains(self, value: Any) -> bool:
        return self._inner.contains(value)

    def update_priority(self, index: int, priority: int) -> None:
        self._inner.update_priority(index, priority)

    def search(self, value: Any) -> int:
        return self._inner.search(value)
    
    def remove(self, index: int, return_priority: bool=False) -> Union[Any, Tuple[Any, int]]:
        return self._inner.remove(index, return_priority)
    
    def extend(self, elements: Iterable) -> None:
        self._inner.extend(elements)

    def to_list(self) -> List[Any]:
        return self._inner.to_list()
    
    def copy(self) -> "PriorityQueue":
        return self._inner.copy()
    
    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.size()
    
    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __contains__(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def __copy__(self) -> "PriorityQueue":
        return self._inner.copy()

    