use super::graph_base::GraphBase;

pub trait WeightedGraph: GraphBase
where
    Self::NodeId: Clone,  // Add trait bound
{
    fn edge_weight(&self, from: Self::NodeId, to: Self::NodeId) -> Option<f64>;

    fn total_weight(&self) -> f64 {
        self.edges()
            .iter()
            // Use cloned() to avoid moving from the reference
            .filter_map(|(from, to)| {
                self.edge_weight(from.clone(), to.clone())
            })
            .sum()
    }
}