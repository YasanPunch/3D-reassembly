import os
import sys

import open3d as o3d
import open3d.visualization.gui as gui  # type: ignore
import open3d.visualization.rendering as rendering  # type: ignore

from pcprocessing.pcprocessing_panel import PCProcessingPanel
from settings.settings import Settings
from settings.settings_panel import SettingsPanel


class App:
    MENU_OPEN = 1
    MENU_EXPORT = 2
    MENU_QUIT = 3
    MENU_SHOW_SETTINGS = 11
    MENU_SHOW_PCPROCESSING = 12
    MENU_ABOUT = 21

    DEFAULT_IBL = "default"

    def __init__(self, width, height):
        self.settings = Settings()

        resource_path = gui.Application.instance.resource_path
        self.settings.new_ibl_name = resource_path + "/" + App.DEFAULT_IBL

        self.window = gui.Application.instance.create_window("Open3D", width, height)
        w = self.window  # to make the code more concise

        self._settings_panel = SettingsPanel(self)
        self._pcprocessing_panel = PCProcessingPanel(self)

        # 3D widget
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(w.renderer)
        self._scene.set_on_sun_direction_changed(self._settings_panel._on_sun_dir)

        # Normally our user interface can be children of all one layout (usually
        # a vertical layout), which is then the only child of the window. In our
        # case we want the scene to take up all the space and the settings panel
        # to go above it. We can do this custom layout by providing an on_layout
        # callback. The on_layout callback should set the frame
        # (position + size) of every child correctly. After the callback is
        # done the window will layout the grandchildren.
        w.set_on_layout(self._on_layout)
        w.add_child(self._scene)
        w.add_child(self._settings_panel._settings_panel)
        w.add_child(self._pcprocessing_panel._pcprocessing_panel)

        # ---- Menu ----
        # The menu is global (because the macOS menu is global), so only create
        # it once, no matter how many windows are created
        if gui.Application.instance.menubar is None:
            file_menu = gui.Menu()
            file_menu.add_item("Open...", App.MENU_OPEN)
            file_menu.add_item("Export Current Image...", App.MENU_EXPORT)
            file_menu.add_separator()
            file_menu.add_item("Quit", App.MENU_QUIT)
            settings_menu = gui.Menu()
            settings_menu.add_item("Lighting & Materials", App.MENU_SHOW_SETTINGS)
            settings_menu.set_checked(App.MENU_SHOW_SETTINGS, True)
            settings_menu.add_item("Point Cloud Processing", App.MENU_SHOW_PCPROCESSING)
            settings_menu.set_checked(App.MENU_SHOW_PCPROCESSING, True)
            help_menu = gui.Menu()
            help_menu.add_item("About", App.MENU_ABOUT)

            menu = gui.Menu()
            menu.add_menu("File", file_menu)
            menu.add_menu("Settings", settings_menu)
            menu.add_menu("Help", help_menu)
            gui.Application.instance.menubar = menu

        # The menubar is global, but we need to connect the menu items to the
        # window, so that the window can call the appropriate function when the
        # menu item is activated.
        w.set_on_menu_item_activated(App.MENU_OPEN, self._on_menu_open)
        w.set_on_menu_item_activated(App.MENU_EXPORT, self._on_menu_export)
        w.set_on_menu_item_activated(App.MENU_QUIT, self._on_menu_quit)
        w.set_on_menu_item_activated(
            App.MENU_SHOW_SETTINGS, self._on_menu_toggle_settings_panel
        )
        w.set_on_menu_item_activated(
            App.MENU_SHOW_PCPROCESSING, self._on_menu_toggle_pcprocessing_panel
        )
        w.set_on_menu_item_activated(App.MENU_ABOUT, self._on_menu_about)
        # Menu ----

        self._settings_panel._apply_settings()

    def _on_layout(self, layout_context):
        # The on_layout callback should set the frame (position + size) of every
        # child correctly. After the callback is done the window will layout
        # the grandchildren.
        r = self.window.content_rect
        self._scene.frame = r
        width = 17 * layout_context.theme.font_size

        height = min(
            r.height,
            self._settings_panel._settings_panel.calc_preferred_size(
                layout_context, gui.Widget.Constraints()
            ).height,
        )
        self._settings_panel._settings_panel.frame = gui.Rect(
            r.get_right() - width, r.y, width, height
        )

        height = min(
            r.height,
            self._pcprocessing_panel._pcprocessing_panel.calc_preferred_size(
                layout_context, gui.Widget.Constraints()
            ).height,
        )
        self._pcprocessing_panel._pcprocessing_panel.frame = gui.Rect(
            r.get_right() - width, r.get_bottom() - height, width, height
        )

    def _on_menu_open(self):
        dlg = gui.FileDialog(
            gui.FileDialog.OPEN, "Choose file to load", self.window.theme
        )
        dlg.add_filter(
            ".ply .stl .fbx .obj .off .gltf .glb",
            "Triangle mesh files (.ply, .stl, .fbx, .obj, .off, .gltf, .glb)",
        )
        dlg.add_filter(
            ".xyz .xyzn .xyzrgb .ply .pcd .pts",
            "Point cloud files (.xyz, .xyzn, .xyzrgb, .ply, .pcd, .pts)",
        )
        dlg.add_filter(".ply", "Polygon files (.ply)")
        dlg.add_filter(".stl", "Stereolithography files (.stl)")
        dlg.add_filter(".fbx", "Autodesk Filmbox files (.fbx)")
        dlg.add_filter(".obj", "Wavefront OBJ files (.obj)")
        dlg.add_filter(".off", "Object file format (.off)")
        dlg.add_filter(".gltf", "OpenGL transfer files (.gltf)")
        dlg.add_filter(".glb", "OpenGL binary transfer files (.glb)")
        dlg.add_filter(".xyz", "ASCII point cloud files (.xyz)")
        dlg.add_filter(".xyzn", "ASCII point cloud with normals (.xyzn)")
        dlg.add_filter(".xyzrgb", "ASCII point cloud files with colors (.xyzrgb)")
        dlg.add_filter(".pcd", "Point Cloud Data files (.pcd)")
        dlg.add_filter(".pts", "3D Points files (.pts)")
        dlg.add_filter("", "All files")

        # A file dialog MUST define on_cancel and on_done functions
        dlg.set_on_cancel(self._on_file_dialog_cancel)
        dlg.set_on_done(self._on_load_dialog_done)
        self.window.show_dialog(dlg)

    def _on_file_dialog_cancel(self):
        self.window.close_dialog()

    def _on_load_dialog_done(self, filename):
        self.window.close_dialog()
        self.load(filename)

    def _on_menu_export(self):
        dlg = gui.FileDialog(
            gui.FileDialog.SAVE, "Choose file to save", self.window.theme
        )
        dlg.add_filter(".png", "PNG files (.png)")
        dlg.set_on_cancel(self._on_file_dialog_cancel)
        dlg.set_on_done(self._on_export_dialog_done)
        self.window.show_dialog(dlg)

    def _on_export_dialog_done(self, filename):
        self.window.close_dialog()
        frame = self._scene.frame
        self.export_image(filename, frame.width, frame.height)

    def _on_menu_quit(self):
        gui.Application.instance.quit()

    def _on_menu_toggle_settings_panel(self):
        self._settings_panel._settings_panel.visible = (
            not self._settings_panel._settings_panel.visible
        )
        gui.Application.instance.menubar.set_checked(
            App.MENU_SHOW_SETTINGS, self._settings_panel._settings_panel.visible
        )

    def _on_menu_toggle_pcprocessing_panel(self):
        self._pcprocessing_panel._pcprocessing_panel.visible = (
            not self._pcprocessing_panel._pcprocessing_panel.visible
        )
        gui.Application.instance.menubar.set_checked(
            App.MENU_SHOW_PCPROCESSING,
            self._pcprocessing_panel._pcprocessing_panel.visible,
        )

    def _on_menu_about(self):
        # Show a simple dialog. Although the Dialog is actually a widget, you can
        # treat it similar to a Window for layout and put all the widgets in a
        # layout which you make the only child of the Dialog.
        em = self.window.theme.font_size
        dlg = gui.Dialog("About")

        # Add the text
        dlg_layout = gui.Vert(em, gui.Margins(em, em, em, em))
        dlg_layout.add_child(gui.Label("Open3D GUI Example"))

        # Add the Ok button. We need to define a callback function to handle
        # the click.
        ok = gui.Button("OK")
        ok.set_on_clicked(self._on_about_ok)

        # We want the Ok button to be an the right side, so we need to add
        # a stretch item to the layout, otherwise the button will be the size
        # of the entire row. A stretch item takes up as much space as it can,
        # which forces the button to be its minimum size.
        h = gui.Horiz()
        h.add_stretch()
        h.add_child(ok)
        h.add_stretch()
        dlg_layout.add_child(h)

        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)

    def _on_about_ok(self):
        self.window.close_dialog()

    def load(self, path):
        self._scene.scene.clear_geometry()
        self.model = None

        geometry = None
        geometry_type = o3d.io.read_file_geometry_type(path)

        mesh = None
        if geometry_type & o3d.io.CONTAINS_TRIANGLES:
            mesh = o3d.io.read_triangle_model(path)
        if mesh is None:
            print("[Info]", path, "appears to be a point cloud")
            cloud = None
            try:
                cloud = o3d.io.read_point_cloud(path)
            except Exception:
                pass
            if cloud is not None:
                print("[Info] Successfully read", path)
                if not cloud.has_normals():
                    cloud.estimate_normals()
                cloud.normalize_normals()
                geometry = cloud
            else:
                print("[WARNING] Failed to read points", path)

        if geometry is not None or mesh is not None:
            try:
                if mesh is not None:
                    # Triangle model
                    self._scene.scene.add_model("__model__", mesh)
                    self.model = mesh
                else:
                    # Point cloud
                    self._scene.scene.add_geometry(
                        "__model__", geometry, self.settings.material
                    )
                    self.model = mesh
                bounds = self._scene.scene.bounding_box
                self._scene.setup_camera(60, bounds, bounds.get_center())
            except Exception as e:
                print(e)

    def export_image(self, path, width, height):
        def on_image(image):
            img = image

            quality = 9  # png
            if path.endswith(".jpg"):
                quality = 100
            o3d.io.write_image(path, img, quality)

        self._scene.scene.scene.render_to_image(on_image)


def main():
    # We need to initialize the application, which finds the necessary shaders
    # for rendering and prepares the cross-platform window abstraction.
    gui.Application.instance.initialize()

    w = App(1024, 768)

    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.exists(path):
            w.load(path)
        else:
            w.window.show_message_box("Error", "Could not open file '" + path + "'")
    else:
        path = "/home/pundima/dev/reassembly/data/cloudcompare/lid/1/top1.obj"
        if os.path.exists(path):
            w.load(path)
        else:
            w.window.show_message_box("Error", "Could not open file '" + path + "'")

    # Run the event loop. This will not return until the last window is closed.
    gui.Application.instance.run()


if __name__ == "__main__":
    main()
