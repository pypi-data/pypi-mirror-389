use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::PyObject;
use pyo3::types::PyList;

#[pyclass]
struct TowerNode {
    data: PyObject,
    next: Option<Box<TowerNode>>,
}

#[pyclass]
pub struct Stack {
    top: Option<Box<TowerNode>>,
    count: usize,
}

#[pymethods]
impl Stack {
    #[new]
    pub fn new() -> Self {
        Self {
            top: None,
            count: 0
        }
    }

    pub fn push(&mut self, value: PyObject) {
        let new_node = Box::new(TowerNode {
            data: value,
            next: self.top.take(),
        });

        self.top = Some(new_node);
        self.count += 1;
    }

    pub fn peek(&self, py: Python) -> Option<PyObject> {
        if let Some(node) = self.top.as_ref() {
            return Some(node.data.clone_ref(py));
        } else {
            None
        }
    }

    pub fn pop(&mut self) -> Option<PyObject> {
        self.top.take().map(|mut node| {
            self.top = node.next.take();
            self.count -= 1;

            return node.data;
        })
    }

    pub fn size(&self) -> usize {
        return self.count;
    }

    pub fn swap(&mut self, index: Option<usize>) -> PyResult<()> {
        let idx = index.unwrap_or(1);

        if idx > self.count {
            return Err(PyValueError::new_err("Index out of bounds"));
        } else if self.is_empty() {
            return Err(PyValueError::new_err("Stack is currently empty"));
        } else if self.count == 1 {
            return Err(PyValueError::new_err("Only 1 element available in Stack - Cannot swap"));
        } else if idx == 0 {
            return Ok(());
        }

        let current_node = self.top.as_mut().unwrap();
        
        let mut target_node = current_node.next.as_mut().ok_or_else(|| {
            PyValueError::new_err("Next node doens't exist, can't swap!")
        })?;

        for _ in 1..idx {
            target_node = target_node.next.as_mut().ok_or_else(|| {
                PyValueError::new_err("Index out of bounds")
            })?;
        }

        std::mem::swap(&mut current_node.data, &mut target_node.data);
        Ok(())
    }

    pub fn contains(&self, py: Python, value: PyObject) -> bool {
        let mut current_node = self.top.as_ref();

        while let Some(node) = current_node {
            if node.data.as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return true;
            }

            current_node = node.next.as_ref();
        }
        return false;
    }

    pub fn copy(&self, py: Python) -> PyResult<PyObject> {
        let mut new_stack = Stack::new();
        let mut elements = Vec::new();

        let mut current_node = self.top.as_ref();
        while let Some(node) = current_node  {
            elements.push(node.data.clone());
            current_node = node.next.as_ref();
        }

        for element in elements.iter().rev() {
            new_stack.push(element.clone());
        }

        Py::new(py, new_stack).map(|py_stack| py_stack.into_py(py))
    }

    pub fn is_empty(&self) -> bool {
        if self.count == 0 {
            return true;
        } else {
            return false;
        }
    }

    pub fn to_list<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let mut elements = Vec::new();
        let mut current_node = self.top.as_ref();

        while let Some(node) = current_node  {
            elements.push(node.data.clone_ref(py));
            current_node = node.next.as_ref();
        }
        let list_bound = PyList::new(py, elements);
        Ok(list_bound)
    }

    pub fn reverse(&mut self) -> PyResult<()> {
        if self.top.is_none() || self.count == 1 {
            return Err(PyValueError::new_err("Reverse will have no effect on current Stack"));
        } else {
            
            let mut current_node = self.top.take();
            let mut previous: Option<Box<TowerNode>> = None;

            while let Some(mut node) = current_node {
                let next = node.next.take();
                node.next = previous;
                previous = Some(node);
                current_node = next;
            }

            self.top = previous;
            Ok(())
        }
    }

    pub fn update_top(&mut self, value: PyObject) -> PyResult<()> {
        if let Some(node) = self.top.as_mut() {
            node.data = value;
            Ok(()) 
        } else {
            Err(PyValueError::new_err("No current top available in Stack"))
        }
    }

    pub fn clear(&mut self) {
        self.top = None;
        self.count = 0;
    }

    pub fn __len__(&self) -> usize {
        return self.size();
    }

    pub fn __copy__(&self, py: Python) -> PyResult<PyObject> {
        self.copy(py)
    }

    pub fn __contains__(&self, py: Python, value: PyObject) -> bool {
        self.contains(py, value)
    }
}