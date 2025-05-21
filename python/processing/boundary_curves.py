import numpy as np
import open3d as o3d


class BoundaryCurves:
    def __init__(self, processing_panel):
        self._processing_panel = processing_panel

    def _extract_pointcloud_boundaries(
        self, point_cloud, clusters, curvature_threshold=0.01, neighbor_radius=4
    ):
        print("Extracting point cloud-based fracture boundaries with continuity...")
        all_linesets = []

        for cluster_indices in clusters:
            cluster_pcd = point_cloud.select_by_index(cluster_indices)
            if len(cluster_pcd.points) < 50:
                continue

            cluster_pcd.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, max_nn=30)
            )

            # Compute curvature
            points = np.asarray(cluster_pcd.points)
            kdtree = o3d.geometry.KDTreeFlann(cluster_pcd)
            boundary_points = []

            for i in range(len(points)):
                [_, idx, _] = kdtree.search_radius_vector_3d(
                    cluster_pcd.points[i], neighbor_radius
                )
                if len(idx) < 5:
                    continue
                neighbors = np.asarray(cluster_pcd.points)[idx, :]
                cov = np.cov(neighbors.T)
                eigvals, _ = np.linalg.eigh(cov)
                eigvals = np.sort(eigvals)
                curvature = eigvals[0] / np.sum(eigvals)
                if curvature > curvature_threshold:
                    boundary_points.append(cluster_pcd.points[i])

            if len(boundary_points) > 1:
                # Build an ordered line set including all points
                boundary_pcd = o3d.geometry.PointCloud(
                    points=o3d.utility.Vector3dVector(boundary_points)
                )
                points_arr = np.asarray(boundary_pcd.points)
                visited = np.zeros(len(points_arr), dtype=bool)
                kdtree = o3d.geometry.KDTreeFlann(boundary_pcd)

                ordered_lines = []

                while not np.all(visited):
                    # Start from an unvisited point
                    unvisited_indices = np.where(not visited)[0]
                    current_idx = unvisited_indices[0]
                    visited[current_idx] = True
                    chain = [current_idx]

                    for _ in range(len(points_arr) - 1):
                        [_, idxs, _] = kdtree.search_knn_vector_3d(
                            points_arr[current_idx], 10
                        )
                        found = False
                        for next_idx in idxs[1:]:  # Skip self
                            if not visited[next_idx]:
                                visited[next_idx] = True
                                ordered_lines.append([current_idx, next_idx])
                                current_idx = next_idx
                                chain.append(current_idx)
                                found = True
                                break
                        if not found:
                            break  # Start new segment

                line_set = o3d.geometry.LineSet(
                    points=o3d.utility.Vector3dVector(points_arr),
                    lines=o3d.utility.Vector2iVector(ordered_lines),
                )
                line_set.paint_uniform_color([1, 0, 0])  # Red lines
                all_linesets.append(line_set)

        return all_linesets
