#---------- Imports ----------

from snaplit._rust_snaplit import Queue as _RustQueue

from typing import Any, Optional, List, Iterator

#---------- Queue Shim ----------

class Queue():
    """
    A high-performance standard, unbounded Queue data structure powered by Rust.

    The Queue supports ordinary queue operations as enqueue, dequeue, peek, search, to_list and copy. 
    Built utilizing Rust's extensive type safety, memory optimization and speed, the Queue offers
    significantly recuded execution time and lessened memory overhead, compared to ordinary Python
    implementations.

    ----- Methods -----

    enqueue(value: Any) -> None:
        Adds an element to the head of the Queue.

    dequeue() -> Optional[Any]:
        Removes and returns an element from the front of the Queue.

    peek() -> Optional[Any]:
        Returns the element from the front of the Queue without mutating it.

    size() -> int:
        Returns the current number of elements in the Queue.

    is_empty() -> bool:
        Returns True is the current Queue holds no elements, else False.

    contains(value: Any) -> bool:
        Returns True is the specified value is present in the current Queue, else False.

    search(value: Any) -> Optional[int]:
        Returns the index of the specified value, or None is the value is nor present.

    to_list() -> List[Any]:
        Returns an iterable list of the elements present in the Queue.

    copy() -> Queue:
        Produces and returns a shallow copy of the current Queue.

    clear() -> None:
        Deletes all elements in the Queue.

    __len__() -> int:
        Returns the current number of elements in the Queue.

    __bool__() -> bool:
        Returns True is the current Queue is not empty, else False.

    __contains__(value: Any) -> bool:
        Returns True is the specified value is present in the current Queue, else False.

    __iter__() -> Iterator[Any]:
        Returns an Iterator version of the current Queue elements.

    ----- Example -----
    
    >>> queue = Queue()
    >>> print(queue.is_empty())
    True

    >>> queue.enqueue('Charmander')
    >>> queue.enqueue('Charmeleon')
    >>> queue.enqueue('Charizard')
    >>> print(queue.size())
    3

    >>> print(queue.peek())
    'Charmander'

    >>> print(queue.dequeue())
    'Charmander'

    >>> print(queue.to_list())
    ['Charmeleon', 'Charizard']

    >>> print(queue.search('Charizard'))
    1
    >>> print(queue.search('Squirtle'))
    None
    """

    def __init__(self):
        self._inner = _RustQueue()

    def enqueue(self, value: Any) -> None:
        self._inner.enqueue(value)

    def dequeue(self) -> Optional[Any]:
        return self._inner.dequeue()

    def peek(self) -> Optional[Any]:
        return self._inner.peek()
    
    def size(self) -> int:
        return self._inner.size()
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def contains(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def search(self, value: Any) -> Optional[int]:
        return self._inner.search(value)
    
    def to_list(self) -> List[Any]:
        return self._inner.to_list()
    
    def copy(self) -> "Queue":
        return self._inner.copy()
    
    def clear(self) -> None:
        self._inner.clear()

    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __len__(self) -> int:
        return self._inner.size()
    
    def __contains__(self, value: Any) -> Any:
        return self._inner.contains(value)
    
    def __iter__(self) -> Iterator[Any]:
        return iter(self._inner.to_list())