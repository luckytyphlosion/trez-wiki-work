
class LineReader:
    __slots__ = ("_line_num", "_lines", "_filename")
    def __init__(self, lines, filename):
        self._lines = lines
        self._filename = filename
        self._line_num = 0

    def __iter__(self):
        while self._line_num < len(self._lines):
            yield self._lines[self._line_num]
            self._line_num += 1

    def __getitem__(self, index):
        return self._lines[index]

    def __len__(self):
        return len(self._lines)

    @property
    def cur_line(self):
        return self._lines[self._line_num]

    def next(self):
        self._line_num += 1
        if self._line_num < len(self._lines):
            return self._lines[self._line_num]
        else:
            return None

    def reset(self):
        self._line_num = 0

    @property
    def line_num(self):
        return self._line_num

    @property
    def filename(self):
        return self._filename

    def at_file_error(self, msg):
        raise RuntimeError(f"At {self._filename}:{self._line_num+1}: {msg}")

    def location(self):
        return f"{self._filename}:{self._line_num+1}"

    def clear_cur_line(self):
        self._lines[self._line_num] = ""

    def is_end_of_file_or_last_line(self):
        return self._line_num >= len(self._lines) - 1
