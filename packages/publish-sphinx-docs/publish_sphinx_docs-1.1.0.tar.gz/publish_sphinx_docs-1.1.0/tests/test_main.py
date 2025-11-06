import click.testing
from click.testing import CliRunner

from .context import publish_sphinx_docs
from publish_sphinx_docs import *

runner = CliRunner()

def test_publish():
    # Maybe use the mock library here to mock subprocess calls
    pass