use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyList;
use pyo3::PyObject;
use std::cmp::Ordering;
use std::collections::VecDeque;
struct LeafNode {
    value: PyObject,
    left: Option<Box<LeafNode>>,
    right: Option<Box<LeafNode>>,
    count: usize,
}

impl LeafNode {
    fn new(data: PyObject) -> Self {
        Self {
            value: data,
            left: None,
            right: None,
            count: 1
        }
    }
}

#[pyclass]
pub struct BinarySearchTree {
    root: Option<Box<LeafNode>>,
    size: usize,
    allow_duplicates: bool,
}

impl BinarySearchTree {
    fn comparison(py: Python, x: PyObject, y: PyObject) -> PyResult<Ordering> {
        let x_ref = x.as_ref(py);
        let y_ref = y.as_ref(py);

        if x_ref.lt(y_ref)? {
            Ok(Ordering::Less)
        } else if x_ref.gt(y_ref)? {
            Ok(Ordering::Greater)
        } else if x_ref.eq(y_ref)? {
            Ok(Ordering::Equal)
        } else {
            Err(PyValueError::new_err("Cannot compare Python Objects"))
        }
    }

    fn node_height(node: &Option<Box<LeafNode>>) -> usize {
        if let Some(n) = node {
            let left_height = Self::node_height(&n.left);
            let right_height = Self::node_height(&n.right);
            1 + left_height.max(right_height)
        } else {
            0
        }
    }

    fn inorder_traversal(py: Python, node: &Option<Box<LeafNode>>, acc: &mut Vec<PyObject>, duplicate: bool) {
        if let Some(ref boxed_node) = node {
            Self::inorder_traversal(py, &boxed_node.left, acc, duplicate);

            if duplicate {
                for _ in 0..boxed_node.count {
                    acc.push(boxed_node.value.clone_ref(py));
                }
            } else {
                acc.push(boxed_node.value.clone_ref(py));
            }

            Self::inorder_traversal(py,&boxed_node.right, acc, duplicate);
        } 
    }

    fn preorder_traversal(py: Python, node: &Option<Box<LeafNode>>, acc: &mut Vec<PyObject>, duplicate: bool) {
        if let Some(ref boxed_node) = node {

            if duplicate {
                for _ in 0..boxed_node.count {
                    acc.push(boxed_node.value.clone_ref(py));
                }
            } else {
                acc.push(boxed_node.value.clone_ref(py));
            }

            Self::preorder_traversal(py, &boxed_node.left, acc, duplicate);
            Self::preorder_traversal(py,&boxed_node.right, acc, duplicate);
        } 
    }

    fn postorder_traversal(py: Python, node: &Option<Box<LeafNode>>, acc: &mut Vec<PyObject>, duplicate: bool) {
        if let Some(ref boxed_node) = node {
            Self::postorder_traversal(py, &boxed_node.left, acc, duplicate);
            Self::postorder_traversal(py,&boxed_node.right, acc, duplicate);

            if duplicate {
                for _ in 0..boxed_node.count {
                    acc.push(boxed_node.value.clone_ref(py));
                }
            } else {
                acc.push(boxed_node.value.clone_ref(py));
            }
        }
    }

    fn prune_traversal(node: &mut Option<Box<LeafNode>>) {
        if let Some(ref mut current_node) = node {

            Self::prune_traversal(&mut current_node.left);
            Self::prune_traversal(&mut current_node.right);

            if current_node.left.is_none() && current_node.right.is_none() {
                *node = None;
            }
        }
    }

    fn remove_node(py: Python, node: &mut Option<Box<LeafNode>>, value: &PyObject) -> PyResult<Option<PyObject>> {
        if let Some(current_node) = node {
            match Self::comparison(py, value.clone(), current_node.value.clone())? {
                Ordering::Less => Self::remove_node(py, &mut current_node.left, value),
                Ordering::Greater => Self::remove_node(py, &mut current_node.right, value),
                Ordering::Equal => {
                    if current_node.count > 1 {
                        current_node.count -= 1;
                        return Ok(Some(current_node.value.clone_ref(py)));
                    }

                    let removed_node = current_node.value.clone_ref(py);

                    match (current_node.left.take(), current_node.right.take()) {
                        (None, None) => {
                            *node = None;
                        }
                        (Some(left), None) => {
                            *node = Some(left)
                        }
                        (None, Some(right)) => {
                            *node = Some(right)
                        }
                        (Some(left), Some(right)) => {
                            let (successor_val, successor_count) = Self::inorder_successor(&right, py)?;
                            current_node.value = successor_val.clone_ref(py);
                            current_node.count = successor_count;
                            current_node.left = Some(left);
                            current_node.right = Self::remove_node_internal(py, right, &successor_val)?;
                        }
                    }

                    Ok(Some(removed_node))
                }
            }
        } else {
            Ok(None)
        }
    }

    fn remove_node_internal(py: Python, node: Box<LeafNode>, value: &PyObject) -> PyResult<Option<Box<LeafNode>>> {
        let mut node = Some(node);
        Self::remove_node(py, &mut node, value)?;
        Ok(node)
    }

    fn inorder_successor(node: &Box<LeafNode>, py: Python) -> PyResult<(PyObject, usize)> {
        let mut current_node = node;
        while let Some(ref left_node) = current_node.left {
            current_node = left_node;
        }
        Ok((current_node.value.clone_ref(py), current_node.count))
    }
}

#[pymethods]
impl BinarySearchTree {
    #[new]
    pub fn new(allow_duplicates: bool) -> Self {
        Self {
            root: None,
            size: 0,
            allow_duplicates: allow_duplicates,
        }
    }

    pub fn add(&mut self, py: Python, value: PyObject) -> PyResult<()> {
        let mut current_node = &mut self.root;

        while let Some(node) = current_node {
            match Self::comparison(py, value.clone(), node.value.clone())? {
                Ordering::Less => {
                    current_node = &mut node.left;
                }
                Ordering::Greater => {
                    current_node = &mut node.right;
                }
                Ordering::Equal => {
                    if self.allow_duplicates {
                        node.count += 1;
                        self.size += 1;
                    }
                    return Ok(());
                }
            }
        }
        *current_node = Some(Box::new(LeafNode::new(value)));
        self.size += 1;

        Ok(())
    }

    pub fn remove(&mut self, py: Python, value: PyObject) -> PyResult<PyObject> {
        let result = Self::remove_node(py, &mut self.root, &value)?;
        if let Some(val) = result {
            self.size -= 1;
            Ok(val)
        } else {
            Err(PyValueError::new_err("Value not found in the current BST"))
        }
    }

    pub fn prune(&mut self, _py: Python) -> PyResult<()> {
        if self.size == 0 {
            return Err(PyValueError::new_err("The current Binary Search Tree holds no nodes"));
        }

        Self::prune_traversal(&mut self.root);
        Ok(())
    }

    pub fn peek_root(&self, py: Python) -> PyResult<PyObject> {
        match self.root.as_ref() {
            Some(node) => Ok(node.value.clone_ref(py)),
            None => Err(PyValueError::new_err("No elements currently available in the BST"))
        }
    }

    pub fn contains(&self, py: Python, value: PyObject) -> PyResult<bool> {
        if self.is_empty() {
            return Ok(false);
        }

        let mut current_node = self.root.as_ref();
        while let Some(node) = current_node {
            match Self::comparison(py, value.clone(), node.value.clone())? {
                Ordering::Less => current_node = node.left.as_ref(),
                Ordering::Greater => current_node = node.right.as_ref(),
                Ordering::Equal => return Ok(true)
            }
        }
        return Ok(false);
    }

    pub fn extend(&mut self, py: Python, iterable: &PyList) -> PyResult<()> {
        for item in iterable.iter() {
            let object = item.extract()?;
            self.add(py, object)?;
        }
        Ok(())
    }

    pub fn min(&self, py: Python) -> PyResult<PyObject> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in the BST"));
        }

        let current_node = self.root.as_ref();
        while let Some(node) = current_node {
            if node.left.is_none() {
                return Ok(node.value.clone_ref(py));
            }
        }
        Err(PyValueError::new_err("Invalid Tree Structure"))
    }

    pub fn max(&self, py: Python) -> PyResult<PyObject> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in the BST"));
        }

        let current_node = self.root.as_ref();
        while let Some(node) = current_node {
            if node.right.is_none() {
                return Ok(node.value.clone_ref(py));
            }
        }
        Err(PyValueError::new_err("Invalid Tree Structure"))
    }

    pub fn at_depth(&self, py: Python, value: PyObject) -> PyResult<usize> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in the BST"));
        }

        let mut count = 0;
        let mut current_node = self.root.as_ref();
        while let Some(node) = current_node {
            match Self::comparison(py, value.clone(), node.value.clone())? {
                Ordering::Less => current_node = node.left.as_ref(),
                Ordering::Greater => current_node = node.right.as_ref(),
                Ordering::Equal => return Ok(count)
            }
            count += 1;
        }
        Err(PyValueError::new_err("Value not found in the Binary Search Tree"))
    }

    pub fn height(&self) -> usize {
        Self::node_height(&self.root)
    }

    pub fn size(&self) -> usize {
        self.size
    }

    pub fn is_empty(&self) -> bool {
        self.size == 0
    }

    pub fn inorder_list<'py>(&self, py: Python<'py>) -> PyResult<&'py PyList> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in the BST"));
        }

        let mut elements = Vec::with_capacity(self.size);
        Self::inorder_traversal(py, &self.root, &mut elements, self.allow_duplicates);
        Ok(PyList::new(py, elements))
    }

    pub fn preorder_list<'py>(&mut self, py: Python<'py>) -> PyResult<&'py PyList> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in the BST"));
        }

        let mut elements = Vec::with_capacity(self.size);
        Self::preorder_traversal(py, &self.root, &mut elements, self.allow_duplicates);
        Ok(PyList::new(py, elements))
    }

    pub fn postorder_list<'py>(&mut self, py: Python<'py>) -> PyResult<&'py PyList> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in the BST"));
        }

        let mut elements = Vec::with_capacity(self.size);
        Self::postorder_traversal(py, &self.root, &mut elements, self.allow_duplicates);
        Ok(PyList::new(py, elements))
    }

    pub fn bfs_list<'py>(&mut self, py: Python<'py>) -> PyResult<&'py PyList> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in the BST"));
        }

        let mut results: Vec<PyObject> = Vec::new();
        let mut queue: VecDeque<&Box<LeafNode>> = VecDeque::new();

        if let Some(ref root_node) = self.root {
            queue.push_back(root_node);
        }

        while let Some(current_node) = queue.pop_front() {
            if self.allow_duplicates {
                for _ in 0..current_node.count {
                    results.push(current_node.value.clone_ref(py));
                }
            } else {
                results.push(current_node.value.clone_ref(py));
            }

            if let Some(ref left_node) = current_node.left {
                queue.push_back(left_node);
            }
            if let Some(ref right_node) = current_node.right {
                queue.push_back(right_node);
            }
        }
        Ok(PyList::new(py, results))
    }

    pub fn copy(&mut self, py: Python) -> PyResult<PyObject> {
        if self.is_empty() {
            return Err(PyValueError::new_err("No elements currently available in the BST"));
        }

        let mut new_tree = BinarySearchTree::new(self.allow_duplicates);
        let tree_list = self.bfs_list(py)?;

        for item in tree_list.iter() {
            let obj = item.extract()?;
            new_tree.add(py, obj)?;
        }
        Py::new(py, new_tree).map(|py_obj| py_obj.to_object(py))
    }

    pub fn clear(&mut self) {
        self.root = None;
        self.size = 0;
    }
}