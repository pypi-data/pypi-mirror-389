#---------- Imports ----------

from snaplit._rust_snaplit import Stack as _RustStack

from typing import Any, Optional, List, Iterator

#---------- Linked List Shim ----------

class Stack():
    """
    A high-performance Stack data structure powered by Rust.

    This Stack supports efficient push, copy, pop, peek, to_list and swap functionality. 
    Built utilizing Rust's extensive type safety, memory optimization and speed, the Stack offers
    significantly recuded execution time and lessened memory overhead, compared to ordinary Python
    implementations.

    ----- Methods -----

    push(value: Any) -> None:
        Add an element to the top of the Stack.

    pop() -> Optional[Any]:
        Removes and returns the top element of the Stack.

    peek() -> Optional[Any]:
        Returns the top value of the Stack without mutating it.

    size() -> int:
        Returns the current number of elements in the Stack.

    swap(index: Optional[int] = None) -> None:
        Swaps the element at the epcified index with the top of the Stack.
        If None, swaps the top 2 elements.

    contains(value: Any) -> bool:
        Returns True is the current Stack contains the specified value, else return False.

    copy() -> Stack:
        Produces and returns a shallow copy of the current Stack.

    is_empty() -> bool:
        Returns True if the current Stack holds no elements.

    to_list() -> List[Any]:
        Returns and interable list of the elements in the Stack.

    reverse() -> None:
        Reverses the order of the Stack in place.

    update_top(value: Any) -> None:
        Updates the current value of the top element.

    clear() -> None:
        Deletes all elements in the Stacks.

    __len__() -> int:
        Returns the current number of elements in the Stack.

    __contains__(value: Any) -> bool:
        Returns True is the current Stack contains the specified value, else return False.

    __bool__() -> bool:
        Returns True is the current Stack has at least one element, else return False.

    __iter__() -> Iterator[Any]:
        Returns an iterator version of the current Stack elements.

    ----- Example -----

    >>> stack = Stack()
    >>> stack.push(10)
    >>> stack.push(20)
    >>> stack.push(30)
    >>> print(stack.peek())
    30

    >>> stack.swap()
    >>> print(stack.to_list())
    [10, 30, 20]

    >>> new_stack = stack.copy()
    >>> print(new_stack.to_list())
    [10, 30, 20]

    >>> stack.reverse()
    >>> print(stack.to_list())
    [20, 30, 10]

    >>> while stack:
    >>>     print(stack.pop())
    20 -> 30 -> 10
         
    """
    def __init__(self):
        self._inner = _RustStack()

    def push(self, value: Any) -> None:
        self._inner.push(value)

    def pop(self) -> Optional[Any]:
        return self._inner.pop()

    def peek(self) -> Optional[Any]:
        return self._inner.peek()
    
    def size(self) -> int:
        return self._inner.size()
    
    def swap(self, index: Optional[int] = None) -> None:
        idx = index if index is not None else 1 
        self._inner.swap(idx)

    def contains(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def copy(self) -> "Stack":
        return self._inner.copy()
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def to_list(self) -> List[Any]:
        return self._inner.to_list()
    
    def reverse(self) -> None:
        self._inner.reverse()

    def update_top(self, value: Any) -> None:
        self._inner.update_top(value)

    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.size()
    
    def __contains__(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def __bool__(self) -> bool:
        return not self.is_empty()
    
    def __iter__(self) -> Iterator[Any]:
        return iter(self.to_list())