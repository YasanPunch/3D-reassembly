import open3d as o3d
import numpy as np
import trimesh
from collections import deque
import time


def get_color(index, total_items=20):
    """
    Gets a distinct color for visualization.
    """
    # Define a list of distinct colors
    colors = [
        [1.0, 0.0, 0.0],  # Red
        [0.0, 0.0, 1.0],  # Blue
        [0.0, 1.0, 0.0],  # Green
        [1.0, 1.0, 0.0],  # Yellow
        [1.0, 0.0, 1.0],  # Magenta
        [0.0, 1.0, 1.0],  # Cyan
        [1.0, 0.5, 0.0],  # Orange
        [0.5, 0.0, 1.0],  # Purple
        [0.0, 0.5, 0.0],  # Dark Green
        [0.5, 0.5, 0.5],  # Gray
        [0.8, 0.2, 0.2],  # Dark Red
        [0.2, 0.2, 0.8],  # Dark Blue
        [0.8, 0.8, 0.2],  # Dark Yellow
        [0.8, 0.2, 0.8],  # Dark Magenta
        [0.2, 0.8, 0.8],  # Dark Cyan
        [0.4, 0.2, 0.0],  # Brown
        [0.6, 0.6, 0.6],  # Light Gray
        [0.9, 0.6, 0.3],  # Light Orange
        [0.3, 0.6, 0.9],  # Light Blue
        [0.6, 0.9, 0.3],  # Light Green
    ]
    return colors[index % len(colors)]


def calculate_region_average_normal(tri_mesh, face_indices):
    """
    Calculate the area-weighted average normal for a region.
    """
    if len(face_indices) == 0:
        return np.array([0, 0, 1])
    
    try:
        face_normals = tri_mesh.face_normals[face_indices]
        face_areas = tri_mesh.area_faces[face_indices]
        
        # Area-weighted average
        weighted_normals = face_normals * face_areas[:, np.newaxis]
        avg_normal = np.sum(weighted_normals, axis=0) / np.sum(face_areas)
        
        # Normalize
        norm = np.linalg.norm(avg_normal)
        if norm > 1e-10:
            avg_normal = avg_normal / norm
        else:
            avg_normal = np.array([0, 0, 1])
    except Exception as e:
        print(f"    Warning: Error calculating average normal: {e}")
        avg_normal = np.array([0, 0, 1])
    
    return avg_normal


def region_growing_segmentation(tri_mesh, params):
    """
    Implements the region growing algorithm.
    """
    print("    [Region Growing] Starting segmentation...")
    start_time = time.time()
    
    # Get parameters
    max_curvature_deg = params.get('max_curvature_deg', 30.0)
    area_limit_fraction = params.get('area_limit_fraction', 0.02)
    
    print(f"    [Region Growing] Parameters:")
    print(f"        - Max curvature: {max_curvature_deg}°")
    print(f"        - Min region area: {area_limit_fraction*100:.1f}% of total")
    
    # Calculate Ne threshold from max curvature
    Ne = np.cos(np.radians(max_curvature_deg))
    print(f"        - Normal similarity threshold (Ne): {Ne:.3f}")
    
    num_faces = len(tri_mesh.faces)
    print(f"    [Region Growing] Processing {num_faces} faces...")
    
    face_visited = np.zeros(num_faces, dtype=bool)
    regions = []
    
    # Precompute face adjacency if not available
    print("    [Region Growing] Computing face adjacency...")
    if not hasattr(tri_mesh, 'face_adjacency') or tri_mesh.face_adjacency is None:
        tri_mesh.face_adjacency = trimesh.graph.face_adjacency(tri_mesh.faces)
    
    # Build adjacency list for faster lookup
    adjacency_list = [[] for _ in range(num_faces)]
    for face1, face2 in tri_mesh.face_adjacency:
        adjacency_list[face1].append(face2)
        adjacency_list[face2].append(face1)
    
    # Region growing main loop
    print("    [Region Growing] Growing regions...")
    processed_faces = 0
    
    for start_face in range(num_faces):
        if face_visited[start_face]:
            continue
            
        # Start new region
        current_region = []
        queue = deque([start_face])
        face_visited[start_face] = True
        
        while queue:
            current_face = queue.popleft()
            current_region.append(current_face)
            
            # Update region average normal
            region_avg_normal = calculate_region_average_normal(tri_mesh, current_region)
            
            # Check all neighbors
            for neighbor_face in adjacency_list[current_face]:
                if face_visited[neighbor_face]:
                    continue
                
                # Check if neighbor normal satisfies similarity criterion
                neighbor_normal = tri_mesh.face_normals[neighbor_face]
                dot_product = np.dot(neighbor_normal, region_avg_normal)
                
                if dot_product >= Ne:
                    face_visited[neighbor_face] = True
                    queue.append(neighbor_face)
        
        if len(current_region) > 0:
            regions.append(np.array(current_region))
            processed_faces += len(current_region)
            
            # Progress update
            if len(regions) % 10 == 0:
                progress = (processed_faces / num_faces) * 100
                print(f"        Progress: {progress:.1f}% ({len(regions)} regions found)")
    
    print(f"    [Region Growing] Initial segmentation complete: {len(regions)} regions found")
    
    # Clean-up stage: eliminate small regions
    print("    [Region Growing] Cleaning up small regions...")
    total_area = tri_mesh.area
    area_threshold = area_limit_fraction * total_area
    
    # Calculate region areas
    region_areas = []
    for region in regions:
        region_area = np.sum(tri_mesh.area_faces[region])
        region_areas.append(region_area)
    
    # Sort regions by area (largest first)
    sorted_indices = np.argsort(region_areas)[::-1]
    sorted_regions = [regions[i] for i in sorted_indices]
    sorted_areas = [region_areas[i] for i in sorted_indices]
    
    # Keep only significant regions
    significant_regions = []
    small_regions_count = 0
    
    for i, (region, area) in enumerate(zip(sorted_regions, sorted_areas)):
        if area >= area_threshold:
            significant_regions.append(region)
        else:
            small_regions_count += 1
    
    print(f"    [Region Growing] Found {len(significant_regions)} significant regions")
    print(f"    [Region Growing] {small_regions_count} small regions will be merged")
    
    # Reassign small regions to adjacent larger regions
    if small_regions_count > 0:
        print("    [Region Growing] Merging small regions...")
        
        # Create a face-to-region mapping for significant regions
        face_to_region = np.full(num_faces, -1, dtype=int)
        for region_idx, region in enumerate(significant_regions):
            face_to_region[region] = region_idx
        
        merged_count = 0
        
        # Process small regions
        for region_idx in sorted_indices:
            region = regions[region_idx]
            area = region_areas[region_idx]
            
            if area >= area_threshold:
                continue
            
            # Find adjacent significant regions
            adjacent_regions = set()
            for face in region:
                for neighbor in adjacency_list[face]:
                    neighbor_region = face_to_region[neighbor]
                    if neighbor_region >= 0:
                        adjacent_regions.add(neighbor_region)
            
            # Assign to the most similar adjacent region
            if adjacent_regions:
                best_region = None
                best_similarity = -1
                region_avg_normal = calculate_region_average_normal(tri_mesh, region)
                
                for adj_region_idx in adjacent_regions:
                    adj_region_normal = calculate_region_average_normal(
                        tri_mesh, significant_regions[adj_region_idx]
                    )
                    similarity = np.dot(region_avg_normal, adj_region_normal)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_region = adj_region_idx
                
                if best_region is not None:
                    # Merge with best region
                    significant_regions[best_region] = np.concatenate([
                        significant_regions[best_region], region
                    ])
                    face_to_region[region] = best_region
                    merged_count += 1
        
        print(f"    [Region Growing] Merged {merged_count} small regions")
    
    elapsed_time = time.time() - start_time
    print(f"    [Region Growing] Segmentation complete in {elapsed_time:.2f} seconds")
    print(f"    [Region Growing] Final region count: {len(significant_regions)}")
    
    return significant_regions


class Segmentation:
    def __init__(self):
        self.params = {
            'max_curvature_deg': 30.0,
            'area_limit_fraction': 0.02,
        }
    
    def segment_mesh(self, path, scene_widget, material):
        """
        Segments a mesh and displays results in the scene widget.
        """
        print(f"\n=== Starting Segmentation for: {path} ===")
        
        try:
            # Load the mesh
            print(f"    Loading mesh from: {path}")
            geometry = None
            geometry_type = o3d.io.read_file_geometry_type(path)
            
            if geometry_type & o3d.io.CONTAINS_TRIANGLES:
                mesh = o3d.io.read_triangle_mesh(path)
                if mesh.is_empty():
                    print(f"    ERROR: Loaded mesh is empty")
                    return False
            else:
                print(f"    ERROR: File does not contain triangles")
                return False
            
            print(f"    Loaded mesh with {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles")
            
            # Ensure the mesh has normals
            if not mesh.has_vertex_normals():
                print("    Computing vertex normals...")
                mesh.compute_vertex_normals()
            
            # Convert to trimesh for segmentation
            print("    Converting to trimesh format...")
            tri_mesh = trimesh.Trimesh(
                vertices=np.asarray(mesh.vertices),
                faces=np.asarray(mesh.triangles),
                vertex_normals=np.asarray(mesh.vertex_normals),
                process=False
            )
            
            # Ensure we have face normals and areas
            print("    Computing face properties...")
            _ = tri_mesh.face_normals
            _ = tri_mesh.area_faces
            
            # Perform region growing segmentation
            regions = region_growing_segmentation(tri_mesh, self.params)
            
            if len(regions) == 0:
                print("    WARNING: No regions found!")
                return False
            
            # Clear the scene
            print("    Clearing scene...")
            scene_widget.scene.clear_geometry()
            
            # Create and display segmented regions
            print(f"    Creating visualization for {len(regions)} regions...")
            
            for i, region in enumerate(regions):
                # Calculate region properties
                area = np.sum(tri_mesh.area_faces[region])
                area_fraction = area / tri_mesh.area
                avg_normal = calculate_region_average_normal(tri_mesh, region)
                
                print(f"    Region {i+1}/{len(regions)}:")
                print(f"        - Faces: {len(region)}")
                print(f"        - Area: {area_fraction*100:.1f}% of total")
                print(f"        - Avg normal: [{avg_normal[0]:.2f}, {avg_normal[1]:.2f}, {avg_normal[2]:.2f}]")
                
                # Create mesh for this region
                region_mesh = o3d.geometry.TriangleMesh()
                region_mesh.vertices = mesh.vertices
                region_mesh.triangles = o3d.utility.Vector3iVector(tri_mesh.faces[region])
                region_mesh.remove_unreferenced_vertices()
                
                if region_mesh.has_vertices() and region_mesh.has_triangles():
                    region_mesh.compute_vertex_normals()
                    
                    # Assign a distinct color
                    color = get_color(i, len(regions))
                    region_mesh.paint_uniform_color(color)
                    print(f"        - Color: RGB({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f})")
                    
                    # Create a colored material for this region
                    region_material = o3d.visualization.rendering.MaterialRecord()
                    region_material.shader = "defaultLit"
                    region_material.base_color = [color[0], color[1], color[2], 1.0]
                    
                    # Add to scene as geometry (not model)
                    scene_widget.scene.add_geometry(f"region_{i}", region_mesh, region_material)
                else:
                    print(f"        - WARNING: Region has no valid geometry")
            
            print(f"\n    Segmentation complete! Displayed {len(regions)} regions.")
            return True
            
        except Exception as e:
            print(f"\n    ERROR during segmentation: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_parameters(self, params):
        """Update segmentation parameters."""
        self.params.update(params)
        print(f"    Updated segmentation parameters: {self.params}")