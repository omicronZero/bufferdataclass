# Content

The template sets up a simple continuous integration-pipeline for Python 3.14.

For every push and pull request, linting, format checking, static type checking, and tests are invoked:
* Ruff: Linting, Formatting
* MyPy: Code checking
* Tests: PyTest (with coverage)

The test summary and coverage are reported as an artifact.

For every push and pull request to the main/master and dev branches, a documentation may be built using sphinx and deployed
to a respective separate branch "gh-docs-<dev/main/master>". To do so, move the [templates/build_docs.yml](./templates/build_docs.yml) to [.github/workflows](./.github/workflows).
Otherwise, you can set up your own documentation publishing on ReadTheDocs (which is the only external documentation provider supported for now).

Deployment to PyPI and TestPyPI is optional (see below).

# Setting up the project

* Either set up an environment with Python 3.14 or change the respective version strings (Look for regex: "3\.?14")
  where adequate
* On your repository under Settings/Branches, check that merging only passes if all checks from linting, tests, etc.
  pass
* Replace ``python_ci_base`` with the name of your app on all files and ``AUTHOR`` with your name 

If you want to enable automatic deployment to PyPI, proceed with the following steps:

* Versioning is performed via [setuptools-scm](https://setuptools-scm.readthedocs.io/en/latest/) which reads the package 
  versions from metadata, e.g., from your git commits. Please read up on it before issuing a public release on PyPI.
* Set up your [PyPI](https://pypi.org/manage/account/publishing/) and [TestPyPI](https://test.pypi.org/manage/account/publishing/) Trusted Publisher Management publishers.<br/>
  Note that your project name **must** match the value you entered in the `project.name`-field in the `pyproject.toml`
* Uncomment the respective lines in the [.github/workflows/check_and_deploy.yml](.github/workflows/check_and_deploy.yml) file.<br/>
  Once you enable it, the default configuration is to publish to TestPyPI from the `main`, `master`, and `testing/deployment` 
  branches, and to PyPI once you perform a published release on GitHub.

# License (MIT-0)

Copyright 2026 Josef Mayr

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
