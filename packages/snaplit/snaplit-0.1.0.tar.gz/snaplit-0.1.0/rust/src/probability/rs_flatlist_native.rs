use pyo3::basic::CompareOp;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::PyObject;
use rand::Rng;
use rustc_hash::FxHashMap;
use std::cmp::Ordering;

#[derive(Debug, Clone)]
struct FlatNode {
    id: usize,
    payload: PyObject,
}

impl FlatNode {
    fn new(id: usize, payload: PyObject) -> Self {
        Self {
            id: id,
            payload: payload,
        }
    }
}

impl Flatlist {
    fn coin_toss(&self) -> bool {
        let mut rng = rand::thread_rng();
        let n = rng.gen_bool(self.probability);
        return n;
    }

    fn get_top_level(&self) -> usize {
        let mut level = 0;

        while level < self.size - 1 && self.coin_toss() {
            level += 1;
        }
        level
    }

    fn py_compare(py: Python, x_value: &PyObject, y_value: &PyObject) -> Ordering {
        let x = x_value.as_ref(py);
        let y = y_value.as_ref(py);

        // Try X < Y
        if let Ok(obj) = x.rich_compare(y, CompareOp::Lt) {
            if obj.is_true().unwrap_or(false) {
                return Ordering::Less
            }
        }

        // Try X == Y
        if let Ok(obj) = x.rich_compare(y, CompareOp::Eq) {
            if obj.is_true().unwrap_or(false) {
                return Ordering::Equal
            }
        }

        // Try X > Y
        if let Ok(obj) = x.rich_compare(y, CompareOp::Gt) {
            if obj.is_true().unwrap_or(false) {
                return Ordering::Greater
            }
        }
        return Ordering::Equal
    }

}

#[pyclass]
pub struct Flatlist {
    size: usize,
    probability: f64,
    nex_id: usize,
    id_map: FxHashMap<usize, usize>,
    list: Vec<Vec<FlatNode>>,
}

#[pymethods]
impl Flatlist {
    #[new]
    pub fn new(num_list: Option<usize>, probability: Option<f64>) -> Self {
        let rs_num = num_list.unwrap_or(4);
        let rs_prob = probability.unwrap_or(0.5);
        Self {
            size: rs_num,
            probability: rs_prob,
            nex_id: 1,
            id_map: FxHashMap::default(),
            list: vec![Vec::new(); rs_num],
        }
    }

    pub fn insert(&mut self, py: Python, payload: PyObject) -> PyResult<bool> {
        let id = self.nex_id;
        let new_node = FlatNode::new(id, payload);
        let top_lvl = self.get_top_level();

        for lvl in 0..=top_lvl {
            let level = &mut self.list[lvl];
            let index = level.binary_search_by(|node| Flatlist::py_compare(py, &node.payload, &new_node.payload)).unwrap_or_else(|i| i);

            level.insert(index, new_node.clone());
        }

        self.id_map.insert(id, top_lvl);
        self.nex_id += 1;
        Ok(true)
    }

    pub fn remove(&mut self, py: Python, key: PyObject) -> PyResult<PyObject> {
        let mut removed_node = None;
        let mut removed_id = 0;

        for level in self.list.iter_mut().rev() {
            level.retain(|node| {
                if node.payload.as_ref(py).eq(key.as_ref(py)).unwrap_or(false) {
                    removed_node = Some(node.payload.clone());
                    removed_id = node.id.clone();
                    false
                } else {
                    true
                }
            });
        }
        
        match removed_node {
            Some(value) => {
                self.id_map.remove(&removed_id);
                return Ok(value)
            },
            None => return Err(PyValueError::new_err(format!("No value with key {} found in list!", key)))
        }
    }

    pub fn contains(&self, py:Python, key: PyObject) -> PyResult<bool> {
        for level in self.list.iter().rev() {
            
            let mut index = 0;
            while index < level.len() {
                let comparison = Flatlist::py_compare(py, &level[index].payload, &key);

                match comparison {
                    Ordering::Less => index += 1,
                    Ordering::Equal => return Ok(true),
                    Ordering::Greater => break,
                }
            }
        }
        Ok(false)
    }

    pub fn get(&self, py:Python, key: PyObject) -> PyResult<Option<PyObject>> {
        for level in self.list.iter().rev() {
            
            let mut index = 0;
            while index < level.len() {
                let comparison = Flatlist::py_compare(py, &level[index].payload, &key);

                match comparison {
                    Ordering::Less => index += 1,
                    Ordering::Equal => return Ok(Some(level[index].payload.clone())),
                    Ordering::Greater => break,
                }
            }
        }
        Ok(None)
    }

    pub fn update(&mut self, py: Python, key: PyObject, new_value: PyObject) -> PyResult<bool> {
        let _ = self.remove(py, key);
        self.insert(py, new_value)?;
        Ok(true)
    }

    pub fn extend(&mut self, py: Python, items: Vec<PyObject>) -> PyResult<bool> {
        for item in items.iter() {
            self.insert(py, item.clone())?;
        }

        Ok(true)
    }

    pub fn index_of(&self, py: Python, key: PyObject) -> PyResult<usize> {
        for (idx, node) in self.list[0].iter().enumerate() {
            if node.payload.as_ref(py).eq(key.as_ref(py)).unwrap_or(false) {
                return Ok(idx);
            }
        }
        return Err(PyValueError::new_err(format!("No node with value {} found in Flatlist!", key)));
    }

    pub fn to_list<'py>(&self, py: Python<'py>) -> PyResult<PyObject> {
        let elements: Vec<PyObject> = self.list[0].iter().map(|node| node.payload.clone_ref(py)).collect();
        Ok(PyList::new(py, elements).into())
    }

    pub fn peek_first(&self, py: Python) -> PyResult<PyObject> {
        let value = self.list[0].first().map(|node| node.payload.clone_ref(py));

        match value {
            Some(val) => return Ok(val),
            None => return Err(PyValueError::new_err("No first value found in Flatlist!")),
        }
    }

    pub fn peek_last(&self, py: Python) -> PyResult<PyObject> {
        let value = self.list[0].last().map(|node| node.payload.clone_ref(py));

        match value {
            Some(val) => return Ok(val),
            None => return Err(PyValueError::new_err("No last value found in Flatlist!")),
        }
    }

    pub fn pop_first(&mut self) -> PyResult<PyObject> {
        if self.list[0].is_empty() {
            return Err(PyValueError::new_err("No nodes currently present in Flatlist!"));
        }

        let node = self.list[0].remove(0);
        let top_lvl = *self.id_map.get(&node.id).unwrap_or(&0);

        self.id_map.remove(&node.id);

        for level in 1..=top_lvl {
            self.list[level].retain(|n| n.id != node.id);
        }

        Ok(node.payload)
    }

    pub fn pop_last(&mut self) -> PyResult<PyObject> {
        if self.list[0].is_empty() {
            return Err(PyValueError::new_err("No nodes currently present in Flatlist!"));
        }

        let node = self.list[0].pop().unwrap();
        let top_lvl = *self.id_map.get(&node.id).unwrap_or(&0);

        self.id_map.remove(&node.id);

        for level in 1..=top_lvl {
            self.list[level].retain(|n| n.id != node.id);
        }

        Ok(node.payload)
    }

    pub fn merge(&mut self, py: Python, other: &Flatlist) -> PyResult<bool> {
        for node in &other.list[0] {
            self.insert(py, node.payload.clone_ref(py))?;
        }
        Ok(true)
    }

    pub fn size(&self) -> PyResult<usize> {
        Ok(self.list[0].len())
    }

    pub fn is_empty(&self) -> PyResult<bool> {
        Ok(self.list[0].is_empty())
    }

    pub fn clear(&mut self) -> PyResult<()> {
        for level in self.list.iter_mut() {
            level.clear();
        }
        self.id_map.clear();
        self.nex_id = 1;
        Ok(())
    }
}