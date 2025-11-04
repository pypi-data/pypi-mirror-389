from ipycanvas import MultiCanvas
from ipywidgets import HBox, Image, Layout, VBox, widgets

from .canvas import CanvasFirmware, CanvasImage, CanvasLink, CanvasScript, CanvasTop
from .menu_icons import MenuIcons
from .popup import CloseWindow
from .terminal import Terminal


class UsecaseDiagram:
    """A class to build canvas object in Notebook"""

    def __init__(self, td_image, width=1120, height=480, enable_coord=False, working_dir=None):
        """Constructs necessary attributes.

        Args:
            td_image (image path): Image to place on the canvas bottom layer.
            width (int, optional): Width of the image. Defaults to 1150.
            height (int, optional): Height of the image. Defaults to 750.
        """
        self.width = width
        self.height = height
        self.canvas = MultiCanvas(4, width=self.width, height=self.height)
        self.canvas.layout.width = "100%"
        self.canvas.layout.height = "100%"
        self.canvas.layout.margin = "0px 0px 0px 50px"
        self.td_image_b = Image.from_file(td_image)
        self.canvas.on_client_ready(self.perform_drawings)

        if enable_coord:
            self.output = Terminal()
            self.output_layout = self.output.get_layout()
            self.canvas_top = CanvasTop(self.canvas, 3, enable_coord, self.output)
        else:
            self.output_layout = None
            self.canvas_top = CanvasTop(self.canvas, 3)

        self.cls_b = CloseWindow(self.canvas[3])
        self.canvas_top.close_list.append(self.cls_b)
        self.menu = MenuIcons(self.canvas_top, self.canvas, None)
        self.script_index = 0
        self.working_dir = working_dir

    def add_image(self, x, y, width, height, image, title):
        """Adds a button on canvas to open an image.
        When clicked within the button area, it pops up specified image window.

        Args:
            x (int): x coordinate w.r.t canvas to place the button.
            y (int): y coordinate w.r.t canvas to place the button.
            width (int): Width of the button.
            height (int): Height of the button.
            image (image path): Image to display when button area is clicked.
            title (str): Title of the popup window.
        """
        canvas_image = CanvasImage(x, y, width, height, image, title, self.canvas)
        self.canvas_top.click_list.append(canvas_image)

    def add_link(self, x, y, width, height, link):
        """Adds an area on to canvas to open any page.

        When clicked within the area, it directs to the given url.

        Args:
            x (int): x coordinate w.r.t canvas to place the link.
            y (int): y coordinate w.r.t canvas to place the link.
            width (int): Width of the link area.
            height (int): Height of the link area.
            link (url): URL to be redirected when clicked.
        """
        canvas_link = CanvasLink(x, y, width, height, link, self.canvas)
        self.canvas_top.click_list.append(canvas_link)

    def add_script(self, x, y, width, height, call_back, prereq_scripts=[], script_index=None):
        """[summary]

        Args:
            x (int): x coordinate w.r.t canvas to place the image button.
            y (int): y coordinate w.r.t canvas to place the image button.
            width (int): Width of the button.
            height (int): Height of the button.
            image (str): Image path.
            title (str): Title of the image. This is shown on the popup Layout.
        """
        if self.output_layout is None:
            self.output = Terminal()
            self.output_layout = self.output.get_layout()
        self.script_index += 1
        script_index = script_index or self.script_index
        canvas_script = CanvasScript(
            x,
            y,
            width,
            height,
            call_back,
            self.output,
            self.canvas,
            self.canvas_top,
            prereq_scripts,
            script_index,
            self.working_dir,
        )
        self.canvas_top.click_list.append(canvas_script)
        return canvas_script

    def add_firmware(self, cb_project_path, mplab_ide_path=None):
        canvas_firmware = CanvasFirmware(
            0, 0, self.canvas, self.canvas_top, cb_project_path, mplab_ide_path, self.working_dir
        )
        self.menu.set_firmware_obj(canvas_firmware)

    def add_usecase_help(self, usecase_help):
        self.menu.set_usecase_help(usecase_help)

    def add_usecase_video(self, yt_video: str = None, youku_video: str = None):
        self.menu.set_usecase_video(yt_video, youku_video)

    def perform_drawings(self):
        """This method draws the given image on the bottom layer of the canvas."""
        self.canvas[0].draw_image(self.td_image_b, 0, 0, self.width, self.height)

    def display_canvas(self):
        """Displays the Usecase Diagram."""
        v_list = VBox([self.menu.return_layout()])
        h_list = [HBox([v_list, self.output_layout])]
        return VBox(h_list)


class OpenDiagram:
    """Shows/ Hides the Usecase diagram."""

    def __init__(self, menu, h_list):
        self.menu = menu
        self.list_items = h_list
        self.res_out = widgets.Output(layout=Layout(height="100%", overflow="hidden", margin="0px"))
        self.left = widgets.Output(layout=Layout(height="100%", overflow="hidden", margin="0px"))

    def depend_layout(self):
        """layout of the entire Usecase diagram division.

        Returns:
            Box layout: Return the Box Layout.
        """
        box = VBox(self.list_items)
        return box


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
