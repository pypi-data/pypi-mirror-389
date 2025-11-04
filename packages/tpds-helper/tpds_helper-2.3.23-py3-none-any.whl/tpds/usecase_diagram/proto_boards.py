import os

from ipycanvas import MultiCanvas
from ipywidgets import Image


class ProtoBoard:
    def __init__(self, img_size=200, max_width=1200):
        """This class handles proto boards addition to Usecase Notebook

        Args:
            img_size (int, optional):
                    [Board image dimension]. Defaults to 200.
            max_width (int, optional):
                    [Max width of the canvas while rendering images].
                    Defaults to 1200.
        """
        self.boards = []
        self.img_size = img_size
        self.max_width = max_width
        self.active_board = None
        curr_path = os.path.abspath(os.path.dirname(__file__))
        self.select_img = Image.from_file(os.path.join(curr_path, "select.png"))

    def add_board(
        self, board_name, board_img, board_kit_hex, board_firmware=None, board_help_docs=None
    ):
        """This method adds a board to list of the boards to render

        Args:
            board_name ([type]): Title of the board
            board_img ([type]): Board image path
            board_kit_hex ([type]): Factory program hex path
            board_firmware ([type], optional):
                        C project (MPLAB) path. Defaults to None.
            board_help_docs ([type], optional): help document path
        """
        board_info = {}
        board_info.update({"name": board_name})
        board_info.update({"img": Image.from_file(board_img)})
        board_info.update({"kit_hex": board_kit_hex})
        board_info.update({"firmware": board_firmware})
        board_info.update({"help_docs": board_help_docs})
        self.boards.append(board_info)

    def render_boards(self, default_selection=None):
        """This method renders the boards on the canvas, It creates
        layers to draw images, text and user clicks
        """
        width = height = 0
        for board in self.boards:
            board.update({"x": width})
            board.update({"y": height})
            width += self.img_size
            if width >= self.max_width:
                width = 0
                height += self.img_size

        if width:
            height += self.img_size
        if len(self.boards) >= (self.max_width / self.img_size):
            width = self.max_width

        self.canvas = MultiCanvas(3, width=width, height=height)
        self.canvas.layout.margin = "50px"
        self.image_canvas = self.canvas[0]
        self.text_canvas = self.canvas[1]
        self.click_canvas = self.canvas[2]
        self.image_canvas.on_client_ready(self.draw_boards)
        self.click_canvas.on_mouse_down(self.handle_mouse_down)
        self.default_selection = default_selection

    def handle_mouse_down(self, x, y):
        """This callback method handles the Click action from User.
                On selecting a valid board, it renders as selected.

        Args:
            x ([type]): x coordinate of the click
            y ([type]): y coordinate of the click
        """
        image_index = int(
            ((int(y / self.img_size)) * (self.max_width / self.img_size)) + (int(x / self.img_size))
        )
        if image_index >= len(self.boards):
            return
        if self.active_board and (image_index == self.boards.index(self.active_board)):
            # Clear the current selection
            self.image_canvas.fill_style = "white"
            self.image_canvas.fill_rect(
                self.active_board.get("x") + 5, self.active_board.get("y") + 170, 50, 50
            )
            self.active_board = None
        else:
            self.__select_board(image_index)

    def draw_boards(self):
        """This method draws the board images and texts"""
        for board in self.boards:
            self.image_canvas.draw_image(board.get("img"), board.get("x"), board.get("y"))
            self.text_canvas.stroke_style = "red"
            self.text_canvas.stroke_rect(
                board.get("x"), board.get("y"), self.img_size, self.img_size
            )
            self.text_canvas.font = "16px serif"
            self.text_canvas.fill_text(board.get("name"), board.get("x") + 1, board.get("y") + 20)
        # 0 is valid selection
        if self.default_selection is not None:
            self.__select_board(self.default_selection)

    def __select_board(self, index):
        if index >= len(self.boards):
            return
        if self.active_board:
            # Clear the current selection
            self.image_canvas.fill_style = "white"
            self.image_canvas.fill_rect(
                self.active_board.get("x") + 5, self.active_board.get("y") + 170, 50, 50
            )

        # Set the new selection and draw the new selection
        self.active_board = self.boards[index]
        self.image_canvas.draw_image(
            self.select_img, self.active_board.get("x") + 5, self.active_board.get("y") + 170
        )

    def get_firmware_project(self):
        """Access method to get C project path

        Returns:
            [str]: Project path
        """
        project_path = None
        if self.active_board is not None:
            project_path = self.active_board.get("firmware")
        return project_path

    def get_kit_hex(self):
        """Access method to get factory hex file

        Returns:
            [str]: Factory hex file path
        """
        hex_path = None
        if self.active_board is not None:
            hex_path = self.active_board.get("kit_hex")
        return hex_path

    def get_selected_board(self):
        """Access method to get selected board

        Returns:
            dict/None: Dictionary of selected board details
        """
        return self.active_board

    def get_help_docs(self):
        """Access method to get help document file

        Returns:
            [str]: help document file path
        """
        if self.active_board is not None:
            return self.active_board.get("help_docs")

        return self.boards[0].get("help_docs")
