import re
import json
from json import JSONDecodeError
import sys
from typing import Callable, Iterable
from colorama import Fore, Style, init

LABELS_TO_SHOW = ("container",)
SKIP_EVERYTHING_BEFORE = "stderr F ", "stdout F"
WORDS_TO_COLOURS = {
    "ERROR": Fore.RED,
    "WARNING": Fore.YELLOW,
    "INFO": Fore.GREEN,
    "DEBUG": Style.DIM,
    "TRACE": Style.DIM,
}
COLOUR_FROM = "|"
MAX_LABELS_SIZE = 10


def colour(log: str) -> str:
    for word, colours in WORDS_TO_COLOURS.items():
        if word in log:
            colour_pos = log.find(COLOUR_FROM)
            if colour_pos == -1:
                colour_pos = 0
            return log[:colour_pos] + colours + log[colour_pos:] + Style.RESET_ALL
    return log


def mutate_log(log: str) -> str:
    log = log.removesuffix("\n")
    for skip_pattern in SKIP_EVERYTHING_BEFORE:
        if (skip_before := log.find(skip_pattern)) != -1:
            log = log[skip_before + len(skip_pattern) :]
    return colour(log)


def add_labels(log: str, log_labels: dict[str, str]) -> str:
    for label in LABELS_TO_SHOW:
        if label_info := log_labels.get(label):
            log = log + f" ({label_info})"
    return log


def find_outer_groups(to_parse: str, start_delim="{", end_delim="}") -> Iterable[str]:
    current_group: str = ""
    in_group = False
    open_delims = 0
    for c in to_parse:
        # Just came out of a group
        if (whitespace := not c.strip()) and in_group and not open_delims:
            yield current_group
            current_group = ""
            in_group = False
        # Just got into a group
        if not whitespace and not in_group:
            in_group = True
        if not in_group:
            continue

        if c == start_delim:
            open_delims += 1
        if open_delims and c == end_delim:
            open_delims -= 1
        current_group += c


def logcli_default(line: str):
    # Throws value error when != 3 groups
    _, labels_keyvals, log_json = find_outer_groups(line)
    labels = dict(re.findall(r'(\w+)="([^"]*)"', labels_keyvals))
    # Can throw decode error and key error
    log: str = json.loads(log_json)["log"]
    return add_labels(mutate_log(log), labels)


def logcli_jsonl(line: str):
    # These lines throw decode error and key error
    log_data = json.loads(line)
    log: str = json.loads(log_data["line"])["log"]
    return add_labels(mutate_log(log), log_data.get("labels", {}))


FORMATTERS: tuple[Callable[[str], str], ...] = logcli_default, logcli_jsonl, mutate_log


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        pretty_line: None | str = None
        for formatter in FORMATTERS:
            try:
                pretty_line = formatter(line)
            except (JSONDecodeError, KeyError, ValueError):
                continue
        if pretty_line is not None:
            print(pretty_line)


if __name__ == "__main__":
    init()
    main()
