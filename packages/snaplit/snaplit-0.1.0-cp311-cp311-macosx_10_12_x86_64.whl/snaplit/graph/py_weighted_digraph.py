#---------- Imports ----------

from snaplit._rust_snaplit import WeightedDigraph as _RustWeightedDigraph

from typing import Any, List, Tuple, Optional, Union

#---------- Weighted Digraph Shim ----------

class WeightedDigraph():
    """
    A high-performance, dynamic **directional weight graph** data structure implemented in Rust.

    The 'WeightedDigraph' class provides an efficient and flexible graph interface for Python,
    backed by an optimized Rust core for swift operations on large or frequently updated networks.

    Each node is assigned a unique integer-based identifier upon insertion and can store any arbitrary
    Python object as its data payload. Edges are directed and carry a floating-point weight, representing
    the connection cost, strength or general distance between the nodes.

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

    add_edge(to_id: int, from_id: int, weight: float) -> None:
        Creates a directional, weighted edge between 2 current nodes.
        Weight represents the general connection cost between nodes.

    remove_edge(to_id: int, from_id: int) -> None:
        Removes a directional edge between 2 current nodes.

    is_connected(to_id: int, from_id: int) -> bool:
        Returns True if an edge exists between the 2 specified nodes, else False.

    get_weight(to_id: int, from_id: iny) -> float:
        Returns the weight value of the connection between specified nodes.

    total_weight() -> float:
        Returns the weight values of all edges present in Graph structure.

    has_path(to_id: int, from_id: int) -> bool:
        Returns True if a path exists between the 2 specified nodes, else False.

    has_cycle() -> bool:
        Returns True, if the internal Digraph is cyclical.

    transpose() -> Digraph:
        Creates and returns a new Digraph instance with all current nodes but inversed edges.
        Edges retain individual weight value.

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

    weighted_degree(id: int) -> float:
        Returns the total weight values of all edges connected to specified node.

    edge_count() -> int:
        Returns the total number of edges in internal Graph structure.

    density() -> float:
        Returns the current density of the Graph structure (e / (n * (n - 1))).
        e = Number of edges, n = Number of nodes.

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

    >>> test_graph = WeightedDigraph()
    >>> test_graph.insert("Aragorn")
    >>> test_graph.insert("Legolas")
    >>> test_graph.insert("Gimli")
    >>> print(test_graph.keys())
    [1, 2, 3]

    >>> test_graph.add_edge(1, 2, weight=3.5)
    >>> test_graph.add_edge(1, 3, weight=5.0)
    >>> print(test_graph.is_connected(1, 2))
    True

    >>> print(test_graph.BFS_list(start_id=1, return_value=true))
    [(1, "Aragorn"), (2, "Legolas"), (3, "Gimli")]
    """
    def __init__(self):
        self._inner = _RustWeightedDigraph()

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

    def add_edge(self, to_id: int, from_id: int, weight: float) -> None:
        if not isinstance(to_id, int):
            raise TypeError("To ID must be of Type: int")
        if not isinstance(from_id, int):
            raise TypeError("From ID must be of Type: int")
        if not isinstance(weight, float):
            raise TypeError("Weight must be of Type: float")
        
        self._inner.add_edge(to_id, from_id, weight)

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
    
    def get_weight(self, to_id: int, from_id: int) -> float:
        if not isinstance(to_id, int):
            raise TypeError("To ID must be of Type: int")
        if not isinstance(from_id, int):
            raise TypeError("From ID must be of Type: int")
        
        return self._inner.get_weight(to_id, from_id)
    
    def total_weight(self) -> float:
        return self._inner.total_weight()
    
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
    
    def weighted_degree(self, id: int) -> float:
        if not isinstance(id, int):
            raise TypeError("ID value must be of Type: int")
        
        return self._inner.weighted_degree(id)
    
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
    
    def transpose(self) -> "WeightedDigraph":
        result = WeightedDigraph()
        result._inner = self._inner.transpose()
        return result
    
    def density(self) -> float:
        return self._inner.density()
    
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