import sys


def read_lines(path):
    """Read a file as raw bytes and split it into lines (as the assignment defines)."""
    with open(path, "rb") as f:          # "rb" = raw bytes, so \r is kept
        data = f.read()
    lines = data.split(b"\n")            # split on the newline byte
    if lines and lines[-1] == b"":       # a final \n (or an empty file) leaves an empty last piece
        lines.pop()                      # drop it
    return lines


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A B", file=sys.stderr)
        sys.exit(2)

    command, path_a, path_b = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        a = read_lines(path_a)
        b = read_lines(path_b)
    except OSError as e:
        print(f"error: cannot read file: {e}", file=sys.stderr)
        sys.exit(2)                      # nothing on stdout, exit code 2

    out = []
    if a == b:
        # temporary: identical files -> every line is a keep line
        for line in a:
            out.append(b" " + line + b"\n")
    else:
        print("diff not written yet", file=sys.stderr)

    sys.stdout.buffer.write(b"".join(out))


if __name__ == "__main__":
    main()