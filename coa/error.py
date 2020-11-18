# -*- coding: utf-8 -*-
""" Project : CoCoA
Date :    april-november 2020
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright © CoCoa-team-17
License: See joint LICENSE file

Module : pycoa.error
About : 

Main class definitions for error management within the pycoa framework.
All Cocoa exceptions should derive from the main CocoaError class.
"""

class CocoaError(Exception):
    """Base class for exceptions in CoCoa."""
    def __init__(self, message):
        self.message = message
        Exception(message)

class CocoaKeyError(CocoaError, KeyError):
    """Exception raised for errors in used key option.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        KeyError(message)
        CocoaError(message)
        
class CocoaWhereError(CocoaError, IndexError):
    """Exception raised for location errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        IndexError(message)
        CocoaError(message)
        
class CocoaTypeError(CocoaError, TypeError):
    """Exception raised for type mismatch errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        TypeError(message)
        CocoaError(message)
        
class CocoaLookupError(CocoaError, LookupError):
    """Exception raised for type lookup errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        LookupError(message)
        CocoaError(message)
        
class CocoaNotManagedError(CocoaError):
    """Exception raised when the error is unknown and not managed.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        CocoaError(message)
    

class CocoaDbError(CocoaError):
    """Exception raised for database errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        CocoaError(message)
    
class CocoaConnectionError(CocoaError,ConnectionError):
    """Exception raised for connection errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        ConnectionError(message)
        CocoaError(message)
        
