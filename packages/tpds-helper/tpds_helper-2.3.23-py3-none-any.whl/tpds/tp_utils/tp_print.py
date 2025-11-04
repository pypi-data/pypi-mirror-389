# -*- coding: utf-8 -*-
# 2018 to present - Copyright Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR
# PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT, SPECIAL,
# PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE OF ANY
# KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP
# HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE FORESEEABLE. TO THE
# FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN
# ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
# THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.

import builtins
import io


def print(*args, **kwargs):
    """A method that redirects the statements either onto terminal
    or onto the canvas based on the arguments provided.

    If an attribute called canvas is passed to this function,
    prints to terminal and also to the canvas.

    Else prints only onto the terminal.
    """
    canvas = kwargs.get("canvas", None)
    if "canvas" in kwargs:
        kwargs.pop("canvas")
    if canvas:
        output = io.StringIO()
        if kwargs.get("end") is not None:
            builtins.print(*args, file=output, **kwargs)
        else:
            builtins.print(*args, file=output, **kwargs, end="")
        contents = output.getvalue()
        output.close()
        canvas.print_message(contents)
    builtins.print(*args, **kwargs)


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
