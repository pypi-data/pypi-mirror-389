#---------- Imports ----------

from snaplit._rust_snaplit import LinkedList as _RustLinkedList

from typing import Any, Optional, List, Iterator

#---------- Linked List Shim ----------

class LinkedList():
    """
    A high-performance linked list data structure powered by Rust.

    The linked list supports efficient prepend, append, add, get, insert and search operations.
    By leveraging Rust's speed and type safety, it offers faster execution and lower memory overhead,
    compared to pure Python implementations, while providing a Python interface.

    ----- Methods -----

    prepend(value: Any) -> None:
        Add an element to the start(head) of the list.

    append(value: Any) -> None:
        Add an element to the end(tail) of the list.

    remove_head() -> Optional[Any]:
        Remove and return the current head of the list. Returns None if list is empty.

    insert(value: Any, index: Optional[int] = None) -> None:
        Inserts a new element at the specified index. If index is None append the lement to the end.

    get(index: int) -> Any:
        Retrieve the element at the specified index.

    contains(value: Any) -> bool:
        Returns True is the value is contained within the list, else False.

    pop(index: Opitional[int] = None) -> Any:
        Remove and return the element at the specified index.
        Defaults to tail element is index is None.

    remove(index: int) -> Optional[Any]:
        Remove and return the lement at the specified index.
        Returns None if the index is out of bounds.

    search(value: Any) -> Optional[int]:
        Return the index of the first occurence of the value in the list, or None if value not found.

    update(value: Any, index: int) -> None:
        Update the element at the specified index.

    to_list() -> List[Any]:
        Converts the linked list int a native Python list

    clear() -> None:
        Remove all elements from the linked list.

    __len__() -> int:
        Return the number of elements currently in the list.

    __getitem__(index: int) -> Any:
        Enable bracket notation to retrive elements eg. linked_list[index].

    __setitem__(value: Any, index: int) -> None:
        Enable bracket notation to set list elements eg. linked_list[index] = value.

    __delitem__(index: int) -> None:
        Enable the deletion of elements by index eg. del linked_list[index].

    __contains__(value: Any) -> bool:
        Enable native Python membership checking in list eg. value in linked_list.

    ----- Example -----

    >>> ll = LinkedList()
    >>> ll.append(10)
    >>> ll.prepend(5)
    >>> print(ll.to_list())
    [5, 10]
    >>> print(len(ll))
    2
    >>> ll.update(15, 1)
    >>> print(ll.get(1))
    15
    >>> print(10 in ll)
    False
    >>> print(15 in ll)
    True
    """
    def __init__(self):
        self._inner = _RustLinkedList()

    def prepend(self, value: Any) -> None:
        self._inner.prepend(value)

    def append(self, value: Any) -> None:
        self._inner.append(value)

    def remove_head(self) -> Optional[Any]:
        return self._inner.remove_head()

    def insert(self, value: Any, index: Optional[int] = None) -> None:
        self._inner.insert(value, index)

    def get(self, index: int) -> Any:
        return self._inner.get(index)

    def contains(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def pop(self, index: Optional[int] = None) -> Any:
        return self._inner.pop(index)
    
    def remove(self, index: int) -> Optional[Any]:
        return self._inner.remove(index)
    
    def search(self, value: Any) -> Optional[int]:
        return self._inner.search(value)
    
    def update(self, value: Any, index: int) -> None:
        self._inner.update(value, index)

    def to_list(self) -> List[Any]:
        return list(self._inner.to_list())
    
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
    
    def __contains__(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def __getitem__(self, index: int) -> Any:
        return self._inner.get(index)
    
    def __setitem__(self, value: Any, index: int) -> None:
        self._inner.update(value, index)

    def __delitem__(self, index: int) -> None:
        self._inner.remove(index)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._inner.to_list())
    