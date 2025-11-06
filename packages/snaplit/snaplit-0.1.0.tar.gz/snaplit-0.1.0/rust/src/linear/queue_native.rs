use pyo3::prelude::*;
use pyo3::exceptions::PyIndexError;
use pyo3::PyObject;
use pyo3::types::PyList;
use std::collections::VecDeque;

#[pyclass]
pub struct Queue {
    array: VecDeque<PyObject>,
}

#[pymethods]
impl Queue {
    #[new]
    pub fn new() -> Self {
        Self {
            array: VecDeque::new(),
        }
    }

    pub fn enqueue(&mut self, value: PyObject) {
        self.array.push_back(value);
    }

    pub fn dequeue(&mut self) -> PyResult<PyObject> {
        self.array.pop_front().ok_or_else(|| PyIndexError::new_err("Queue is empty"))
    }

    pub fn peek(&self) -> Option<PyObject> {
        self.array.front().cloned()
    }

    pub fn size(&self) -> usize {
        self.array.len()
    }

    pub fn is_empty(&self) -> bool {
        self.array.is_empty()
    }

    pub fn contains(&self, py: Python, value: PyObject) -> bool {
        for item in &self.array {
            if item.as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return true;
            }
        }
        false
    }

    pub fn search(&self, py: Python, value: PyObject) -> Option<usize> {
        for (index, node) in self.array.iter().enumerate() {
            if node.as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return Some(index);
            }
        }
        None
    }

    pub fn to_list<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let mut elements = Vec::new();

        for item in self.array.iter() {
            elements.push(item);
        }

        let list_bound = PyList::new(py, elements);
        Ok(list_bound)
    }

    pub fn copy(&self, py: Python) -> PyResult<PyObject> {
        let mut new_queue = Queue::new();

        for element in self.array.iter() {
            new_queue.enqueue(element.clone());
        }

        Py::new(py, new_queue).map(|py_queue| py_queue.into_py(py))
    }

    pub fn clear(&mut self) {
        self.array.clear();
    }

    pub fn __len__(&self) -> usize {
        self.array.len()
    }

    pub fn __bool__(&self) -> bool {
        !self.array.is_empty()
    }

    pub fn __copy__(&self, py: Python) -> PyResult<PyObject> {
        self.copy(py)
    }

    pub fn __contains__(&self, py: Python, value: PyObject) -> bool {
        self.contains(py, value)
    }
}