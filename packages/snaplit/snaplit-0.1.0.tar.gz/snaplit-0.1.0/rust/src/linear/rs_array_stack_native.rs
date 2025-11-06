use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::PyObject;
use pyo3::types::PyList;

#[pyclass]
pub struct ArrayStack {
    capacity: usize,
    stack: Vec<PyObject>,
}

#[pymethods]
impl ArrayStack {
    #[new]
    pub fn new(size: Option<usize>) -> Self {
        Self {
            capacity: size.unwrap_or(0),
            stack: Vec::new(),
        }
    }

    pub fn push(&mut self, value: PyObject) -> PyResult<()> {
        if self.stack.len() >= self.capacity && self.capacity != 0 {
            return Err(PyValueError::new_err("Stack is at max capacity"));
        }

        self.stack.push(value);
        Ok(())
    }

    pub fn pop(&mut self, py: Python) -> PyResult<PyObject> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Stack"));
        }

        let result = self.stack.pop().unwrap().clone_ref(py);
        Ok(result)
    }

    pub fn peek(&self, py: Python) -> PyResult<PyObject> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Stack"));
        }

        let result = self.stack.last().unwrap().clone_ref(py);
        Ok(result)
    }

    pub fn size(&self) -> usize {
        self.stack.len()
    }

    pub fn swap(&mut self, index: usize) -> PyResult<()> {
        let stack_size = self.stack.len();
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Stack"));
        } else if index >= stack_size {
            return Err(PyValueError::new_err("Index out of bounds"));
        } else if stack_size == 1 {
            return Err(PyValueError::new_err("Only 1 element available in Stack - Cannot swap"));
        }

        let top_idx = stack_size - 1;

        self.stack.swap(index, top_idx);
        Ok(())
    }

    pub fn contains(&self, py: Python, value: PyObject) -> bool {
        if self.is_empty() {
            return false;
        } else {
            for item in self.stack.iter() {
                if item.as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                    return true;
                }
            }
        }
        false
    }

    pub fn copy(&self, py: Python) -> PyResult<PyObject> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements in Stack to copy"));
        }

        let mut new_stack = ArrayStack {
            capacity: self.capacity,
            stack: Vec::new(),
        };

        for item in self.stack.iter() {
            new_stack.push(item.clone_ref(py))?;
        }

        Py::new(py, new_stack).map(|py_obj| py_obj.to_object(py))
    }

    pub fn is_empty(&self) -> bool {
        return self.stack.len() == 0;
    }

    pub fn is_full(&self) -> bool {
        if self.capacity == self.stack.len() && self.capacity != 0 {
            return true;
        } else {
            return false;
        }
    }

    pub fn top_index(&self) -> usize {
        self.stack.len() - 1
    }

    pub fn reverse(&mut self, py: Python) -> PyResult<()> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Stack"));
        }

        let mut new_array = Vec::new();
        for item in self.stack.iter() {
            new_array.insert(0, item.clone_ref(py));
        }
        self.stack = new_array;
        Ok(())
    }

    pub fn to_list<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let mut elements = Vec::with_capacity(self.stack.len());

        for item in self.stack.iter() {
            elements.push(item.clone_ref(py));
        }
        
        let list_bound = PyList::new(py, elements);
        Ok(list_bound)
    }

    pub fn extend(&mut self, py: Python, iterable: &PyList) -> PyResult<()> {
        let iter_len = iterable.len();
        let array_len = self.stack.len();
        if iter_len + array_len > self.capacity && self.capacity != 0 {
            return Err(PyValueError::new_err("Stack doens't have enough capacity for these elements"));
        }

        for item in iterable.iter() {
            self.push(item.to_object(py))?;
        }
        Ok(())
    }

    pub fn update_top(&mut self, value: PyObject) -> PyResult<()> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in Stack"));
        }

        let last_index = self.size() - 1;
        self.stack[last_index] = value;
        Ok(())
    }

    pub fn clear(&mut self) {
        self.stack.clear();
    }
}