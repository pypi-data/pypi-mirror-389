#---------- Imports ----------

from snaplit._rust_snaplit import HyperGraph as _RustHypergraph

from typing import Any, List, Optional

#---------- Hypergraph Shim ----------

class Hypergraph():
    """
    A high-performance hypergraph data structure for representing relationsships between arbitrary
    entities, powered by a comprehensive Rust backend.

    A hypergraph generalizes a ordinary graph structure by allowing edges (called 'hyperedges') to connect
    any number of nodes, rather than just 2. This makes the graph-class ideal for modeling complex, many-to-many
    relationships, such as memmberships or multi-agent systems.

    The Hypergraph class provides efficient and optimized methods for manipulating nodes and edges, structural queries,
    and topological measurements. Internally operations arepowered by Rust, ensuring low-latency insertion,
    deletion and traversal or large graphs.

    ----- Methods -----

    insert(payload: Any) -> None:
        Inserts a new node with the specified Python payload.

    remove(key: int) -> Any:
        Remove a node and return its internal payload.

    extract(key: int) -> Any:
        Retrieves and returns the internal node's payload without removing it.

    update(payload: Any, id: int) -> None:
        Replace the existing payload of the specified node with new value.

    contains(id: int) -> bool:
        Checks whether node with specified ID exists in the internal Graph.

    keys() -> list[int]:
        Return the ID keys of all nodes currently sstored in the internal Graph.

    add_edge(id: str, vertices: Option[list[nt]] = None) -> None:
        Creates a new hyperedge and connect one or more existing nodes.

    remove_edge(id: str) -> bool:
        Remove a hyperedge by its identifying string-ID

    connect(edge_id: str, node_id: int) -> None:
        Add a node to an existing hyperedge.

    disconnect(edge_id: str, node_id: int) -> None:
        Remove a node from an existing hyperedge.

    edges() -> list[str]:
        Return all hyperedge identifying keys.

    edge_count() -> int:
        Return the number of hyperedges currently present in the internal Graph.

    node_count() -> int:
        Return the number of nodes currently present in the internal Graph.

    edge_size(edge_id: str) -> int:
        Returns the number of nodes currently present within the specified hyperedge.

    is_connected(edge_id: str, node_id: int) -> bool:
        Determines whether a node exists within the specified hyperedge.

    edges_of(node_id: int) -> list[str]:
        List all hyperedges that include the given node.

    nodes_of(edge_id: str) -> list[int]:
        List all nodes that exist within the specified hyperedge.

    intersection(edge_id1: str, edge_id2: str) -> list[int]:
        Compute the intersecting nodes between 2 hyperedges.

    degree(node_id: int) -> int:
        Return the number of hyperedges attached to the specified node.

    max_degree() -> int:
        Returns the largest degree number amongst all nodes.

    min_degree() -> int:
        Returns the smallest degree number amongst all nodes.

    average_degree() -> float:
        Returns the average degree number amongst all nodes.

    is_empty() -> bool:
        Returns True if the internal Graph holds no nodes.

    clear() -> None:
        Removes all nodes and hyperedges, resetting the entire internal Graph structure.

    __len__() -> int:
        Returns the current number of nodes in Graph structure ('len(hypergraph)')

    __bool__() -> bool:
        Returns True is the current Graph structure is not empty ('if hypergraph:')

    __contains__(id: int) -> bool:
        Returns True if the specified node is present in the internal Graph ('id in hypergraph')

    __iter__() -> Iterator:
        Iterates over node IDs in the internal Graph structure.
    """

    def __init__(self):
        self._inner = _RustHypergraph()

    def insert(self, payload: Any) -> bool:
        return self._inner.insert(payload)
    
    def remove(self, key: int) -> Any:
        if not isinstance(key, int):
            raise TypeError(f"Key must be of Type: int - Current type {type(key)}")
        
        return self._inner.remove(key)
    
    def extract(self, key: int) -> Any:
        if not isinstance(key, int):
            raise TypeError(f"Key must be of Type: int - Current type {type(key)}")
        
        return self._inner.extract(key)
    
    def keys(self) -> List[int]:
        return self._inner.keys()
    
    def contains(self, key: int) -> bool:
        if not isinstance(key, int):
            raise TypeError(f"Key must be of Type: int - Current type {type(key)}")
        
        return self._inner.contains(key)
    
    def update(self, payload: Any, id: int) -> None:
        if not isinstance(id, int):
            raise TypeError(f"ID must be of Type: int - Current type {type(id)}")
        
        self._inner.update(payload, id)

    def add_edge(self, id: str, vertices: Optional[List[int]] = None) -> None:
        if not isinstance(id, str):
            raise TypeError(f"ID must be of Type: str - Current type {type(id)}")
        if vertices is not None and not isinstance(vertices, list):
            raise TypeError(f"Vertices must be of Type: List[int] - Current type {type(vertices)}")
        
        self._inner.add_edge(id, vertices)

    def remove_edge(self, id: str) -> bool:
        if not isinstance(id, str):
            raise TypeError(f"ID must be of Type: str - Current type {type(id)}")
        
        return self._inner.remove_edge(id)
    
    def connect(self, edge_id: str, node_id: int) -> None:
        if not isinstance(edge_id, str):
            raise TypeError(f"Edge ID must be of Type: str - Current type {type(edge_id)}")
        if not isinstance(node_id, int):
            raise TypeError(f"Node ID must be of Type: int - Current type {type(node_id)}")
        
        self._inner.connect(edge_id, node_id)

    def disconnect(self, edge_id: str, node_id: int) -> None:
        if not isinstance(edge_id, str):
            raise TypeError(f"Edge ID must be of Type: str - Current type {type(edge_id)}")
        if not isinstance(node_id, int):
            raise TypeError(f"Node ID must be of Type: int - Current type {type(node_id)}")
        
        self._inner.disconnect(edge_id, node_id)

    def edges(self) -> List[str]:
        return self._inner.edges()
    
    def is_connected(self, edge_id: str, node_id: int) -> bool:
        if not isinstance(edge_id, str):
            raise TypeError(f"Edge ID must be of Type: str - Current type {type(edge_id)}")
        if not isinstance(node_id, int):
            raise TypeError(f"Node ID must be of Type: int - Current type {type(node_id)}")
        
        return self._inner.is_connected(edge_id, node_id)
    
    def edges_of(self, node_id: int) -> List[str]:
        if not isinstance(node_id, int):
            raise TypeError(f"Node ID must be of Type: int - Current type {type(node_id)}")
        
        return self._inner.edges_of(node_id)
    
    def nodes_of(self, edge_id: str) -> List[int]:
        if not isinstance(edge_id, str):
            raise TypeError(f"Edge ID must be of Type: str - Current type {type(edge_id)}")
        
        return self._inner.nodes_of(edge_id)
    
    def intersection(self, edge_id1: str, edge_id2: str) -> List[int]:
        if not isinstance(edge_id1, str):
            raise TypeError(f"Edge ID 1 must be of Type: str - Current type {type(edge_id1)}")
        if not isinstance(edge_id2, str):
            raise TypeError(f"Edge ID 2 must be of Type: str - Current type {type(edge_id2)}")
        
        return self._inner.intersection(edge_id1, edge_id2)
    
    def degree(self, node_id: int) -> int:
        if not isinstance(node_id, int):
            raise TypeError(f"Node ID must be of Type: int - Current type {type(node_id)}")
        
        return self._inner.degree(node_id)
    
    def max_degree(self) -> int:
        return self._inner.max_degree()
    
    def min_degree(self) -> int:
        return self._inner.min_degree()
    
    def average_degree(self) -> float:
        return self._inner.average_degree()
    
    def edge_size(self, edge_id: str) -> int:
        if not isinstance(edge_id, str):
            raise TypeError(f"Edge ID must be of Type: str - Current type {type(edge_id)}")
        
        return self._inner.edge_size(edge_id)
        
    def is_empty(self) -> bool:
        return self._inner.is_empty()
    
    def node_count(self) -> int:
        return self._inner.node_count()
    
    def edge_count(self) -> int:
        return self._inner.edge_count()
    
    def clear(self) -> None:
        self._inner.clear()

    def __len__(self) -> int:
        return self._inner.node_count()

    def __bool__(self) -> bool:
        return not self._inner.is_empty()
    
    def __contains__(self, id: int) -> bool:
        if not isinstance(id, int):
            raise TypeError(f"ID must be of Type: int - Current type {type(id)}")
        
        return self._inner.contains(id)
    
    def __iter__(self):
        for key in self._inner.keys():
            yield key