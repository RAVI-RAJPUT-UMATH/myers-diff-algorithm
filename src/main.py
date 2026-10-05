import sys


def read_lines(path):
    """Read a file as raw bytes and split it into lines (as the assignment defines)."""
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def shortest_edit(A, B):
    """Forward Myers loop. Returns the trace: one copy of V per value of d."""
    N, M = len(A), len(B)
    MAX = N + M
    offset = MAX + 1                     # V[offset + k] stores diagonal k (k can be negative)
    V = [0] * (2 * MAX + 3)
    trace = []

    for d in range(MAX + 1):
        for k in range(-d, d + 1, 2):
            # choose: come DOWN from k+1 (insert) or RIGHT from k-1 (delete)
            if k == -d or (k != d and V[offset + k - 1] < V[offset + k + 1]):
                x = V[offset + k + 1]            # down
            else:
                x = V[offset + k - 1] + 1        # right
            y = x - k
            # follow the snake: free diagonal moves while lines match
            while x < N and y < M and A[x] == B[y]:
                x += 1
                y += 1
            V[offset + k] = x
            if x >= N and y >= M:
                trace.append(V[offset - d: offset + d + 1])
                return trace
        # save only diagonals -d..d for this round (index k + d)
        trace.append(V[offset - d: offset + d + 1])
    return trace


def backtrack(trace, N, M):
    """Walk back from (N, M) to (0, 0). Returns edits as (tag, x, y) in forward order."""
    x, y = N, M
    edits = []
    for d in range(len(trace) - 1, -1, -1):
        if d == 0:
            while x > 0 and y > 0:                   # the first snake
                edits.append(("=", x - 1, y - 1))
                x -= 1
                y -= 1
            break

        prev = trace[d - 1]                          # V after round d-1, index k + (d-1)
        k = x - y
        if k == -d or (k != d and prev[k - 1 + d - 1] < prev[k + 1 + d - 1]):
            prev_k = k + 1                           # we came down
        else:
            prev_k = k - 1                           # we came right
        prev_x = prev[prev_k + d - 1]
        prev_y = prev_x - prev_k

        while x > prev_x and y > prev_y:             # undo the snake
            edits.append(("=", x - 1, y - 1))
            x -= 1
            y -= 1
        if x == prev_x:
            edits.append(("+", x, y - 1))            # down move = insert B[y-1]
        else:
            edits.append(("-", x - 1, y))            # right move = delete A[x-1]
        x, y = prev_x, prev_y

    edits.reverse()
    return edits


def diff_lines(a, b):
    """Return a list of (tag, line) with tag in ' ', '-', '+'."""
    n, m = len(a), len(b)

    # speed trick 1: skip the common start and common end
    start = 0
    while start < n and start < m and a[start] == b[start]:
        start += 1
    end_a, end_b = n, m
    while end_a > start and end_b > start and a[end_a - 1] == b[end_b - 1]:
        end_a -= 1
        end_b -= 1

    # speed trick 2: turn each distinct line into a small integer
    ids = {}
    A = [ids.setdefault(line, len(ids)) for line in a[start:end_a]]
    B = [ids.setdefault(line, len(ids)) for line in b[start:end_b]]

    result = [(" ", a[i]) for i in range(start)]
    if A or B:
        trace = shortest_edit(A, B)
        for tag, x, y in backtrack(trace, len(A), len(B)):
            if tag == "=":
                result.append((" ", a[start + x]))
            elif tag == "-":
                result.append(("-", a[start + x]))
            else:
                result.append(("+", b[start + y]))
    result.extend((" ", a[i]) for i in range(end_a, n))
    return result

def to_ranges(indexes):
    """Turn sorted positions like [3,4,5,9] into '3-6,9-10'. Empty -> '.'"""
    if not indexes:
        return "."
    parts = []
    start = prev = indexes[0]
    for i in indexes[1:]:
        if i == prev + 1:                    # touching -> same range
            prev = i
        else:
            parts.append(f"{start}-{prev + 1}")   # end is not included
            start = prev = i
    parts.append(f"{start}-{prev + 1}")
    return ",".join(parts)


def char_ranges(old_line, new_line):
    """Myers on the characters of one line pair. Returns (old ranges, new ranges)."""
    s = old_line.decode("utf-8")             # str indexes count code points, so 😀 = 1
    t = new_line.decode("utf-8")
    n, m = len(s), len(t)

    # skip common start and end (same trick as Part A)
    start = 0
    while start < n and start < m and s[start] == t[start]:
        start += 1
    end_s, end_t = n, m
    while end_s > start and end_t > start and s[end_s - 1] == t[end_t - 1]:
        end_s -= 1
        end_t -= 1

    A, B = s[start:end_s], t[start:end_t]
    old_idx, new_idx = [], []
    if A or B:
        for tag, x, y in backtrack(shortest_edit(A, B), len(A), len(B)):
            if tag == "-":
                old_idx.append(start + x)    # deleted character in old line
            elif tag == "+":
                new_idx.append(start + y)    # inserted character in new line
    return to_ranges(old_idx), to_ranges(new_idx)

def format_lines(edits, highlight=False):
    """Print the diff. Inside each change block, all - lines come before + lines.
    With highlight=True, add a '?' line after each paired + line."""
    out = []
    dels, ins = [], []

    def flush():
        for line in dels:
            out.append(b"-" + line + b"\n")
        for i, line in enumerate(ins):
            out.append(b"+" + line + b"\n")
            if highlight and i < len(dels):          # i-th + pairs with i-th -
                old_r, new_r = char_ranges(dels[i], line)
                out.append(f"? {old_r} | {new_r}\n".encode())
        dels.clear()
        ins.clear()

    for tag, line in edits:
        if tag == " ":
            flush()
            out.append(b" " + line + b"\n")
        elif tag == "-":
            dels.append(line)
        else:
            ins.append(line)
    flush()
    return out


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
        sys.exit(2)

    edits = diff_lines(a, b)
    out = format_lines(edits, command == "highlight")
    sys.stdout.buffer.write(b"".join(out))


if __name__ == "__main__":
    main()