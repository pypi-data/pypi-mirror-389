#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@summary: A script checking a CHANGELOG.md for syntax errors and prints some information about.

@author: Frank Brehm
@contact: frank@brehm.online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""
from __future__ import absolute_import, print_function

# Standard modules
import logging
import os
import platform
import pprint
import re
import sys
from pathlib import Path

# 3rd party modules
import click

# from click import Option, UsageError

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.insert(0, str(root))

try:
    sys.path.remove(str(parent))
except ValueError:  # Already removed
    pass

# Own modules
from fb_logging import __version__ as __pkg_version__
from fb_logging.changelog import ChangelogParsingError
from fb_logging.changelog import load as changelog_load
from fb_logging.colored import ColoredFormatter
from fb_logging.colored import colorstr

__version__ = "0.2.0"

LOG = logging.getLogger(__name__)


# =============================================================================
def pp(value, indent=4, width=150, depth=None):
    """
    Return a pretty print string of the given value.

    @return: pretty print string
    @rtype: str
    """
    pretty_printer = pprint.PrettyPrinter(indent=indent, width=width, depth=depth)
    return pretty_printer.pformat(value)


# # =============================================================================
# class MutuallyExclusiveOption(Option):

#     # -------------------------------------------------------------------------
#     def __init__(self, *args, **kwargs):
#         self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
#         help = kwargs.get('help', '')
#         if self.mutually_exclusive:
#             ex_str = ', '.join(self.mutually_exclusive)
#             kwargs['help'] = help + (
#                 ' NOTE: This argument is mutually exclusive with '
#                 ' arguments: [' + ex_str + '].'
#             )
#         super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

#     # -------------------------------------------------------------------------
#     def handle_parse_result(self, ctx, opts, args):
#         if self.mutually_exclusive.intersection(opts) and self.name in opts:
#             raise UsageError(
#                 "Illegal usage: `{}` is mutually exclusive with arguments `{}`.".format(
#                     self.name, ', '.join(self.mutually_exclusive)
#                 )
#             )

#         return super(MutuallyExclusiveOption, self).handle_parse_result(
#             ctx,
#             opts,
#             args
#         )


# =============================================================================
class CheckChangelogApp(object):
    """
    Click context environment class for the check-changelog application.

    Checks a CHANGELOG.md for syntax errors and prints some information about.
    """

    # -------------------------------------------------------------------------
    @classmethod
    def get_generic_appname(cls, appname=None):
        """Get the base name of the currently running application."""
        if appname:
            v = str(appname).strip()
            if v:
                return v
        return os.path.basename(sys.argv[0])

    # -------------------------------------------------------------------------
    @classmethod
    def terminal_can_colors(cls, debug=False):
        """
        Detect, whether the current terminal is able to perform ANSI color sequences.

        Both stdout and stderr file handles are inspected.

        @return: both stdout and stderr can perform ANSI color sequences
        @rtype: bool
        """
        cur_term = ""
        if "TERM" in os.environ:
            cur_term = os.environ["TERM"].lower().strip()

        colored_term_list = (
            r"ansi",
            r"linux.*",
            r"screen.*",
            r"[xeak]term.*",
            r"gnome.*",
            r"rxvt.*",
            r"interix",
        )
        term_pattern = r"^(?:" + r"|".join(colored_term_list) + r")$"
        re_term = re.compile(term_pattern)

        ansi_term = False
        env_term_has_colors = False

        if cur_term:
            if cur_term == "ansi":
                env_term_has_colors = True
                ansi_term = True
            elif re_term.search(cur_term):
                env_term_has_colors = True
        if debug:
            sys.stderr.write(
                "ansi_term: {a!r}, env_term_has_colors: {h!r}\n".format(
                    a=ansi_term, h=env_term_has_colors
                )
            )

        has_colors = False
        if env_term_has_colors:
            has_colors = True
        for handle in [sys.stdout, sys.stderr]:
            if hasattr(handle, "isatty") and handle.isatty():
                if debug:
                    msg = "{} is a tty.".format(handle.name)
                    sys.stderr.write(msg + "\n")
                if platform.system() == "Windows" and not ansi_term:
                    if debug:
                        sys.stderr.write("Platform is Windows and not ansi_term.\n")
                    has_colors = False
            else:
                if debug:
                    msg = "{} is not a tty.".format(handle.name)
                    sys.stderr.write(msg + "\n")
                if ansi_term:
                    pass
                else:
                    has_colors = False

        return has_colors

    # -------------------------------------------------------------------------
    def __init__(
        self,
        changelog_file,
        action="check",
        appname=None,
        verbose=0,
        version=__pkg_version__,
        has_colors=None,
    ):
        """Initialise the application object."""
        if changelog_file is None:
            self.changelog_file = None
        else:
            self.changelog_file = Path(changelog_file)
        if appname:
            self.appname = self.get_generic_appname()
        else:
            self.appname = self.get_generic_appname()
        self.verbose = verbose
        self.version = version
        if has_colors is not None:
            self.has_colors = bool(has_colors)
        else:
            self.has_colors = self.terminal_can_color()

        self.action = action

        self.init_logging()

        if self.verbose > 1:
            LOG.debug(f"Parameter 'has_colors' was {has_colors!r}.")

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""
        out = "<%s(" % (self.__class__.__name__)

        fields = []
        cfile = None
        if self.changelog_file is not None:
            cfile = str(self.changelog_file)

        fields.append(f"changelog_file={cfile!r}")
        fields.append(f"action={self.action!r}")
        fields.append(f"appname={self.appname!r}")
        fields.append(f"verbose={self.verbose!r}")
        fields.append(f"version={self.version!r}")
        fields.append(f"has_colors={self.has_colors!r}")

        out += ", ".join(fields) + ")>"
        return out

    # -------------------------------------------------------------------------
    def terminal_can_color(self):
        """
        Detect, whether the current terminal is able to perform ANSI color sequences.

        Both stdout and stderr file handles are inspected.

        @return: both stdout and stderr can perform ANSI color sequences
        @rtype: bool

        """
        if self.verbose > 3:
            return self.terminal_can_colors(debug=True)
        return self.terminal_can_colors(debug=False)

    # -------------------------------------------------------------------------
    def colored(self, msg, color):
        """
        Colorize the given string somehow.

        Wrapper function to colorize the message. Depending, whether the current
        terminal can display ANSI colors, the message is colorized or not.

        @param msg: The message to colorize
        @type msg: str
        @param color: The color to use, must be one of the keys of COLOR_CODE
        @type color: str

        @return: the colorized message
        @rtype: str

        """
        if not self.terminal_can_color:
            return msg
        return colorstr(msg, color)

    # -------------------------------------------------------------------------
    def init_logging(self):
        """
        Initialize the logger object.

        It creates a colored loghandler with all output to STDERR.
        Maybe overridden in descendant classes.

        @return: None
        """
        log_level = logging.INFO
        if self.verbose:
            log_level = logging.DEBUG

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # create formatter
        format_str = ""
        if self.verbose:
            format_str = "[%(asctime)s]: "
        format_str += self.appname + ": "
        if self.verbose:
            if self.verbose > 1:
                format_str += "%(name)s(%(lineno)d) %(funcName)s() "
            else:
                format_str += "%(name)s "
        format_str += "%(levelname)s - %(message)s"
        formatter = None
        if self.has_colors:
            formatter = ColoredFormatter(format_str)
        else:
            formatter = logging.Formatter(format_str)

        # create log handler for console output
        lh_console = logging.StreamHandler(sys.stderr)
        lh_console.setLevel(log_level)
        lh_console.setFormatter(formatter)

        root_logger.addHandler(lh_console)

        return

    # -------------------------------------------------------------------------
    def __call__(self):
        """
        Execute the main action of converting.

        Makes the application object callable.
        """
        LOG.debug(f"Checking {self.changelog_file!r} ...")

        try:
            if self.changelog_file:
                filename = str(self.changelog_file)
                LOG.debug(f"Reading {self.changelog_file!r} ...")
                with self.changelog_file.open("rb") as fp:
                    changes = changelog_load(fp)
            else:
                filename = "STDIN"
                changes = changelog_load(sys.stdin)
        except ChangelogParsingError as e:
            fn = self.colored(filename, "RED")
            LOG.error(f"Wrong formatted {fn}: " + str(e))
            sys.exit(5)

        if self.action == "last":
            if len(changes):
                if str(changes[0]["version"].lower()) == "unreleased" and len(changes) > 1:
                    print(str(changes[1]["version"]))
                else:
                    print(str(changes[0]["version"]))
            sys.exit(0)

        if self.action == "list":
            for change in changes:
                print(str(change["version"]))
            sys.exit(0)

        star = self.colored("*", "GREEN")
        fn = self.colored(filename, "CYAN")
        nr_changes = self.colored(str(len(changes)) + " changes", "CYAN")
        print(f"{star} File {fn} seems to be a valid CHANGELOG file, " f"found {nr_changes}.")
        sys.exit(0)


# =============================================================================

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument(
    "changelog_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True, path_type=Path),
    required=False,
)
@click.option("--check", "-C", "action", flag_value="check", default=True)
@click.option("--list-revisions", "--list", "-l", "action", flag_value="list")
@click.option("--last-revision", "--last", "-L", "action", flag_value="last")
@click.option(
    "--color/--no-color", "has_color", default=None, help="Set colored output for messages."
)
@click.option(
    "-v", "--verbose", count=True, type=click.IntRange(0, 5), help="Increase the verbosity level."
)
@click.version_option()
@click.pass_context
def main(ctx, changelog_file, action, has_color, verbose):
    """
    Check a CHANGELOG.md for syntax errors and prints some information about.

    If CHANGELOG_FILE is omitted, then the input will be read from STDIN.
    """
    ctx.obj = CheckChangelogApp(
        changelog_file, action=action, verbose=verbose, has_colors=has_color
    )

    if verbose > 2:
        click.echo(
            "{c}-Object:\n{a}".format(c=ctx.__class__.__name__, a=pp(ctx.__dict__)),
            file=sys.stderr,
        )

    ctx.obj()


# =============================================================================
if __name__ == "__main__":
    main()


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
