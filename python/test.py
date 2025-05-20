import open3d as o3d
import numpy as np
import random


def voxel_downsample(point_cloud, voxel_size=3.0):
    """
    Voxel downsamples a point cloud.

    Args:
        point_cloud (open3d.geometry.PointCloud): The input point cloud.
        voxel_size (float): The size of the voxels to use for downsampling.

    Returns:
        open3d.geometry.PointCloud: The voxel downsampled point cloud.
    """
    downsampled_pcd = point_cloud.voxel_down_sample(voxel_size=voxel_size)
    return downsampled_pcd


def region_growing(
    point_cloud, k_neighbors=30, normal_threshold=0.95, min_cluster_size=10
):
    """
    Performs region growing on a point cloud based on normal comparison.

    Args:
        point_cloud (open3d.geometry.PointCloud): The input point cloud.
        k_neighbors (int): The number of neighbors to consider for normal estimation and region growing.
        normal_threshold (float): The cosine similarity threshold for comparing normals.  A value
            close to 1 means the normals must be very similar to be in the same region.
        min_cluster_size (int): Minimum number of points in a cluster.

    Returns:
        list of lists: A list of clusters, where each cluster is a list of point indices.
    """

    # 1. Estimate normals for the point cloud.  Important for region growing.
    # print("Estimating normals...")
    # point_cloud.estimate_normals(
    #     search_param=o3d.geometry.KDTreeSearchParamHybrid(
    #         radius=0.1, max_nn=k_neighbors
    #     )
    # )
    # point_cloud.orient_normals_to_align_with_directions()  # Ensure normals point in consistent direction
    # o3d.visualization.draw_geometries(
    #     [point_cloud]
    # )

    points = np.asarray(point_cloud.points)
    normals = np.asarray(point_cloud.normals)
    n_points = len(points)
    print(f"Number of points: {n_points}")

    # 2. Create a KDTree for efficient neighbor search.  Crucial for performance.
    print("Creating KDTree...")
    pcd_tree = o3d.geometry.KDTreeFlann(point_cloud)

    # 3. Initialize data structures for region growing.
    print("Initializing data structures...")
    unvisited = set(range(n_points))  # Set of unvisited point indices
    clusters = []  # List to store the resulting clusters
    visited = [False] * n_points

    # 4.  Iterate through each unvisited point as a potential seed.
    print("Starting region growing...")
    while unvisited:
        seed_index = unvisited.pop()  # Pick a random unvisited point
        if visited[seed_index]:
            continue
        current_cluster = [seed_index]  # Initialize a new cluster
        visited[seed_index] = True
        unvisited_queue = [seed_index]  # Queue for breadth-first search

        # 5. Breadth-first search to grow the region.
        while unvisited_queue:
            growing_index = unvisited_queue.pop(0)  # Dequeue a point index
            seed_point = points[growing_index]
            seed_normal = normals[growing_index]

            # Find neighbors of the current point.
            [k, neighbor_indices, distances] = pcd_tree.search_radius_vector_3d(
                seed_point, radius=20
            )
            # print(
            #     f"neighbor_indices {len(neighbor_indices)} for seed_point {seed_point}"
            # )

            # Check each neighbor to see if it should be added to the region.
            for neighbor_index in neighbor_indices:
                if not visited[neighbor_index]:
                    neighbor_normal = normals[neighbor_index]
                    # Cosine similarity between normals.
                    similarity = np.dot(seed_normal, neighbor_normal)
                    # print(f"{similarity}, {seed_normal}, {neighbor_normal}")
                    if similarity > normal_threshold:
                        visited[neighbor_index] = True
                        unvisited.discard(neighbor_index)  # Remove from unvisited set
                        current_cluster.append(neighbor_index)  # Add to cluster
                        unvisited_queue.append(
                            neighbor_index
                        )  # Enqueue for further growth

        # 6.  Filter small clusters.  Important for noise removal.
        if len(current_cluster) >= min_cluster_size:
            clusters.append(current_cluster)

    print(f"Found {len(clusters)} clusters.")
    return clusters


def visualize_clusters(point_cloud, clusters):
    """
    Visualizes the clusters in a point cloud with different colors.

    Args:
        point_cloud (open3d.geometry.PointCloud): The input point cloud.
        clusters (list of lists): A list of clusters, where each cluster is a list of point indices.
    """
    print(f"Visualizing {len(clusters)} clusters...")
    points = np.asarray(point_cloud.points)
    n_points = len(points)
    cluster_colors = [
        [random.random(), random.random(), random.random()]
        for _ in range(len(clusters))
    ]
    # 0,0,0 for unclustered points
    colors = [[0, 0, 0]] * n_points  # Initialize all points to black (unclustered)

    # Assign a unique color to each point based on its cluster.
    for i, cluster_indices in enumerate(clusters):
        for point_index in cluster_indices:
            colors[point_index] = cluster_colors[i]

    point_cloud.colors = o3d.utility.Vector3dVector(
        colors
    )  # Assign colors to the point cloud
    o3d.visualization.draw_geometries(
        [point_cloud]
    )  # Visualize the colored point cloud


if __name__ == "__main__":
    # 1. Load the point cloud (replace with your actual point cloud file).
    # Example: Use a built-in dataset or read from a file.
    # bunny.ply,  fragment.ply,  teapot.ply
    print("Loading point cloud...")
    # point_cloud = o3d.io.read_point_cloud("path/to/your/point_cloud.ply")
    point_cloud = o3d.io.read_point_cloud(
        "/home/pundima/dev/reassembly/data/cloudcompare/tombstone/1/low.ply"
    )

    if point_cloud.is_empty():
        print(
            "Error: Point cloud is empty or could not be loaded.  Make sure the path is correct."
        )
        exit()

    print("Voxel downsampling")
    point_cloud = voxel_downsample(point_cloud)
    o3d.visualization.draw_geometries([point_cloud])

    # 2. Perform region growing.
    clusters = region_growing(
        point_cloud, k_neighbors=20, normal_threshold=0.90, min_cluster_size=50
    )

    # 3. Visualize the results.
    visualize_clusters(point_cloud, clusters)
    print("Done!")
