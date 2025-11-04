from __future__ import annotations

__version__ = "0.2.5"

import re
import subprocess
from argparse import ArgumentParser, Namespace
from copy import copy
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Loc:
    beg: int
    end: int
    kind: str
    cmd: Path | str  # actual path or command


class ParseError(Exception):
    pass


class RunCmdError(Exception):
    pass


class Transform:
    kinds = {"SRC", "RUN", "CMD"}
    pattern_beg = f"^(<!-- MDUP:BEG \\((?P<kind>{'|'.join(kinds)}):(?P<cmd>.+)\\) -->)$"
    pattern_end = "^(<!-- MDUP:END -->)$"

    def __init__(self, input_file: Path, output_file: Path):
        self.input_file = input_file
        self.output_file = output_file
        self._lines = self._read_lines()

    def transform(self) -> "Transform":
        locs = self._parse_pattern_locs()

        # iterate in reverse order so that we don't have to worry about line numbers
        for loc in reversed(locs):
            res = Transform._kind_to_func(loc.kind)(loc.cmd)
            self._lines[loc.beg + 1 : loc.end] = res

        return self

    def write(self) -> None:
        with open(self.output_file, "wt") as fp:
            for line in self._lines:
                fp.write(line)

    def _read_lines(self) -> list[str]:
        with open(self.input_file, "rt") as fp:
            return fp.readlines()

    def _parse_pattern_locs(self) -> list[Loc]:
        cur_loc = None
        out = []

        for i, line in enumerate(self._lines):
            if m := re.match(self.pattern_beg, line):
                if cur_loc:
                    raise ParseError(f"Found new BEG before END on line {i+1}")

                kind = m.groupdict()["kind"]
                cmd = m.groupdict()["cmd"]

                # distinguish between path and commands
                # commands are unaltered, but paths are resolved rel. to the input file
                if kind != "CMD":
                    cmd = (self.input_file.parent / m.group(3)).resolve()

                cur_loc = Loc(beg=i, end=None, kind=kind, cmd=cmd)

            elif m := re.match(self.pattern_end, line):
                if not cur_loc:
                    raise ParseError(f"Found END without BEG on line {i+1}")
                cur_loc.end = i
                out.append(copy(cur_loc))  # TODO: avoid copy?
                cur_loc = None

        return out

    @staticmethod
    def _kind_to_func(kind: str):
        if kind == "SRC":
            return Transform.include_src
        if kind in ("RUN", "CMD"):
            return Transform.run_cmd

        raise ValueError(f"Unknown {kind=}")

    @staticmethod
    def _fmt_code_block(data: list[str], pre: str) -> list[str]:
        data[-1] = data[-1].rstrip() + "\n"
        return [f"```{pre}\n", *data, "```\n"]

    @staticmethod
    def include_src(path: Path) -> list[str]:
        """Include a source file in a code block.
        Format the code block using the file extension (e.g. py, sh).
        """
        with open(path, "rt") as fp:
            data = fp.readlines()
        return Transform._fmt_code_block(data, pre=path.suffix.lstrip("."))

    @staticmethod
    def run_cmd(cmd: Path | str) -> list[str]:
        """Run a command (actual command, e.g. `date` or a script, e.g. `./script.sh`),
        then include stdout in a code block.

        If the return code is non-zero, raise a RuntimeError with context info.
        """
        proc = subprocess.run(
            ["bash", "-c", f"{cmd}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        stdout = proc.stdout.decode("utf-8")
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8")
            raise RunCmdError(f"Error running `{cmd}`:\nstdout:\n{stdout}\nstderr:\n{stderr}\n")
        return Transform._fmt_code_block(stdout.splitlines(keepends=True), pre="")


def main():
    args = parse_args()

    tf = Transform(input_file=args.input, output_file=args.output or args.input)
    tf.transform().write()


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", type=Path, required=True, help="input markdown file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output markdown file; if not specified, the input file will be edited in place",
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")

    return parser.parse_args()


if __name__ == "__main__":
    main()
