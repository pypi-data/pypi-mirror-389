use std::collections::{HashMap, HashSet};

// Definiciones de estructuras de datos básicas
#[derive(Debug, Clone)]
pub struct Node<T> {
    pub id: usize,
    pub value: T,
}

#[derive(Debug, Clone)]
pub struct Edge<E> {
    pub from: usize,
    pub to: usize,
    pub data: E,
}

// Alias comunes para mejorar la legibilidad
pub type AdjacencyList = HashMap<usize, Vec<usize>>;
pub type WeightedAdjacencyList = HashMap<usize, Vec<(usize, f64)>>;
pub type NodeSet = HashSet<usize>;