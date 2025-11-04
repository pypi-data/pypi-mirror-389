from ipywidgets import HBox, Layout, VBox, widgets


class Terminal:
    """For the detailed output from scripts,
    Terminal is created beside the Transaction Digram.
    """

    def __init__(self):
        """Constructs necessary attributes"""
        self.clear = widgets.Button(
            description="Clear Output",
            tooltip="clear log output",
            style={"button_color": "skyblue"},
            width="50%",
        )
        self.clear.on_click(self.on_clear_click)

        self.terminal = widgets.Button(
            description="Hide Terminal",
            style={"button_color": "skyblue"},
            width="50%",
            icon="fa-eye-slash",
        )
        self.terminal.on_click(self.on_terminal_click)

        self.log = widgets.Output(
            layout=widgets.Layout(
                width="320px", height="480px", overflow="hidden scroll", border="2px solid black"
            )
        )

        self.inner_box_layout = Layout(
            display="flex", flex_flow="column", align_items="stretch", width="100%"
        )
        self.outer_box_layout = Layout(
            display="flex",
            flex_flow="column",
            align_items="stretch",
            width="96%",
            margin="0px 0px 0px 10px",
        )

    def on_clear_click(self, b):
        """Clear the terminal output when clear button is clicked.

        Args:
            b (ipywidgets button object): button associated to this function.
        """
        self.log.clear_output()

    def on_terminal_click(self, b):
        """Show/ Hide the terminal window.

        Args:
            b (ipywidgets button object): button associated to this function.
        """
        if self.inner_box_layout.width == "0%":
            self.inner_box_layout.width = "100%"
            self.log.layout.border = "2px solid black"
            self.terminal.description = "Hide Terminal"
            self.terminal.icon = "fa-eye-slash"
        else:
            self.inner_box_layout.width = "0%"
            self.log.layout.border = "0px"
            self.terminal.description = "Show Terminal"
            self.terminal.icon = "fa-eye"

    def get_layout(self):
        """Layout of the terminal

        Returns:
            Box Layout: Return the layout of the terminal
        """
        return VBox(
            [
                HBox([self.clear], layout=Layout(display="flex", justify_content="flex-end")),
                self.log,
            ],
            layout=Layout(margin="0px 0px 0px 10px"),
        )


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
