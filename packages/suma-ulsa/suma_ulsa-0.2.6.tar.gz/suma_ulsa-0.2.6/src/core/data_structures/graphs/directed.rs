use crate::graph::base::{BaseGraph, GraphBase};
use std::collections::HashMap;

pub trait DirectedGraph: GraphBase {
    fn predecessors(&self, node: Self::NodeId) -> Vec<Self::NodeId>;
    fn successors(&self, node: Self::NodeId) -> Vec<Self::NodeId>;
}

// Grafo dirigido simple
pub struct DirectedSimpleGraph<T> {
    pub base: BaseGraph<T, ()>,
    pub adjacency: HashMap<usize, Vec<usize>>,
}

impl<T> DirectedSimpleGraph<T> {
    pub fn new() -> Self {
        Self {
            base: BaseGraph::new(),
            adjacency: HashMap::new(),
        }
    }

    pub fn add_directed_edge(&mut self, from: usize, to: usize) {
        self.base.add_edge(from, to, ());
        self.adjacency.entry(from).or_insert_with(Vec::new).push(to);
    }
}

impl<T> GraphBase for DirectedSimpleGraph<T> {
    type NodeId = usize;
    type NodeData = T;
    type EdgeData = ();

    fn nodes(&self) -> Vec<usize> {
        self.base.nodes.keys().cloned().collect()
    }

    fn edges(&self) -> Vec<(usize, usize)> {
        self.base.edges.keys().cloned().collect()
    }

    fn node_data(&self, id: usize) -> Option<&T> {
        self.base.nodes.get(&id)
    }

    fn edge_data(&self, from: usize, to: usize) -> Option<&()> {
        self.base.edges.get(&(from, to))
    }
}

impl<T> DirectedGraph for DirectedSimpleGraph<T> {
    fn predecessors(&self, node: usize) -> Vec<usize> {
        self.adjacency
            .iter()
            .filter_map(|(&from, neighbors)| {
                if neighbors.contains(&node) {
                    Some(from)
                } else {
                    None
                }
            })
            .collect()
    }

    fn successors(&self, node: usize) -> Vec<usize> {
        self.adjacency.get(&node).cloned().unwrap_or_default()
    }
}