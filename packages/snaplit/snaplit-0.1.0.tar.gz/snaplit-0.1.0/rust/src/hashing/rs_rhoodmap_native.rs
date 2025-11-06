use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyDict, PyList, PyTuple};
use pyo3::PyObject;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::mem::swap;

/// ---------------------------------------------------------------------------------
/// Implementation of Enum types & Conversion of Python objects -> Rust data types
/// ---------------------------------------------------------------------------------

#[derive(Debug, Clone)]
enum Slot {
    Empty,
    Occupied(RobinBucket),
}

enum Hashable {
    Int(i64),
    Float(u64),
    Str(String),
    Bool(bool),
}

impl Hash for Hashable {
    fn hash<H: Hasher>(&self, state: &mut H) {
        match self {
            Hashable::Int(i) => i.hash(state),
            Hashable::Float(f) => f.hash(state),
            Hashable::Str(s) => s.hash(state),
            Hashable::Bool(b) => b.hash(state),
        }
    }
}

/// ---------------------------------------------------------------------------------
/// Implementation of Robin Bucket structure/class & related operations
/// ---------------------------------------------------------------------------------

#[allow(dead_code)]
#[derive(Debug, Clone)]
struct RobinBucket {
    key: PyObject,
    value: PyObject,
    hash: usize,
    distance: usize,
}

impl RobinBucket {
    fn new(key: PyObject, value: PyObject, hash: usize) -> Self {
        Self { 
            key: key,
            value: value,
            hash: hash,
            distance: 0,
        }
    }
}

/// ---------------------------------------------------------------------------------
/// Implementation of RhoodMap structure/class & related operations
/// ---------------------------------------------------------------------------------

#[pyclass]
pub struct RhoodMap {
    capacity: usize,
    map_size: usize,
    series: Vec<Slot>,
}

impl RhoodMap {
    fn python_to_rust(py: Python, item: &PyObject) -> PyResult<Hashable> {
        // Converts Python native data types -> Rust native data types
        if let Ok(i) = item.extract::<i64>(py) {
            return Ok(Hashable::Int(i));
        } else if let Ok(f) = item.extract::<f64>(py) {
            return Ok(Hashable::Float(f.to_bits()));
        } else if let Ok(s) = item.extract::<String>(py)  {
            return Ok(Hashable::Str(s));
        } else if let Ok(b) = item.extract::<bool>(py) {
            return Ok(Hashable::Bool(b));
        } else {
            return Err(PyValueError::new_err("Unsupported data type for Rust conversion"));
        }
    }

    fn generate_hash<T: Hash>(&self, key: &T) -> usize {
        // Generates the intial Hash index for Robin Hood insertion
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        let hash_value = hasher.finish();
        let map_capacity = self.capacity;
        return (hash_value as usize) % map_capacity;
    }

    fn shift_slots(&mut self, mut index: usize) -> PyResult<()> {
        // Loop until internal conditions are met -> Slot::Empty / Slot::Occupied
        loop {
            // Match Slot at the current index.
            match self.series[index].clone() {
                // If Slot == Empty -> Break from current Loop.
                Slot::Empty => {
                    break;
                },
                // If Slot == Occupied -> Check for further condiftions:
                Slot::Occupied(mut bucket) => {
                    // If Bucket's distance is 0 (Bucket is at 'Home' square), break from current loop.
                    if bucket.distance == 0 {
                        break;
                    }

                    // Decrement the current Bucket's probe distance by 1 & calculate previous index.
                    bucket.distance -= 1;
                    let prev_idx = if index == 0 {
                        self.capacity - 1
                    } else {
                        index - 1
                    };

                    // Shift the Slots back 1 space & set the current to Empty.
                    self.series[prev_idx] = Slot::Occupied(bucket);
                    self.series[index] = Slot::Empty;

                    // Increment the index counter by 1 (Cyclical counter).
                    index = (index + 1) % self.capacity;
                }
            }
        }
        // Returns PyResult<Ok> when loop is finished shifting necessary Slots.
        Ok(())
    }
}

#[pymethods]
impl RhoodMap {
    #[new]
    pub fn new(capacity: Option<usize>) -> Self {
        let rhm_cap = capacity.unwrap_or(1024);
        Self {
            capacity: rhm_cap,
            map_size: 0,
            series: vec![Slot::Empty; rhm_cap],
        }
    }

    pub fn insert(&mut self, py: Python, key: PyObject, value: PyObject) -> PyResult<bool> {
        // check if the map size is currently above or equal to capacity - Map is full!
        if self.map_size >= self.capacity {
            return Err(PyValueError::new_err(format!("Maximum capacity ({}) reached! Unable to insert key-value", self.capacity)));
        }

        // Convert key to Rust data type & produce hash-value.
        let rust_hash = Self::python_to_rust(py, &key)?;
        let mut index = Self::generate_hash(&self, &rust_hash);

        // Generate the new Bucket to insert.
        let mut new_bucket = RobinBucket::new(key.clone_ref(py), value, index);
        
        // Iterate over internal Vectors starting at 'Index'.
        for _ in 0..self.capacity {
            // Match current Slot to determine action.
            match &mut self.series[index] {
                // If Slot::Empty -> Insert new Bucket and increment Map size.
                Slot::Empty => {
                    self.series[index] = Slot::Occupied(new_bucket);
                    self.map_size += 1;
                    return Ok(true);
                },
                // If Slot::Occupied -> If the probe distance is higher, then take the new slot.
                Slot::Occupied(bucket) => {
                    if new_bucket.distance >= bucket.distance {
                        swap(bucket, &mut new_bucket);
                    }
                }
            }
            // Increment new bucket's probe distance by 1 & update index counter (Cyclical counter).
            new_bucket.distance += 1;
            index = (index + 1) % self.capacity;
        }
        // DEFAULT = Raise an Error if attempted to insert the value too many times without success.
        return Err(PyValueError::new_err(format!("Could not insert key {} into RhoodMap", key)));
    }

    pub fn remove(&mut self, py: Python, key: PyObject) -> PyResult<PyObject> {
        // Convert key to Rust data type & produce hash-value.
        let rust_hash = Self::python_to_rust(py, &key)?;
        let mut index = Self::generate_hash(&self, &rust_hash);

        // Iterate over internal Rust Vectors to check Slots.
        for _ in 0..self.capacity {
            // Match Slot at current index -> Slot::Empty / Slot::Occupied.
            match &mut self.series[index] {
                // If current Slot is Empty -> Value could not be found!
                Slot::Empty => {
                    return Err(PyValueError::new_err(format!("Could not locate key {} in rhoodMap", key)));
                },
                // If current Slot is Occupied -> Check if the internal key matches.
                // If it matches -> Extract and return internal value & shift slots to ensure probe chain.
                Slot::Occupied(bucket) => {
                    if bucket.key.as_ref(py).eq(key.as_ref(py))? {
                        let removed_value = bucket.value.clone_ref(py);
                        self.series[index] = Slot::Empty;
                        self.map_size -= 1;
                        self.shift_slots((index + 1) % self.capacity)?;
                        return Ok(removed_value);
                    }
                }
            }
            // Increment current 'Index' by 1 (Cylical counter).
            index = (index + 1) % self.capacity;
        }
        // DEFAULT = Raise an Error if attempted to insert the value too many times without success.
        return Err(PyValueError::new_err(format!("Could not locate key {} in rhoodMap", key)));
    }

    pub fn get(&self, py: Python, key: PyObject) -> PyResult<PyObject> {
        // Convert key to Rust data type & produce hash-value for initial indexing.
        let rust_hash = Self::python_to_rust(py, &key)?;
        let mut index = Self::generate_hash(&self, &rust_hash);

        // Iterate over internal rhoodMap Vector - If iterate full length and no return, Vector is full!
        for _ in 0..self.capacity {
            // Match Slot at 'Index'.
            match &self.series[index] {
                // If Slot::Empty -> Return 'None' (Value not found!).
                Slot::Empty => {
                    return Ok(py.None());
                },
                // If Slot::Occupied -> Return stored value from RobinBucket (Value found!).
                Slot::Occupied(bucket) => {
                    if bucket.key.as_ref(py).eq(key.as_ref(py))? {
                        return Ok(bucket.value.clone_ref(py));
                    }
                }
            }
            // Increment index by 1 (Cyclical counter).
            index = (index + 1) % self.capacity;
        }
        // DEFAULT = Iterated over entire .Series Vector and no value was found!
        Ok(py.None())
    }

    pub fn update(&mut self, py: Python, key: PyObject, new_value: PyObject) -> PyResult<bool> {
        // Convert key to Rust data type & produce hash-value for initial indexing.
        let rust_hash = Self::python_to_rust(py, &key)?;
        let mut index = Self::generate_hash(&self, &rust_hash);

        // Internal loop to iterate over entries starting from hashed index
        loop {
            match &mut self.series[index] {
                // If the loop encounters an 'Empty' slot -> No updating occurs.
                Slot::Empty => {
                    return Ok(false);
                },
                // If the loop encounters an 'Occupied' slot -> Check if 'Key' matches and then update.
                Slot::Occupied(bucket) => {
                    if bucket.key.as_ref(py).eq(key.as_ref(py))? {
                        bucket.value = new_value.clone_ref(py);
                        return Ok(true);
                    }
                }
            }
            // Increment the index value by 1 (Cyclical counter). 
            index = (index + 1) % self.capacity;
        }
    }

    pub fn contains(&self, py: Python, key: PyObject) -> PyResult<bool> {
        // Convert key to Rust data type & produce hash-value for initial indexing.
        let rust_hash = Self::python_to_rust(py, &key)?;
        let mut index = Self::generate_hash(&self, &rust_hash);

        // Internal loop to iterate over entries starting from hashed index
        loop {
            match &self.series[index] {
                // If the loop encounters an 'Empty' slot -> Return 'False'.
                Slot::Empty => {
                    return Ok(false)
                },
                // If the loop encounters an 'Occupied' slot -> Check the stored 'Key' value.
                Slot::Occupied(bukcet) => {
                    if bukcet.key.as_ref(py).eq(key.as_ref(py))? {
                        return Ok(true);
                    }
                }
            }
            // Increment the index value by 1 (Cyclical counter)
            index = (index - 1) % self.capacity;
        }
    }

    pub fn from_keys<'py>(&self, py: Python<'py>, iterable: &PyAny) -> PyResult<&'py PyList> {
        // Initiate new Vector list.
        let mut elements = Vec::new();

        // Iterate over all key elements in Iterable parameter.
        for key_object in iterable.iter()? {
            // Extract the key from behind Result-type.
            let key = key_object?;
            // Use internal .get() method to extract final value.
            let value = self.get(py, key.to_object(py))?;

            // Check if the value recieved is 'None' before adding to elements Vec.
            if !value.is_none(py) {
                elements.push(value);
            }
        }
        // Convert and return the elements list.
        Ok(PyList::new(py, &elements))
    }

    pub fn keys<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        // Instantializa new Rust Vectors to store key-values.
        let mut elements = Vec::new();

        // Iterate through individual Slots in internal rhoodMap Vector.
        for slot in self.series.iter() {
            // Match Slot enum-type.
            match slot {
                Slot::Occupied(bucket) => {
                    elements.push(&bucket.key);
                },
                Slot::Empty => {
                    continue;
                }
            }
        }
        // Convert 'Elements' vectors into a Python native list.
        Ok(PyList::new(py, elements))
    }

    pub fn values<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        // Instantializa new Rust Vectors to store values.
        let mut elements = Vec::new();

        // Iterate through individual Slots in internal rhoodMap Vector.
        for slot in self.series.iter() {
            // Match Slot enum-type.
            match slot {
                Slot::Occupied(bucket) => {
                    elements.push(&bucket.value);
                },
                Slot::Empty => {
                    continue;
                }
            }
        }
        // Convert 'Elements' vectors into a Python native list.
        Ok(PyList::new(py, elements))
    }

    pub fn items<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        // Instantializa new Rust Vectors to store key-value pairs.
        let mut elements = Vec::new();

        // Iterate through individual Slots in internal rhoodMap Vector.
        for slot in self.series.iter() {
            // Match Slot enum-type.
            match slot {
                Slot::Occupied(bucket) => {
                    elements.push((&bucket.key, &bucket.value));
                },
                Slot::Empty => {
                    continue;
                }
            }
        }
        // Convert 'Elements' vectors into a Python native list.
        Ok(PyList::new(py, elements))
    }

    pub fn copy(&self, py: Python<'_>) -> PyResult<PyObject> {
        // Instantiate an empty rhoodMap variable.
        let mut new_map = RhoodMap::new(Some(self.capacity));

        // Iterate through all stored items.
        for tuple in self.items(py)?.iter() {
            // Downcast entry to PyTuple to extract key & value pairs safely.
            let tup = tuple.downcast::<PyTuple>()?;
            let key = tup.get_item(0)?;
            let value = tup.get_item(1)?;

            // Converts &PyAny -> PyObjects to safely add to new_map variable.
            new_map.insert(py, key.to_object(py), value.to_object(py))?;
        }
        // Convert the new, fully-loaded rhoodMap to a new PyObject.
        Ok(Py::new(py, new_map)?.into_py(py))
    }

    pub fn info<'py>(&self, py: Python<'py>) -> PyResult<&'py PyDict> {
        // Extract the necessary metrics from internal variables
        let percentage = self.percentage()?;
        let keys = self.keys(py)?.into();
        let values = self.values(py)?.into();

        // Contruct a Rust Vector consisting of individual Tuples(String, Object).
        let key_vals: Vec<(&str, PyObject)> = vec![
            ("type", "RhoodMap".to_object(py)),
            ("capacity", self.capacity.to_object(py)),
            ("size", self.map_size.to_object(py)),
            ("percentage", percentage.to_object(py)),
            ("keys", keys),
            ("values", values),
        ];

        // Convert Vector to Python Dictionary and return value.
        let dict = key_vals.into_py_dict(py);
        Ok(dict)
    }

    pub fn capacity(&self) -> PyResult<usize> {
        // Returns internal var: 'capacity' to user. 
        Ok(self.capacity)
    }

    pub fn size(&self) -> PyResult<usize> {
        // Returns internal var: 'map_size' to user.
        Ok(self.map_size)
    }

    pub fn percentage(&self) -> PyResult<f64> {
        // Calculate the percentage of internal Rust Vector is currently occupied.
        let precentage = (self.map_size as f64 / self.capacity as f64) * 100.0;
        Ok(precentage)
    }

    pub fn is_empty(&self) -> PyResult<bool> {
        // Returns 'True' if the internal var: 'map_size' is less than or equal to 0. 
        Ok(self.map_size == 0)
    }

    pub fn clear(&mut self) -> PyResult<()> {
        // Set Slots in internal Rust Vectors to Slot::Empty & reset variable 'map_size' to 0.
        self.map_size = 0;
        self.series = vec![Slot::Empty; self.capacity];
        Ok(())
    }
}
