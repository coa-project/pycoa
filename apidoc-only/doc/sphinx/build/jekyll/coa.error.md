---
date: '2021-12-09T15:56:56.735Z'
docname: coa.error
images: {}
path: /coa-error
title: coa.error module
---

# coa.error module

Project : PyCoA
Date :    april 2020 - march 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.error

## About :

Main class definitions for error management within the pycoa framework.
All Coa exceptions should derive from the main CoaError class.

## Summary

Exceptions:

| `CoaConnectionError`

 | Exception raised for connection errors.

 |
| `CoaDbError`

         | Exception raised for database errors.

                                                                                                                                                                         |
| `CoaError`

           | Base class for exceptions in PyCoa.

                                                                                                                                                                           |
| `CoaKeyError`

        | Exception raised for errors in used key option.

                                                                                                                                                               |
| `CoaLookupError`

     | Exception raised for type lookup errors.

                                                                                                                                                                      |
| `CoaNoData`

          | Exception raised when there is no data to plot or to manage (invalid cut)

                                                                                                                                     |
| `CoaNotManagedError`

 | Exception raised when the error is unknown and not managed.

                                                                                                                                                   |
| `CoaTypeError`

       | Exception raised for type mismatch errors.

                                                                                                                                                                    |
| `CoaWhereError`

      | Exception raised for location errors.

                                                                                                                                                                         |
## Reference


### exception CoaConnectionError(message)
Bases: `coa.error.CoaError`, `ConnectionError`

Exception raised for connection errors.

Attributes:

    message – explanation of the error


### exception CoaDbError(message)
Bases: `coa.error.CoaError`

Exception raised for database errors.

Attributes:

    message – explanation of the error


### exception CoaError(message)
Bases: `Exception`

Base class for exceptions in PyCoa.


### exception CoaKeyError(message)
Bases: `coa.error.CoaError`, `KeyError`

Exception raised for errors in used key option.

Attributes:

    message – explanation of the error


### exception CoaLookupError(message)
Bases: `coa.error.CoaError`, `LookupError`

Exception raised for type lookup errors.

Attributes:

    message – explanation of the error


### exception CoaNoData(message)
Bases: `coa.error.CoaError`, `IndexError`

Exception raised when there is no data to plot or to manage (invalid cut)


### exception CoaNotManagedError(message)
Bases: `coa.error.CoaError`

Exception raised when the error is unknown and not managed.

Attributes:

    message – explanation of the error


### exception CoaTypeError(message)
Bases: `coa.error.CoaError`, `TypeError`

Exception raised for type mismatch errors.

Attributes:

    message – explanation of the error


### exception CoaWhereError(message)
Bases: `coa.error.CoaError`, `IndexError`

Exception raised for location errors.

Attributes:

    message – explanation of the error
