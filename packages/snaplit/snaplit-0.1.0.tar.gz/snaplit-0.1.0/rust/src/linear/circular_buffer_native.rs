use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::PyObject;

#[pyclass]
pub struct CircularBuffer {
    head: usize,
    tail: usize,
    count: usize,
    capacity: usize,
    array: Vec<PyObject>,
}

#[pymethods]
impl CircularBuffer {
    #[new]
    pub fn new(py: Python, size: usize) -> Self {
        let none_obj = py.None().into_py(py);

        Self {
            head: 0,
            tail: 0,
            count: 0,
            capacity: size,
            array: vec![none_obj; size],
        }
    }

    pub fn enqueue(&mut self, value: PyObject) -> PyResult<()> {
        if self.count == self.capacity {
            Err(PyValueError::new_err("Circular Buffer is currently full!"))
        } else {
            self.array[self.head] = value;
            self.head = (self.head + 1) % self.capacity;
            self.count += 1;
            Ok(())
        }
    }

    pub fn dequeue(&mut self, py: Python) -> PyResult<PyObject> {
        if self.count == 0 {
            return Err(PyValueError::new_err("Circular Buffer is currently empty!"))
        } else {
            let value = self.array[self.tail].clone_ref(py);
            self.tail= (self.tail + 1) % self.capacity;
            self.count -= 1;
            Ok(value)
        }
    }

    pub fn peek(&self, py: Python) -> Option<PyObject> {
        if self.count == 0 {
            None
        } else {
            Some(self.array[self.tail].clone_ref(py))
        }
    }

    pub fn size(&self) -> usize {
        self.count
    }

    pub fn capacity(&self) -> usize {
        self.capacity
    }

    pub fn is_empty(&self) -> bool {
        self.count == 0
    }

    pub fn is_full(&self) -> bool {
        self.count == self.capacity
    }

    pub fn contains(&self, py: Python, value: PyObject) -> bool {
        for i in 0..self.count {
            let index = (self.tail + i) % self.capacity;
            if self.array[index].as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return true;
            }
        }
        false
    }

    pub fn search(&self, py: Python, value: PyObject) -> Option<usize> {
        for i in 0..self.count {
            let index = (self.tail + i) % self.capacity;
            if self.array[index].as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return Some(i);
            }
        }
        None
    }

    pub fn extend(&mut self, py: Python, iterable: &PyAny) -> PyResult<()> {
        let items = iterable
            .iter()?
            .map(|item| item.map(|i| i.into_py(py)))
            .collect::<PyResult<Vec<PyObject>>>()?;

        let available_slots = self.capacity - self.count;
        let needed_slots = items.len();

        if needed_slots > available_slots {
            return Err(PyValueError::new_err(format!("Not enough space available in Circular Buffer - Needed slots: {}, available slots: {}", needed_slots, available_slots)));
        } else {
            for idx in items {
                self.enqueue(idx)?;
            }
            Ok(())
        }
    }

    pub fn update(&mut self, index: usize, value: PyObject) -> PyResult<()> {
        if index >= self.count {
            return Err(PyValueError::new_err("Index out of bounds"));
        }

        let real_idx = (self.tail + index) % self.capacity;
        self.array[real_idx] = value;
        Ok(())
    }

    pub fn to_list<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let mut elements = Vec::with_capacity(self.count);

        for i in 0..self.count {
            let index = (self.tail + i) % self.capacity;
            elements.push(self.array[index].clone_ref(py));
        }

        let list_bound = PyList::new(py, elements);
        Ok(list_bound)
    }

    pub fn copy(&self, py: Python) -> PyResult<PyObject>{
        let mut new_buffer = CircularBuffer::new(py, self.capacity);

        for i in 0..self.count {
            let index = (self.tail + i) % self.capacity;
            new_buffer.enqueue(self.array[index].clone_ref(py))?;
        }

        Py::new(py, new_buffer).map(|py_buffer| py_buffer.into_py(py))
    }

    pub fn subarray<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let mut elements = Vec::with_capacity(self.count);

        for i in 0..self.count {
            let index = (self.tail + i) % self.capacity;
            elements.push(self.array[index].clone_ref(py));
        }
        Ok(PyList::new(py, elements))
    }

    pub fn clear(&mut self , py: Python) {
        let none_obj = py.None();

        self.head = 0;
        self.tail = 0;
        self.count = 0;
        self.array = vec![none_obj.into_py(py); self.capacity]
    }

    pub fn __len__(&self) -> usize {
        self.count
    }

    pub fn __bool__(&self) -> bool {
        !self.is_empty()
    }

    pub fn __getitem__(&self, py: Python, index: usize) -> PyResult<PyObject> {
        if index >= self.count {
            return Err(PyValueError::new_err("Index out of bounds"));
        } else {
            let real_idx = (self.tail + index) % self.capacity;
            Ok(self.array[real_idx].clone_ref(py))
        }
    }

    pub fn __contains__(&self, py: Python, value: PyObject) -> bool {
        self.contains(py, value)
    }

    pub fn __copy__(&self, py: Python) -> PyResult<PyObject> {
        self.copy(py)
    }
}