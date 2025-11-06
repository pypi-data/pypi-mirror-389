use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::PyObject;


#[derive(Clone, Copy)]
pub enum HeapType {
    Min,
    Max,
}

struct HeapItem {
    priority: i32,
    value: PyObject,
}

impl HeapItem {
    pub fn new(priority: i32, value: PyObject, ) -> Self {
        Self {
            priority: priority,
            value: value 
        }
    }
}

#[pyclass]
pub struct PriorityQueue {
    priority: HeapType,
    array: Vec<HeapItem>,
}

#[pymethods]
impl PriorityQueue {
    #[new]
    pub fn new(priority_type: &str) -> PyResult<Self> {
        let heap_type = match priority_type.to_lowercase().as_str() {
            "min" => HeapType::Min,
            "max" => HeapType::Max,
            _ => return Err(PyValueError::new_err("Priority Type must be 'min' or 'max'")),
        };

        Ok(Self {
            priority: heap_type,
            array: Vec::new(),
        })
    }

    pub fn enqueue(&mut self, value: PyObject, priority: i32) {
        let item = HeapItem::new(priority, value);
        let index = self.array.len() - 1;
        self.array.push(item);
        self.heapify_up(index);
    }

    pub fn dequeue(&mut self, py: Python) -> PyResult<PyObject> {
        let array_length = self.array.len();
        if array_length == 0 {
            return Err(PyValueError::new_err("No elements currently stored in Priority queue"));
        }

        let removed_item = self.array[0].value.clone_ref(py);

        if array_length == 1 {
            self.array.pop();
        } else {
            self.array[0] = self.array.pop().unwrap();
            self.heapify_down(None);
        }

        Ok(removed_item)
    }

    pub fn peek(&self, py: Python, return_priority: Option<bool>) -> PyResult<PyObject> {
        if self.array.len() == 0 {
            return Err(PyValueError::new_err("No element in the Queue to return"));
        }

        let rtr_prio = return_priority.unwrap_or(false);

        let item_value = self.array[0].value.clone_ref(py);
        let item_priority = self.array[0].priority.to_object(py);

        if rtr_prio {
            Ok((item_value, item_priority).to_object(py))
        } else {
            Ok(item_value)
        }
    }

    pub fn is_empty(&self) -> bool {
        self.array.is_empty()
    }

    pub fn size(&self) -> usize {
        self.array.len()
    }

    pub fn is_min_heap(&self) -> bool {
        matches!(self.priority, HeapType::Min)
    }

    pub fn is_max_heap(&self) -> bool {
        matches!(self.priority, HeapType::Max)
    }

    pub fn contains(&self, py: Python, value: PyObject) -> bool {
        for item in self.array.iter() {
            if item.value.as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return true;
            }
        }
        false
    }

    pub fn update_priority(&mut self, index: usize, priority: i32) -> PyResult<()> {
        let array_length = self.array.len();
        
        if index >= array_length {
            return Err(PyValueError::new_err("Index out of bounds"));
        } else if array_length == 0 {
            return Err(PyValueError::new_err("Currently no elements available in the Queue"));
        }
        
        self.array[index].priority = priority;
        self.heapify_up(index);
        self.heapify_down(Some(index));
            
        Ok(())
    }

    pub fn search(&self, py: Python, value: PyObject) -> PyResult<usize> {
        if self.array.len() == 0 {
            return Err(PyValueError::new_err("No elements available in Queue"));
        }

        for (index, item) in self.array.iter().enumerate() {
            if item.value.as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return Ok(index);
            }
        }
        Err(PyValueError::new_err(format!("No entry with value {} found in Queue", value)))
    }

    pub fn remove(&mut self, py: Python, index: usize, return_priority: Option<bool>) -> PyResult<PyObject> {
        let array_length = self.array.len();
        let rtr_prio = return_priority.unwrap_or(false);
        
        if array_length == 0 {
            return Err(PyValueError::new_err("No elements currently available in Queue"));
        } else if array_length <= index {
            return Err(PyValueError::new_err("Index out of bounds"));
        }

        let removed_item = self.array[index].value.clone_ref(py);
        let removed_priority = self.array[index].priority.to_object(py);

        if array_length == 1 {
            self.array.pop();
        } else {
            self.array[index] = self.array.pop().unwrap();

            self.heapify_up(index);
            self.heapify_down(Some(index));
        }

        if rtr_prio {
            Ok((removed_item, removed_priority).to_object(py))
        } else {
            Ok(removed_item)
        }
    }

    pub fn extend(&mut self, iterable: &PyList) -> PyResult<()> {
        for obj in iterable.iter() {
            let (value, priority): (PyObject, i32) = obj.extract()?;
            self.enqueue(value, priority);
        }
        Ok(())
    }

    pub fn to_list<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        let mut elements = Vec::with_capacity(self.array.len());

        for item in self.array.iter() {
            let element = (item.value.clone_ref(py), item.priority).to_object(py);
            elements.push(element);
        }
        let list_bound = PyList::new(py, elements);
        Ok(list_bound)
    }

    pub fn copy(&self, py: Python) -> PyResult<PyObject> {
        let mut new_queue = PriorityQueue {
            priority: self.priority,
            array: Vec::with_capacity(self.array.len())
        };

        for item in self.array.iter() {
            new_queue.array.push(HeapItem {
                priority: item.priority,
                value: item.value.clone_ref(py),
            });
        }

        Py::new(py, new_queue).map(|py_obj| py_obj.to_object(py))
    }

    pub fn clear(&mut self) {
        self.array.clear();
    }

    pub fn __len__(&self) -> usize {
        self.size()
    }

    pub fn __bool__(&self) -> bool {
        !self.is_empty()
    }

    pub fn __contains__(&self, py: Python, value: PyObject) -> bool {
        self.contains(py, value)
    }

    pub fn __copy__(&self, py: Python) -> PyResult<PyObject> {
        self.copy(py)
    }

    fn heapify_up(&mut self, mut index: usize) {
        while index > 0 {
            let parent_idx = (index - 1) / 2;

            let should_swap = match self.priority {
                HeapType::Min => self.array[index].priority < self.array[parent_idx].priority,
                HeapType::Max => self.array[index].priority > self.array[parent_idx].priority,
            };

            if should_swap {
                self.array.swap(index, parent_idx);
                index = parent_idx;
            } else {
                break;
            }
        }
    }

    fn heapify_down(&mut self, index: Option<usize>) {
        let mut idx: usize = index.unwrap_or(0);
        let array_length = self.array.len();

        loop {
            let left_child = (idx * 2) + 1;
            let right_child = (idx * 2) + 2;

            let mut selected = idx;

            match self.priority {
                HeapType::Min => {
                    if left_child < array_length && self.array[left_child].priority < self.array[selected].priority {
                        selected = left_child;
                    }
                    if right_child < array_length && self.array[right_child].priority < self.array[selected].priority {
                        selected = right_child;
                    }
                }
                HeapType::Max => {
                    if left_child < array_length && self.array[left_child].priority > self.array[selected].priority {
                        selected = left_child;
                    }
                    if right_child < array_length && self.array[right_child].priority > self.array[selected].priority {
                        selected = right_child;
                    }
                }
            }

            if selected != idx {
                self.array.swap(idx, selected);
                idx = selected;
            } else {
                break;
            }
        }
    }
}