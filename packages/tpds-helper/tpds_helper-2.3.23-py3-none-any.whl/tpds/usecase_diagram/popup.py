import os

from ipywidgets import Image


class CloseWindow:
    """Adds a close button to the popup window."""

    def __init__(self, canvas_layer):
        """Constructs necessary attributes.

        Args:
            canvas_layer (main canvas layer): Layer to show close button.
                                                Same as popup window layer.
        """
        self.canvas = canvas_layer
        self.x = 955
        self.y = 15
        self.width = 35
        self.height = 25

    def is_selected(self, x_in, y_in):
        """Checks if close button is clicked.

        Args:
            x_in (int): x coordinate w.r.t mouse click event is returned.
            y_in (int): y coordinate w.r.t mouse click event is returned.

        Returns:
            bool: True if the close button is clicked, else False.
        """
        return ((x_in > self.x) and (x_in < (self.x + self.width))) and (
            (y_in > self.y) and (y_in < (self.y + self.height))
        )

    def layout(self):
        """Draws a close button on canvas popup window."""
        self.canvas.fill_style = "white"
        self.canvas.fill_rect(self.x, self.y, self.width, self.height)
        self.canvas.stroke_style = "black"
        self.canvas.line_width = 2
        self.canvas.begin_path()
        self.canvas.move_to(self.x + 5, self.y + 5)
        self.canvas.line_to(self.x + self.width - 5, self.y + self.height - 5)
        self.canvas.move_to(self.x + self.width - 5, self.y + 5)
        self.canvas.line_to(self.x + 5, self.y + self.height - 5)
        self.canvas.stroke()

    def render(self):
        """Clears the layer when close button is clicked."""
        self.canvas.clear()


class Popup:
    """Opens a Popup window when image button or script button is clicked.

    The Output is shown on the Popup Window.
    """

    def __init__(self, title, canvas_layer):
        """Constructs necessary attributes

        Args:
            title (str): Title to the Popup window
            canvas_layer (main canvas layer): Layer to get Popup window.
        """
        self.title = title
        self.canvas_layer = canvas_layer
        self.startx = 100
        self.starty = 10
        self.endx = 900
        self.endy = 445
        self.text_list = []
        self.close = CloseWindow(self.canvas_layer)

    def get_layout(self, flag=True):
        """Gets the main layout when the buttons are clicked.

        Args:
            flag (bool, optional): False if there is an error while executing the clicked step.
                                    (e.g. When scripts are not being run in order)
                                    Defaults to True.
        """
        self.canvas_layer.fill_style = "#FFFFFFCC"
        self.canvas_layer.fill_rect(0, 0, self.canvas_layer.width, self.canvas_layer.height)
        if flag:
            self.canvas_layer.fill_style = "#4BB543"
        else:
            self.canvas_layer.fill_style = "#e40222"
        self.canvas_layer.fill_rect(self.startx, self.starty, self.endx, self.endy)
        self.canvas_layer.fill_style = "white"
        self.canvas_layer.fill_rect(
            self.startx + 10, self.starty + 35, self.endx - (2 * 10), self.endy - (2 * 10) - 35
        )
        self.canvas_layer.font = "32px serif"
        self.canvas_layer.text_align = "start"
        self.canvas_layer.text_baseline = "top"
        self.canvas_layer.fill_text(self.title, self.startx + 10, self.starty)
        self.close.layout()

    def get_footer(self, flag=True):
        """Adds a footer part to the main layout if necessary

        Args:
            flag (bool, optional): False: Image Output doesn't need any footer.
                                            Scripts point to terminal. So footer is needed.
                                            Defaults to True.
        """
        if flag:
            self.canvas_layer.fill_style = "#4BB543"
        else:
            self.canvas_layer.fill_style = "#e40222"
        self.canvas_layer.fill_rect(self.startx, self.starty + self.endy, self.endx, 20)
        self.canvas_layer.font = "24px serif"
        self.canvas_layer.text_baseline = "top"
        self.canvas_layer.fill_style = "white"
        self.canvas_layer.fill_text(
            "Refer Terminal(on the right) for detailed log.",
            self.startx + 10,
            self.starty + self.endy - 10,
        )

    def draw_image(self, image_file):
        """When image button is clicked, image is drawn on the popup window.

        Args:
            image_file (path str): Path to the image.
        """
        self.get_layout(flag=True)
        self.canvas_layer.draw_image(
            Image.from_file(image_file),
            self.startx + 10 + 35,
            self.starty + 35,
            self.endx - (2 * 10) - (2 * 35),
            self.endy - 35 - (2 * 10),
        )

    def print_message(self, message):
        """When script button is clicked, required information is shown on popup.

        Args:
            message (str): Message to be shown on the popup.
        """
        if len(self.text_list) == 0:
            self.get_layout(flag=True)
            self.get_footer(flag=True)

        if len(self.text_list) == 10:
            self.text_list.pop(0)
        self.text_list.append(message)
        self.canvas_layer.fill_style = "white"
        self.canvas_layer.fill_rect(
            self.startx + 10, self.starty + 10 + 35, self.endx - (2 * 10), self.endy - (2 * 10) - 35
        )
        self.canvas_layer.font = "20px serif"
        self.canvas_layer.text_align = "start"
        self.canvas_layer.text_baseline = "top"
        self.canvas_layer.fill_style = "black"
        for i in range(len(self.text_list)):
            self.canvas_layer.fill_text(
                self.text_list[i][:90], self.startx + 20, self.starty + 20 + 35 + 20 * i
            )

    def usecase_complete(self, img):
        """Called after the successful execution of use case.

        Helps the user to understand that the use case is successfully run.

        Args:
            img (path str): Successful Execution Image path.
        """
        curr_path = os.path.abspath(os.path.dirname(__file__))
        self.canvas_layer.fill_style = "white"
        self.canvas_layer.fill_rect(300, 200, 500, 150)
        self.canvas_layer.stroke_style = "#4BB543"
        self.canvas_layer.line_width = 5
        self.canvas_layer.stroke_rect(300, 200, 500, 150)
        self.canvas_layer.font = "48px serif"
        self.canvas_layer.text_align = "start"
        self.canvas_layer.text_baseline = "middle"
        self.canvas_layer.fill_style = "black"
        self.canvas_layer.fill_text("Use Case Completed!!!", 320, 250)
        self.canvas_layer.draw_image(
            Image.from_file(os.path.join(curr_path, img)), 470, 280, 150, 150
        )


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
