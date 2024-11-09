from shelf import Shelf, Row, RowAlignment, Compartment

SHELF_DEPTH = 25  # cm
BOARD_THICKNESS = 2.5  # cm
BACKBOARD_THICKNESS = 0.5  # cm


def main():
    shelf = Shelf(
        depth=SHELF_DEPTH,
        board_thickness=BOARD_THICKNESS,
        backboard_thickness=BACKBOARD_THICKNESS,
    )

    shelf.add_row(Row(RowAlignment.TOP, 80, [
        Compartment(30, 33),
        Compartment(77, 25),
    ]))
    shelf.add_row(Row(RowAlignment.BOTTOM, -65, [
        Compartment(55, 32),
        Compartment(27, 32),
        Compartment(30, 57, vertical_span=2),
        Compartment(100, 25),
    ]))
    shelf.add_row(Row(RowAlignment.BOTTOM, -18, [
        Compartment(100, 25),
        None,
        Compartment(27, 32),
        Compartment(55, 25),
    ]))
    shelf.add_row(Row(RowAlignment.BOTTOM, 60, [
        Compartment(30, 33),
        Compartment(55, 25),
    ]))

    shelf.render("shelf.dae")


if __name__ == "__main__":
    main()
