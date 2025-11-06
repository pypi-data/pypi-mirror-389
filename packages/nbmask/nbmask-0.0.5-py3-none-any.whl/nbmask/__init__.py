"""IPython extension to mask sensitive data from cell outputs"""

import io
import os
import re
import sys
import shlex
import inspect
import warnings

from pathlib import Path

from functools import lru_cache

from IPython.display import display
from IPython.utils.capture import capture_output

from IPython.core.displayhook import DisplayHook
from IPython.core.displaypub import DisplayPublisher

from IPython.core.magic import Magics, magics_class, line_magic, cell_magic

from IPython.core.getipython import get_ipython


SECRETS = set()


@lru_cache
def get_pattern():
    """Utility function to remove username from string"""

    patterns = [re.escape(secret) for secret in SECRETS]

    username = os.getenv("USER")

    if username is not None:
        patterns.append(r"\b%s\b" % re.escape(username))

    combined = "|".join(patterns)

    return re.compile(combined, re.IGNORECASE)


def masked_text(text: str):
    """Utility function to remove username from string"""
    return get_pattern().sub("...", text)


def patch_publisher(publisher, *, verbose=False):
    """Patch active DisplayPublisher to mask text/plain outputs"""

    if not inspect.ismethod(publisher.publish):
        warnings.warn(f"{publisher} publish is not a method!")
        return publisher

    publish = publisher.publish

    def new_publish(data, *args, **kwargs) -> None:
        if "text/plain" in data:
            text = data["text/plain"]
            text = masked_text(text)
            data["text/plain"] = text

        publish(data, *args, **kwargs)

    publisher.publish = new_publish


def patch_display_hook(displayhook):
    """Patch active DisplayHook to mask text/plain outputs"""

    if not inspect.ismethod(displayhook.write_format_data):
        warnings.warn(f"{displayhook} write_format_data is not a method!")
        return displayhook

    write_format_data = displayhook.write_format_data

    def new_write_format_data(format_dict, *args, **kwargs) -> None:
        """Write the format data dict to the frontend."""

        if "text/plain" in format_dict:
            text = format_dict["text/plain"]
            text = masked_text(text)
            format_dict["text/plain"] = text

        write_format_data(format_dict, *args, **kwargs)

    displayhook.write_format_data = new_write_format_data


def patch_text_writer(stream):
    if not isinstance(stream, io.TextIOBase):
        warnings.warn(f"{stream} is not a TextIOBase!")
        return 

    if not inspect.isbuiltin(stream.write):
        # warnings.warn(f"{stream} write is not a builtin!")
        return

    write = stream.write

    def new_write(text):
        text = masked_text(text)
        write(text)

    stream.write = new_write


@magics_class
class NBMaskMagics(Magics):
    @line_magic
    def nbmask(self, line, cell=None):
        """Line magic to add mask patterns"""
        args = shlex.split(line)
        SECRETS.update(args)
        get_pattern.cache_clear()

    @cell_magic
    def masked(self, line, cell=None):
        """Cell magic to mask print/logging outputs"""
        cell = cell if cell else line
        shell = get_ipython()

        with capture_output() as c:
            shell.run_cell(cell)

        if c.stderr:
            output = masked_text(c.stderr)
            print(output, file=sys.stderr)

        if c.stdout:
            output = masked_text(c.stdout)
            print(output)

        for output in c.outputs:
            display(output)


def update_formatters(ipython):
    """Update some formatters (legacy)"""

    def masked_display(value, p, cycle):
        """IPython custom display handler"""
        text = masked_text(repr(value))
        p.text(text)

    text_formatter = ipython.display_formatter.formatters["text/plain"]
    text_formatter.for_type(str, masked_display)
    text_formatter.for_type(Path, masked_display)


def load_ipython_extension(ipython):
    ipython.register_magics(NBMaskMagics)

    patch_text_writer(sys.stdout)
    patch_text_writer(sys.stderr)

    if isinstance(ipython.display_pub, DisplayPublisher):
        patch_publisher(ipython.display_pub)

    if isinstance(sys.displayhook, DisplayHook):
        patch_display_hook(sys.displayhook)
