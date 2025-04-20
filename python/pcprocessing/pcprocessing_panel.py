import open3d.visualization.gui as gui  # type: ignore


class PCProcessingPanel:
    def __init__(self, app):
        self.app = app

        w = app.window  # to make the code more concise
        em = w.theme.font_size

        self._pcprocessing_panel = gui.Vert(
            0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em)
        )

        common_ctrls = gui.CollapsableVert(
            "Common controls", 0.25 * em, gui.Margins(em, 0, 0, 0)
        )

        self._process_button = gui.Button("Process")
        self._process_button.horizontal_padding_em = 0.5
        self._process_button.vertical_padding_em = 0
        self._process_button.set_on_clicked(self._on_process)

        common_ctrls.add_child(self._process_button)

        self._pcprocessing_panel.add_child(common_ctrls)

    def _on_process(self):
        self.process()

    def process(self):
        print(self.app.model)
