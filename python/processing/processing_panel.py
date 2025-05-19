import open3d as o3d
import open3d.visualization.gui as gui  # type: ignore

from processing.segmentation import Segmentation


class ProcessingPanel:
    def __init__(self, app):
        self.app = app

        w = app.window  # to make the code more concise
        em = w.theme.font_size

        self._processing_panel = gui.Vert(
            0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em)
        )

        common_ctrls = gui.CollapsableVert(
            "Common controls", 0.25 * em, gui.Margins(em, em, 0, 0)
        )

        self._process_button = gui.Button("Process")
        self._process_button.horizontal_padding_em = 0.5
        self._process_button.vertical_padding_em = 0
        self._process_button.set_on_clicked(self._on_process)

        common_ctrls.add_child(self._process_button)
        self._processing_panel.add_child(common_ctrls)

        mesh_ctrls = gui.CollapsableVert(
            "Mesh controls", 0.25 * em, gui.Margins(em, em, 0, 0)
        )

        self._segment_mesh_button = gui.Button("Segment Mesh")
        self._segment_mesh_button.horizontal_padding_em = 0.5
        self._segment_mesh_button.vertical_padding_em = 0
        self._segment_mesh_button.set_on_clicked(self._on_segment_mesh)

        mesh_ctrls.add_child(self._segment_mesh_button)
        self._processing_panel.add_child(mesh_ctrls)

    def _on_process(self):
        m = o3d.io.read_triangle_mesh(self.app.mesh_path)
        m.compute_triangle_normals()
        print(m.triangle_normals)
        o3d.visualization.draw_geometries([m])  # type: ignore

    def _on_segment_mesh(self):
        m = o3d.io.read_triangle_mesh(self.app.mesh_path)
        s = Segmentation()
        s.region_growing_mesh(m)
