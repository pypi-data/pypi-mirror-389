#---------- Imports ----------

from snaplit._rust_snaplit import Digraph as _RustDigraph

from typing import Any, List, Tuple, Optional, Union

#---------- Digraph Shim ----------

class Digraph():
    """
    A dynamic, directional graph data structure with comprehensive Python object storage, powered on the backend
    by a high-performance Rust implementation.

    Digraph allows for swift and efficient insertion, deletion, and traversal of individual nodes, 
    along with query operations on edges/nodes. Internally nodes are assigned unique, individual identifying 
    integer keys upon insertion, and can hold any Python object instance as payload.

    ----- Methods -----

    insert(item: Any) -> bool:
        Inserts a new node with specified item-value as payload.

    remove(key: int) -> Any:
        Removes node by identifying key number, and returns its internal payload.

    extract(key: int) -> Any:
        Retrieves node by identifying key number, and returns its internal payload without removing it.

    keys() -> List[int]:
        Returns a list of all unique key values stored in internal structure.

    contains(key: int) -> bool:
        Checks if a node exists by identifying key number.

    update(item: Any, key: int) -> None:
        Update the payload of an internal node by its identifying key number.

    add_edge(to_id: int, from_id: int) -> None:
        Creates an directional edge from 'from_id' -> 'to_id'.

    remove_edge(to_id: int, from_id: int) -> None:
        Removes a directional edge from 'from_id' -> 'to_id'.

    is_connected(to_id: int, from_id: int) -> bool:
        Returns True if a directional edge exists between the 2 specified nodes, else False.

    has_path(to_id: int, from_id: int) -> bool:
        Returns True if a directional path exists between the 2 specified nodes, else False.

    has_cycle() -> bool:
        Returns True, if the internal Digraph is cyclical.

    transpose() -> Digraph:
        Creates and returns a new Digraph instance with all current nodes but inversed edges. 

    neighbours(index: int) -> List[int]:
        Returns the identifying node keys of all neighbours.

    edges() -> List[Tuple[int, Any]]:
        Returns all current nodes - their identifying key-values and payloads

    BFS_list(start_id: int, return_value: Optional[bool] = False) -> Union[List[int], List[int, Any]]:
        Performs a Breadth-First Search traversal of the graph and returns ID nums.
        If 'return_value = True' also return payload values.

    DFS_list(start_id: int, return_value: Optional[bool] = False) -> Union[List[int], List[int, Any]]:
        Performs a Depth-First Search traversal of the graph and returns ID nums.
        If 'return_value = True' also return payload values.

    degree(id: int) -> int:
        Returns the number of neighbours to the specified node.

    edge_count() -> int:
        Returns the total number of edges in internal Graph structure.

    is_empty() -> bool:
        Checks if the internal Graph holds no nodes.

    node_count() -> int:
        Returns the current number of nodes present in the internal Graph structure.

    clear() -> None:
        Empties the internal Graph of all current nodes and edges.

    __len__() -> int:
        Returns the current number of nodes present in the internal Graph structure.

    __bool__() -> bool:
        Returns False if the internal Graph structure is currently empty, else True.

    __contains__(key: int) -> bool:
        Checks if a node exists by identifying key number.

    ----- Example -----

    >>> test_graph = Digraph()
    >>> test_graph.insert("Aragorn")
    >>> test_graph.insert("Legolas")
    >>> test_graph.insert("Gimli")
    >>> print(test_graph.keys())
    [1, 2, 3]

    >>> test_graph.add_edge(1, 2)
    >>> test_graph.add_edge(1, 3)
    >>> print(test_graph.is_connected(1, 2))
    True

    >>> print(test_graph.BFS_list(start_id=1, return_value=true))
    [(1, "Aragorn"), (2, "Legolas"), (3, "Gimli")]
    """
    def __init__(self):
        self._inner = _RustDigraph()

    def insert(self, item: Any) -> bool:
        return self._inner.insert(item)
    
    def remove(self, key: int) -> Any:
        if not isinstance(key, int):
            raise TypeError("Key must be of Type: int")

        return self._inner.remove(key)
    
    def extract(self, key: int) -> Any:
        if not isinstance(key, int):
            raise TypeError("Key must be of Type: int")
        
        return self._inner.extract(key)
    
    def keys(self) -> List[int]:
        return self._inner.keys()
    
    def contains(self, key: int) -> bool:
        if not isinstance(key, int):
            raise TypeError("Key must be of Type: int")
        
        return self._inner.contains(key)
    
    def update(self, item: Any, index: int) -> None:
        if not isinstance(index, int):
            raise TypeError("Index must be of Type: int")
        
        self._inner.update(item, index)

    def add_edge(self, to_id: int, from_id: int) -> None:
        if not isinstance(to_id, int):
            raise TypeError("To ID must be of Type: int")
        if not isinstance(from_id, int):
            raise TypeError("From ID must be of Type: int")
        
        self._inner.add_edge(to_id, from_id)

    def remove_edge(self, to_id: int, from_id: int) -> None:
        if not isinstance(to_id, int):
            raise TypeError("To ID must be of Type: int")
        if not isinstance(from_id, int):
            raise TypeError("From ID must be of Type: int")
        
        self._inner.remove_edge(to_id, from_id)

    def is_connected(self, to_id: int, from_id: int) -> bool:
        if not isinstance(to_id, int):
            raise TypeError("To ID must be of Type: int")
        if not isinstance(from_id, int):
            raise TypeError("From ID must be of Type: int")
        
        return self._inner.is_connected(to_id, from_id)
    
    def neighbours(self, index: int) -> List[int]:
        if not isinstance(index, int):
            raise TypeError("Index must be of Type: int")
        
        return self._inner.neighbours(index)
    
    def edges(self) -> List[Tuple[int, Any]]:
        return self._inner.edges()
    
    def BFS_list(self, start_id: int, return_value: Optional[bool] = False) -> Union[List[int], List[Tuple[int, Any]]]:
        if not isinstance(start_id, int):
            raise TypeError("Starting ID must be of Type: int")
        if not isinstance(return_value, bool):
            raise TypeError("Return value must be of Type: bool")
        
        return self._inner.bfs_list(start_id, return_value)
    
    def DFS_list(self, start_id: int, return_value: Optional[bool] = False) -> Union[List[int], List[Tuple[int, Any]]]:
        if not isinstance(start_id, int):
            raise TypeError("Starting ID must be of Type: int")
        if not isinstance(return_value, bool):
            raise TypeError("Return value must be of Type: bool")
        
        return self._inner.dfs_list(start_id, return_value)
    
    def degree(self, id: int) -> int:
        return self._inner.degree(id)
    
    def edge_count(self) -> int:
        return self._inner.edge_count()
    
    def has_path(self, to_id: int, from_id: int) -> bool:
        if not isinstance(to_id, int):
            raise TypeError("To ID must be of Type: int")
        if not isinstance(from_id, int):
            raise TypeError("From ID must be of Type: int")
        
        return self._inner.has_path(to_id, from_id)
    
    def has_cycle(self) -> bool:
        return self._inner.has_cycle()
    
    def transpose(self) -> "Digraph":
        result = Digraph()
        result._inner = self._inner.transpose()
        return result
    
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def node_count(self) -> int:
        return self._inner.node_count()
    
    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.node_count()
    
    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __contains__(self, item: int) -> bool:
        return self._inner.contains(item)

    def __iter__(self):
        return iter(self._inner.keys())