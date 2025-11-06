#---------- Imports ----------

from snaplit._rust_snaplit import ArrayStack as _RustArrayStack

from typing import Any, List, Iterable, Iterator

#---------- Array Stack Shim ----------

class ArrayStack():
    """
    ArrayStack is a high-performance, Pythonic wrapper around a Rust-powered, array-based stack data structure.

    This class leverages native Rust type safety and memory optimization for efficient array-based stack
    operations, offering quick and efficient push/pop performance, constant-time access to stack top element,
    and general utility methods tailored for real-world use. ArrayStack is particularly suited for perforamance-
    sensitive applications that requires both operation speed and memory efficiency.

    ----- Parameters -----

    size: int = 0:
        Specifies the maximum capacity of the internal stack array.
        If set to 0 (Default setting) the array is unnbounded and has no upper limit.

    ----- Methods -----

    push(value: Any) -> None:
        Push the specified value to the top of the stack.

    pop() -> Any:
        Removes and returns the current top value of the stack.

    peek() -> Any:
        Returns the current top value of the stack without mutating it.

    swap(index: int) -> None:
        Swap the current top element with the element at the specified index.

    contains(value: Any) -> bool:
        Checks if the specified value is currently present in the internal stack.

    extend(elements: Iterable[Any]) -> None:
        Push multiple elements onto the top of the current stack.

    reverse() -> None:
        Reverse the entire internal stack.

    update_top(value: Any) -> None:
        Replace the current top element with the specified value.

    to_list() -> List[Any]:
        Converts the entire internal array stack to a basic Python list.

    copy() -> ArrayStack:
        Create and return a shallow copy of the current internal stack.

    size() -> int:
        Returns the number of elements currently stored in the internal stack.

    is_empty() -> bool:
        Returns True if the current internal stack is without elements, else False.

    is_full() -> bool:
        Returns True if the current internal stack is at max capacity, else False.

    top_index() -> int:
        Returns the index number of the current top element in the internal stack.

    clear() -> None:
        Remove all elements from the internal stack.

    __len__() -> int:
        Enables the use of Python's internal 'len()' functionality. 
        Returns the current number of elements present in the innternal stack.

    __bool__() -> bool:
        Enables the use of Python's internal 'if stack' functionality.
        Returns True if the current stack contains at least one element.

    __contains__(value: Any) -> bool:
        Enables the use of Python's internal 'value in stack' functionality.
        Returns True if the current stack contains the specified value, else False.

    __iter__() -> Iterator[Any]:
        Enables the use of Python's internal iteration operations ('for x in stack').
        Returns an internal Python list that allows for iteration.

    __copy__() -> ArrayStack:
        Enables the use of Python's internal 'copy()' functionality.
        Returns a new instance of the current stack.

    ----- Example -----

    >>> stack = ArrayStack()
    >>> stack.push(10)
    >>> stack.push(50)
    >>> stack.push(40)
    >>> print(stack.peek())
    40

    >>> print(stack.pop())
    40

    >>> stack.extend([20, 25, 30])
    >>> print(stack.to_list())
    [10, 50, 20, 25, 30]

    >>> print(stack.size())
    5
    >>> print(stack.is_empty())
    False
    """
    def __init__(self, size: int = 0):
        self._inner = _RustArrayStack(size=size)

    def push(self, value: Any) -> None:
        self._inner.push(value)

    def pop(self) -> Any:
        return self._inner.pop()
    
    def peek(self) -> Any:
        return self._inner.peek()
    
    def swap(self, index: int) -> None:
        self._inner.swap(index)

    def contains(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def extend(self, elements: Iterable[Any]) -> None:
        self._inner.extend(Iterable)

    def reverse(self) -> None:
        self._inner.reverse()

    def update_top(self, value: Any) -> None:
        self._inner.update_top(value)

    def to_list(self) -> List[Any]:
        return self._inner.to_list()
    
    def copy(self) -> "ArrayStack":
        return self._inner.copy()
    
    def size(self) -> int:
        return self._inner.size()
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def is_full(self) -> bool:
        return self._inner.is_full()
    
    def top_index(self) -> int:
        return self._inner.top_index()
    
    def clear(self) -> None:
        self._inner.clear()

    def ___len__(self) -> int:
        return self._inner.size()
    
    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __contains__(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def __iter__(self) -> Iterator[Any]:
        return iter(self._inner.to_list())
    
    def __copy__(self) -> "ArrayStack":
        return self._inner.copy()
    

    
