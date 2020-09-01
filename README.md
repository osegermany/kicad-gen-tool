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
