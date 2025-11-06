use pyo3::prelude::*;
use pyo3::PyObject;

#[derive(Debug, Clone)]
struct CuckooBucket {
    entries: Vec<Option<u16>>,
}

#[allow(dead_code)]
impl CuckooBucket {
    fn new(bucket_size: usize) -> Self {
        Self {
            entries: vec![None; bucket_size],
        }
    }

    fn insert(&mut self, fingerprint: u16) -> bool {
        for slot in self.entries.iter_mut() {
            if slot.is_none() {
                *slot = Some(fingerprint);
                return true;
            }
        }
        false
    }

    fn delete(&mut self, fingerprint: u16) -> bool {
        for slot in self.entries.iter_mut() {
            if let Some(value) = slot {
                if *value == fingerprint {
                    *slot = None;
                    return true;
                }
            }
        }
        false
    }

    fn contains(&self, fingerprint: u16) -> bool {
        let result = self.entries.contains(&Some(fingerprint));
        result
    }

    fn swap(&mut self, fingerprint: u16) -> Option<u16> {
        for slot in self.entries.iter_mut() {
            if let Some(existing) = slot {
                let evicted_value = *existing;
                *slot = Some(fingerprint);
                return Some(evicted_value);
            }
        }
        None
    }

    fn is_full(&self) -> bool {
        if self.entries.iter().all(|x| x.is_none()) {
            return false;
        } else {
            return true;
        }
    }
}

impl CuckooFilter {
    fn produce_fingerprint(&self, hash: u64) -> u16 {
        let fingerprint = (hash & 0xFFFF) as u16;
        if fingerprint == 0 {
            1
        } else {
            fingerprint
        }
    }

    fn first_index(&self, hash: u64) -> usize {
        (hash as usize) % self.buckets.len()
    }

    fn second_index(&mut self, index: usize, fingerprint: u16) -> usize {
        let fingerprint_hash = self.hash_fingerprint(fingerprint);
        (index ^ fingerprint_hash) % self.buckets.len()
    }

    fn hash_fingerprint(&mut self, fingerprint: u16) -> usize {
        let mut hashed = fingerprint as u64;
        hashed ^= hashed >> 33;
        hashed = hashed.wrapping_mul(0xff51afd7ed558ccd);
        hashed ^= hashed >> 33;
        hashed = hashed.wrapping_mul(0xc4ceb9fe1a85ec53);
        hashed ^= hashed >> 33;
        hashed as usize
    }
}

#[pyclass]
pub struct CuckooFilter {
    buckets: Vec<CuckooBucket>,
    size: usize,
    bucket_size: usize,
    retries: usize
}

#[pymethods]
impl CuckooFilter {
    #[new]
    pub fn new(size: Option<usize>, bucket_size: Option<usize>, retries: Option<usize>) -> Self {
        let capacity = size.unwrap_or(100);
        let bucket_size = bucket_size.unwrap_or(4);
        Self {
            buckets: vec![CuckooBucket::new(bucket_size); capacity],
            size: 0,
            bucket_size: bucket_size,
            retries: retries.unwrap_or(4),
        }
    }

    pub fn insert(&mut self, py: Python<'_>, item: PyObject) -> PyResult<bool> {
        let py_hash = item.as_ref(py).hash()? as u64;

        let fingerprint = self.produce_fingerprint(py_hash);
        let index_1 = self.first_index(py_hash);
        let index_2 = self.second_index(index_1, fingerprint);

        if self.buckets[index_1].insert(fingerprint) || self.buckets[index_2].insert(fingerprint) {
            self.size += 1;
            return Ok(true);
        }

        // Cuckoo functionality
        let mut cuckoo_idx = if rand::random() { index_1 } else { index_2 };
        let mut fp = fingerprint;

        for _ in 0..self.retries {
            if let Some(evicted_value) = self.buckets[cuckoo_idx].swap(fp) {
                fp = evicted_value;
                cuckoo_idx = self.second_index(cuckoo_idx, fp);
                if self.buckets[cuckoo_idx].insert(fp) {
                    self.size += 1;
                    return Ok(true);
                }
            } else {
                break;
            }
        }
        Ok(false) // Fingerprint entry failed to insert after all retry attempts
    }

    pub fn contains(&mut self, py: Python<'_>, item: PyObject) -> PyResult<bool> {
        let py_hash = item.as_ref(py).hash()? as u64;
        let fingerprint = self.produce_fingerprint(py_hash);
        let index_1 = self.first_index(py_hash);
        let index_2 = self.second_index(index_1, fingerprint);

        Ok(
            self.buckets[index_1].contains(fingerprint) || self.buckets[index_2].contains(fingerprint)
        )
    }

    pub fn delete(&mut self, py: Python<'_>, item: PyObject) -> PyResult<bool> {
        let py_hash = item.as_ref(py).hash()? as u64;
        let fingerprint = self.produce_fingerprint(py_hash);
        let index_1 = self.first_index(py_hash);
        let index_2 = self.second_index(index_1, fingerprint);

        if self.buckets[index_1].delete(fingerprint) || self.buckets[index_2].delete(fingerprint) {
            self.size -= 1;
            return Ok(true);
        }
        Ok(false)
    }

    pub fn len(&self) -> usize {
        self.size
    }

    pub fn is_empty(&self) -> bool {
        self.size == 0
    }

    pub fn load_factor(&self) -> f64 {
        let total = self.buckets.len() * self.bucket_size;
        self.size as f64 / total as f64
    }

    pub fn clear(&mut self) {
        for bucket in self.buckets.iter_mut() {
            for slot in bucket.entries.iter_mut() {
                *slot = None;
            }
        }
        self.size = 0;
    }
}