"""Definition of rule based proxy models.

Here is an exemple of use:

Define the models:
>>> model = MyModel()
>>> view = MyView()
>>> rule_model = RuleFilterProxyModel()
>>> rule_model.setSourceModel(model)
>>> view.setModel(rule_model)

Define a function rule to filter the model
Here we want to keep the rows where the model data is in the rule types.
>>> type_is_rule = FuncFilterRule(
>>>     qtc.Qt.UserRole + 1,
>>>     lambda rule_types, model_type: model_type in rule_types, ["type1", "type2"]
>>> )
>>> rule_model.add_filter_rule(type_is_rule)

By default, the rule is active and will filter the model, but you can deactivate it:
>>> type_is_rule.rule_active = False
>>> rule_model.invalidateFilter()

Your model is not filtered anymore.

You can also activate/deactivate all the filters on th model:
>>> rule_model.set_rule_filters_enabled(False)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Generic
from typing import TypeVar
from typing import override

from Qt import QtCore as qtc


if TYPE_CHECKING:
    from collections.abc import Callable

T_model = TypeVar("T_model")


class FilterRule(Generic[T_model], qtc.QObject):
    """A rule for filtering a model."""

    modified = qtc.Signal()

    def __init__(self, role: int | qtc.Qt.ItemDataRole, rule_active: bool = True):
        super().__init__()
        self._role = role
        self._active = rule_active

    def is_enabled(self) -> bool:
        """Return whether the rule is enabled or not."""
        return self._active

    def enable(self):
        """Enable the rule."""
        self._active = True
        self.modified.emit()

    def disable(self):
        """Disable the rule."""
        self._active = False
        self.modified.emit()

    @property
    def role(self) -> qtc.Qt.ItemDataRole:
        """Return the role to use for the rule."""
        return self._role

    def accept_row(self, _: T_model):
        """Return whether the rule accept the row."""
        return True


T_rule = TypeVar("T_rule")


class FuncFilterRule(Generic[T_rule, T_model], FilterRule[T_model]):
    """A function based filter rule."""

    def __init__(
        self,
        role: int | qtc.Qt.ItemDataRole,
        func: Callable[[T_rule, T_model], bool],
        value: T_rule,
        rule_active: bool = True,
    ):
        super().__init__(role, rule_active)
        self._func = func
        self._value = value

    def get_value(self) -> T_rule:
        """Return the value of the rule filter."""
        return self._value

    def set_value(self, value: T_rule):
        """Set the value to filter against."""
        self._value = value
        self.modified.emit()

    def accept_row(self, model_data: T_model):
        """Implement the logic to accept the row of the model."""
        return self._func(self._value, model_data)


class EqualFilterRule(FuncFilterRule[T_rule, T_model]):
    """Accept the row if the value is equal."""

    def __init__(self, role: int, value: T_rule | None):
        super().__init__(
            role=role,
            func=lambda rval, mval: rval is None or rval == mval,
            value=value,
        )


class ActiveFilterRule(FilterRule[T_model]):
    """Activeness filter."""

    def __init__(
        self,
        role: int | qtc.Qt.ItemDataRole,
        active_only: bool = True,
        rule_active: bool = True,
    ):
        super().__init__(role, rule_active)
        self._active_only = active_only

    def is_active_only(self) -> bool:
        """Return the value of the filter."""
        return self._active_only

    def set_active_only(self, value: bool):
        """Set the active only state of the rule."""
        self._active_only = value
        self.modified.emit()

    def toggle(self):
        """Change the value of the rule."""
        self.set_active_only(not self.is_active_only())

    def accept_row(self, model_data: T_model):
        """Accept the row implementation."""
        return not self._active_only or (self._active_only and model_data)


class RuleFilterProxyModel(qtc.QSortFilterProxyModel):
    """Filter proxy model based on rules."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rules: list[FilterRule] = []

    def add_filter_rule(self, rule: FilterRule, auto_invalidate: bool = False):
        """Set the role used to filter the activeness."""
        self._rules.append(rule)
        if auto_invalidate:
            rule.modified.connect(self.invalidateFilter)

    def add_filter_rules(self, rules: list[FilterRule], auto_invalidate: bool = False):
        """Set the role used to filter the activeness."""
        self._rules.extend(rules)
        if auto_invalidate:
            for rule in rules:
                rule.modified.connect(self.invalidateFilter)

    def set_rule_filters_enabled(self, enabled: bool):
        """Set the activeness of filters."""
        for rule in self._rules:
            rule.enable() if enabled else rule.disable()

    @override
    def filterAcceptsRow(self, source_row, source_parent):
        """Filter the rows to keep the rows that match the active state."""
        super_accept = super().filterAcceptsRow(source_row, source_parent)

        active_rules = [rule for rule in self._rules if rule.is_enabled()]

        if not active_rules or not super_accept:
            return super_accept

        source_index = self.sourceModel().index(source_row, 0, source_parent)

        for rule in active_rules:
            model_value = self.sourceModel().data(source_index, role=rule.role)
            rule_accept = rule.accept_row(model_value)
            if not rule_accept:
                return False

        return True
