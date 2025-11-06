use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::PyObject;
use pyo3::types::PyList;

/// ---------------------------------------------------------------------------------
/// Internal WagonNode structures & public LinkedList
/// ---------------------------------------------------------------------------------

struct WagonNode {
    data: PyObject,
    next: Option<Box<WagonNode>>
}

#[pyclass]
pub struct LinkedList {
    head: Option<Box<WagonNode>>,
    count: usize
}

/// ---------------------------------------------------------------------------------
/// LinkedList & WagonNode related methods and operations
/// ---------------------------------------------------------------------------------

#[pymethods]
impl LinkedList {
    #[new]
    pub fn new() -> Self {
        Self {
            head: None,
            count: 0 
        }
    }

    pub fn prepend(&mut self, value: PyObject) {
        let new_node = Box::new(WagonNode {
            data: value,
            next: self.head.take()
        });

        self.head = Some(new_node);
        self.count += 1;
    }

    pub fn append(&mut self, value: PyObject) {
        // Create a new WagonNode to store value.
        let new_node = Box::new(WagonNode {
            data: value,
            next: None
        });

        // Check if the internal 'head' variable is None.
        if self.head.is_none() {
            self.head = Some(new_node);
        } else {
            let mut current = self.head.as_mut().unwrap();

            // Iterates over stored WagonNode-instances until the end is reached.
            while current.next.is_some() {
                current = current.next.as_mut().unwrap();
            }

            // Append the new WagonNode to the final node.
            current.next = Some(new_node);
        }
        // Increment internal counter by 1.
        self.count += 1;
    }

    pub fn remove_head(&mut self) -> Option<PyObject> {
        // check is the 'head' variables exists -> Then remove the value and return it.
        if let Some(mut node) = self.head.take() {
            self.head = node.next.take();
            self.count -= 1;
            return Some(node.data);
        } else {
            // If the 'head' variable == None -> Return None to user.
            return None;
        }
    }

    pub fn insert(&mut self, value: PyObject, index: Option<usize>) -> PyResult<()> {
        // Unwrap the Option<usize> - Defaults to internal counter if None.
        let idx = index.unwrap_or(self.count);

        // Check if the index is out of bounds -> Return Error if True.
        if idx > self.count {
            return Err(PyValueError::new_err("Index out of bounds"))
        }

        // If the index value is 0 -> Replace the current 'head' with the new node.
        if idx == 0 {
            let new_node = Box::new(WagonNode {
                data: value,
                next: self.head.take(),
            });
            self.head = Some(new_node);
        } else {
            let mut current_node = self.head.as_mut();
            for _ in 0..(idx - 1) {
                match current_node {
                    Some(node) => current_node = node.next.as_mut(),
                    None => return Err(PyValueError::new_err("Corrupted List")),
                }
            }

            if let Some(node) = current_node {
                let next_node = node.next.take();
                let new_node = Box::new(WagonNode {
                    data: value,
                    next: next_node,
                });
                node.next = Some(new_node);
            }
        }
        self.count += 1;
        Ok(())
    }

    pub fn get(&self, py: Python, index: usize) -> PyResult<PyObject> {
        // Check if the index is out of bounds -> Return Error if True.
        if index >= self.count {
            return Err(PyValueError::new_err("Index out of bounds"))
        }

        // Initialize a counter variable & take the current 'head' as current node.
        let mut counter = 0;
        let mut current_node = self.head.as_ref();

        // Iterate over internal WagonNode-instances until counter matches index num.
        while let Some(node) = current_node {
            if counter == index {
                // Return copy of the stored WagonNode value.
                return Ok(node.data.clone_ref(py));
            }

            // Else replace current node variable and increment counter by 1.
            current_node = node.next.as_ref();
            counter += 1;
        }

        // DEFAULT = Index value doesn't exist in internal Linked List.
        Err(PyValueError::new_err("Index not found"))
    }

    pub fn contains(&self, py: Python, value: PyObject) -> bool {
        // Take current 'head' variable to begin Linked List iteration.
        let mut current_node = self.head.as_ref();

        // Iterate over internal WagonNode-instances until correct value is encountered. 
        while let Some(node) = current_node {
            if node.data.as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return true;
            }

            // If value is not encountered take the next WagonNode as current node.
            current_node = node.next.as_ref();
        }

        // DEFAULT = If the value wasn't found -> Return False.
        false
    }

    pub fn pop(&mut self, index: Option<usize>) -> PyResult<PyObject> {
        let idx = index.unwrap_or(self.count.checked_sub(1).ok_or_else(|| PyValueError::new_err("List is Empty"))?);

        // Remove the WagonNode at specified index - If no index specified revert to popping final node instance.
        self.remove(idx).ok_or_else(|| PyValueError::new_err("Index out of bounds"))
    }

    pub fn remove(&mut self, index: usize) -> Option<PyObject> {
        if index >= self.count {
            return None;
        }

        if index == 0 {
            return self.remove_head();
        }

        let mut current_node = self.head.as_mut()?;
        for _ in 0..(index - 1) {
            current_node = current_node.next.as_mut()?;
        }

        let removed_node = current_node.next.take();
        if let Some(mut node) = removed_node {
            current_node.next = node.next.take();
            self.count -= 1;
            Some(node.data)
        } else {
            None
        }
    }

    pub fn search(&self, py: Python, value: PyObject) -> Option<usize> {
        let mut current_node = self.head.as_ref();
        let mut index = 0;

        while let Some(node) = current_node {
            if node.data.as_ref(py).eq(value.as_ref(py)).unwrap_or(false) {
                return Some(index);
            }
            current_node = node.next.as_ref();
            index += 1;
        }
        None
    }

    pub fn update(&mut self, value: PyObject, index: usize) -> PyResult<()> {
        // Returns Error if specified index is out of bounds.
        if index >= self.count {
            return Err(PyValueError::new_err("Index out of bounds"))
        }

        // Create counter variable to check if specified index is reached.
        let mut counter = 0;
        let mut current_node = self.head.as_mut();

        // Iterate over internal WagonNode-instances..
        while let Some(node) = current_node {
            // If index is correct -> Replace stored PyObject with new value.
            if counter == index {
                node.data = value;
                return Ok(());
            }

            // Else take next WagonNode to check & increment counter by 1.
            current_node = node.next.as_mut();
            counter += 1;
        }

        // DEFAULT = Specified index was not encountered in Linked List. 
        Err(PyValueError::new_err("No data found at index"))
    }

    pub fn to_list<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        // Initialize a Rust Vector to store WagonNode values.
        let mut elements = Vec::new();
        let mut current_node = self.head.as_ref();

        // Iterate over internal WagonNode-instances & store related values in Elements Vector.
        while let Some(node) = current_node {
            elements.push(node.data.clone_ref(py));
            current_node = node.next.as_ref();
        }

        // Convert Rust Vector into PyList instance and return it to user.
        let list_bound = PyList::new(py, elements);
        Ok(list_bound)
    }

    pub fn size(&self) -> PyResult<usize> {
        // Returns the current number of stored WagonNodes.
        Ok(self.count)
    }

    pub fn is_empty(&self) -> PyResult<bool> {
        // Check if LinkedList currently stores no WagonNodes.
        let value = self.count == 0;
        Ok(value)
    }

    pub fn clear(&mut self) {
        // Sets 'head' variable to None (clearing WagonNodes) & resets count to 0.
        self.head = None;
        self.count = 0;
    }
}

