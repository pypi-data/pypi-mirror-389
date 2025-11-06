use pyo3::prelude::*;
use pyo3::PyObject;
use crate::other::rs_bit_array::BitArray;

#[allow(dead_code)]
#[pyclass]
pub struct BloomFilter {
    probability: f64,
    size: usize,
    hash_count: usize,
    array: BitArray,
}

impl BloomFilter {
    fn get_size(x_value: usize, y_value: f64) -> usize {
        assert!(y_value > 0.0 && y_value < 1.0, "probability value must be 0 - 1");
        let n = x_value as f64;
        let m = -(n * y_value.ln()) / (2f64.ln().powi(2));
        m.ceil() as usize
    }

    fn get_hash_count(m: usize, n: usize) -> usize {
        assert!(n > 0, "n value must be more than 0");
        let m = m as f64;
        let n = n as f64;
        let k = (m / n) * 2f64.ln();
        k.ceil() as usize
    }
}

#[pymethods]
impl BloomFilter {
    #[new]
    pub fn new(size: usize, probability: f64) -> Self {
        let final_size = Self::get_size(size, probability);
        Self {
            probability: probability,
            size: final_size,
            hash_count: Self::get_hash_count(final_size, size),
            array: BitArray::new(final_size),
        }
    }

    pub fn add(&mut self, py: Python<'_>, item: PyObject) -> PyResult<()> {
        let py_hash = item.as_ref(py).hash()?;

        let h1 = py_hash as usize;
        let h2 = (h1 >> 17) | (h1 << 47);

        for i in 0..self.hash_count {
            let combined_hash = h1.wrapping_add(i).wrapping_mul(h2);
            let index = combined_hash % self.size;
            self.array.set(index);
        }
        Ok(())
    }

    pub fn contains(&self, py: Python<'_>, item: PyObject) -> PyResult<bool> {
        let py_hash = item.as_ref(py).hash()?;

        let h1 = py_hash as usize;
        let h2 = (h1 >> 17) | (h1 << 47);

        for i in 0..self.hash_count {
            let combined_hash = h1.wrapping_add(i).wrapping_mul(h2);
            let index = combined_hash % self.size;
            if !self.array.get(index) {
                return Ok(false);
            }
        }
        return Ok(true);
    }

    pub fn clear(&mut self) {
        self.array.clear_all();
    }
}