import open3d as o3d
import open3d.visualization.gui as gui  # type: ignore
import open3d.visualization.rendering as rendering
import os

from processing.boundary_curves import BoundaryCurves
from processing.segmentation import Segmentation


class ProcessingPanel:
    def __init__(self, app):
        self.app = app
        self.segmentation = Segmentation()

        w = app.window  # to make the code more concise
        em = w.theme.font_size
        separation_height = int(round(0.5 * em))

        self._panel = gui.Vert(
            0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em)
        )

        self.label = gui.Label("Processing Panel")
        self._panel.add_child(self.label)
        self._panel.add_fixed(separation_height)

        # Segmentation parameters section
        seg_params = gui.CollapsableVert(
            "Segmentation Parameters", 0.25 * em, gui.Margins(em, 0, 0, 0)
        )
        
        # Max curvature parameter
        h = gui.Horiz(0.25 * em)
        h.add_child(gui.Label("Max Curvature (deg):"))
        self._max_curvature_edit = gui.NumberEdit(gui.NumberEdit.Type.DOUBLE)
        self._max_curvature_edit.set_value(30.0)
        self._max_curvature_edit.set_on_value_changed(self._on_max_curvature_changed)
        h.add_child(self._max_curvature_edit)
        seg_params.add_child(h)
        
        # Area limit parameter
        h = gui.Horiz(0.25 * em)
        h.add_child(gui.Label("Min Area (%):"))
        self._area_limit_edit = gui.NumberEdit(gui.NumberEdit.Type.DOUBLE)
        self._area_limit_edit.set_value(2.0)
        self._area_limit_edit.set_on_value_changed(self._on_area_limit_changed)
        h.add_child(self._area_limit_edit)
        seg_params.add_child(h)
        
        self._panel.add_child(seg_params)
        self._panel.add_fixed(separation_height)

        # Process controls section
        process_ctrls = gui.CollapsableVert(
            "Process controls", 0.25 * em, gui.Margins(em, 0, 0, 0)
        )

        self._segment_mesh_button = gui.Button("Segment")
        self._segment_mesh_button.horizontal_padding_em = 0.5
        self._segment_mesh_button.vertical_padding_em = 0
        self._segment_mesh_button.set_on_clicked(self._on_segment)

        self._boundary_lines_button = gui.Button("Boundary Lines")
        self._boundary_lines_button.horizontal_padding_em = 0.5
        self._boundary_lines_button.vertical_padding_em = 0
        self._boundary_lines_button.set_on_clicked(self._on_boundary_lines)

        process_ctrls.add_child(self._segment_mesh_button)
        process_ctrls.add_child(self._boundary_lines_button)
        self._panel.add_child(process_ctrls)
        self._panel.add_fixed(separation_height)

    def _on_max_curvature_changed(self, value):
        """Update max curvature parameter."""
        self.segmentation.update_parameters({'max_curvature_deg': value})

    def _on_area_limit_changed(self, value):
        """Update area limit parameter."""
        self.segmentation.update_parameters({'area_limit_fraction': value / 100.0})

    def _on_segment(self):
        """Perform segmentation on selected models."""
        print("\n=== SEGMENTATION PROCESS STARTED ===")
        
        if len(self.app._scenes_selected) == 0:
            print("ERROR: No scenes selected!")
            return
        
        processed_count = 0
        
        for i in self.app._scenes_selected:
            if i == 0:  # Skip processed scene
                print(f"Skipping scene 0 (processed scene)")
                continue

            print(f"\nProcessing scene {i}...")
            
            # Get the scene widget and path
            if i >= len(self.app._scenes) or i >= len(self.app._scenes_paths):
                print(f"ERROR: Invalid scene index {i}")
                continue
                
            scene_widget = self.app._scenes[i]
            path = self.app._scenes_paths[i]
            
            print(f"File: {os.path.basename(path)}")
            
            # Perform segmentation
            success = self.segmentation.segment_mesh(
                path, 
                scene_widget, 
                self.app.settings.material
            )
            
            if success:
                processed_count += 1
            else:
                print(f"Failed to segment: {path}")
        
        print(f"\n=== SEGMENTATION COMPLETE ===")
        print(f"Successfully processed {processed_count} models")

    def _on_boundary_lines(self):
        boundaryCurves = BoundaryCurves()

        line_material = rendering.MaterialRecord()
        line_material.shader = "unlitLine"
        line_material.line_width = 2.0
        line_material.base_color = [0.0, 0.0, 0.0, 1.0]

        for i in self.app._scenes_selected:
            if i == 0:
                continue

            path = self.app._scenes_paths[i]
            point_cloud, line_sets = boundaryCurves.extract_pointcloud_boundaries(path)
            self.app._scenes[i].scene.clear_geometry()
            self.app._scenes[i].scene.add_geometry(
                "PointCloud", point_cloud, self.app.settings.material
            )
            for idx, line_set in enumerate(line_sets):
                self.app._scenes[i].scene.add_geometry(
                    f"LineSetPCD_{idx}",
                    create_point_cloud_from_lineset(line_set),
                    self.app.settings.material,
                )


def create_point_cloud_from_lineset(line_set):
    """
    Creates a PointCloud object from a LineSet's points.
    """
    if not line_set.has_points():
        print("Warning: LineSet has no points. Returning empty PointCloud.")
        return o3d.geometry.PointCloud()

    pcd = o3d.geometry.PointCloud()
    pcd.points = line_set.points
    pcd.paint_uniform_color([0.0, 0.0, 0.0])

    return pcd