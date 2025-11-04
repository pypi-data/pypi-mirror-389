use super::graph_base::GraphBase;

pub trait UndirectedGraph: GraphBase {
    fn neighbors(&self, node: Self::NodeId) -> Vec<Self::NodeId>;

    // Implementación por defecto para grado
    fn degree(&self, node: Self::NodeId) -> usize {
        self.neighbors(node).len()
    }
}