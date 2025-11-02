"""StandAlone models node oriented."""

from __future__ import annotations

from typing import TYPE_CHECKING

from Qt import QtCore as qtc


if TYPE_CHECKING:
    from collections.abc import Iterator


def _iter_indices(
    model: qtc.QAbstractItemModel,
    columns: list[int] | None = None,
    parent_index: qtc.QModelIndex | None = None,
    recursive: bool = False,
) -> Iterator[qtc.QModelIndex]:
    """Iterate over given model indices.

    Args:
        model: Model to iter indices.
        columns: column of indices.
        parent_index: Index to start.
        recursive: is recursive.

    Yields:
        Indices of the model.
    """
    if parent_index is None:
        parent_index = qtc.QModelIndex()

    if isinstance(model, qtc.QAbstractListModel):
        columns = [0]

    columns = list(range(model.columnCount(parent_index))) if columns is None else columns

    row_count = model.rowCount(parent_index)

    for row in range(row_count):
        index0 = model.index(row, 0, parent_index)
        for column in columns:
            index = model.index(row, column, parent_index)
            yield index

        if recursive:
            yield from _iter_indices(model, columns, index0, recursive)


def iter_indices(
    model: qtc.QAbstractItemModel,
    column: int = 0,
    parent_index: qtc.QModelIndex | None = None,
    recursive: bool = False,
) -> Iterator[qtc.QModelIndex]:
    """Iterate over given model indices.

    Args:
        model: Model to iter indices.
        column: column of indices.
        parent_index: Index to start.
        recursive: is recursive.

    Yields:
        Indices of the model.
    """
    yield from _iter_indices(
        model,
        columns=[column],
        parent_index=parent_index,
        recursive=recursive,
    )
