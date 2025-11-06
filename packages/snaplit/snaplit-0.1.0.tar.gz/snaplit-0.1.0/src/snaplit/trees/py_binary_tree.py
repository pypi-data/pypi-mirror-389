#---------- Imports ----------

from snaplit._rust_snaplit import BinarySearchTree as _RustBST

from typing import Any, List, Iterable

#---------- Binary Search Tree Shim ----------

class BinarySearchTree():
    """
    A memory- and performance-efficient Binary Search Tree (BST) backed by Rust backend and functionality.

    This class provide a Pythonic interface to an extensive Rust-powered BST and its operations. 
    Leveraging Rust's strong type safety, zero-cost abstractions, and efficient memory management, this Python
    class allows users to utilize fast and safe BST operations with a familiar API.

    Requires that individual Python entries supports __eq__ operations. 

    ----- Parameters -----

    allow_duplicates: bool = False
        Whether to allow duplicate entries in the BST.

    ----- Methods -----

    add(value: Any) -> None:
        Insert a value into the BST structure.
        Value must support __eq__ operation.

    remove(value: Any) -> Any:
        Removes and returns the specified value from the BST or raises an ValueError.
        Value must support __eq__ operation.

    prune() -> None:
        Deletes all leaf nodes from the BST (individual nodes with NO child nodes).

    peek_root() -> Any:
        Returns the current root node vlaue without mutating the current BST.

    contains(value: Any) -> bool:
        Checks whether the BST contains the specified value.
        Value must support __eq__ operation.

    extend(elements: Iterable) -> None:
        Add multiple elements to BST.
        Individual elements must support __eq__ operation.

    min() -> Any:
        Returns the smallest value present in the BST. 
        Internal elements must support __eq__ operation.

    max() -> Any:
        Returns the largest value present in the BST. 
        Internal elements must support __eq__ operation.

    at_depth(value: Any) -> int:
        Return the depth (0-based) of the specified value. Raises and ValueError if not present in BST. 
        Value must support __eq__ operation.

    height() -> int:
        Returns the current height of the BST.

    size() -> int:
        Returns the current number of elements present in the BST. Supports duplicate entries.

    is_empty() -> bool:
        Returns True is the current BST contains no elements, else False.

    inorder_list() -> List[Any]:
        Returns the elements of the BST as a list using inorder traversal.

    preorder_list() -> List[Any]:
        Returns the elements of the BST as a list using preorder traversal.

    postorder_list() -> List[Any]:
        Returns the elements of the BST as a list using postorder traversal
        
    BFS_list() -> List[Any]:
        Returns the lements of the BST as a list using breadth-first traversal.

    copy() -> BinarySearchTree:
        Returns a deep copy of the current BST instance.

    clear() -> None:
        Removes all elements from the current BST.
        An inplace operation. 

    __len__() -> int:
        Enables the use of Python's internal 'len()' functionality. 
        Returns the current number of elements present in the BST.  
    
    __bool__() -> bool:
        Enables the use of Python's internal 'if BST' functionality.
        Returns True if the current BST contains at least one element.

    __contains__(value: Any) -> bool:
        Enables the use of Python's internal 'value in BST' functionality.
        Returns True if the curent BST contains the specified value, else False.

    __iter__() -> Iterator:
        Enables the use of Python's internal iteration operations ('for x in BST').
        Returns an inorder Python list that allows for iteration.

    __copy__() -> BinarySearchTree:
        Enables the use of Python's internal 'copy()' functionality.
        Returns a new instance of the current BST. 

    ----- Example -----

    >>> bst = BinarySearchTree(allow_duplicates=False)
    >>> bst.add(10)
    >>> bst.add(5)
    >>> bst.add(15)

    >>> print(bst.inorder_list())
    [5, 10, 15]
    >>> print(bst.contains(10))
    True
    >>> print(bst.contains(20))
    False
    >>> print(bst.peek_root())
    10
    >>> print(bst.size())
    3
    >>> print(bst.height())
    1
    """

    def __init__(self, allow_duplicates: bool=False):
        self._inner = _RustBST(allow_duplicates=allow_duplicates)

    def add(self, value: Any) -> None:
        self._inner.add(value)

    def remove(self, value: Any) -> Any:
        return self._inner.remove(value)

    def prune(self) -> None:
        self._inner.prune()

    def peek_root(self) -> Any:
        return self._inner.peek_root()

    def contains(self, value: Any) -> bool:
        return self._inner.contains(value)

    def extend(self, elements: Iterable) -> None:
        self._inner.extend(elements)

    def min(self) -> Any:
        return self._inner.min()

    def max(self) -> Any:
        return self._inner.max()

    def at_depth(self, value: Any) -> int:
        return self._inner.at_depth(value)

    def height(self) -> int:
        return self._inner.height()

    def size(self) -> int:
        return self._inner.size()

    def is_empty(self) -> bool:
        return self._inner.is_empty()

    def inorder_list(self) -> List[Any]:
        return self._inner.inorder_list()

    def preorder_list(self) -> List[Any]:
        return self._inner.preorder_list()

    def postorder_list(self) -> List[Any]:
        return self._inner.postorder_list()

    def BFS_list(self) -> List[Any]:
        return self._inner.bfs_list()

    def copy(self) -> "BinarySearchTree":
        new_instance = self._inner.copy()
        new_tree = self.__class__.__new__(self.__class__)
        new_tree._inner = new_instance
        return new_tree

    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.size()

    def __bool__(self) -> bool:
        return not self._inner.is_empty()

    def __contains__(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def __iter__(self):
        return iter(self.inorder_list())

    def __copy__(self) -> "BinarySearchTree":
        return self.copy()