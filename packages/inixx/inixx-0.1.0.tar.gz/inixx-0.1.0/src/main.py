import math

def _euclidean_distance(p1, p2):
    """Calculate the Euclidean distance between two points."""
    if len(p1) != len(p2):
        raise ValueError("Points must have the same number of dimensions")

    sum_of_squares = 0
    for i in range(len(p1)):
        sum_of_squares += (p1[i] - p2[i]) ** 2

    return math.sqrt(sum_of_squares)

def _get_clusters(X, labels):
    """Organize points into a dictionary of clusters."""
    clusters = {}
    unique_labels = set(labels)

    for label in unique_labels:
        clusters[label] = []

    for i, point in enumerate(X):
        clusters[labels[i]].append(point)

    return clusters

def _calculate_max_intra_cluster_diameter(clusters):
    """Find the maximum distance between points within any single cluster."""
    max_diameter = 0.0

    for label, points in clusters.items():
        if len(points) < 2:
            continue

        cluster_max_diameter = 0.0
        # Iterate through all unique pairs of points in the cluster
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                distance = _euclidean_distance(points[i], points[j])
                if distance > cluster_max_diameter:
                    cluster_max_diameter = distance

        if cluster_max_diameter > max_diameter:
            max_diameter = cluster_max_diameter

    return max_diameter

def _calculate_min_inter_cluster_distance(clusters):
    """Find the minimum distance between any two clusters."""
    min_distance = float('inf')
    cluster_labels = list(clusters.keys())

    if len(cluster_labels) < 2:
        return 0.0 # Or float('inf') depending on definition, 0.0 avoids errors

    # Iterate through all unique pairs of clusters
    for i in range(len(cluster_labels)):
        for j in range(i + 1, len(cluster_labels)):
            cluster_i = clusters[cluster_labels[i]]
            cluster_j = clusters[cluster_labels[j]]

            # Find the minimum distance between any point in i and any point in j
            current_min_pair_dist = float('inf')
            for p_i in cluster_i:
                for p_j in cluster_j:
                    distance = _euclidean_distance(p_i, p_j)
                    if distance < current_min_pair_dist:
                        current_min_pair_dist = distance

            if current_min_pair_dist < min_distance:
                min_distance = current_min_pair_dist

    return min_distance

def dunn_index(X, labels):
    """
    Calculates the Dunn Index for a given clustering.

    The Dunn Index is the ratio of the minimum inter-cluster distance
    to the maximum intra-cluster diameter. A higher value means
    better clustering (more compact and well-separated).

    Parameters:
    X (list of lists or tuples): The input data, where each inner
                                 list/tuple is a data point.
    labels (list or tuple): The cluster labels for each sample.

    Returns:
    float: The Dunn Index score.
    """
    if len(X) != len(labels):
        raise ValueError("Data (X) and labels must have the same length")

    # 1. Organize points into clusters
    clusters = _get_clusters(X, labels)

    if len(clusters) < 2:
        print("Warning: Dunn Index is not defined for a single cluster. Returning 0.")
        return 0.0

    # 2. Calculate max intra-cluster (max cluster diameter)
    max_diameter = _calculate_max_intra_cluster_diameter(clusters)

    # 3. Calculate min inter-cluster (min cluster separation)
    min_separation = _calculate_min_inter_cluster_distance(clusters)

    # 4. Calculate Dunn Index
    if max_diameter == 0:
        # Handle division by zero. This can happen if all clusters
        # have only one point.
        print("Warning: Max cluster diameter is 0. Returning 0.")
        return 0.0

    return min_separation / max_diameter
