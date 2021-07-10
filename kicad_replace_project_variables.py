# SPDX-FileCopyrightText: 2021 Robin Vobruba <hoijui.quaero@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from string import Template
import re
import os
import sys
import click
from git import Repo
import replace_vars
from datetime import date
from pathlib import Path

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
DATE_FORMAT="%Y-%m-%d"

# Quotes all KiCad text entries that are not yet quoted and contain a variable of the form '${KEY}'
filter_kicad_quote   = replace_vars.RegexTextFilter(
        r'(?P<pre>\(gr_text\s+)(?P<text>[^"\s]*\${[-_0-9a-zA-Z]*}[^\s"]*)(?P<post>\s+[\)\(])',
        r'\g<pre>"\g<text>"\g<post>')
# Unquotes all KiCad text entries that are quoted and do not contain white-space
filter_kicad_unquote = replace_vars.RegexTextFilter(
        r'(?P<pre>\(gr_text\s+)"(?P<text>[^"\s\\]+)"(?P<post>\s+[\)\(])',
        r'\g<pre>\g<text>\g<post>')

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def kicad_replace_project_vars() -> None:
    pass

def git_remote_to_https_url(url) -> str:
    public_url = re.sub(r"^git@", "https://", url)
    public_url = public_url.replace(".com:", ".com/", 1)
    public_url = re.sub(r"\.git$", "", public_url)
    return public_url

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("src", type=click.File("r"))
@click.argument("dst", type=click.File("w"))
@click.argument("additional_replacements", type=replace_vars.KEY_VALLUE_PAIR, nargs=-1)
@click.option('--src-file-path', '-p', type=click.Path(), envvar='PROJECT_SRC_FILE_PATH',
        default=None, help='The path to the source file, relative to the repo root')
@click.option('--repo-path', '-r', type=click.Path(), envvar='PROJECT_REPO_PATH',
        default='.', help='The path to the local git repo')
@click.option('--repo-url', '-u', type=click.STRING, envvar='PROJECT_REPO_URL',
        default=None, help='Public project repo URL')
@click.option('-n', '--name', type=click.STRING, envvar='PROJECT_NAME',
        default=None, help='Project name (prefferably without spaces)')
@click.option('--vers', type=click.STRING, envvar='PROJECT_VERSION',
        default=None, help='Project version (prefferably without spaces)')
@click.option('-d', '--version-date', type=click.STRING, envvar='PROJECT_VERSION_DATE',
        default=None, help='Date at which this version of the project was committed/released')
@click.option('--build-date', type=click.STRING, envvar='PROJECT_BUILD_DATE',
        default=None, help=('Date at which the currently being-made build of '
            + 'the project is made. This should basically always be left on the '
            + 'default, which is the current date.'))
#@click.option('--recursive', '-R', type=click.STRING, default=None,
#       help='If --src-file-path points to a directory, and this is a globWhether to skip the actual replacing')
@click.option('--date-format', type=click.STRING, default=DATE_FORMAT,
        help=('The format for the version and the build dates; '
            + 'see pythons date.strftime documentation'))
@click.option('--kicad-pcb', is_flag=True, help='Whether the filtered file is a *.kicab_pcb')
@click.option('--dry', is_flag=True, help='Whether to skip the actual replacing')
@click.option('--verbose', is_flag=True, help='Whether to output additional info to stderr')
def replace_single_command(src, dst, additional_replacements, src_file_path=None, repo_path='.',
        repo_url=None, name=None, vers=None, version_date=None, build_date=None,
        date_format=DATE_FORMAT, kicad_pcb=False, dry=False,
        verbose=False) -> None:
    # convert tuple to dict
    add_repls_dict = {}
    for key, value in additional_replacements:
        add_repls_dict[key] = value
    replace_single(src, dst, add_repls_dict, src_file_path, repo_path,
            repo_url, name, vers, version_date, build_date,
            date_format, kicad_pcb, dry, verbose)

def replace_single(src, dst, additional_replacements={}, src_file_path=None, repo_path='.',
        repo_url=None, name=None, vers=None, version_date=None, build_date=None,
        date_format=DATE_FORMAT, kicad_pcb=False, dry=False,
        verbose=False) -> None:
    repo = Repo(repo_path)
    vcs_branch = repo.head.reference
    vcs_remote_tracking_branch = vcs_branch.tracking_branch()
    vcs_remote = vcs_remote_tracking_branch.remote_name
    if repo_url is None:
        remote_urls = repo.remotes[vcs_remote].urls
        try:
            repo_url = next(remote_urls)
        except StopIteration as err:
            raise ValueError('No remote urls defined in repo "%s"' % repo_path) from err
        if not repo_url.startswith('https://'):
            repo_url = git_remote_to_https_url(repo_url)
    if name is None:
        name = os.path.basename(os.path.abspath(repo_path))
    if vers is None:
        vers = repo.git.describe('--tags', '--dirty', '--broken', '--always')
    if version_date is None:
        version_date = date.fromtimestamp(repo.head.ref.commit.committed_date).strftime(date_format)
    if build_date is None:
        build_date = date.today().strftime(date_format)
    if src_file_path is None:
        src_file_path = src.name
    if src_file_path == '-':
        print('WARNING: "src_file_path" has the generic value "%s"'
                % src_file_path, file=sys.stderr)
    if not kicad_pcb and src_file_path and src_file_path.endswith(".kicad_pcb"):
        kicad_pcb=True
        print('WARNING: Automatically set kicad_pcb=True due to appropriate file-suffix',
                file=sys.stderr)
    pre_filter=None
    post_filter=None
    if kicad_pcb:
        pre_filter=filter_kicad_quote
        post_filter=filter_kicad_unquote
        if verbose:
            print('INFO: KiCad PCB filters will be applied', file=sys.stderr)
    additional_replacements.setdefault('PROJECT_REPO_URL', repo_url)
    additional_replacements.setdefault('PROJECT_NAME', name)
    additional_replacements.setdefault('PROJECT_VERSION', vers)
    additional_replacements.setdefault('PROJECT_VERSION_DATE', version_date)
    additional_replacements.setdefault('PROJECT_BUILD_DATE', build_date)
    additional_replacements.setdefault('SOURCE_FILE_PATH', src_file_path)
    replace_vars.replace_vars_by_lines_in_stream(
            src, dst, additional_replacements, dry, verbose,
            pre_filter=pre_filter, post_filter=post_filter)



@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("src_root", type=click.Path(exists=True, dir_okay=True, readable=True))
@click.argument("glob", type=click.STRING)
@click.argument("dst_root", type=click.Path(exists=True, dir_okay=True, writable=True))
@click.argument("additional_replacements", type=replace_vars.KEY_VALLUE_PAIR, nargs=-1)
@click.option('--src-file-path', '-p', type=click.Path(), envvar='PROJECT_SRC_FILE_PATH',
        default=None, help='The path to the source file, relative to the repo root')
@click.option('--repo-path', '-r', type=click.Path(), envvar='PROJECT_REPO_PATH',
        default='.', help='The path to the local git repo')
@click.option('--repo-url', '-u', type=click.STRING, envvar='PROJECT_REPO_URL',
        default=None, help='Public project repo URL')
@click.option('-n', '--name', type=click.STRING, envvar='PROJECT_NAME',
        default=None, help='Project name (prefferably without spaces)')
@click.option('--vers', type=click.STRING, envvar='PROJECT_VERSION',
        default=None, help='Project version (prefferably without spaces)')
@click.option('-d', '--version-date', type=click.STRING, envvar='PROJECT_VERSION_DATE',
        default=None, help='Date at which this version of the project was committed/released')
@click.option('--build-date', type=click.STRING, envvar='PROJECT_BUILD_DATE',
        default=None, help='Date at which the currently being-made build of the project is made.' +
        ' This should basically always be left on the default, which is the current date.')
#@click.option('--recursive', '-R', type=click.STRING, default=None,
#       help='If --src-file-path points to a directory, and this is a globWhether to skip the actual replacing')
@click.option('--date-format', type=click.STRING, default=DATE_FORMAT,
        help='The format for the version and the build dates; see pythons date.strftime documentation')
@click.option('--kicad-pcb', is_flag=True, help='Whether the filtered file is a *.kicab_pcb')
@click.option('--dry', is_flag=True, help='Whether to skip the actual replacing')
@click.option('--verbose', is_flag=True, help='Whether to output additional info to stderr')
def replace_recursive_command(src_root='.', glob='*.kicad_pcb', dst_root='./build/gen-src',
        additional_replacements=(), src_file_path=None, repo_path='.',
        repo_url=None, name=None, vers=None, version_date=None, build_date=None,
        date_format=DATE_FORMAT, kicad_pcb=False, dry=False,
        verbose=False) -> None:
    '''
    Replaces template values, generating a KiCad PCB file,
    with a KiCad PCB file as input.
    Scanns for all *.kicad_pcb files in the project,
    and replaces variables of the form ${KEY} in there.
    Use $${KEY} for quoting variables you do not want expanded.
    '''
    add_repls_dict = {}
    for key, value in additional_replacements:
        add_repls_dict[key] = value
    replace_recursive(src_root, glob, dst_root, add_repls_dict, src_file_path, repo_path,
            repo_url, name, vers, version_date, build_date,
            date_format, kicad_pcb, dry, verbose)

def replace_recursive(src_root='.', glob='*.kicad_pcb', dst_root=None,
        additional_replacements={}, src_file_path=None, repo_path='.',
        repo_url=None, name=None, vers=None, version_date=None,
        build_date=None, date_format=DATE_FORMAT, kicad_pcb=False,
        dry=False, verbose=False) -> None:
    if src_root == dst_root:
        dst_root = None
    if verbose:
        print('INFO: Scanning directory "%s" for "%s" ...' % (src_root, glob), file=sys.stderr)
    if dst_root:
        dst_root_abs = os.path.abspath(dst_root)
    for path in Path(src_root).rglob(glob):
        print(str(path), file=sys.stderr)
        print(str(dst_root_abs), file=sys.stderr)
        print(str(path.absolute()), file=sys.stderr)
        if dst_root and os.path.commonpath([os.path.abspath(path), dst_root_abs]) == dst_root_abs:
            # Exclude files in the dst_root
            continue
        src_path = str(path)
        if dst_root:
            dst_path = os.path.join(dst_root, os.path.relpath(src_path, src_root))
            os.makedirs(os.path.dirname(os.path.abspath(dst_path)), exist_ok=True)
        else:
            dst_path = src_path + ".TMP"
        if verbose:
            if dst_root:
                print('INFO: Processing file from "%s" -> "%s" ...'
                        % (src_path, dst_path), file=sys.stderr)
            else:
                print('INFO: Processing file "%s" ...' % src_path, file=sys.stderr)
        src = click.open_file(src_path, "r")
        dst = click.open_file(dst_path, "w")
        replace_single(src, dst, additional_replacements, src_file_path, repo_path,
                repo_url, name, vers, version_date, build_date,
                date_format, kicad_pcb, dry, verbose)
        if not dst_root:
            os.rename(dst.name, src.name)


if __name__ == '__main__':
    replace_single_command()
    #replace_recursive_command()
