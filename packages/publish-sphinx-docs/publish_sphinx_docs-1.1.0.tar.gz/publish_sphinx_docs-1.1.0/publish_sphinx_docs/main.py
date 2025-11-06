import os
from pathlib import Path
import subprocess as sp

import click


BUILD_DIR = "docs/_build/tmp"
GITLAB_CLI = """
image: alpine:latest

pages:
  stage: deploy
  script:
  - echo 'Nothing to do...'
  artifacts:
    paths:
    - public
  only:
  - master
"""


@click.command()
@click.option(
  '--docs-dir',
  default="docs",
  show_default=True,
  help='Name of your Sphinx documentation directory',
)
@click.option(
  '--docs-remote',
  prompt=True,
  default=lambda: os.getenv('DOCS_REMOTE', ''),
  show_default='DOCS_REMOTE environment variable',
  help='URL of your Github Pages or Gitlab Pages repository '
  'e.g. https://github.com/user/repo or git@github.com:user/repo',
)
def publish(docs_remote, docs_dir, build_dir=BUILD_DIR):
    """
    Use Sphinx, which needs to be installed in your virtual environment,
    to build your documentation as a single HTML page,
    then push the result to your Github Pages or
    Gitlab Pages repository.
    """
    # Build docs
    build_dir = Path(build_dir)

    if "gitlab" in docs_remote.lower():
        sp.run([
          "sphinx-build", "-b", "singlehtml", docs_dir,
          str(build_dir / 'public')
        ])

        # Add the required Gitlab CLI file to BUILD_DIR
        with (build_dir / ".gitlab-ci.yml").open("w") as tgt:
            tgt.write(GITLAB_CLI)


    elif "github" in docs_remote.lower():
        sp.run([
          "sphinx-build", "-b", "singlehtml", docs_dir, str(build_dir)
        ])

    # Use ghp-import to do the Git magic,
    # then push to docs_remote master branch
    sp.run(["ghp-import", "--no-jekyll", "--branch=docs-build", str(build_dir)])
    sp.run(["git", "push", docs_remote, "docs-build:master", "--force"])

    # Clean up
    sp.run(["rm", "-rf", str(build_dir)])
    sp.run(["git", "branch", "-D", "docs-build"])
