from __future__ import annotations

__version__ = "0.3.0"

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
    cmd: Path | str  # actual path or command
    pre: str | None  # code block pre, like ```pre; if None, no code block is used


class ParseError(Exception):
    pass


class RunError(Exception):
    pass


class Transform:
    PATTERN_BEG = re.compile(r"^(<!-- (MDUP:BEG) (?P<cmd>[^;]+)\s*(\s*;\s*(?P<pre>\w+))? -->)$")
    PATTERN_END = re.compile(r"^(<!-- MDUP:END -->)$")

    def __init__(self, input_file: Path, output_file: Path):
        self.input_file = input_file
        self.output_file = output_file
        self.cwd = self.input_file.parent

        with open(self.input_file, "rt") as fp:
            self.lines = fp.readlines()

    def run(self) -> "Transform":
        locs = self.parse_pattern_locs()

        # iterate in reverse order so that we don't have to worry about line numbers
        for loc in reversed(locs):
            self.lines[loc.beg + 1 : loc.end] = self.run_cmd(loc)

        return self

    def write(self) -> None:
        with open(self.output_file, "wt") as fp:
            for line in self.lines:
                fp.write(line)

    def parse_pattern_locs(self) -> list[Loc]:
        cur_loc = None
        out = []

        for i, line in enumerate(self.lines):
            if m := self.PATTERN_BEG.match(line):
                if cur_loc:
                    raise ParseError(f"Found new BEG before END on line {i+1}")

                cur_loc = Loc(beg=i, end=None, cmd=m.groupdict()["cmd"], pre=m.groupdict()["pre"])

            elif m := self.PATTERN_END.match(line):
                if not cur_loc:
                    raise ParseError(f"Found END without BEG on line {i+1}")
                cur_loc.end = i
                out.append(copy(cur_loc))
                cur_loc = None

        return out

    def run_cmd(self, loc: Loc) -> list[str]:
        """Run a command (actual command, e.g. `date` or a script, e.g. `./script.sh`),
        then include stdout in a code block.

        If the return code is non-zero, raise a RuntimeError with context info.
        """
        proc = subprocess.run(
            ["bash", "-c", loc.cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            cwd=self.cwd,
        )
        stdout = proc.stdout.decode("utf-8")
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8")
            raise RunError(f"Error running `{loc.cmd}`:\nstdout:\n{stdout}\nstderr:\n{stderr}\n")

        out = stdout.splitlines(keepends=True)
        out[-1] = out[-1].rstrip() + "\n"

        pre = loc.pre or ""
        return [f"```{pre}\n", *out, "```\n"]


def main():
    args = parse_args()

    Transform(input_file=args.input, output_file=args.output or args.input).run().write()


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
