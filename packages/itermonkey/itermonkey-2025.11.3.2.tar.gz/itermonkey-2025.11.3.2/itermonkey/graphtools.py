import networkx as nx

def hamiltonian_cycle(graph: nx.Graph) -> list | None:
    """Finds a Hamiltonian cycle in the graph if one exists using backtracking.
    A Hamiltonian cycle is a cycle that visits each vertex exactly once and returns to the starting vertex."""
    def backtrack(path):
        if len(path) == len(graph.nodes):
            if path[0] in graph.neighbors(path[-1]):
                return path + [path[0]]
            else:
                return None

        for neighbor in graph.neighbors(path[-1]):
            if neighbor not in path:
                result = backtrack(path + [neighbor])
                if result:
                    return result
        return None

    for starting_node in graph.nodes:
        cycle = backtrack([starting_node])
        if cycle:
            return cycle
    return None

if __name__ == "__main__":
    # Example usage
    G = nx.Graph()
    edges = [(0, 1), (1, 2), (2, 0), (1, 3), (3, 0)]
    G.add_edges_from(edges)

    cycle = hamiltonian_cycle(G)
    if cycle:
        print("Hamiltonian Cycle found:", cycle)
    else:
        print("No Hamiltonian Cycle exists in the graph.")