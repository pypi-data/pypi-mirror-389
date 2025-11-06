use pyo3::exceptions::PyIndexError;
use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::PyObject;

#[pyclass]
pub struct RingBuffer {
    head: usize,
    tail: usize,
    count: usize,
    total: usize,
    array: Vec<PyObject>,
}

#[pymethods]
impl RingBuffer {
    #[new]
    pub fn new(py: Python, size: usize) -> Self {
        let none_obj = py.None().into_py(py);

        Self {
            head: 0,
            tail: 0,
            count: 0,
            total: size,
            array: vec![none_obj; size],
        }
    }

    pub fn enqueue(&mut self, value: PyObject) {
        self.array[self.head] = value;
        self.head = (self.head + 1) % self.total;

        if self.count == self.total {
            self.tail = (self.tail + 1) % self.total;
        } else {
            self.count += 1;
        }
    }

    pub fn dequeue(&mut self, py: Python) -> PyObject {
        if self.count == 0 {
            return py.None();
        }

        let value = self.array[self.tail].clone_ref(py);
        self.tail= (self.tail + 1) % self.total;
        self.count -= 1;
        value
    }

    pub fn peek(&self, py: Python) -> Option<PyObject> {
        if self.count == 0 {
            None
        } else {
            Some(self.array[self.tail].clone_ref(py))
        }
    }

    pub fn size(&self) -> usize {
        return self.count;
    }

    pub fn capacity(&self) -> usize {
        return self.total;
    }

    pub fn extend(&mut self, py: Python, iterable: &PyAny) -> PyResult<()> {
        for item in iterable.iter()? {
            let obj = item?;
            self.enqueue(obj.into_py(py));
        }
        Ok(())
    }

    pub fn contains(&self, py: Python, value: PyObject) -> bool {
        for i in 0..self.count {
            let index = (self.tail + i) % self.total;
            if self.array[index].as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return true;
            }
        }
        false
    }

    pub fn search(&self, py: Python, value: PyObject) -> Option<usize> {
        for i in 0..self.count {
            let index = (self.tail + i) % self.total;
            if self.array[index].as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return Some(i);
            }
        }
        None
    }

    pub fn update(&mut self, _py: Python, index: usize, value: PyObject) -> PyResult<()> {
        if index >= self.count {
            return Err(PyIndexError::new_err("Index out of bounds"));
        }

        let real_idx = (self.tail + index) % self.total;
        self.array[real_idx] = value;
        Ok(())
    }

    pub fn is_empty(&self) -> bool {
        self.count == 0
    }

    pub fn is_full(&self) -> bool {
        if self.count == self.total {
            return true;
        } else {
            return false;
        }
    }

    pub fn to_list<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let mut elements = Vec::with_capacity(self.count);

        for i in 0..self.count {
            let index = (self.tail + i) % self.total;
            elements.push(self.array[index].clone_ref(py));
        }

        let list_bound = PyList::new(py, elements);
        Ok(list_bound)
    }

    pub fn copy(&self, py: Python) -> PyResult<PyObject>{
        let mut new_buffer = RingBuffer::new(py, self.total);

        for i in 0..self.count {
            let index = (self.tail + i) % self.total;
            new_buffer.enqueue(self.array[index].clone_ref(py));
        }

        Py::new(py, new_buffer).map(|py_buffer| py_buffer.into_py(py))
    }

    pub fn subarry<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let mut elements = Vec::with_capacity(self.count);

        for i in 0..self.count {
            let index = (self.tail + i) % self.total;
            elements.push(self.array[index].clone_ref(py));
        }
        Ok(PyList::new(py, elements))
    }

    pub fn clear(&mut self , py: Python) {
        let none_obj = py.None();

        self.head = 0;
        self.tail = 0;
        self.count = 0;
        self.array = vec![none_obj.into_py(py); self.total]
    }

    pub fn __len__(&self) -> usize {
        self.count
    }

    pub fn __bool__(&self) -> bool {
        !self.is_empty()
    }

    pub fn __getitem__(&self, py: Python, index: usize) -> Option<PyObject> {
        Some(self.array[index].clone_ref(py))
    }

    pub fn __contains__(&self, py: Python, value: PyObject) -> bool {
        self.contains(py, value)
    }

    pub fn __copy__(&self, py: Python) -> PyResult<PyObject> {
        self.copy(py)
    }
}