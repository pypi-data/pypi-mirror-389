#---------- Imports ----------

from snaplit._rust_snaplit import AVLTree as _RustAVL

from typing import Any, List, Iterable, Iterator

#---------- Adelson-Velsky & Landis Tree Shim ----------

class AVLTree():
    """
    An efficient, Rust-powered implementation of a Adelson-Velsky & Landis (AVL) self-balancing Binary Search Tree.

    This AVLTree class provides efficient tree insertions, deletion and value lookups with a time complexity of
    O(lon n) by constantly maintaining tree balance after each major operations ('add', 'remove'). The AVLTree also
    supports optional duplicate operations and storage.

    Requires that individual Python entries supports __eq__ operations. 

    ----- Parameters -----

    allow_duplicates: bool = False:
        Whether to allow duplicate entries in the AVL Tree.

    ----- Methods -----

    add(value: Any) -> None:
        Inserts a value into the AVL Tree Structure.
        Implements rebalancing functionality behind-the-scene.

    remove(value: Any) -> Any:
        Removes and returns the specified value from the AVL Tree or raise a ValueError.
        Implements rebalancing functionality behind-the-scene.

    peek_root() -> Any:
        Returns the root value without mutating the current AVL Tree structure.

    contains(value: Any) -> bool:
        Checks whether the AVL Tree contains the specified value.
    
    extend(elements: Iterable[Any]) -> None:
        Add multiple elements to the AVL Tree structure.
        Implements rebalancing functionality behind-the-scene.

    min() -> int:
        Returns the smallest available value present in the AVL Tree.

    max() -> int:
        Returns the largest available value present in the AVL Tree.

    at_depth() -> int:
        Return the depth (0-based) of the specified value. Raises and ValueError if not present in AVL Tree.

    height() -> int:
        Returns the current height of the AVL Tree.

    size() -> int:
        Returns the current number of elements present in the AVL Tree. Supports duplicate entries.

    is_empty() -> bool:
        Returns True if the current AVL Tree no elements, else False.

    inorder_list() -> List[Any]:
        Returns the elements of the AVL Tree as a list using inorder traversal.

    preorder_list() -> List[Any]:
        Returns the elements of the AVL Tree as a list using preorder traversal.

    postorder_list() -> List[Any]:
        Returns the elements of the AVL Tree as a list using postorder traversal.

    BFS_list() -> List[Any]:
        Returns the elements of the AVL Tree as a list using Breadth-First Search traversal.

    copy() -> AVLTree:
        Returns a deep copy of the current AVL Tree.

    clear() -> None:
        Removes all elements from the current AVL Tree.
        An inplace operation.

    __len__() -> int:
        Enables the use of Python's internal 'len()' functionality. 
        Returns the current number of elements present in the AVL Tree.

    __bool__() -> bool:
        Enables the use of Python's internal 'if AVL' functionality.
        Returns True if the current AVL tree contains at least one element.

    __contains__(value: Any) -> bool:
        Enables the use of Python's internal 'value in AVL' functionality.
        Returns True if the curent AVL contains the specified value, else False.

    __iter__() -> Iterator:
        Enables the use of Python's internal iteration operations ('for x in AVL').
        Returns an inorder Python list that allows for iteration.

    __copy__() -> BinarySearchTree:
        Enables the use of Python's internal 'copy()' functionality.
        Returns a new instance of the current AVL.

    ----- Example -----

    >>> avl = AVLTree(allow_duplicates=allow_duplicates)
    >>> avl.add(50)
    >>> avl.add(25)
    >>> avl.add(60)
    >>> avl.add(35)
    >>> avl.add(70)

    >>> len(avl)
    5
    >>> print(avl.peek_root())
    50
    >>> 35 in avl
    True
    >>> print(avl.contains(100))
    False

    >>> print(avl.inorder_list())
    ['25', '35', '50', '60', '70']
    >>> print(avl.preorder_list())
    ['50', '25', '35', '60', '70']
    >>> print(avl.postorder_list())
    ['35', '25', '70', '60', '50']
    >>> print(avl.BFS_list())
    ['50', '25', '60', '35', '70']

    >>> print(avl.min())
    25
    >>> print(avl.max())
    75
    >>> print(avl.height())
    3
    >>> print(avl.at_depth(35))
    2
    >>> print(avl.is_empty())
    False
    """

    def __init__(self, allow_duplicates: bool = False):
        self._inner = _RustAVL(allow_duplicates=allow_duplicates)

    def add(self, value: Any) -> None:
        self._inner.add(value)

    def remove(self, value: Any) -> Any:
        return self._inner.remove(value)
    
    def peek_root(self) -> Any:
        return self._inner.peek_root()
    
    def contains(self, value: Any) -> bool:
        return self._inner.contains(value)
    
    def extend(self, elements: Iterable[Any]) -> None:
        self._inner.extend(elements)

    def min(self) -> int:
        return self._inner.min()

    def max(self) -> int:
        return self._inner.max()
    
    def at_depth(self, value: Any) -> int:
        return self._inner.at_depth(value)
    
    def height(self) -> int:
        return self._inner.height()
    
    def size(self) -> int:
        return self._inner.size()
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def inorder_list(self) -> List[any]:
        return self._inner.inorder_list()
    
    def preorder_list(self) -> List[any]:
        return self._inner.preorder_list()
    
    def postorder_list(self) -> List[any]:
        return self._inner.postorder_list()
    
    def BFS_list(self) -> List[any]:
        return self._inner.bfs_list()
    
    def copy(self) -> "AVLTree":
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
    
    def __iter__(self) -> Iterator[Any]:
        return iter(self._inner.inorder_list())
    
    def __copy__(self) -> "AVLTree":
        return self._inner.bfs_list()

