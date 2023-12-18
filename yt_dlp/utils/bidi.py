import enum
import unicodedata

# BDn  Definitions
# Pn   Paragraph levels
# Xn   Explicit levels and directions
# Wn   Weak types
# Nn   Neutral types
# In   Implicit levels
# Ln   Resolved levels

MAX_DEPTH = 125


@enum.unique
class BidiClass(enum.IntEnum):
    AL = 0
    AN = 1
    B = 2
    BN = 3
    CS = 4
    EN = 5
    ES = 6
    ET = 7
    FSI = 8
    L = 9
    LRE = 10
    LRI = 11
    LRO = 12
    NSM = 13
    ON = 14
    PDF = 15
    PDI = 16
    R = 17
    RLE = 18
    RLI = 19
    RLO = 20
    S = 21
    WS = 22

    def __str__(self):
        return self.name


class DirStatus(enum.IntEnum):
    Depth = 0b00_0111_1111

    NoIsolate = 0b00_0000_0000
    Isolate = 0b00_1000_0000

    Neutral = 0b00_0000_0000
    LeftToRight = 0b10_0000_0000
    RightToLeft = 0b01_0000_0000


_X6_excludes = (
    BidiClass.B, BidiClass.BN, BidiClass.RLE, BidiClass.LRE,
    BidiClass.RLO, BidiClass.LRO, BidiClass.PDF, BidiClass.RLI,
    BidiClass.LRI, BidiClass.FSI, BidiClass.PDI,
)


_X9_excludes = (
    BidiClass.RLE, BidiClass.LRE, BidiClass.RLO,
    BidiClass.LRO, BidiClass.PDF, BidiClass.BN,
)


def bidi(data: str, debug=False):
    classes_gen = map(BidiClass.__getitem__, map(unicodedata.bidirectional, data))
    bidi_classes = memoryview(bytearray(classes_gen))
    if debug:
        for index, char in enumerate(data):
            if char.isupper():
                bidi_classes[index] = BidiClass.R

    buffer = list(data)
    _do_bidi(buffer, bidi_classes)
    return "".join(buffer)


def _do_bidi(data: list[str], bidi_classes: memoryview):
    paragraph_slices = separate_paragraphs(bidi_classes)

    for paragraph_slice in paragraph_slices:
        paragraph = bidi_classes[paragraph_slice]
        paragraph_level = _first_strong_character(paragraph)
        line = ', '.join(f"{str(BidiClass(value)):>3}" for value in paragraph)
        print(f"{paragraph_level}: {line}")

        # X1 through X9
        explicit_levels = calculate_explicit_levels(paragraph, paragraph_level)
        levels = ', '.join(f"{level:>3}" for level in explicit_levels)
        print(f"   {levels}")
        # TODO: X10

        # TODO: W1, W2, W3, W4, W5, W6, W7
        # TODO: N0, N1, N2

        # I1, I2
        resolve_implicit_levels(paragraph, explicit_levels)
        # TODO: L1

        level_runs = [(1, 0, 0)]
        while True:
            levels = ', '.join(f"{level:>3}" for level in explicit_levels)
            print(f"   {levels}")
            print("   " + repr(''.join(data)))

            level_runs = list(yield_level_runs(paragraph, explicit_levels))
            max_level = max(level for level, _, _ in level_runs)
            if not max_level:
                break

            offset = paragraph_slice.start
            for level, start, stop in level_runs:
                if level != max_level:
                    continue

                source = slice(stop + offset - 1, start + offset - 1, -1)
                target = slice(start + offset, stop + offset)
                data[target] = data[source]
                for index in range(start, stop):
                    explicit_levels[index] -= 1
        # TODO: L2, L3

        print()


def yield_level_runs(bidi_classes: memoryview, embedding_levels: memoryview, *, offset: int = 0):
    items = zip(bidi_classes, embedding_levels, strict=True)

    current_level = None
    start_index = index = offset
    for index, (bidi_class, level) in enumerate(items, offset):
        if bidi_class in _X9_excludes:
            continue
        if level != current_level:
            if current_level is not None:
                yield current_level, start_index, index
            current_level = level
            start_index = index

    index += 1
    if start_index < index:
        yield current_level, start_index, index


def resolve_implicit_levels(bidi_classes: memoryview, levels: memoryview):
    for index, (bidi_class, level) in enumerate(zip(bidi_classes, levels, strict=True)):
        if level & 1:
            if bidi_class in (BidiClass.L, BidiClass.AN, BidiClass.EN):
                levels[index] += 1
        elif bidi_class == BidiClass.R:
                levels[index] += 1
        elif bidi_class in (BidiClass.AN, BidiClass.EN):
                levels[index] += 2


def _first_strong_character(data: memoryview, allow_underflow=True):
    isolate_level = 0

    for bidi_class in data:
        if bidi_class in (BidiClass.LRI, BidiClass.RLI, BidiClass.FSI):
            isolate_level += 1

        elif bidi_class == BidiClass.PDI:
            if not allow_underflow:
                return 0
            if isolate_level:
                isolate_level -= 1

        elif not isolate_level and bidi_class in (BidiClass.L, BidiClass.AL, BidiClass.R):
            return int(bidi_class != BidiClass.L)

    return 0


def separate_paragraphs(bidi_classes):
    start_index = index = 0

    for index, bidi_class in enumerate(bidi_classes, 1):
        if bidi_class == BidiClass.B:
            yield slice(start_index, index)
            start_index = index

    if start_index < index:
        yield slice(start_index, index)


class _DirStatusStack:
    def __init__(self):
        self._data = [0] * (MAX_DEPTH + 2)
        self._pointer = -1
        self.last = 0

    def push(self, value):
        self._pointer += 1
        self._data[self._pointer] = value
        self.last = value

    def pop(self):
        self._pointer -= 1
        self.last = self._data[self._pointer] if self._pointer >= 0 else 0

    def __len__(self):
        return self._pointer + 1

    @property
    def empty(self):
        return self._pointer < 0


def calculate_explicit_levels(bidi_classes: memoryview, paragraph_level: int):
    # X1
    stack = _DirStatusStack()
    stack.push(paragraph_level)

    isolate_overflows = 0
    embedding_overflows = 0
    valid_isolate_count = 0

    embedding_levels = memoryview(bytearray(len(bidi_classes)))

    for index, bidi_class in enumerate(bidi_classes):
        # X2, X3, X4, X5
        if bidi_class in (BidiClass.RLE, BidiClass.LRE, BidiClass.RLO, BidiClass.LRO):
            if bidi_class in (BidiClass.RLE, BidiClass.RLO):
                new_level = _next_odd(stack.last)
            else:  # bidi_class in (BidiClass.LRE, BidiClass.LRO)
                new_level = _next_even(stack.last)

            if new_level <= MAX_DEPTH and not isolate_overflows and not embedding_overflows:
                directional_override =(
                    DirStatus.RightToLeft if bidi_class == BidiClass.RLO
                    else DirStatus.LeftToRight if bidi_class == BidiClass.LRO
                    else DirStatus.Neutral)
                stack.push(new_level | directional_override)

            elif not isolate_overflows:
                embedding_overflows += 1

        # X5a, X5b, X5c
        elif bidi_class in (BidiClass.RLI, BidiClass.LRI, BidiClass.FSI):
            if bidi_class == BidiClass.FSI:
                paragraph_level = _first_strong_character(bidi_classes[index+1:], allow_underflow=False)
                bidi_class = (BidiClass.LRI, BidiClass.RLI)[paragraph_level]

            embedding_levels[index] = stack.last & DirStatus.Depth
            if stack.last & DirStatus.LeftToRight:
                bidi_class = bidi_classes[index] = BidiClass.L
            elif stack.last & DirStatus.RightToLeft:
                bidi_class = bidi_classes[index] = BidiClass.R

            if bidi_class == BidiClass.RLI:
                new_level = _next_odd(stack.last)
            else:  # bidi_class == BidiClass.LRI
                new_level = _next_even(stack.last)

            if new_level <= MAX_DEPTH and not isolate_overflows and not embedding_overflows:
                valid_isolate_count += 1
                stack.push(new_level | DirStatus.Isolate)
            else:
                isolate_overflows += 1

        # X6
        elif bidi_class not in _X6_excludes:
            embedding_levels[index] = stack.last & DirStatus.Depth
            if stack.last & DirStatus.LeftToRight:
                bidi_class = bidi_classes[index] = BidiClass.L
            elif stack.last & DirStatus.RightToLeft:
                bidi_class = bidi_classes[index] = BidiClass.R

        # X6a
        elif bidi_class == BidiClass.PDI:
            if isolate_overflows > 0:
                isolate_overflows -= 1
            elif valid_isolate_count > 0:
                embedding_overflows = 0
                while not stack.last & DirStatus.Isolate:
                    stack.pop()
                stack.pop()
                valid_isolate_count -= 1

            embedding_levels[index] = stack.last & DirStatus.Depth
            if stack.last & DirStatus.LeftToRight:
                bidi_class = bidi_classes[index] = BidiClass.L
            elif stack.last & DirStatus.RightToLeft:
                bidi_class = bidi_classes[index] = BidiClass.R

        # X7
        elif bidi_class == BidiClass.PDF:
            if isolate_overflows > 0:
                pass
            elif embedding_overflows > 0:
                embedding_overflows -= 1
            elif not stack.last & DirStatus.Isolate and len(stack) >= 2:
                stack.pop()

        # X8
        # XXX: What is this suppose to do??

        # X9
        # We will ignore RLE, LRE, RLO, LRO, PDF, and BN later in the process

    return embedding_levels


def _next_odd(dir_status: int):
    return (dir_status & DirStatus.Depth) + 1 | 1


def _next_even(dir_status: int):
    return (dir_status & DirStatus.Depth) + 2 & 0b111_1110


if __name__=="__main__":
    arabic = "\N{Arabic Letter Alef} \N{Arabic Letter Khah}"
    hebrew = "\N{Hebrew Letter Pe} \N{Hebrew Letter Nun}"
    data = "\n".join([
        "",
        "This is a\N{ACUTE ACCENT} test",
        arabic,
        f"\N{LRI}{arabic}\N{PDI}lol",
        f"\N{LRI}lol\N{PDI}{arabic}",
        f"\N{LRI}lol{arabic}",
        f"\N{LRI}lol\N{PDI}lol",
        f"this {arabic} work",
        f"this {hebrew} work",
    ])
    debug_trans = str.maketrans("><=", "\N{LRI}\N{RLI}\N{PDI}")
    debug_rev_trans = str.maketrans("\N{LRI}\N{RLI}\N{PDI}", "><=")

    data = "he said “<car MEANS CAR=.” “<IT DOES=”, she agreed."

    print(repr(data))
    result = bidi(data.translate(debug_trans))
    print(repr(result.translate(debug_rev_trans)))
