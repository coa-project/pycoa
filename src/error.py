# -*- coding: utf-8 -*-
""" Project : PyCoA
Date :    april 2020 - june 2024
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : src.error

About :
-------

Main class definitions for error management within the pycoa.framework.
All Coa exceptions should derive from the main CoaError class.
"""
class CoaWarning(Exception):
    """Base class for exceptions in PyCoa."""

    def __init__(self, message):
        #self.message = message
        message = '  ' + message + '  '
        pycoatexterror = 'PYCOA Warning ! '
        center=int((len(message)-len(pycoatexterror))/2)
        self.message = ' '*len(message)+'\n'\
        + ' '*center+pycoatexterror+' '*center+'\n'\
        + message.center(30)+'\n'+' '*len(message)
        print('\033[45m'+self.message)
        Exception(message)

class CoaError(Exception):
    """Base class for exceptions in PyCoa."""

    def __init__(self, message):
        #self.message = message
        message = '  ' + message + '  '
        pycoatexterror = 'PYCOA Error ! '
        center=int((len(message)-len(pycoatexterror))/2)
        self.message = ' '*len(message)+'\n'\
        + ' '*center+pycoatexterror+' '*center+'\n'\
        + message.center(30)+'\n'+' '*len(message)
        print('\033[1;30;41m'+self.message)
        Exception(message)


class CoaNoData(CoaError, IndexError):
    """Exception raised when there is no data to plot or to manage (invalid cut)"""

    def __init__(self, message):
        self.message = message
        IndexError(message)
        CoaError(message)


class CoaKeyError(CoaError, KeyError):
    """Exception raised for errors in used key option.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        KeyError(message)
        CoaError(message)


class CoaWhereError(CoaError, IndexError):
    """Exception raised for location errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        IndexError(message)
        CoaError(message)


class CoaTypeError(CoaError, TypeError):
    """Exception raised for type mismatch errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        TypeError(message)
        CoaError(message)


class CoaLookupError(CoaError, LookupError):
    """Exception raised for type lookup errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        LookupError(message)
        CoaError(message)


class CoaNotManagedError(CoaError):
    """Exception raised when the error is unknown and not managed.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        CoaError(message)


class CoaDbError(CoaError):
    """Exception raised for database errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        CoaError(message)


class CoaConnectionError(CoaError, ConnectionError):
    """Exception raised for connection errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        ConnectionError(message)
        CoaError(message)
