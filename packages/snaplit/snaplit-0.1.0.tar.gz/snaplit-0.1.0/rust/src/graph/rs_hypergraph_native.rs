use pyo3::{exceptions::PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyList};
use pyo3::PyObject;
use rustc_hash::{FxHashMap, FxHashSet};

#[allow(dead_code)]
#[derive(Debug, Clone)]
struct HyperNode {
    node_id: usize,
    payload: PyObject,
}

#[allow(dead_code)]
impl HyperNode {
    fn new(id: usize, payload: PyObject) -> Self {
        Self {
            node_id: id,
            payload: payload,
        }
    }
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
struct HyperEdge {
    edge_id: String,
    vertices: FxHashSet<usize>,
}

impl HyperEdge {
    fn new(id: String) -> Self {
        Self {
            edge_id: id, 
            vertices: FxHashSet::default(),
        }
    }
}

impl HyperGraph {
    fn node_removal(&mut self, id: usize) {
        if let Some(edge_ids) = self.node_to_edge.remove(&id) {
            for edge_id in edge_ids {
                if let Some(edge) = self.hyperedges.get_mut(&edge_id) {
                    edge.vertices.remove(&id);
                }
            }
        }
    }
}

#[pyclass]
pub struct HyperGraph {
    nodes: FxHashMap<usize, HyperNode>,
    hyperedges: FxHashMap<String, HyperEdge>,
    node_to_edge: FxHashMap<usize, FxHashSet<String>>,
    next_id: usize,
}

#[pymethods]
impl HyperGraph {
    #[new]
    pub fn new() -> Self {
        Self {
            nodes: FxHashMap::default(),
            hyperedges: FxHashMap::default(),
            node_to_edge: FxHashMap::default(),
            next_id: 1,
        }
    }

    pub fn insert(&mut self, payload: PyObject) -> PyResult<bool> {
        let new_node = HyperNode::new(self.next_id, payload);

        if self.nodes.contains_key(&self.next_id) {
            return Ok(false);
        } else {
            let id = self.next_id;
            self.nodes.insert(id, new_node);
            self.next_id += 1;
            Ok(true)
        }
    }

    pub fn remove(&mut self, py: Python, key: usize) -> PyResult<PyObject> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        match self.nodes.remove(&key) {
            Some(value) => {
                Self::node_removal(self, key);
                return Ok(value.payload.clone_ref(py));
            },
            None => return Err(PyValueError::new_err("Value not found in graph")),
        }
    }

    pub fn extract(&self, py: Python, key: usize) -> PyResult<PyObject> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let node = self.nodes.get(&key);
        match node {
            Some(value) => return Ok(value.payload.clone_ref(py)),
            None => return Err(PyValueError::new_err("Value not found in Graph")),
        }
    }

    pub fn keys<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        Ok(PyList::new(py, self.nodes.keys()))
    }

    pub fn contains(&self, key: usize) -> PyResult<bool> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let result = self.nodes.contains_key(&key);
        Ok(result)
    }

    pub fn update(&mut self, py: Python, payload: PyObject, id: usize) -> PyResult<()> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let new_node = match self.nodes.get_mut(&id) {
            Some(node_value) => node_value,
            None => return Err(PyValueError::new_err("Value not found in graph")),
        };

        new_node.payload = payload.clone_ref(py);
        Ok(())
    }

    pub fn add_edge(&mut self, id: String, vertices: Option<Vec<usize>>) -> PyResult<()> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if self.hyperedges.contains_key(&id) {
            return Err(PyValueError::new_err(format!("Edge {} already exists!", id)));
        }

        let mut new_edge = HyperEdge::new(id.clone());

        if let Some(vs) = vertices {
            for node_id in vs {
                if !self.nodes.contains_key(&node_id) {
                    return Err(PyValueError::new_err(format!("Node with ID {} does not exist in Graph", node_id)));
                }
                new_edge.vertices.insert(node_id);

                self.node_to_edge.entry(node_id).or_default().insert(id.clone());
            }
        }

        self.hyperedges.insert(id, new_edge);

        Ok(())
    }

    pub fn remove_edge(&mut self, id: String) -> PyResult<bool> {
        if let Some(edge) = self.hyperedges.remove(&id) {
            for node_id in edge.vertices {
                if let Some(edges) = self.node_to_edge.get_mut(&node_id) {
                    edges.remove(&id);
                    if edges.is_empty() {
                        self.node_to_edge.remove(&node_id);
                    }
                }
            }
            Ok(true)
        } else {
            Ok(false)
        }
    } 

    pub fn connect(&mut self, edge_id: &str, node_id: usize) -> PyResult<()> {
        if !self.hyperedges.contains_key(edge_id) {
            return Err(PyValueError::new_err(format!("Edge with ID {} not found!", edge_id)));
        }

        if !self.nodes.contains_key(&node_id) {
            return Err(PyValueError::new_err(format!("Node with ID {} not found!", node_id)));
        }

        let edge = self.hyperedges.get_mut(edge_id).unwrap();
        edge.vertices.insert(node_id);

        self.node_to_edge.entry(node_id).or_default().insert(edge_id.to_string());

        Ok(())
    }

    pub fn disconnect(&mut self, edge_id: &str, node_id: usize) -> PyResult<()> {
        if !self.hyperedges.contains_key(edge_id) {
            return Err(PyValueError::new_err(format!("Edge with ID {} not found!", edge_id)));
        }

        if !self.nodes.contains_key(&node_id) {
            return Err(PyValueError::new_err(format!("Node with ID {} not found!", node_id)));
        }

        let edge = self.hyperedges.get_mut(edge_id).unwrap();
        edge.vertices.remove(&node_id);

        if let Some(edges) = self.node_to_edge.get_mut(&node_id) {
            edges.remove(edge_id);
            if edges.is_empty() {
                self.node_to_edge.remove(&node_id);
            }
        }
        Ok(())
    }

    pub fn edges<'py>(&self, py: Python<'py>,) -> PyResult<&'py PyList> {
        if self.hyperedges.is_empty() {
            return Err(PyValueError::new_err("No hyper edges currently available in Graph"));
        }

        Ok(PyList::new(py, self.hyperedges.keys()))
    }

    pub fn is_connected(&self, edge_id: String, node_id: usize) -> PyResult<bool> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }
        if !self.nodes.contains_key(&node_id) {
            return Err(PyValueError::new_err(format!("Node with ID {} not found!", node_id)));
        }

        if self.hyperedges.is_empty() {
            return Err(PyValueError::new_err("No hyper-edges currently available in Graph"));
        }
        if !self.hyperedges.contains_key(&edge_id) {
            return Err(PyValueError::new_err(format!("Hyper edge with ID {} not found!", edge_id)));
        }

        let edge = self.hyperedges.get(&edge_id).unwrap();
        if edge.vertices.contains(&node_id) {
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn edges_of<'py>(&self, py: Python<'py>, node_id: usize) -> PyResult<&'py PyList> {
        if self.hyperedges.is_empty() {
            return Err(PyValueError::new_err("No hyper edges currently available in Graph"));
        }

        
        if let Some(node) = self.node_to_edge.get(&node_id) {
            Ok(PyList::new(py, node))
        } else {
            return Err(PyValueError::new_err(format!("Node with ID {} not found in graph!", node_id)));
        }
    }

    pub fn nodes_of<'py>(&self, py: Python<'py>, edge_id: &str) -> PyResult<&'py PyList> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No nodes currently available in Graph"));
        }

        if let Some(edge) = self.hyperedges.get(edge_id) {
            Ok(PyList::new(py, &edge.vertices))
        } else {
            return Err(PyValueError::new_err(format!("Edge with ID {} not found in Graph!", edge_id)));
        }
    }

    pub fn intersection<'py>(&self, py: Python<'py>, edge_id1: &str, edge_id2: &str) -> PyResult<&'py PyList> {
        let edge_1 = self.hyperedges.get(edge_id1).ok_or_else(|| PyValueError::new_err(format!("Hyper edge with ID {} not found in Graph", edge_id1)))?;
        let edge_2 = self.hyperedges.get(edge_id2).ok_or_else(|| PyValueError::new_err(format!("Hyper edge with ID {} not found in Graph", edge_id2)))?;

        let (smaller_set, larger_set) = if edge_1.vertices.len() <= edge_2.vertices.len() {
            (&edge_1.vertices, &edge_2.vertices)
        } else {
            (&edge_2.vertices, &edge_1.vertices)
        };

        let intersection: Vec<usize> = smaller_set.iter().filter(|node_id| larger_set.contains(node_id)).copied().collect();
        Ok(PyList::new(py, intersection))
    }

    pub fn degree(&self, node_id: usize) -> PyResult<usize> {
        if let Some(node) = self.node_to_edge.get(&node_id) {
            Ok(node.len())
        } else {
            return Err(PyValueError::new_err(format!("Node with ID {} not found in Graph", node_id)));
        }
    }

    pub fn max_degree(&self) -> PyResult<usize> {
        let mut maximum = 0;

        for list in self.node_to_edge.values() {
            maximum = maximum.max(list.len())
        }
        Ok(maximum)
    }

    pub fn min_degree(&self) -> PyResult<usize> {
        let mut minimum = usize::MAX;

        for list in self.node_to_edge.values() {
            minimum = minimum.min(list.len())
        }
        
        if minimum == usize::MAX {
            return Ok(0);
        }
        Ok(minimum)
    }

    pub fn average_degree(&self) -> PyResult<f32> {
        let mut total: f32 = 0.0;
        let size = self.node_to_edge.len() as f32;

        for (_, list) in self.node_to_edge.iter() {
            total += list.len() as f32;
        }

        Ok(total / size)
    }

    pub fn edge_size(&self, edge_id: &str) -> PyResult<usize> {
        if let Some(edge) = self.hyperedges.get(edge_id) {
            Ok(edge.vertices.len())
        } else {
            return Err(PyValueError::new_err(format!("Hyperedge with ID {} not found in Graph!", edge_id)));
        }
    }

    pub fn is_empty(&self) -> PyResult<bool> {
        if self.nodes.is_empty() {
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn node_count(&self) -> PyResult<usize> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let count = self.nodes.len();
        Ok(count)
    }

    pub fn edge_count(&self) -> PyResult<usize> {
        if self.hyperedges.is_empty() {
            return Err(PyValueError::new_err("No hyper edges currently available in Graph"));
        }

        let count = self.hyperedges.len();
        Ok(count)
    }

    pub fn clear(&mut self) -> PyResult<()> {
        self.nodes.clear();
        self.hyperedges.clear();
        self.node_to_edge.clear();
        self.next_id = 1;
        Ok(())
    }
}