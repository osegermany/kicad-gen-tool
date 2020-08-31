These are some basic scripts to help you in automatically generate files
out of KiCad projects.

More specifically, it allows you to generate:

* Gerber & drill files
* PNG renders of the Gerber files

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
