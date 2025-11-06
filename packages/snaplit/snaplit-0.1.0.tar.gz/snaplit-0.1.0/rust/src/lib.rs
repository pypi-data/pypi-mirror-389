// Imports
use pyo3::prelude::*;
// rust mods
mod linear;
mod trees;
mod graph;
mod hashing;
mod probability;
mod other;

// imports from rust folders (Linear)
use linear::linked_list_native::LinkedList;
use linear::stack_native::Stack;
use linear::rs_array_stack_native::ArrayStack;
use linear::queue_native::Queue;
use linear::ring_buffer_native::RingBuffer;
use linear::circular_buffer_native::CircularBuffer;
use linear::priority_queue_native::PriorityQueue;

// imports from rust folders (Tree)
use trees::rs_binary_tree_native::BinarySearchTree;
use trees::rs_avl_tree_native::AVLTree;
use trees::rs_trie_native::Trie;

// imports from rust folders (Graph)
use graph::rs_base_graph_native::BaseGraph;
use graph::rs_digraph_native::Digraph;
use graph::rs_weighted_graph_native::WeightedGraph;
use graph::rs_weighted_digraph_native::WeightedDigraph;
use graph::rs_hypergraph_native::HyperGraph;

// imports from rust folders (Hashing);
use hashing::rs_snapmap_native::SnapMap;
use hashing::rs_rhoodmap_native::RhoodMap;

// imports from rust folders (Probability)
use probability::rs_bloom_filter_native::BloomFilter;
use probability::rs_cuckoo_filter_native::CuckooFilter;
use probability::rs_flatlist_native::Flatlist;

// Final export to Python
#[pymodule]
pub fn _rust_snaplit(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<LinkedList>()?;
    m.add_class::<Stack>()?;
    m.add_class::<ArrayStack>()?;
    m.add_class::<Queue>()?;
    m.add_class::<RingBuffer>()?;
    m.add_class::<CircularBuffer>()?;
    m.add_class::<PriorityQueue>()?;
    m.add_class::<BinarySearchTree>()?;
    m.add_class::<AVLTree>()?;
    m.add_class::<Trie>()?;
    m.add_class::<SnapMap>()?;
    m.add_class::<RhoodMap>()?;
    m.add_class::<BloomFilter>()?;
    m.add_class::<CuckooFilter>()?;
    m.add_class::<Flatlist>()?;
    m.add_class::<BaseGraph>()?;
    m.add_class::<Digraph>()?;
    m.add_class::<WeightedGraph>()?;
    m.add_class::<WeightedDigraph>()?;
    m.add_class::<HyperGraph>()?;
    Ok(())
}
