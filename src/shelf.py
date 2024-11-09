from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Any, Dict

from scene import Simple3dScene

HORIZONTAL_OVERLAP = 0.2  # cm


@dataclass
class Compartment:
    width: float
    height: float
    vertical_span: int = 1


class RowAlignment(Enum):
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class Row:
    alignment: RowAlignment
    indent: float
    compartments: List[Optional[Compartment]]


@dataclass
class Point:
    x: float
    y: float

    def add_x(self, width: float):
        self.x += width

    def add_y(self, height: float):
        self.y += height

    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)


@dataclass
class Rect(Point):
    width: float
    height: float

    @property
    def top(self):
        return self.y + self.height

    @property
    def right(self):
        return self.x + self.width


@dataclass
class Interval:
    start: float
    width: float

    @property
    def end(self):
        return self.start + self.width


class Shelf(Simple3dScene):

    def __init__(self, depth: float, board_thickness: float, backboard_thickness: float):
        super().__init__()
        self.depth = depth
        self.board_thickness = board_thickness
        self.backboard_thickness = backboard_thickness
        self.backboard_indent = self.backboard_thickness / 4
        self.rows: List[Row] = []
        self.material = self.create_simple_material((0.9, 0.9, 0.9))

    def add_row(self, row: Row):
        self.rows.append(row)

    def render(self, filename: str):
        if not self.rows:
            return

        rect_stack = self.calculate_rect_stack()
        for row_index, row in enumerate(rect_stack):
            self.render_row(row_index, row, rect_stack)

        self.write(filename)

    def render_row(self, row_index, row, rect_stack):
        self.render_vertical_and_backboards(row)
        self.render_bottom_boards(row_index, row, rect_stack)
        self.render_top_boards(row_index, row, rect_stack)

    def render_top_boards(self, row_index, row, rect_stack):
        # top boards
        if row_index == len(rect_stack) - 1:
            start_x = None
            start_y = None
            last_right = None
            for rect in row:
                if rect:
                    if start_x is None:
                        start_x = row[0].x
                        start_y = row[0].top

                    last_right = rect.right
                    if rect.y == start_y:
                        continue
                    else:
                        self.add_horizontal_board(Point(start_x, start_y), rect.x - start_x)
                        start_x = rect.x
                        start_y = rect.top

                # if gap
                else:
                    self.add_horizontal_board(Point(start_x, start_y), last_right - start_x)
                    start_x = None
                    start_y = None

            self.add_horizontal_board(Point(start_x, start_y), last_right - start_x)

        # if row ends are smaller
        is_row_end_smaller = False
        row_end_top = None
        row_end = None
        row_end_start = None
        for rect in reversed(row):
            if rect:
                if not row_end:
                    row_end = rect.right
                    row_end_top = rect.top
                    row_end_start = rect.x

                if rect.top > row_end_top:
                    is_row_end_smaller = True
                    break
                else:
                    row_end_start = rect.x

            else:
                break

        if is_row_end_smaller:
            self.add_horizontal_board(Point(row_end_start, row_end_top), row_end - row_end_start)

        # TODO: if the row start is smaller

    def render_bottom_boards(self, row_index: int, row: List[Optional[Rect]], rect_stack: List[List[Optional[Rect]]]):
        # bottom boards
        start_x = min(row[0].x, rect_stack[row_index - 1][0].x if row_index > 0 else row[0].x)
        start_y = row[0].y
        last_right = None
        for rect in row:
            if rect:
                # if we start after a gyp
                if not start_x:
                    start_x = rect.x
                    start_y = rect.y

                last_right = rect.right
                if rect.y == start_y:
                    continue
                else:
                    self.add_horizontal_board(Point(start_x, start_y), rect.x - start_x)
                    start_x = rect.x
                    start_y = rect.y

            # if gap
            else:
                if last_right:
                    self.add_horizontal_board(Point(start_x, start_y), last_right - start_x)
                    start_x = None
                    start_y = None
        last_right = row[-1].right
        # if row below is longer:
        if row_index > 0:
            last_index_below = None
            for index, rect in enumerate(rect_stack[row_index - 1]):
                if rect and rect.x <= last_right <= rect.right:
                    last_index_below = index

            if last_index_below is not None:
                last_index_top = rect_stack[row_index - 1][last_index_below].top
                for index, rect in enumerate(rect_stack[row_index - 1][last_index_below + 1:]):
                    if rect:
                        if rect.top == last_index_top:
                            last_index_below += 1
                        else:
                            break

                last_right_below = rect_stack[row_index - 1][last_index_below].right
                last_right = max(last_right, last_right_below)
        self.add_horizontal_board(Point(start_x, start_y), last_right - start_x)

    def render_vertical_and_backboards(self, row: List[Optional[Rect]]):
        for index, rect in enumerate(row):
            if rect:
                # backboard
                self.add_box(start=(rect.x + self.backboard_indent,
                                    rect.y + self.backboard_indent,
                                    self.backboard_indent),
                                    # self.depth - self.backboard_thickness - self.backboard_indent),
                             dimensions=(rect.width - 2 * self.backboard_indent,
                                         rect.height - 2 * self.backboard_indent,
                                         self.backboard_thickness),
                             material=self.material)

                # left board
                if index == 0:
                    self.add_vertical_board(Point(rect.x, rect.y), rect.height)

                # right board
                self.add_vertical_board(Point(rect.right, rect.y), rect.height)

    def calculate_rect_stack(self) -> List[List[Optional[Rect]]]:
        rect_stack: List[List[Rect]] = []
        interval_stack = self.calculate_intervals()

        start_y = 0
        for row_index, row in enumerate(self.rows):
            rects: List[Optional[Rect]] = []
            max_height = max(row.compartments, key=lambda c: c.height if c else 0).height
            for index, compartment in enumerate(row.compartments):
                if compartment:
                    interval = interval_stack[row_index][index]

                    # if first row
                    if row_index == 0:
                        if row.alignment == RowAlignment.TOP:
                            y = start_y + max_height - compartment.height
                            rects.append(Rect(interval.start, y, interval.width, compartment.height))

                    # for other rows just check the previous row for the height
                    else:
                        below_rects = find_overlapping_rects(interval, rect_stack[row_index - 1])
                        if not below_rects:
                            below_rects = [rect_stack[row_index - 1][0]]

                        y = max([r.top for r in below_rects])
                        rects.append(Rect(interval.start, y, interval.width, compartment.height))

                else:
                    rects.append(None)

            rect_stack.append(rects)

        print("Rect stack:")
        for rects in rect_stack:
            print(list(map(lambda r: f"x={r.x} y={r.y} r={r.right} t={r.top}" if r else 'gap', rects)))

        return rect_stack

    def calculate_intervals(self) -> List[List[Optional[Interval]]]:
        interval_stack = []

        start_x = 0
        for index, row in enumerate(self.rows):
            start_x = start_x + row.indent
            current_x = start_x
            intervals = []
            gap_counter = 0
            for compartment in row.compartments:
                if compartment:
                    intervals.append(Interval(current_x, compartment.width))
                    current_x += compartment.width
                else:
                    gap_counter += 1
                    intervals.append(None)
                    current_x += find_nth_span(self.rows[index - 1], gap_counter).width

            interval_stack.append(intervals)

        print("Interval stack:")
        for intervals in interval_stack:
            print(list(map(lambda i: f"{i.start} - {i.end}" if i else 'gap', intervals)))

        return interval_stack

    def add_vertical_board(self, start_point: Point, height: float):
        self.add_box(start=(start_point.x - self.board_thickness / 2, start_point.y + self.board_thickness / 2, 0),
                     dimensions=(self.board_thickness, height - self.board_thickness, self.depth),
                     material=self.material)

    def add_horizontal_board(self, start_point: Point, width: float):
        self.add_box(start=(start_point.x - self.board_thickness / 2, start_point.y - self.board_thickness / 2, 0),
                     dimensions=(width + self.board_thickness, self.board_thickness, self.depth + HORIZONTAL_OVERLAP),
                     material=self.material)


def height_offset(alignment: RowAlignment, baseline_y: float, height: float) -> Point:
    if alignment == RowAlignment.TOP:
        return Point(0, baseline_y - height)

    return Point(0, 0)


def find_nth_span(row: Row, n: int) -> Compartment:
    span_counter = 0
    for compartment in row.compartments:
        if compartment and compartment.vertical_span > 1:
            span_counter += 1
            if span_counter == n:
                return compartment

    raise ValueError(f"Row has less than {n} spanning compartments")


def find_overlapping_rects(interval: Interval, rects: List[Optional[Rect]]) -> List[Rect]:
    overlapping_rects = []
    for rect in rects:
        if rect and interval.start < rect.x + rect.width and interval.end > rect.x:
            overlapping_rects.append(rect)

    return overlapping_rects
