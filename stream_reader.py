"""Generic marker-delimited section extraction.

Not specific to the "Board:" section, so later iterations can reuse it
for "Commands:" or any other section without duplicating this logic.
"""


def read_lines(stream):
    return [line.strip() for line in stream.read().splitlines()]


def read_section(lines, start_marker, end_marker=None):
    start = lines.index(start_marker) + 1
    section = []
    i = start
    while i < len(lines) and lines[i] != end_marker:
        if lines[i]:
            section.append(lines[i])
        i += 1
    return section
