import open3d.visualization.gui as gui  # type: ignore


class PCProcessingPanel:
    def __init__(self, app):
        self.app = app

        w = app.window  # to make the code more concise
        em = w.theme.font_size

        self._pcprocessing_panel = gui.Vert(
            0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em)
        )
