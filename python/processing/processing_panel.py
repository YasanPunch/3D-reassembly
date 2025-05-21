import open3d as o3d
import open3d.visualization.gui as gui  # type: ignore

from processing.segmentation import Segmentation
from processing.boundary_curves import BoundaryCurves


class ProcessingPanel:
    def __init__(self, app):
        self.app = app

        w = app.window  # to make the code more concise
        em = w.theme.font_size
        separation_height = int(round(0.5 * em))

        self._panel = gui.Vert(
            0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em)
        )

        self.label = gui.Label("Processing Panel")
        self._panel.add_child(self.label)
        self._panel.add_fixed(separation_height)

        common_ctrls = gui.CollapsableVert(
            "Common controls", 0.25 * em, gui.Margins(em, 0, 0, 0)
        )

        self._process_button = gui.Button("Process")
        self._process_button.horizontal_padding_em = 0.5
        self._process_button.vertical_padding_em = 0
        self._process_button.set_on_clicked(self._on_process)

        common_ctrls.add_child(self._process_button)
        self._panel.add_child(common_ctrls)
        self._panel.add_fixed(separation_height)

        mesh_ctrls = gui.CollapsableVert(
            "Mesh controls", 0.25 * em, gui.Margins(em, 0, 0, 0)
        )

        self._segment_mesh_button = gui.Button("Segment Mesh")
        self._segment_mesh_button.horizontal_padding_em = 0.5
        self._segment_mesh_button.vertical_padding_em = 0
        self._segment_mesh_button.set_on_clicked(self._on_segment_mesh)

        mesh_ctrls.add_child(self._segment_mesh_button)
        self._panel.add_child(mesh_ctrls)
        self._panel.add_fixed(separation_height)

    def _on_process(self):
        m = o3d.io.read_triangle_mesh(self.app.mesh_path)
        m.compute_triangle_normals()
        print(m.triangle_normals)
        o3d.visualization.draw_geometries([m])  # type: ignore

    def _on_segment_mesh(self):
        m = o3d.io.read_triangle_mesh(self.app.mesh_path)
        s = Segmentation(self)
        s.region_growing_mesh(m)
