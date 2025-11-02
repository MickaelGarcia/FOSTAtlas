"""Definition of a proxy model that can group elements from a table model.

This module provides a set of classes to group rows from a QAbstractTableModel
into a hierarchical structure using rules. It includes support for recursive
grouping, aggregation of data, and integration with Qt's model/view system.
"""

from __future__ import annotations

import abc
import collections

from typing import TYPE_CHECKING
from typing import Any

from Qt import QtCore as qtc


if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Generator
    from collections.abc import Iterable
    from collections.abc import Iterator


class GroupItem:
    """Internal item stored in the group proxy model.

    Represents a node in the grouped hierarchy, which may either reference
    a source model row or act as a container for other grouped items.
    """

    def __init__(
        self,
        row: int,
        source_model_row: int = -1,
        parent: GroupItem | None = None,
        grouping_rule: GroupingRule | None = None,
    ):
        """Initialize the group item.

        Args:
            row: Row index of this item within its parent.
            source_model_row: Row index in the source model (-1 if group node).
            parent: Parent group item, or None if root.
            grouping_rule: Rule used to group this item.
        """
        self._children = []
        self._row = row
        self._src_row = source_model_row
        self._parent = parent
        self._rule = grouping_rule

        if self._parent:
            self._parent._children.append(self)

    def has_child(self, index: int) -> bool:
        """Return True if this item has a child at the given index."""
        return index < len(self._children)

    def child(self, index: int) -> GroupItem:
        """Return the child item at the given index."""
        return self._children[index]

    def child_count(self) -> int:
        """Return the number of child items."""
        return len(self._children)

    def clear(self) -> None:
        """Remove all child items."""
        self._children = []

    @property
    def parent(self) -> GroupItem | None:
        """Return the parent of the item."""
        return self._parent

    @property
    def row(self) -> int:
        """Return the row index within the proxy model."""
        return self._row

    @property
    def source_row(self) -> int:
        """Return the corresponding row index in the source model."""
        return self._src_row

    @property
    def rule(self) -> GroupingRule | None:
        """Return the grouping rule applied to this item."""
        return self._rule

    def is_mapping_source(self) -> bool:
        """Return True if this item directly maps to a source row."""
        return self._src_row != -1

    def iter_source_rows(self) -> Iterator[int]:
        """Iterate recursively over all source row indices of this group."""
        if self.is_mapping_source():
            yield self._src_row
            return

        for child in self._children:
            yield from child.iter_source_rows()


class AggregateRule(qtc.QObject):
    """Represents an aggregation rule for a specific column and role."""

    def __init__(
        self,
        column: int,
        role: qtc.Qt.ItemDataRole,
        agg_column: int | None = None,
        agg_role: qtc.Qt.ItemDataRole | None = None,
        aggregator: Callable[[Generator[Any, None, None]], Any] | None = None,
    ):
        """Initialize the aggregation rule.

        Args:
            column: Column for which to compute aggregation.
            role: Data role to aggregate.
            agg_column: Column used for aggregation (defaults to `column`).
            agg_role: Role used for aggregation (defaults to `role`).
            aggregator: Function computing the aggregated value.
        """
        if agg_column is None:
            agg_column = column

        if agg_role is None:
            agg_role = role

        if aggregator is None:

            def aggregator(items):
                return next(items)

        self._column = column
        self._role = role
        self._agg_column = agg_column
        self._agg_role = agg_role
        self._aggregator = aggregator
        super().__init__()

    @property
    def column(self) -> int:
        """Return the column on which this rule applies."""
        return self._column

    @property
    def role(self) -> qtc.Qt.ItemDataRole:
        """Return the data role to aggregate."""
        return self._role

    @property
    def aggregate_column(self) -> int:
        """Return the column used for aggregation."""
        return self._agg_column

    @property
    def aggregate_role(self) -> qtc.Qt.ItemDataRole:
        """Return the role used for aggregation."""
        return self._agg_role

    def aggregate(self, item_generator: Generator[Any, None, None]) -> Any:
        """Apply the aggregator to the given items."""
        return self._aggregator(item_generator)


class AbstractAggregator(abc.ABC):
    """Abstract base class for data aggregation handlers."""

    @abc.abstractmethod
    def aggregate_data(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
        role: qtc.Qt.ItemDataRole,
    ):
        """Aggregate and return data for the given item."""

    @abc.abstractmethod
    def set_aggregate_data(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
        value: Any,
        role: qtc.Qt.ItemDataRole,
    ):
        """Set aggregated data for the given item."""

    @abc.abstractmethod
    def aggregate_flags(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
    ):
        """Aggregate and return item flags."""

    def flags(
        self,
        model: GroupingProxyModel,
        index: qtc.QModelIndex,
    ):
        """Return combined flags for a grouped or source item."""
        if not index.isValid():
            return None

        item = index.internalPointer()
        assert isinstance(item, GroupItem)

        src_model = model.sourceModel()
        children_count = model.rowCount(index)

        if not children_count:
            return src_model.flags(model.mapToSource(index))

        return self.aggregate_flags(src_model, item, index.column())

    def data(
        self,
        model: GroupingProxyModel,
        index: qtc.QModelIndex,
        role: qtc.Qt.ItemDataRole,
    ):
        """Return aggregated or source data depending on group level."""
        item = index.internalPointer()
        assert isinstance(item, GroupItem)

        src_model = model.sourceModel()
        children_count = model.rowCount(index)

        if not children_count:
            return src_model.data(model.mapToSource(index), role)

        return self.aggregate_data(src_model, item, index.column(), role)

    def set_data(
        self,
        model: GroupingProxyModel,
        index: qtc.QModelIndex,
        value: Any,
        role: qtc.Qt.ItemDataRole,
    ):
        """Set data for a source or grouped item."""
        item = index.internalPointer()
        assert isinstance(item, GroupItem)

        src_model = model.sourceModel()
        children_count = model.rowCount(index)

        if not children_count:
            return src_model.setData(model.mapToSource(index), value, role)

        return self.set_aggregate_data(src_model, item, index.column(), value, role)


class Aggregator(AbstractAggregator):
    """Concrete implementation of an aggregator using custom functions."""

    def __init__(self):
        """Initialize the aggregator with no configured functions."""
        self._funcs: dict[
            tuple[int, qtc.Qt.ItemDataRole],
            tuple[
                int,
                qtc.Qt.ItemDataRole,
                Callable[[Generator[Any, None, None]], Any],
            ],
        ] = {}

    def set_aggregate_func_for_column(
        self,
        column: int,
        role: qtc.Qt.ItemDataRole,
        aggregate_func: Callable[[Generator[Any, None, None]], Any],
        aggregate_column: int | None = None,
        aggregate_role: qtc.Qt.ItemDataRole | None = None,
    ) -> None:
        """Define a custom aggregation function for a column and role."""
        if aggregate_column is None:
            aggregate_column = column

        if aggregate_role is None:
            aggregate_role = role

        self._funcs[(column, role)] = (
            aggregate_column,
            aggregate_role,
            aggregate_func,
        )

    def aggregate_flags(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
    ):
        """Return default enabled/selectable flags for grouped items."""
        return qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsSelectable

    def set_aggregate_data(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
        value: Any,
        role: qtc.Qt.ItemDataRole,
    ) -> bool:
        """Prevent data modification on grouped items."""
        return False

    def aggregate_data(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
        role: qtc.Qt.ItemDataRole,
    ):
        """Compute aggregated data using registered functions."""
        agg_data = self._funcs.get((column, role))
        if not agg_data:
            return None

        agg_column, agg_role, func = agg_data
        grp_indices = (
            source_model.index(c_idx, agg_column) for c_idx in item.iter_source_rows()
        )
        return func(source_model.data(i, agg_role) for i in grp_indices)


class GroupingRule:
    """Defines how rows should be grouped in the proxy model."""

    def __init__(
        self,
        column: int,
        role: qtc.Qt.ItemDataRole = qtc.Qt.DisplayRole,
        absorb_source: bool = False,
    ):
        """Initialize the grouping rule.

        Args:
            column: Source model column used for grouping.
            role: Role used for grouping comparison.
            absorb_source: Whether to hide grouped source data.
        """
        self._aggregates: dict[
            tuple[int, qtc.Qt.ItemDataRole],
            tuple[
                int,
                qtc.Qt.ItemDataRole,
                Callable[[Generator[Any, None, None]], Any],
            ],
        ] = {}
        self._absorbed: set[tuple[int, qtc.Qt.ItemDataRole]] = set()

        self.set_aggregate_func_for_column(
            0,
            qtc.Qt.DisplayRole,
            lambda gen: next(gen),
            column,
            role,
            absorb_source,
        )
        self.set_aggregate_func_for_column(
            0,
            qtc.Qt.DecorationRole,
            lambda gen: next(gen),
            column,
            role,
            absorb_source,
        )

        self._column = column
        self._role = role
        self._sub_group_rule: GroupingRule | None = None

    def set_absorb_source(self, column: int, role: qtc.Qt.ItemDataRole, value: bool):
        """Mark whether a column/role pair should absorb source data."""
        key = (column, role)
        if not value and key in self._absorbed:
            self._absorbed.remove(key)
            return
        self._absorbed.add(key)

    def iter_absorbed_columns(self) -> Iterable[tuple[int, qtc.Qt.ItemDataRole]]:
        """Iterate over absorbed column/role pairs."""
        return iter(self._absorbed)

    def set_aggregate_func_for_column(
        self,
        column: int,
        role: qtc.Qt.ItemDataRole,
        aggregate_func: Callable[[Generator[Any, None, None]], Any],
        aggregate_column: int | None = None,
        aggregate_role: qtc.Qt.ItemDataRole | None = None,
        absorb_source: bool = False,
    ):
        """Assign an aggregation function for a specific column and role."""
        if aggregate_column is None:
            aggregate_column = column

        if aggregate_role is None:
            aggregate_role = role

        self._aggregates[(column, role)] = (
            aggregate_column,
            aggregate_role,
            aggregate_func,
        )

        if absorb_source:
            self.set_absorb_source(aggregate_column, aggregate_role, True)

    def aggregate_data(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
        role: qtc.Qt.ItemDataRole,
    ):
        """Return aggregated data computed for a group item."""
        agg_data = self._aggregates.get((column, role))
        if not agg_data:
            return None
        agg_column, agg_role, func = agg_data
        grp_indices = (
            source_model.index(c_idx, agg_column) for c_idx in item.iter_source_rows()
        )
        return func(source_model.data(i, agg_role) for i in grp_indices)

    def aggregate_flags(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
    ):
        """Return default item flags for grouped items."""
        return qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsSelectable

    def set_aggregate_data(
        self,
        source_model: qtc.QAbstractTableModel,
        item: GroupItem,
        column: int,
        value: Any,
        role: qtc.Qt.ItemDataRole,
    ) -> bool:
        """Disable editing on aggregated items."""
        return False

    def set_sub_rule(self, grouping_rule: GroupingRule) -> None:
        """Attach a sub-grouping rule for nested grouping."""
        self._sub_group_rule = grouping_rule

    @property
    def sub_rule(self) -> GroupingRule | None:
        """Return the sub-grouping rule, if any."""
        return self._sub_group_rule

    @property
    def column(self) -> int:
        """Return the column used for grouping."""
        return self._column

    @property
    def role(self) -> qtc.Qt.ItemDataRole:
        """Return the role used for grouping."""
        return self._role


class GroupingProxyModel(qtc.QAbstractProxyModel):
    """Proxy model grouping elements of a table model into a tree model."""

    def __init__(self, *args, **kwargs):
        """Initialize the grouping proxy model."""
        super().__init__(*args, **kwargs)
        self._group_rule: GroupingRule | None = None
        self._grouped = False
        self._root = GroupItem(0)
        self._absorbed: set[tuple[int, qtc.Qt.ItemDataRole]] = set()

    def invalidate(self) -> None:
        """Rebuild the proxy model structure from the source model."""
        self._build_groups()

    def _recursive_build_groups(
        self,
        parent_item: GroupItem,
        src_indices: Iterable[qtc.QModelIndex],
        group_rule: GroupingRule | None,
    ):
        """Recursively construct groups based on the grouping rule."""
        if group_rule is None:
            for row, src_index in enumerate(src_indices):
                GroupItem(
                    row,
                    src_index.row(),
                    parent=parent_item,
                )
            return

        for absorbed_key in group_rule.iter_absorbed_columns():
            self._absorbed.add(absorbed_key)

        sub_rule = group_rule.sub_rule
        model = self.sourceModel()
        index_by_group = collections.defaultdict(list)

        for idx in src_indices:
            group_value = model.data(idx, group_rule.role)
            index_by_group[group_value].append(idx)

        for k, (_, grp_indices) in enumerate(index_by_group.items()):
            group_item = GroupItem(
                k,
                parent=parent_item,
                grouping_rule=group_rule,
            )
            self._recursive_build_groups(group_item, grp_indices, sub_rule)

    def _build_groups(self) -> None:
        """Rebuild the entire group tree structure."""
        src_model = self.sourceModel()
        if not src_model:
            return
        self.beginResetModel()
        self._root.clear()
        self._absorbed = set()

        if not self._grouped or not self._group_rule:
            for row in range(src_model.rowCount()):
                GroupItem(row, row, parent=self._root)
            self.endResetModel()
            return

        src_indices = (
            src_model.index(row, self._group_rule.column)
            for row in range(src_model.rowCount())
        )
        self._recursive_build_groups(self._root, src_indices, self._group_rule)
        self.endResetModel()

    def set_group_rule(self, group_rule: GroupingRule, invalidate: bool = False):
        """Assign a new grouping rule to the model."""
        self._group_rule = group_rule
        if invalidate:
            self._build_groups()
        self.group()

    def ungroup(self) -> None:
        """Disable grouping and flatten the proxy model."""
        self._grouped = False
        self._build_groups()

    def group(self) -> None:
        """Enable grouping and rebuild the structure."""
        self._grouped = True
        self._build_groups()

    def is_grouped(self) -> bool:
        """Return True if the model is currently grouped."""
        return self._grouped
