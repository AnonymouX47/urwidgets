## Seting up a development environment

### Requirements
- [Python >= 3.7](https://www.python.org/)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- A new virtual environment
  - This is to ensure all contributors are always on the same page as far as dependency versions are concerned.

### Steps
To install/upgrade all the required python packages for core development, run:

```shell
make install-req
```
OR
```shell
pip install --upgrade -r requirements.txt
```

To install the required packages for building the documentation, run:

```shell
make install-req-docs
```
OR
```shell
pip install --upgrade -r docs/requirements.txt
```

To install the package in `develop` or `editable` mode:

```shell
make install
```
OR
```shell
python -m pip install -e .
```
This way, the package and the command-line entry-point are always available within the virtual environment.

**NOTE:** This is required to build the docs and to run tests.

* * *

Now that you have setup a development environment, you can create a new branch and start making changes (after reading the guidelines below :smiley:) and when done, contribute your changes by opening a [pull request](https://github.com/AnonymouX47/urwidgets/pulls).


## Guidelines
- For feature suggestions, please open a new **Feature Request** in the [issues section](https://github.com/AnonymouX47/urwidgets/issues) first to discuss how it would be implemented... you should propose your idea there.
- Every **pull request** should be **from a branch other than the default** (`main`).
- Always test that everything works as expected before opening a pull request.


## Style
**NAMES tell WHAT... CODE tell HOW... COMMENTS tell WHY, when necessary (and WHAT, when impossible to make it obvious with names)**

_The points below apply to the **Python** aspects of this project._

- Maximum line length is 88 characters.
- Endeavour to run the checks and tests (as described in the sections below) before commiting changes.
  - Note that this might not confer compatibility across multiple Python versions or platforms, final checks will be done automatically when you push the changes or open a PR.
- Format your code with `black` (see [Code Formatting](#code-formatting) below).
- All functions or methods should be annotated.
  - **Note:** Currently, annotations are only for better and quicker comprehension of the defined interfaces, by the library users and package developers.
  - So, forgive me, they might not entirely comply with standards.
- All modules, classes and functions should have docstrings (as specified below).
- All docstrings should be written according to the [Google style](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings) for the following reasons:
  - Uniformity.
  - The reference sections of the documentation are auto-generated from the modules using the `autodoc` and `napoleon` extensions of [Sphinx](https://www.sphinx-doc.org/en/master/).
  - Google-style docstrings + `napoleon` is used instead of pure reStructuredText docstrings for the sake of readability and to reduce the requirements for contribution.
- Try to keep things (definitions, names, dict keys, etc...) **sorted** wherever reasonably possible.
  - Makes finding things faster and easier :smiley:.
- Please try as much as possible to follow formats or styles already established in the project.

* * *

**_GUIDELINES are not LAWS, CONVENTIONS are not RULES but they're good to follow when there's a valid REASON to._**

That said... Please, no one's perfect. So, help point things out or just correct things when they're done otherwise.
Thanks!


## Pre-commit Checks and Tests

Run:

```shell
make
```
to run linting and formatting checks and tests locally before commiting changes.

If you don't have the `make` utility, see the separate steps below.

### Code linting
Run:

```shell
make lint
```
OR

```shell
flake8 .
```
if you don't have the `make` utility.

### Check code formatting
To simply check the formatting without modifying the files, run:

```shell
make check-format
```
OR

```shell
black --check --diff --color .
```
if you don't have the `make` utility.

### Check imports formatting
To simply check the imports without modifying the files, run:

```shell
make check-imports
```
OR

```shell
isort --check --diff --color .
```
if you don't have the `make` utility.


## Corrections

### Code formatting
To re-format wrong formatted modules (and write to file), run:

```shell
make format
```
OR

```shell
black .
```
if you don't have the `make` utility.

### Imports formatting
To re-format wrong formatted imports (and write to file), run:

```shell
make imports
```
OR

```shell
isort .
```
if you don't have the `make` utility.


## Documentation

### Build the documentation
Run:

```shell
make docs
```
OR

```shell
cd docs; make html; cd ..
```

* * *

Nothing is too small... but some things can be too much though, like rewriting the entire package in one pull request. :grin:

Looking forward to your contributions... Thanks :heart:!
