use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{IntoPyDict, PyDict, PyList, PyTuple};
use pyo3::PyObject;
use rustc_hash::{FxHashMap, FxHasher};
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

/// ---------------------------------------------------------------------------------
/// Implementation Hashable Enum & Conversion of Python objects -> Rust data types
/// ---------------------------------------------------------------------------------

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
/// Implementation of Cuckoo Bucket structure/class & related operations
/// ---------------------------------------------------------------------------------
 
#[derive(Debug, Clone)]
struct CuckooBucket {
    capacity: usize,
    slots: Vec<(PyObject, PyObject)>,
    index: FxHashMap<u64, usize>,
}

impl CuckooBucket {
    fn new(slot_num: usize) -> Self {
        Self {
            capacity: slot_num,
            slots: Vec::new(),
            index: FxHashMap::default(),
        }
    }

    fn is_full(&self) -> bool {
        // Check if the current CuckooBucket (self) is currently filled with elements
        self.slots.len() >= self.capacity 
    }

    fn get_values(&self, py: Python) -> Vec<Py<PyAny>> {
        // Takes the values from the CuckooBucket and returns a Vec!
        let mut elements = Vec::new();
        for (_key, value) in &self.slots {
            elements.push(value.clone_ref(py));
        }
        return elements;
    }

    fn get_keys(&self, py: Python) -> Vec<Py<PyAny>> {
        // Takes the keys from the CuckooBucket and returns a Vec!
        let mut elements = Vec::new();
        for (key, _value) in &self.slots {
            elements.push(key.clone_ref(py));
        }
        return elements;
    }

    fn get_items(&self, py: Python) -> Vec<(Py<PyAny>, Py<PyAny>)> {
        // Takes the item (keys & values) from the CuckooBucket and returns a Vec!
        let mut elements = Vec::new();
        for (key, value) in &self.slots {
            elements.push((key.clone_ref(py), value.clone_ref(py)));
        }
        return elements;
    }

    fn shift_indices(&mut self, position: usize) {
        for (_, pos) in self.index.iter_mut() {
            if *pos > position {
                *pos -= 1;
            }
        }
    }
}

/// ---------------------------------------------------------------------------------
/// Implementation of SnapMap structure/class & related operations
/// ---------------------------------------------------------------------------------

#[pyclass]
pub struct SnapMap {
    capacity: usize,
    map_size: usize,
    bucket_size: usize,
    first_layer: Vec<CuckooBucket>,
    second_layer: Vec<CuckooBucket>,
}

impl SnapMap {
    // Hardcoded Number of Max eviction/insertion attempts before failing (**Rehash**)
    const MAX_EVICTIONS: usize = 100;

    fn generate_map_capacity(capacity: usize, size: usize) -> usize {
        // Generate the max capacity of elements in both internal layers
        return capacity / size as usize;
    }

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

    fn generate_first_hash<T: Hash>(&self, key: &T) -> usize {
        // Generates the intial Hash index for Cuckoo insertion
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        let hash_value = hasher.finish();
        let map_capacity = self.first_layer.len();
        return (hash_value as usize) % map_capacity;
    }

    fn generate_second_hash<T: Hash>(&self, key: &T) -> usize {
        // Generates the secondary Hash index for Cuckoo insertion
        let mut hasher = FxHasher::default();
        key.hash(&mut hasher);
        let hash_value = hasher.finish();
        let map_capacity = self.second_layer.len();
        return (hash_value as usize) % map_capacity;
    }
}

#[pymethods]
impl SnapMap {
    #[new]
    pub fn new(capacity: Option<usize>, bucket_size: Option<usize>) -> Self {
        let sm_cap = capacity.unwrap_or(1024);
        let sm_buc = bucket_size.unwrap_or(4);
        let final_size = Self::generate_map_capacity(sm_cap, sm_buc);
        Self {
            capacity: sm_cap,
            map_size: 0,
            bucket_size: sm_buc,
            first_layer: vec![CuckooBucket::new(sm_buc); final_size],
            second_layer: vec![CuckooBucket::new(sm_buc); final_size],
        }
    }

    pub fn insert(&mut self, py: Python, key: PyObject, value: PyObject) -> PyResult<bool> {
        let mut key = key;
        let mut value = value;

        if self.map_size >= self.capacity {
            return Err(PyValueError::new_err(format!("Max capacity ({}) reached! Unable to insert key-value", self.capacity)));
        }

        // Try inserting key-value pair in Map-structure (100 attempts)
        for _ in 0..Self::MAX_EVICTIONS {

            // Convert key to Rust data type & produce 2 hash-values
            let rust_hash = SnapMap::python_to_rust(py, &key)?;

            let idx1 = SnapMap::generate_first_hash(&self, &rust_hash);
            let idx2 = SnapMap::generate_second_hash(&self, &rust_hash);

            // Compute a new hash value for indexing in CuckooBucket
            let mut h = DefaultHasher::new();
            rust_hash.hash(&mut h);
            let idx_value = h.finish();

            // Extract mutable references to the 2 Buckets
            let first_bucket = &mut self.first_layer[idx1];
            let second_bucket = &mut self.second_layer[idx2];

            // Duplicate check for both buckets.
            if first_bucket.slots.iter().any(|(k, _)| k.as_ref(py).eq(key.as_ref(py)).unwrap_or(false)) {
                return Ok(false);
            }
            if second_bucket.slots.iter().any(|(k, _)| k.as_ref(py).eq(key.as_ref(py)).unwrap_or(false)) {
                return Ok(false);
            }

            // Attempt to insert key-value pair in first layer
            if !first_bucket.is_full() {
                first_bucket.slots.push((key.clone_ref(py), value.clone_ref(py)));
                let position = first_bucket.slots.len() - 1;
                first_bucket.index.insert(idx_value, position);
                self.map_size += 1;
                return Ok(true);
            } 

            // Attempt to insert key-value pair in second layer
            if !second_bucket.is_full() {
                second_bucket.slots.push((key.clone_ref(py), value.clone_ref(py)));
                let position = second_bucket.slots.len() - 1;
                second_bucket.index.insert(idx_value, position);
                self.map_size += 1;
                return Ok(true);
            }

            // If both insertions fail - Push out oldest key-value pair and forcibly insert new pair.
            let evicted_pair = first_bucket.slots.pop().expect("Slot should be full!");
            first_bucket.slots.push((key, value));
            let position = first_bucket.slots.len() - 1;
            first_bucket.index.insert(idx_value, position);

            // Reassign the eviced key and value to retry
            key = evicted_pair.0;
            value = evicted_pair.1;
        }

        // If all 100 insertion attempts fail return Error (**Rehash**)
        Err(PyValueError::new_err(format!("Eviction maximum ({}) reached! Unable to insert key-values", Self::MAX_EVICTIONS)))
    }

    pub fn remove(&mut self, py: Python, key: PyObject) -> PyResult<PyObject> {
        // Convert key to Rust data type & produce 2 hash-values
        let rust_hash = SnapMap::python_to_rust(py, &key)?;

        let idx1 = SnapMap::generate_first_hash(&self, &rust_hash);
        let idx2 = SnapMap::generate_second_hash(&self, &rust_hash);

        // Compute a new hash value for indexing in CuckooBucket
        let mut h = DefaultHasher::new();
        rust_hash.hash(&mut h);
        let idx_value = h.finish();

        // Extract mutable references to the 2 Buckets
        let first_bucket = &mut self.first_layer[idx1];
        let second_bucket = &mut self.second_layer[idx2];

        // Check if the 1st Bucket holds value - If so remove it, update internal variables and return it.
        let pos_option1 = first_bucket.index.get(&idx_value).copied();
        if let Some(positon) = pos_option1 {
            let (_, rem_val) = first_bucket.slots.remove(positon);
            
            first_bucket.index.remove(&idx_value);
            first_bucket.shift_indices(positon);

            self.map_size -= 1;
            return Ok(rem_val);
        }

        // Check if the 2nd Bucket holds value - If so remove it, update internal variables and return it.
        let pos_option2 = second_bucket.index.get(&idx_value).copied();
        if let Some(positon) = pos_option2 {
            let (_, rem_val) = second_bucket.slots.remove(positon);

            second_bucket.index.remove(&idx_value);
            second_bucket.shift_indices(positon);

            self.map_size -= 1;
            return Ok(rem_val);
        }
        // DEFAULT = Returns 'None' value if key-value is not found in both layers.
        Ok(py.None())
    }

    pub fn get(&self, py: Python, key: PyObject) -> PyResult<PyObject> {
        // Convert key to Rust data type & produce 2 hash-values
        let rust_hash = SnapMap::python_to_rust(py, &key)?;

        let idx1 = SnapMap::generate_first_hash(&self, &rust_hash);
        let idx2 = SnapMap::generate_second_hash(&self, &rust_hash);

        // Attempt to find key-value in first layer
        for (k, v) in &self.first_layer[idx1].slots {
            if k.as_ref(py).eq(key.as_ref(py))? {
                return Ok(v.clone_ref(py));
            }
        }

        // Attempt to find key-value in second layer
        for (k, v) in &self.second_layer[idx2].slots {
            if k.as_ref(py).eq(key.as_ref(py))? {
                return Ok(v.clone_ref(py));
            }
        }
        // DEFAULT = Returns 'None' value if key-value is not found in both layers.
        return Ok(py.None());
    }

    pub fn update(&mut self, py: Python, key: PyObject, new_value: PyObject) -> PyResult<bool> {
        // Convert key to Rust data type & produce 2 hash-values
        let rust_hash = SnapMap::python_to_rust(py, &key)?;

        let idx1 = SnapMap::generate_first_hash(&self, &rust_hash);
        let idx2 = SnapMap::generate_second_hash(&self, &rust_hash);

        // Extract mutable references to the 2 Buckets
        let first_bucket = &mut self.first_layer[idx1];
        let second_bucket = &mut self.second_layer[idx2];

        // Iterate through the first bucket slots and compare keys.
        for (k, v) in &mut first_bucket.slots {
            if k.as_ref(py).eq(key.as_ref(py))? {
                *v = new_value.clone_ref(py);
                return Ok(true);
            }
        }

        // Iterate through the second bucket slots and compare keys.
        for (k, v) in &mut second_bucket.slots {
            if k.as_ref(py).eq(key.as_ref(py))? {
                *v = new_value.clone_ref(py);
                return Ok(true);
            }
        }
        // DEFAULT = Returns 'False' value if key-value is not found in both layers.
        Ok(false)
    }

    pub fn contains(&self, py: Python, key: PyObject) -> PyResult<bool> {
        // Convert key to Rust data type & produce 2 hash-values
        let rust_hash = SnapMap::python_to_rust(py, &key)?;

        let idx1 = SnapMap::generate_first_hash(&self, &rust_hash);
        let idx2 = SnapMap::generate_second_hash(&self, &rust_hash);

        // Compute a new hash value for indexing in CuckooBucket
        let mut h = DefaultHasher::new();
        rust_hash.hash(&mut h);
        let idx_value = h.finish();

        // Check if value exists in first layer
        if self.first_layer[idx1].index.contains_key(&idx_value) {
            return Ok(true);
        }

        // Check if value exists in second layer
        if self.second_layer[idx2].index.contains_key(&idx_value) {
            return Ok(true);
        }

        // If key doesn't exist in both layers return false to user.
        return Ok(false);
    }

    pub fn from_keys<'py>(&self, py: Python<'py>, iterable: &PyAny) -> PyResult<&'py PyList> {
        // Initiate new Vector list
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
        // Initiate new Vector list
        let mut elements = Vec::new();

        // Iterate over Buckets in both internal Layers
        for layer in [&self.first_layer, &self.second_layer] {
            for bucket in layer {
                if !bucket.slots.is_empty() {
                    // Added cloned keys to Elements Vector
                    elements.extend(bucket.get_keys(py).iter().cloned());
                }
            }
        }
        // Convert Rust vector into PyList
        Ok(PyList::new(py, &elements))
    }

    pub fn values<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        // Initiate new Vector list
        let mut elements = Vec::new();

        // Iterate over Buckets in both internal Layers
        for layer in [&self.first_layer, &self.second_layer] {
            for bucket in layer {
                if !bucket.slots.is_empty() {
                    // Added cloned values to Elements Vector
                    elements.extend(bucket.get_values(py).iter().cloned());
                }
            }
        }
        // Convert Rust vector into PyList
        Ok(PyList::new(py, &elements))
    }

    pub fn items<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        // Initiate new Vector list
        let mut elements = Vec::new();

        // Iterate over Buckets in both internal Layers
        for layer in [&self.first_layer, &self.second_layer] {
            for bucket in layer {
                if !bucket.slots.is_empty() {
                    // Added cloned values to Elements Vector
                    elements.extend(bucket.get_items(py).iter().cloned());
                }
            }
        }
        // Convert Rust vector into PyList
        Ok(PyList::new(py, &elements))
    }

    pub fn copy(&self, py: Python<'_>) -> PyResult<PyObject> {
        // Instantiate an empty SnapMap variable.
        let mut new_map = SnapMap::new(Some(self.capacity), Some(self.bucket_size));

        // Iterate through all stored items.
        for tuple in self.items(py)?.iter() {
            // Downcast entry to PyTuple to extract key & value pairs safely.
            let tup = tuple.downcast::<PyTuple>()?;
            let key = tup.get_item(0)?;
            let value = tup.get_item(1)?;

            // Converts &PyAny -> PyObjects to safely add to new_map variable.
            new_map.insert(py, key.to_object(py), value.to_object(py))?;
        }
        // Convert the new, fully-loaded SnapMap to a new PyObject.
        Ok(Py::new(py, new_map)?.into_py(py))
    }

    pub fn info<'py>(&self, py: Python<'py>) -> PyResult<&'py PyDict> {
        // Extract the necessary metrics from internal variables
        let percentage = self.percentage()?;
        let keys = self.keys(py)?.into();
        let values = self.values(py)?.into();

        // Contruct a Rust Vector consisting of individual Tuples(String, Object).
        let key_vals: Vec<(&str, PyObject)> = vec![
            ("type", "SnapMap".to_object(py)),
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
        // Return the internal capacity property from SnapMap.
        Ok(self.capacity)
    }

    pub fn size(&self) -> PyResult<usize> {
        // Return the internal .map_sisze() counter from SnapMap.
        Ok(self.map_size)
    }

    pub fn percentage(&self) -> PyResult<f64> {
        // Give a percentage count of how full the current SnapMap is.
        Ok((self.map_size as f64 / self.capacity as f64) * 100.0)
    }

    pub fn is_empty(&self) -> PyResult<bool> {
        // Checks whether the current SnapMap hold no elements. 
        Ok(self.map_size == 0)
    }

    pub fn clear(&mut self) -> PyResult<()> {
        // Iterate through the 1st layer and resets all internal variables and vectors.
        for bucket in self.first_layer.iter_mut() {
            bucket.slots.clear();
            bucket.index.clear();
        }

        // Iterate through the 2nd layer and resets all internal variables and vectors.
        for bucket in self.second_layer.iter_mut() {
            bucket.slots.clear();
            bucket.index.clear();
        }

        self.map_size = 0;
        Ok(())
    }
}
