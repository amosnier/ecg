"""This is a template file

Adapt it to your own needs or create a symlink to it if you can use it
as is. It provides what YouCompleteMe needs to handle the virtual
environment used for this project (if applicable).

"""

from pathlib import Path

def Settings(**kwargs):
    return {
        'interpreter_path': '{}{}'.format(str(Path.home()), '/.virtualenvs/ecg/bin/python')
    }
