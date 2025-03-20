# -*- coding: utf-8 -*-
""" 
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.error

About :
-------

Main class definitions for error management within the PYVOA.framework.
All Pyvoa exceptions should derive from the main PyvoaError class.
"""
import os
import sys
import time
from time import sleep
from IPython import get_ipython

def blinking_centered_text(typemsg,message,blinking=0,text_color="37", bg_color="41"):
    """
    center blinking color output message
    """
    color_codes = {
        'black': '30',
        'red': '31',
        'green': '32',
        'yellow': '33',
        'blue': '34',
        'magenta': '35',
        'cyan': '36',
        'white': '37',
        'default': '39',
    }

    bg_codes = {name: str(int(code) + 10) for name, code in color_codes.items()}
    text_code = color_codes.get(text_color.lower(), color_codes["white"])
    bg_code = bg_codes.get(bg_color.lower(), bg_codes["red"])

    if blinking:
        ansi_start = f"\033[5;{text_code};{bg_code}m"
    else:
        ansi_start = f"\033[;{text_code};{bg_code}m"
    ansi_reset = "\033[0m"

    env = get_ipython().__class__.__name__
    if env != 'ZMQInteractiveShell':
        rows, columns = os.popen('stty size', 'r').read().split()
        columns = int(columns)
        typemsg = typemsg.center(columns)
        message = message.center(columns)
        sys.stdout.write(f'{ansi_start}{typemsg}{ansi_reset}\n')
        sys.stdout.write(f'{ansi_start}{message}{ansi_reset}\n')
    else:
        print(f'{ansi_start}{typemsg}{ansi_reset}\n')
        print(f'{ansi_start}{message}{ansi_reset}\n')

class PyvoaInfo(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        blinking_centered_text('PYVOA Info !',message, blinking=0,text_color='black', bg_color='blue')
        Exception(message)

class PyvoaDBInfo(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        blinking_centered_text('PYVOA Info !',message, blinking=0,text_color='white', bg_color='blue')
        Exception(message)

class PyvoaWarning(Exception):
    """Base class for exceptions in PYVOA."""

    def __init__(self, message):
        blinking_centered_text('PYVOA Warning !',message, blinking=0,text_color='black', bg_color='orange')
        Exception(message)

class PyvoaError(Exception):
    """Base class for exceptions in PYVOA."""
    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        sys.exit(0)
        #Exception(message)

class PyvoaNoData(PyvoaError, IndexError):
    """Exception raised when there is no data to plot or to manage (invalid cut)"""

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        IndexError(message)
        PyvoaError(message)

class PyvoaWhereError(PyvoaError, IndexError):
    """Exception raised for location errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        IndexError(message)
        PyvoaError(message)


class PyvoaTypeError(PyvoaError, TypeError):
    """Exception raised for type mismatch errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        TypeError(message)
        PyvoaError(message)


class PyvoaLookupError(PyvoaError, LookupError):
    """Exception raised for type lookup errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        LookupError(message)
        PyvoaError(message)


class PyvoaNotManagedError(PyvoaError):
    """Exception raised when the error is unknown and not managed.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        PyvoaError(message)


class PyvoaDbError(PyvoaError):
    """Exception raised for database errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        PyvoaError(message)


class PyvoaConnectionError(PyvoaError, ConnectionError):
    """Exception raised for connection errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        blinking_centered_text('PYVOA Error !',message, blinking=1,text_color='white', bg_color='red')
        ConnectionError(message)
        PyvoaError(message)
