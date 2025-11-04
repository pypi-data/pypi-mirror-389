import warnings
import json
import urllib.request

from IPython.display import HTML, display
from ipywidgets import Box, Layout, VBox, widgets
import webbrowser
from tpds.tp_utils import Client, tp_input_dialog


class MenuIcons:
    """Adds RESET and HELP buttons to the Usecase Diagram"""

    def __init__(self, canv_top, canvas, canvas_setup):
        """Constructs required attributes.

        Args:
            canv_top (object): Canvas_top object which includes list of buttons.
            canvas (object): Main canvas object
        """
        self.canv_top = canv_top
        self.canvas = canvas
        self.canvas_setup = canvas_setup
        self.help = widgets.Button(
            description="Usecase Help",
            tooltip="Open Usecase Help",
            style={"button_color": "skyblue"},
            icon="fa-question-circle",
        )
        self.usecase_help = None
        self.video_link = "https://www.youtube.com/embed/ocSoVkBMwfY"
        self.youku_link = None
        self.help.on_click(self.on_help_click)

        self.reset = widgets.Button(
            description="Reset",
            tooltip="Reset Transaction Diagram",
            style={"button_color": "skyblue"},
            icon="fa-refresh",
        )
        self.reset.on_click(self.on_reset_click)

        self.learn = widgets.Button(
            description="Learn",
            tooltip="Play Usecase video",
            style={"button_color": "skyblue"},
            icon="fa-info-circle",
        )
        self.learn.on_click(self.on_learn_click)

        self.firmware_obj = None
        self.c_project = widgets.Button(
            description="MPLAB X Project",
            tooltip="Launch MPLAB X IDE Project",
            style={"button_color": "skyblue"},
            icon="fa-hand-o-right",
        )
        self.c_project.on_click(self.on_c_project_click)

        self.c_proj_folder = widgets.Button(
            description="C Source Folder",
            tooltip="Explore C Source files",
            style={"button_color": "skyblue"},
            icon="fa-folder-open-o",
        )
        self.c_proj_folder.on_click(self.on_c_proj_folder_click)

        self.inner_box_layout = widgets.Layout(
            display="flex", flex_flow="row-reverse", overflow="hidden"
        )
        self.outer_box_layout = widgets.Layout(
            display="flex", flex_flow="row-reverse", overflow="hidden", width="100%", height="35px"
        )

        self.info_out = widgets.Output(
            layout=Layout(height="0px", overflow="hidden", margin="0px 0px 0px 50px")
        )
        self.t_out = widgets.Output(layout=Layout(height="100%", overflow="hidden", margin="0px"))
        self.box1 = widgets.HBox(
            children=[self.c_proj_folder, self.c_project, self.help, self.learn, self.reset],
            layout=self.inner_box_layout,
        )
        self.box2 = widgets.HBox(children=[self.box1], layout=self.outer_box_layout)

    def on_help_click(self, b):
        """Invoked when help button is clicked.

        Args:
            b (object): Corresponding ipywidget button object.
        """
        # if self.help.description != 'Close':
        #     self.__reset_menu_layout()
        #     self.help.icon = 'fa-times-circle'
        #     self.help.style.button_color = '#FF605C'
        #     self.help.description = 'Close'
        #     self.t_out.layout.height = '0px'
        #     self.info_out.layout.height = '100%'
        #     with self.info_out:
        #         display(HTML(
        #                 """<iframe width="100%" height="650"
        #                 src="https://www.youtube.com/embed/Oxmhqt5lc2Y?autoplay=1"
        #                 allow="autoplay; encrypted-media" frameborder="1">
        #                 </iframe>"""))
        # else:
        #     self.__reset_menu_layout()
        if self.usecase_help:
            self.client = Client(None)
            if callable(self.usecase_help) and self.usecase_help():
                self.open_usecase_help(self.usecase_help())
            else:
                self.open_usecase_help(self.usecase_help)
            self.client.client.recv()
            self.client.client.close()

    def open_usecase_help(self, path):
        self.client.send_message("open_link", [path])

    def set_usecase_help(self, usecase_help):
        self.usecase_help = usecase_help

    def set_usecase_video(self, yt_link, youku_link):
        if yt_link:
            self.video_link = yt_link
        if youku_link:
            self.youku_link = youku_link

    def on_learn_click(self, b):
        """Invoked when help button is clicked.

        Args:
            b (object): Corresponding ipywidget button object.
        """
        if self.learn.description != "Close":
            self.__reset_menu_layout()
            self.learn.icon = "fa-info-circle"
            self.learn.style.button_color = "#FF605C"
            self.learn.description = "Close"
            self.t_out.layout.height = "0px"
            self.info_out.layout.height = "100%"
            data = json.load(urllib.request.urlopen('http://ipinfo.io/json'))
            if self.youku_link and data.get('country', "") == "CN":
                webbrowser.open(self.youku_link)
                self.__reset_menu_layout()
            else:
                with warnings.catch_warnings():
                    # this will suppress all warnings in this block
                    warnings.filterwarnings(
                        "ignore", message="Consider using IPython.display.IFrame instead"
                    )
                    with self.info_out:
                        display(
                            HTML(
                                f"""<iframe width="100%" height="650"
                                src="{self.video_link}"
                                allow="autoplay; encrypted-media" frameborder="1">
                                </iframe>"""
                            )
                        )
        else:
            self.__reset_menu_layout()

    def __reset_menu_layout(self):
        self.help.icon = "fa-question-circle"
        self.help.style.button_color = "skyblue"
        self.help.description = "Usecase Help"
        self.learn.icon = "fa-info-circle"
        self.learn.style.button_color = "skyblue"
        self.learn.description = "Learn"
        self.info_out.clear_output()
        self.info_out.layout.height = "0%"
        self.t_out.layout.height = "100%"

    def on_c_project_click(self, b):
        if self.firmware_obj:
            self.firmware_obj.render()

    def on_c_proj_folder_click(self, b):
        if self.firmware_obj:
            path = self.firmware_obj.get_c_src_folder()
            assert path is not None, "No Source folder available to open"
            c_project_files = tp_input_dialog.OpenExplorerFolder(path=path)
            c_project_files.invoke_dialog()
        else:
            self.firmware_obj.open_source_render()

    def set_firmware_obj(self, firmware_obj):
        self.firmware_obj = firmware_obj

    def on_reset_click(self, b):
        """Invoked when Reset button is clicked.

        Clears the scripts execution status ti default.
        This reverts the usecase diagram to default.

        Args:
            b (object): corresponding ipywidgets button object.
        """
        self.canv_top.t_canvas[2].clear()
        script_list = [btn for btn in self.canv_top.click_list if ((hasattr(btn, "exec_status")))]
        for script in script_list:
            script.exec_status = False
        self.info_out.layout.height = "0px"
        self.info_out.clear_output()
        self.t_out.layout.height = "100%"
        self.help.icon = "fa-question-circle"
        self.help.style.button_color = "skyblue"
        self.help.description = "Usecase Help"
        self.learn.icon = "fa-info-circle"
        self.learn.style.button_color = "skyblue"
        self.learn.description = "Learn"
        if self.firmware_obj:
            self.firmware_obj.handle_working_dir_copy(True)

    def return_layout(self):
        """Returns Layout along with Reset and Help buttons.

        Returns:
            Box Layout: Returns box layout of the buttons(reset, help)
        """
        with self.t_out:
            display(Box([self.canvas]))
        return VBox([self.box2, self.t_out, self.info_out])
        # return self.canvas


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
