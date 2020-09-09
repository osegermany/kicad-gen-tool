## Deprecation Warning!

We recommend to use the formidable
**[KiBot](https://github.com/INTI-CMNB/KiBot) tool** instead.

It can generate much more then just Gerbers
and 2D renders of the PCBs.

## Introduction

These are scripts to help you generate files
out of [KiCad](https://kicad-pcb.org/) (electronics) projects.

More specifically, it allows you to generate:

* [Gerber](https://en.wikipedia.org/wiki/Gerber_format)
  & [drill](https://en.wikipedia.org/wiki/PCB_NC_formats) files
* PNG renders of the PCB (made from the Gerber & drill files)

## Why should I use this?

If you host your KiCad based electronics designs in a git repo,
you may be storing the generated files in the repo as well.
That however, comes with the following drawbacks:

* the repo size increases unnecessarily,
  especially with binary files like PNGs
* when accessing the repo,
  one never knows if the generated files
  are really generated from the latest version of the sources

When able to auto-generate these files,
one can do it in a CI job
(available to every repo on GitHub and GitLab out of the box),
and refer to the generated file on the projects *pages* site.

## How does it work?

### Install Prerequisites

* BASH
* git
* Python
* `pcb-tools` (a Python library)

on a regular Debian based Linux,
you can install all of this with:

```bash
sudo apt-get install bash python3-pip
pip install pcb-tools
```

### Get the tool

In the repo of your project in which you want to use this tool,
which would be one that supports *\*.kicad_pcb* files,
you would do this to install this tool (in the project root dir):

```bash
pip install pcb-tools
mkdir -p doc-tools
git submodule add https://github.com/osegermany/kicad-pcb-generate-doc-tool.git doc-tools/kicad-pcb-generate
```

> **NOTE**\
> There might be a tool to automate this in a more user friendly way,
> comparable to a package manager like `Oh-My-ZSH` or `apt`.

### Run

This will generate the PCB derived artifacts for all KiCad PCBs in the repo:

```bash
doc-tools/kicad-pcb-generate/generate_sources
doc-tools/kicad-pcb-generate/generate_output
```

Output can be found under the *build* directory.
