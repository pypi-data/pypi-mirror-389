use std::collections::VecDeque;
use pyo3::{exceptions::PyValueError, types::PyTuple};
use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::PyObject;
use rustc_hash::{FxHashMap, FxHashSet};

#[allow(dead_code)]
#[derive(Debug, Clone)]
struct WeightedNode {
    id: usize,
    payload: PyObject,
    neighbours: FxHashMap<usize, f64>,
}

#[allow(dead_code)]
impl WeightedNode {
    fn new(id: usize, payload: PyObject) -> Self {
        Self {
            id: id,
            payload: payload,
            neighbours: FxHashMap::default(),
        }
    }
}

#[pyclass]
pub struct WeightedDigraph {
    nodes: FxHashMap<usize, WeightedNode>,
    next_id: usize,
    count: usize,
}

impl WeightedDigraph {
    fn removal(&mut self, id: usize) {
        for (_, item) in self.nodes.iter_mut() {
            if item.neighbours.contains_key(&id) {
                item.neighbours.remove(&id);
            }
        }
    }

    fn insert_with_id(&mut self, id: usize, payload: PyObject) {
        let new_node = WeightedNode::new(id, payload);

        self.nodes.insert(id, new_node);
    }

    fn dfs_cycle(&self, node_id: usize, visited: &mut FxHashSet<usize>, rec_stack: &mut FxHashSet<usize>) -> bool {

        visited.insert(node_id);
        rec_stack.insert(node_id);

        if let Some(node) = self.nodes.get(&node_id) {
            for (&neighbour_id, _) in &node.neighbours {
                if !visited.contains(&neighbour_id) {
                    if self.dfs_cycle(neighbour_id, visited, rec_stack) {
                        return true;
                    }
                } else if rec_stack.contains(&neighbour_id) {
                    return true;
                }
            }
        } 
        rec_stack.remove(&node_id);
        false
    }
}

#[pymethods]
impl WeightedDigraph {
    #[new]
    pub fn new() -> Self {
        Self {
            nodes: FxHashMap::default(),
            next_id: 1,
            count: 0,
        }
    }

    pub fn insert(&mut self, item: PyObject) -> PyResult<bool> {
        let new_node = WeightedNode::new(self.next_id, item);

        if self.nodes.contains_key(&self.next_id) {
            return Ok(false)
        } else {
            self.nodes.insert(self.next_id, new_node);
            self.next_id += 1;
            self.count += 1;
            Ok(true)
        }
    }

    pub fn remove(&mut self, py: Python, key: usize) -> PyResult<PyObject> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        match self.nodes.remove(&key) {
            Some(value) => {
                self.count -= 1;
                Self::removal(self, key);
                return Ok(value.payload.clone_ref(py))
            },
            None => return Err(PyValueError::new_err("Value not found in Graph")),
        }
    }

    pub fn extract(&mut self, py: Python, key: usize) -> PyResult<PyObject> {
        let node = self.nodes.get(&key);
        match node {
            Some(value) => return Ok(value.payload.clone_ref(py)),
            None => return Err(PyValueError::new_err("Value not found in Graph"))
        }
        
    }

    pub fn keys<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let mut elements = Vec::new();

        for item in self.nodes.keys().into_iter() {
            elements.push(item);
        }

        let final_list = PyList::new(py, elements);
        Ok(final_list.into())
    }

    pub fn contains(&self, key: usize) -> PyResult<bool> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let result = self.nodes.contains_key(&key);
        Ok(result)
    }

    pub fn update(&mut self, py: Python, item: PyObject, index: usize) -> PyResult<()> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let new_node = match self.nodes.get_mut(&index) {
            Some(node_value) => node_value,
            None => return Err(PyValueError::new_err("Index not found in present Graph"))
        };

        new_node.payload = item.clone_ref(py);
        Ok(())
    }

    pub fn add_edge(&mut self, to_id: usize, from_id: usize, weight: f64) -> PyResult<()> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if !self.nodes.contains_key(&to_id) {
            return Err(PyValueError::new_err("To ID node not found in current Graph"));
        }

        if !self.nodes.contains_key(&from_id) {
            return Err(PyValueError::new_err("From ID node not found in current Graph"));
        }
        
        let from_node = self.nodes.get_mut(&from_id).expect("From ID node not found!");
        from_node.neighbours.insert(to_id, weight);
        
        Ok(())
    }

    pub fn remove_edge(&mut self, to_id: usize, from_id: usize) -> PyResult<()> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if !self.nodes.contains_key(&to_id) {
            return Err(PyValueError::new_err("To ID node not found in current Graph"));
        }

        if !self.nodes.contains_key(&from_id) {
            return Err(PyValueError::new_err("From ID node not found in current Graph"));
        }

        if self.is_connected(to_id, from_id)? {
            let from_node = self.nodes.get_mut(&from_id).expect("From ID node not found!");
            from_node.neighbours.remove(&to_id);

            Ok(())
        } else {
            return Err(PyValueError::new_err("No connection between x and y nodes"));
        }
    }

    pub fn is_connected(&self, to_id: usize, from_id: usize) -> PyResult<bool> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if !self.nodes.contains_key(&to_id) {
            return Err(PyValueError::new_err("To ID node not found in current Graph"));
        }

        if !self.nodes.contains_key(&from_id) {
            return Err(PyValueError::new_err("From ID node not found in current Graph"));
        }

        if to_id == from_id {
            return Err(PyValueError::new_err("Cannot connect nodes to oneself"));
        }

        let from_node = self.nodes.get(&from_id).expect("From ID node not found!");
        if from_node.neighbours.contains_key(&to_id) {
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn get_weight(&self, to_id: usize, from_id: usize) -> PyResult<f64> {
        if self.is_connected(to_id, from_id)? {
            let node = self.nodes.get(&from_id).expect("From ID node found!");
            return Ok(*node.neighbours.get(&to_id).expect("Weight not found in node!"));
        } else {
            return Err(PyValueError::new_err("X and Y nodes are not connected"));
        }
    }

    pub fn total_weight(&self) -> PyResult<f64> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let mut total: f64 = 0.0;
        for (_, node) in self.nodes.iter() {
            for (_, weight) in node.neighbours.iter() {
                total += weight;
            }
        }

        Ok(total)
    }

    pub fn neighbours<'py>(&self, py: Python<'py>, index: usize) -> PyResult<&'py PyList> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let new_node = match self.nodes.get(&index) {
            Some(value) => value,
            None => return Err(PyValueError::new_err("Index not found in present Graph")),
        };

        let final_list = PyList::new(py, new_node.neighbours.clone());
        Ok(final_list.into())
    }

    pub fn edges<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let mut elements = Vec::new();
        
        for (num, item) in self.nodes.iter() {
            elements.push((num, item.payload.clone_ref(py)).to_object(py));
        }

        let final_list = PyList::new(py, elements);
        Ok((final_list).into())
    }

    pub fn bfs_list<'py>(&self, py: Python<'py>, start_id: usize, return_value: Option<bool>) -> PyResult<&'py PyList> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if !self.nodes.contains_key(&start_id) {
            return Err(PyValueError::new_err("Index value not found in Graph"));
        }

        let rtn_val = return_value.unwrap_or(false);
        let mut visited = FxHashSet::default();
        let mut id_queue = VecDeque::new();
        let mut results = Vec::new();

        visited.insert(start_id);
        id_queue.push_back(start_id);

        while let Some(current_id) = id_queue.pop_front() {
            let node = self.nodes.get(&current_id).ok_or_else(|| {
                PyValueError::new_err("Corrupted Graph structure: Node missing during BFS")
            })?;

            if rtn_val {
                let py_tuple = PyTuple::new(
                    py,
                    &[current_id.to_object(py), node.payload.clone_ref(py)]
                );
                results.push(py_tuple.to_object(py));
            } else {
                results.push(current_id.to_object(py));
            }

            for (neigh_id, _) in &node.neighbours {
                if !visited.contains(neigh_id) {
                    visited.insert(*neigh_id);
                    id_queue.push_back(*neigh_id);
                }
            }
        }

        let final_list = PyList::new(py, results);
        Ok((final_list).into())
    }

    pub fn dfs_list<'py>(&self, py: Python<'py>, start_id: usize, return_value: Option<bool>) -> PyResult<&'py PyList> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if !self.nodes.contains_key(&start_id) {
            return Err(PyValueError::new_err("Index value not found in Graph"));
        }

        let rtn_val = return_value.unwrap_or(false);
        let mut visited = FxHashSet::default();
        let mut id_stack = VecDeque::new();
        let mut results = Vec::new();

        visited.insert(start_id);
        id_stack.push_back(start_id);

        while let Some(current_id) = id_stack.pop_back() {
            let node = self.nodes.get(&current_id).ok_or_else(|| {
                PyValueError::new_err("Corrupted Graph structure: Node missing during BFS")
            })?;

            if rtn_val {
                let py_tuple = PyTuple::new(
                    py,
                    &[current_id.to_object(py), node.payload.clone_ref(py)]
                );
                results.push(py_tuple.to_object(py));
            } else {
                results.push(current_id.to_object(py));
            }

            for (neigh_id, _) in &node.neighbours {
                if !visited.contains(neigh_id) {
                    visited.insert(*neigh_id);
                    id_stack.push_back(*neigh_id);
                }
            }
        }

        let final_list = PyList::new(py, results);
        Ok((final_list).into())
    }

    pub fn degree(&self, id: usize) -> PyResult<usize> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if !self.nodes.contains_key(&id) {
            return Err(PyValueError::new_err("ID value not found in Graph"));
        }

        let mut count = 0;
        let node = self.nodes.get(&id).expect("Degree node not found!");

        for _ in node.neighbours.iter() {
            count += 1;
        }

        Ok(count)
    }

    pub fn weighted_degree(&self, id: usize) -> PyResult<f64> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if !self.nodes.contains_key(&id) {
            return Err(PyValueError::new_err("ID value not found in Graph"));
        }

        let mut total: f64 = 0.0;
        let node = self.nodes.get(&id).expect("No node found!");

        for (_, weight) in node.neighbours.iter() {
            total += weight;
        }

        Ok(total)
    }

    pub fn edge_count(&self) -> PyResult<usize> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let mut count = 0;
        for (_, item) in self.nodes.iter() {
            let num = item.neighbours.len();
            count += num;
        }

        Ok(count)
    }

    pub fn has_path(&self, to_id: usize, from_id: usize) -> PyResult<bool> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        if !self.nodes.contains_key(&to_id) {
            return Err(PyValueError::new_err("To ID node not found in current Graph"));
        }

        if !self.nodes.contains_key(&from_id) {
            return Err(PyValueError::new_err("From ID node not found in current Graph"));
        }

        let mut visited = FxHashSet::default();
        let mut id_queue = VecDeque::new();

        visited.insert(from_id);
        id_queue.push_back(from_id);

        while let Some(current_id) = id_queue.pop_front() {
            if current_id == to_id {
                return Ok(true);
            }

            let node = self.nodes.get(&current_id).ok_or_else(|| {
                PyValueError::new_err("Corrupted Graph structure: Node missing during BFS")
            })?;

            for (neigh_id, _) in &node.neighbours {
                if !visited.contains(neigh_id) {
                    visited.insert(*neigh_id);
                    id_queue.push_back(*neigh_id);
                }
            }
        }
        Ok(false)
    }

    pub fn transpose(&self, py: Python) -> PyResult<PyObject> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let mut new_digraph =  WeightedDigraph::new();
        new_digraph.next_id = self.next_id;
        new_digraph.count = self.count;

        for (id, item) in self.nodes.iter() {
            new_digraph.insert_with_id(*id, item.payload.clone_ref(py));
        }

        for (from_id, node) in self.nodes.iter() {
            for (to_id, weight) in &node.neighbours {
                if let Some(reversed_node) = new_digraph.nodes.get_mut(to_id) {
                    reversed_node.neighbours.insert(*from_id, *weight);
                }
            }
        }

        Py::new(py, new_digraph).map(|py_object| py_object.into_py(py))
    }

    pub fn has_cycle(&self) -> PyResult<bool> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let mut visited = FxHashSet::default();
        let mut rec_stack = FxHashSet::default();


        for &node_id in self.nodes.keys() {
            if !visited.contains(&node_id) {
                if self.dfs_cycle(node_id, &mut visited, &mut rec_stack) {
                    return Ok(true);
                }
            }
        }
        return Ok(false);
    }

    pub fn is_empty(&self) -> PyResult<bool> {
        if self.count == 0 {
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn node_count(&self) -> PyResult<usize> {
        Ok(self.count)
    }

    pub fn density(&self) -> PyResult<f64> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Graph"));
        }

        let edge_count = self.edge_count()?;
        let result = edge_count / (self.count * (self.count - 1));
        Ok(result as f64)
    }

    pub fn clear(&mut self) -> PyResult<()> {
        if self.nodes.is_empty() {
            return Err(PyValueError::new_err("Graph is already empty"))
        }

        self.nodes.clear();
        self.next_id = 1;
        self.count = 0;
        Ok(())
    }
}