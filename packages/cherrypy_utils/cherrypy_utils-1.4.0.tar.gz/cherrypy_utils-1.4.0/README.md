# Overview

This is a generic utility library full of helper functions relating to cherrypy webservice routines.
Included are handlers for:

- authentication (authentication.py)
- sqlalchemy with cherrypy (cherrypy_sqlalchemy_utils.py & database.py)
- json parsing and constructing orm entities from json (json_utils.py)
- timestamp (ISO and posix epoch) parsing (timestamp.py)
- url construction and parsing from parts (similar to os.path.join) (url_utils.py)
- ldap login utilities (login/ldap_auth.py & login/models.py)

## Usage

To use this package in your project, simply install it with `pip install cherrypy_utils`

## Development

This package is developed using Pipenv for package management, which makes dealing with pip packages easier.
Check out more here: https://pipenv.pypa.io/en/latest/install/#using-installed-packages

It also uses pyenv to manage multiple different installed versions of python.
Currently, this package targets python 3.6.8.

The package uses the black formatter and enforces a strict formatting policy, automatic formatting on save is required.
