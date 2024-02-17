from setuptools import setup

classifiers = [
    "Environment :: Console",
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: Developers",
    "Operating System :: POSIX :: Linux",
    "Operating System :: MacOS",
    "Operating System :: Android",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries",
]

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(
    name="urwidgets",
    version="0.2.1",
    author="AnonymouX47",
    author_email="anonymoux47@gmail.com",
    url="https://github.com/AnonymouX47/urwidgets",
    description="A collection of widgets for urwid (https://urwid.org)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    classifiers=classifiers,
    python_requires=">=3.7",
    install_requires=["urwid>=2.1,<3.0"],
    project_urls={
        "Changelog": "https://github.com/AnonymouX47/urwidgets/blob/main/CHANGELOG.md",
        "Documentation": "https://urwidgets.readthedocs.io/",
        "Source": "https://github.com/AnonymouX47/urwidgets",
        "Tracker": "https://github.com/AnonymouX47/urwidgets/issues",
    },
    keywords=[
        "terminal",
        "console",
        "xterm",
        "library",
        "tui",
        "urwid",
        "curses",
    ],
)
