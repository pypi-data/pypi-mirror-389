
#[derive(Debug, Clone)]
pub struct BitArray {
    data: Vec<u64>,
    len: usize,
}

#[allow(dead_code)]
impl BitArray {
    pub fn new(len: usize) -> Self {
        let size = (len + 63) / 64;
        Self {
            data: vec![0; size],
            len: len,
        }
    }

    pub fn len(&self) -> usize {
        self.len
    }

    pub fn set(&mut self, index: usize) {
        assert!(index < self.len, "index out of bounds");
        let word = index / 64;
        let bit = index % 64;
        self.data[word] |= 1 << bit;
    }

    pub fn get(&self, index: usize) -> bool {
        assert!(index < self.len, "index out of bounds");
        let word = index / 64;
        let bit = index % 64;
        (self.data[word] >> bit) & 1 == 1
    }

    pub fn toggle(&mut self, index: usize) {
        assert!(index < self.len, "index out of bounds");
        let word = index / 64;
        let bit = index % 64;
        self.data[word] ^= 1 << bit;
    }

    pub fn clear(&mut self, index: usize) {
        assert!(index < self.len, "index out of bounds");
        let word = index / 64;
        let bit = index % 64;
        self.data[word] &= !(1 << bit);
    }

    pub fn clear_all(&mut self) {
        for word in self.data.iter_mut() {
            *word = 0;
        }
    }

    pub fn fill_all(&mut self) {
        for word in self.data.iter_mut() {
            *word = !0;
        }
    }
}