import collections
from collections.abc import Generator
import os
import subprocess
from typing import List
import xml.etree.ElementTree
import logging

import dateutil.parser

from svine import exceptions

SVN_COMMAND = "svn"
logger = logging.getLogger(__name__)


class RemoteClient:
    """
    A client for remote Subversion repositories.
    Can only handle a limited number of subcommands, see API.
    """

    def __init__(self, url: str):
        self.url = url

    @staticmethod
    def __extract_xml_element_text(
        element: xml.etree.ElementTree.Element | None,
    ) -> str | None:
        """
        Returns the text from an XML element if the element is not None and the text not an empty string.
        Else returns None.

        :param element: The element whose text to return
        :return: The element text or None
        """
        return element.text if element is not None and len(element.text) > 0 else None

    def info(self) -> collections.namedtuple:
        cmd = ["--xml", self.url]

        result = self.run_command("info", cmd, do_combine=True)

        root = xml.etree.ElementTree.fromstring(result)

        named_fields = [
            "url",
            "relative_url",
            "entry_kind",
            "entry_path",
            "entry_revision",
            "repository_root",
            "repository_uuid",
            "wcinfo_wcroot_abspath",
            "wcinfo_schedule",
            "wcinfo_depth",
            "commit_author",
            "commit_date",
            "commit_revision",
        ]
        c = collections.namedtuple("SvnInfo", named_fields)

        entry_attr = root.find("entry").attrib
        commit_attr = root.find("entry/commit").attrib

        relative_url = root.find("entry/relative-url")
        author = root.find("entry/commit/author")
        wc_root_abspath = root.find("entry/wc-info/wcroot-abspath")
        wc_info_schedule = root.find("entry/wc-info/schedule")
        wc_info_depth = root.find("entry/wc-info/depth")

        info = {
            "url": root.find("entry/url").text,
            "relative_url": RemoteClient.__extract_xml_element_text(relative_url),
            "entry_kind": entry_attr["kind"],
            "entry_path": entry_attr["path"],
            "entry_revision": int(entry_attr["revision"]),
            "repository_root": root.find("entry/repository/root").text,
            "repository_uuid": root.find("entry/repository/uuid").text,
            "wcinfo_wcroot_abspath": RemoteClient.__extract_xml_element_text(
                wc_root_abspath
            ),
            "wcinfo_schedule": RemoteClient.__extract_xml_element_text(
                wc_info_schedule
            ),
            "wcinfo_depth": RemoteClient.__extract_xml_element_text(wc_info_depth),
            "commit_author": RemoteClient.__extract_xml_element_text(author),
            "commit_date": dateutil.parser.parse(root.find("entry/commit/date").text),
            "commit_revision": int(commit_attr["revision"]),
        }

        return c(**info)

    def list(self) -> Generator[str, None, None]:
        """
        Yields the contents of the remote repository root directory line by line.
        """
        for line in self.run_command("ls", [self.url]):
            line = line.strip()
            if line:
                yield line

    def log(self, limit: int = None) -> Generator[collections.namedtuple, None, None]:
        """
        Retrieves the log entries for the remote repository and generates more accessible log entries as named tuples.

        :param limit: The max. number of log entries to yield
        """
        args = []

        if limit is not None:
            args += ["-l", str(limit)]

        result = self.run_command("log", args + ["--xml", self.url], do_combine=True)

        yield from self.generate_log_entries(result)

    @staticmethod
    def generate_log_entries(
        result: str,
    ) -> Generator[collections.namedtuple, None, None]:
        """
        Takes an XML string resulting from an 'svn log' call and generates from it
        named tuples that represent a single log entry.

        Fields in the log entry tuples are:

        - date: The date the revision has been committed
        - msg: The revision message
        - revision: The revision number
        - author: The author of the revision
        """
        root = xml.etree.ElementTree.fromstring(result)
        named_fields = ["date", "msg", "revision", "author"]
        c = collections.namedtuple("LogEntry", named_fields)

        for e in root.iter("logentry"):
            entry_info = {x.tag: x.text for x in list(e)}

            date = None
            date_text = entry_info.get("date")
            if date_text is not None:
                date = dateutil.parser.parse(date_text)

            log_entry = {
                "msg": entry_info.get("msg"),
                "author": entry_info.get("author"),
                "revision": int(e.get("revision")),
                "date": date,
            }

            yield c(**log_entry)

    def run_command(
        self,
        subcommand: str,
        args: List[str],
        do_combine: bool = False,
        encoding: str = "utf-8",
        errors: str = "replace",
    ) -> str | List[str]:
        """
        Runs the given non-interactive 'svn' subcommand with the given arguments
        using Python's subprocess.

        :param subcommand: The subcommand to run
        :param args: Arguments passed to the subcommand
        :param do_combine: Whether output should be combined (default: False)
        :param encoding: Encoding to use for decoding subprocess data (default: utf-8)
        :param errors: Strategy for dealing with decoding errors (default: replace)
        :return: The command output, either combined in a single string, or as a list of lines, depending on do_combine
        """
        cmd = [SVN_COMMAND, "--non-interactive", subcommand] + args

        logger.debug(f"Run command: {cmd}")

        env = os.environ.copy()
        env["LANG"] = os.environ.get(
            "LANG", os.environ.get("SVN_COMMAND_OUTPUT_ENCODING", "en_US.UTF-8")
        )

        p = subprocess.Popen(
            cmd,
            cwd=None,
            env=env,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            stderr=subprocess.PIPE,
            encoding=encoding,
            errors=errors,
        )

        stdout, stderr = p.communicate()
        return_code = p.returncode

        if return_code != 0:
            raise exceptions.SvnException(
                f"Command failed with ({return_code}): {cmd}\nstdout:\n\n{stdout}\nstderr:\n\n{stderr}"
            )

        if do_combine:
            return stdout

        return stdout.strip("\n").split("\n")
