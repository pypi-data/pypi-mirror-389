import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

from ipywidgets import Image
from pygments import formatters, highlight, lexers

from tpds.tp_utils import Client

from .popup import Popup


class CanvasTop:
    """A class to hold buttons list and canvas layer for popup window.

    Buttons list includes image, link and script button areas,
    along with a special button to close popup window.

    """

    def __init__(self, canvas, layer, enable_coord=False, output=None):
        """Constructs necessary attributess

        Args:
            canvas (canvas): The main canvas to interact with.
            layer (int): a canvas layer value for the popup window.
                        (Multicanvas has layers based on input)
        """
        self.t_canvas = canvas
        self.canvas = canvas[layer]
        self.centerX = canvas.width / 2
        self.centerY = canvas.height / 2
        self.click_list = list()
        self.close_list = list()
        self.canvas.on_mouse_down(self.on_click_check)
        if enable_coord:
            self.output = output
            self.canvas.on_mouse_move(self.on_mouse_move)

    def on_click_check(self, x, y):
        """To check whether specific button has been clicked or not.

        Calls respective render function if clicked on the button area.

        Args:
            x (int): x coordinate w.r.t the canvas is returned
                        when mouse click event happens.
            y (int): y coordinate w.r.t the canvas is returned
                        when mouse click event happens.
        """
        if self.close_list[0].is_selected(x, y):
            self.close_list[0].render()
        else:
            sel = [button for button in self.click_list if button.is_selected(x, y)]
            if sel:
                self.canvas.clear()
                sel[0].render()

    def on_mouse_move(self, x, y):
        with self.output.log:
            print(f"Mouse Coordinates: {round(x):04d}:{round(y):04d}", end="\r")


class CanvasLink:
    """Adds a link object on canvas."""

    def __init__(self, x, y, width, height, link, canvas):
        """Constructs required attributes

        Args:
            x (int): x coordinate w.r.t canvas to place the link.
            y (int): y coordinate w.r.t canvas to place the link.
            width (int): Width of the link area.
            height (int): Height of the link area.
            link (url): URL to be redirected when clicked.
            canvas (canvas object): Main canvas object to interact with.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.link = link
        self.canvas = canvas
        self.canvas.on_client_ready(self.layout)

    def layout(self):
        """Layout the button to distinguish as a link."""
        # self.canvas[1].stroke_style = 'blue'
        # self.canvas[1].shadow_offset_x = 0
        # self.canvas[1].shadow_offset_y = 0
        # self.canvas[1].shadow_blur = 0
        # self.canvas[1].begin_path()
        # self.canvas[1].line_width = 3
        # self.canvas[1].move_to(self.x, self.y+self.height)
        # self.canvas[1].line_to(self.x+self.width, self.y+self.height)
        # self.canvas[1].stroke()
        pass

    def is_selected(self, x_in, y_in):
        """Checks if the link is clicked.

        Args:
            x_in (int): x coordinate w.r.t mouse click event is returned.
            y_in (int): y coordinate w.r.t mouse click event is returned.

        Returns:
            bool: True if the link button is clicked, else False.
        """
        return ((x_in > self.x) and (x_in < (self.x + self.width))) and (
            (y_in > self.y) and (y_in < (self.y + self.height))
        )

    def render(self):
        """If a link object is clicked, respective URL is opened."""
        self.client = Client(None)
        self.open_link()
        self.client.client.recv()
        self.client.client.close()

    def open_link(self):
        self.client.send_message("open_link", [self.link])


class CanvasImage:
    """Adds an image object button on canvas."""

    def __init__(self, x, y, width, height, image, title, canvas):
        """Constructs required attributes.

        Args:
            x (int): x coordinate w.r.t canvas to place the image button.
            y (int): y coordinate w.r.t canvas to place the image button.
            width (int): Width of the button.
            height (int): Height of the button.
            image (str): Image path.
            title (str): Title of the image. This is shown on the popup Layout.
            canvas (canvas): Canvas on which the button is placed.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = image
        self.canvas = canvas
        self.popup = Popup(title, self.canvas[3])
        self.canvas.on_client_ready(self.layout)
        self.val = 20

    def layout(self):
        """Layout of the image button."""
        # self.canvas[1].stroke_style = '#2bff00'
        # self.canvas[1].line_width = 3
        # self.canvas[1].line_join = 'round'
        # self.canvas[1].shadow_color = 'black'
        # self.canvas[1].shadow_offset_x = 1
        # self.canvas[1].shadow_offset_y = 1
        # self.canvas[1].shadow_blur = 1
        # self.canvas[1].stroke_rect(
        #     self.x-1, self.y-1,
        #     self.width+1, self.height+1)
        # self.canvas[1].shadow_offset_x = 0
        # self.canvas[1].shadow_offset_y = 0
        # self.canvas[1].shadow_blur = 0
        # self.canvas[1].fill_style = '#2bff00'
        # self.canvas[1].fill_rect(
        #                       self.x-3, self.y-self.val,
        #                       self.width+4, self.val)
        # self.canvas[1].font = '16px serif'
        # self.canvas[1].text_align = 'start'
        # self.canvas[1].text_baseline = 'top'
        # self.canvas[1].fill_style = 'black'
        # self.canvas[1].shadow_offset_x = 0
        # self.canvas[1].shadow_offset_y = 0
        # self.canvas[1].shadow_blur = 0
        # self.canvas[1].fill_text('C Code Snippet', self.x, self.y-self.val+3)
        pass

    def is_selected(self, x_in, y_in):
        """Checks if the image button is clicked.

        Args:
            x_in (int): x coordinate w.r.t mouse click event is returned.
            y_in (int): y coordinate w.r.t mouse click event is returned.

        Returns:
            bool: True if the image button is clicked, else False.
        """
        return ((x_in > self.x) and (x_in < (self.x + self.width))) and (
            (y_in > self.y) and (y_in < (self.y + self.height))
        )

    def render(self):
        """When clicked, the button's corresponding image is poped up."""
        self.popup.draw_image(self.image)


class CanvasScript:
    """Adds a script button on the canvas."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        call_back,
        output,
        canvas,
        canvas_top,
        prereq_scripts,
        index,
        working_dir=None,
    ):
        """Constructs required attributes.

        Args:
            x (int): x coordinate w.r.t canvas to place the script button.
            y (int): y coordinate w.r.t canvas to place the script button.
            width (int): Width of the button.
            height (int): Height of the button.
            call_back (function): Call back function to be called when clicked.
            output (output terminal): Terminal object for log to redirect.
            canvas (canvas): canvas object
            canvas_top (canvas): canvas top class object
            prereq_scripts (list): prerequisite scripts to be called before
                                    executing this step.
            index (int): Order of the scripts to run.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.call_back = call_back
        self.canvas = canvas
        self.output = output
        self.canv_top = canvas_top
        self.prereq_scripts = prereq_scripts
        self.index = index
        self.exec_status = False
        self.canvas.on_client_ready(self.layout)
        self.working_dir = working_dir

    def layout(self):
        """Layouting the script button."""
        # self.canvas[1].stroke_style = '#e40222'
        # self.canvas[1].line_width = 3
        # self.canvas[1].line_join = 'round'
        # self.canvas[1].shadow_color = 'black'
        # self.canvas[1].shadow_offset_x = 1
        # self.canvas[1].shadow_offset_y = 1
        # self.canvas[1].shadow_blur = 1
        # self.canvas[1].stroke_rect(
        #     self.x, self.y, self.width, self.height)
        # self.canvas[1].font = '12px serif'
        # self.canvas[1].text_align = 'start'
        # self.canvas[1].text_baseline = 'top'
        # self.canvas[1].fill_style = '#e40222'
        # index_x = self.x+(self.width/2)-10
        # self.canvas[1].fill_text(
        #     self.index, index_x, self.y+5)
        # curr_path = os.path.abspath(os.path.dirname(__file__))
        # self.canvas[1].draw_image(
        #     Image.from_file(os.path.join(curr_path, 'click_icon.png')),
        #     index_x+10, self.y+2, 25, 25)
        # self.canvas[1].shadow_offset_x = 0
        # self.canvas[1].shadow_offset_y = 0
        # self.canvas[1].shadow_blur = 0
        pass

    def is_selected(self, x_in, y_in):
        """Checks if the script button is clicked.

        Args:
            x_in (int): x coordinate w.r.t mouse click event is returned.
            y_in (int): y coordinate w.r.t mouse click event is returned.

        Returns:
            bool: True if the script button is clicked, else False.
        """
        return ((x_in > self.x) and (x_in < (self.x + self.width))) and (
            (y_in > self.y) and (y_in < (self.y + self.height))
        )

    def prGreen(self, m):
        """Changes the print statement color to green.

        Args:
            m (str): Statement to apply the change.
        """
        print("\033[1;32;47m{}\033[00m".format(m))

    def prRed(self, m):
        """Changes the print statement color to red.

        Args:
            m (str): Statement to apply the change.
        """
        print("\033[1;31;47m{}\033[00m".format(m))

    def render(self):
        """When any script button is clicked,
        render method is invoked to call corresponding function.
        """
        with self.output.log:
            self.popup = Popup("Step {} Execution Status".format(str(self.index)), self.canvas[3])
            self.errorpopup = ErrorPopUp(self.popup)
            script_list = [
                btn for btn in self.canv_top.click_list if ((hasattr(btn, "exec_status")))
            ]
            depend_list = [btn for btn in script_list if (self in btn.prereq_scripts)]
            try:
                is_allowed = all([temp.exec_status for temp in self.prereq_scripts])
                if is_allowed:
                    self.step_status_clear(self)
                    curr_dir = os.getcwd()
                    os.chdir(self.working_dir)
                    self.call_back(b=None)
                    os.chdir(curr_dir)
                    self.exec_status = True
                    # self.popup.print_message(
                    #     'Step Completed, Proceed to next step')
                    self.step_status_complete(self)
                    for script in depend_list:
                        self.clear_execution(script)
                    all_exec_status = [
                        tot.exec_status for tot in script_list if (tot.exec_status is False)
                    ]
                    if not all_exec_status:
                        self.prGreen("Usecase Execution is Completed\n")
                        # self.popup.usecase_complete('done_icon.png')
                else:
                    str_val = f"Step{self.index} can't be executed before "
                    for script in self.prereq_scripts:
                        if not script.exec_status:
                            str_val += "Step" + str(script.index) + "\n"
                    self.errorpopup.traceback_print(str_val, footer=False)
            except Exception:
                self.prRed("\nError while executing Step-{}".format(str(self.index)))
                # traceback.print_exc()
                tb_text = "".join(traceback.format_exc())

                lexer = lexers.get_lexer_by_name("pytb", stripall=True)
                formatter = formatters.get_formatter_by_name("terminal256")
                tb_colored = highlight(tb_text, lexer, formatter)

                print(tb_colored)
                exc_type, exc_value, exc_tb = sys.exc_info()
                tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
                self.errorpopup.traceback_print("".join(tb.format_exception_only()))
                for script in depend_list:
                    self.clear_execution(script)
        os.chdir(curr_dir)

    def step_status_complete(self, current_script):
        """Changes the execution state of the script object after execution.

        Args:
            current_script (object): Script button object.
        """
        self.prGreen("Executed Step-{} ".format(str(current_script.index)) + "Successfully\n")
        curr_path = os.path.abspath(os.path.dirname(__file__))
        px = current_script.x + 5
        py = current_script.y
        self.canvas[2].draw_image(
            Image.from_file(os.path.join(curr_path, "done_icon.png")), px, py, 30, 30
        )
        # self.canvas[2].stroke_style = '#4BB543'
        # self.canvas[2].line_width = 3
        # self.canvas[2].stroke_rect(
        #     current_script.x, current_script.y,
        #     current_script.width, current_script.height)

    def step_status_clear(self, current_script):
        """Clears the layout of the script button to default.

        Args:
            current_script (object): Script button object.
        """
        self.canvas[2].clear_rect(
            current_script.x - 2,
            current_script.y - 2,
            current_script.width + 4,
            current_script.height + 4,
        )

    def clear_execution(self, current_script):
        """Clears the execution state to default when Reset button is clicked.

        Args:
            current_script (object): Script button object.
        """
        px = current_script.x + current_script.width - 30
        py = current_script.y + 5
        self.canvas[2].clear_rect(px, py, 25, 25)
        self.canvas[2].clear_rect(
            current_script.x - 2,
            current_script.y - 2,
            current_script.width + 4,
            current_script.height + 4,
        )
        current_script.exec_status = False
        script_list = [
            btn
            for btn in self.canv_top.click_list
            if ((hasattr(btn, "exec_status") and (current_script in btn.prereq_scripts)))
        ]
        for script in script_list:
            self.clear_execution(script)


class CanvasFirmware:
    """Adds a script button on the canvas."""

    def __init__(
        self, x, y, canvas, canvas_top, cb_project_path, mplab_ide_path=None, working_dir=None
    ):
        """Constructs required attributes.

        Args:
            x (int): x coordinate w.r.t canvas to place the script button.
            y (int): y coordinate w.r.t canvas to place the script button.
            canvas (canvas): canvas object
            canvas_top (canvas): canvas top class object
            cb_project_path(call_back): call back to get active board project
                                            path
        """
        self.x = x
        self.y = y
        self.width = 100
        self.height = 100
        self.canvas = canvas
        self.cancas_top = canvas_top
        self.cb_project_path = cb_project_path
        self.mplab_ide_path = mplab_ide_path
        self.working_dir = working_dir
        self.canvas.on_client_ready(self.layout)

    def layout(self):
        """Layouting the script button."""
        # curr_path = os.path.abspath(os.path.dirname(__file__))
        # self.canvas[1].draw_image(
        #     Image.from_file(os.path.join(curr_path, 'mplab.png')),
        #     self.x, self.y, self.width, self.height)
        self.canvas[1].shadow_offset_x = 0
        self.canvas[1].shadow_offset_y = 0
        self.canvas[1].shadow_blur = 0

    def is_selected(self, x_in, y_in):
        """Checks if the script button is clicked.

        Args:
            x_in (int): x coordinate w.r.t mouse click event is returned.
            y_in (int): y coordinate w.r.t mouse click event is returned.

        Returns:
            bool: True if the script button is clicked, else False.
        """
        return ((x_in > self.x) and (x_in < (self.x + self.width))) and (
            (y_in > self.y) and (y_in < (self.y + self.height))
        )

    def render(self):
        """When any script button is clicked,
        render method is invoked to call corresponding function.
        """
        self.popup = Popup("Opening MPLABX", self.canvas[3])
        self.epopup = ErrorPopUp(self.popup)
        self.popup.canvas_layer.font = "28px serif"
        self.popup.canvas_layer.text_align = "start"
        self.popup.canvas_layer.text_baseline = "top"
        self.popup.canvas_layer.fill_style = "black"

        try:
            assert (
                self.mplab_ide_path is not None
            ), "MPLAB X IDE path is not set in File -> Preferences -> MPLABX Path. \
                    \nSet the path before clicking on MPLAB X Project"
            assert (
                self.cb_project_path() is not None
            ), "Project Path is not available... Set Path in the Usecase"
            assert (
                self.working_dir is not None
            ), "Working dir is not set... Set directory in the Usecase"

            self.popup.get_layout(flag=True)
            self.popup.canvas_layer.fill_style = "black"
            self.popup.canvas_layer.fill_text(
                "Opening firmware... ensure all Usecase steps are",
                self.popup.startx + 20,
                self.popup.starty + 20 + 35,
            )
            self.popup.canvas_layer.fill_text(
                "executed at least once prior to loading firmware!",
                self.popup.startx + 20,
                self.popup.starty + 20 + 35 + 40,
            )
            project_path = self.handle_working_dir_copy()
            subprocess.Popen(
                [
                    self.mplab_ide_path,
                    "--open",
                    project_path,
                ]
            )
        except AssertionError as msg:
            self.epopup.traceback_print(str(msg), footer=False)

    def open_source_render(self):
        self.popup = Popup("Caution", self.canvas[3])
        self.popup.get_layout(flag=False)
        self.popup.canvas_layer.font = "28px serif"
        self.popup.canvas_layer.text_align = "start"
        self.popup.canvas_layer.text_baseline = "top"
        self.popup.canvas_layer.fill_style = "black"
        self.popup.canvas_layer.fill_text(
            "Project Path is not available... Check Usecase settings",
            self.popup.startx + 20,
            self.popup.starty + 20 + 35,
        )

    def handle_working_dir_copy(self, do_overwrite=False):
        if self.cb_project_path():
            do_copy = True
            working_dir = os.path.join(self.working_dir, "firmware")
            if os.path.exists(working_dir):
                do_copy = False

            if do_copy or do_overwrite:
                original_dir = self.cb_project_path().split("firmware")[0] + "firmware"
                if os.path.exists(original_dir):
                    if os.path.exists(working_dir):
                        shutil.rmtree(working_dir)
                    shutil.copytree(original_dir, working_dir, dirs_exist_ok=True)
                elif os.path.exists(original_dir + ".zip"):
                    shutil.unpack_archive(original_dir + ".zip", working_dir)

                # Copy resources
                original_dir = os.path.dirname(original_dir)
                exclude_extn = [".ipynb"]
                if do_overwrite is False and any(
                    File.endswith(".h") for File in os.listdir(os.path.dirname(working_dir))
                ):
                    exclude_extn += [".h", ".c"]
                files = [
                    x
                    for x in os.listdir(original_dir)
                    if Path(os.path.join(original_dir, x)).is_file()
                ]
                files = [x for x in files if not x.endswith(tuple(exclude_extn))]
                for fname in files:
                    shutil.copy(
                        os.path.join(original_dir, fname),
                        os.path.join(os.path.dirname(working_dir), fname),
                    )

            return os.path.join(
                os.path.dirname(working_dir),
                "firmware" + "firmware".join(self.cb_project_path().split("firmware")[1:]),
            )

    def get_c_src_folder(self):
        try:
            assert (
                self.cb_project_path() is not None
            ), "This Usecase doesn't have firmware project..."
            c_src_folder = None
            project_path = self.handle_working_dir_copy()
            c_src_folder, _ = os.path.split(project_path)
            return os.path.join(c_src_folder, "src")
        except BaseException as exp:
            self.popup = Popup("Opening C Source Folder", self.canvas[3])
            self.epopup = ErrorPopUp(self.popup)
            self.popup.canvas_layer.font = "28px serif"
            self.popup.canvas_layer.text_align = "start"
            self.popup.canvas_layer.text_baseline = "top"
            self.popup.canvas_layer.fill_style = "black"
            self.epopup.traceback_print(str(exp), footer=False)


class ErrorPopUp:
    def __init__(self, popup):
        self.popup = popup
        self.val = None

    def traceback_print(self, s, footer=True):
        """Redirects the traceback error message onto the popup window."""
        self.val = s
        self.popup.canvas_layer.clear()
        self.popup.get_layout(flag=False)
        if footer:
            self.popup.get_footer(flag=False)
        self.popup.canvas_layer.font = "20px serif"
        self.popup.canvas_layer.text_align = "start"
        self.popup.canvas_layer.text_baseline = "top"
        self.popup.canvas_layer.fill_style = "black"
        for i, si in enumerate(self.val.split("\n")):
            if i < 20:
                self.popup.canvas_layer.fill_text(
                    si[0:90], self.popup.startx + 20, self.popup.starty + 20 + 35 + 20 * i
                )


__all__ = ["CanvasTop", "CanvasLink", "CanvasImage", "CanvasScript", "CanvasFirmware", "ErrorPopUp"]

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
