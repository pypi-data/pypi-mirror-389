use std::collections::{HashMap, HashSet};
use crate::core::data_structures::graphs::{
    implementations::base_graph::BaseGraph,
    traits::{GraphBase, UndirectedGraph, WeightedGraph}
};

pub struct UndirectedWeightedGraph<T> {
    pub base: BaseGraph<T, f64>,
    pub adjacency: HashMap<usize, HashSet<usize>>,
}

impl<T> UndirectedWeightedGraph<T> {
    pub fn new() -> Self {
        Self {
            base: BaseGraph::new(),
            adjacency: HashMap::new(),
        }
    }

    pub fn add_weighted_edge(&mut self, a: usize, b: usize, weight: f64) {
        self.base.add_edge(a, b, weight);
        self.base.add_edge(b, a, weight); // Simetría

        self.adjacency.entry(a).or_insert_with(HashSet::new).insert(b);
        self.adjacency.entry(b).or_insert_with(HashSet::new).insert(a);
    }
}

impl<T> GraphBase for UndirectedWeightedGraph<T> {
    type NodeId = usize;
    type NodeData = T;
    type EdgeData = f64;

    fn nodes(&self) -> Vec<usize> {
        self.base.nodes.keys().cloned().collect()
    }

    fn edges(&self) -> Vec<(usize, usize)> {
        // Solo incluir cada arista una vez (a < b)
        self.base.edges
            .keys()
            .filter(|(a, b)| a < b)
            .cloned()
            .collect()
    }

    fn node_data(&self, id: usize) -> Option<&T> {
        self.base.nodes.get(&id)
    }

    fn edge_data(&self, from: usize, to: usize) -> Option<&f64> {
        self.base.edges.get(&(from, to))
    }
}

impl<T> UndirectedGraph for UndirectedWeightedGraph<T> {
    fn neighbors(&self, node: usize) -> Vec<usize> {
        self.adjacency
            .get(&node)
            .map(|set| set.iter().cloned().collect())
            .unwrap_or_default()
    }
}

impl<T> WeightedGraph for UndirectedWeightedGraph<T> {
    fn edge_weight(&self, from: usize, to: usize) -> Option<f64> {
        self.base.edges.get(&(from, to)).cloned()
    }
}