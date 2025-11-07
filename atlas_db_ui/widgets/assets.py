"""Asset view widget module."""

from __future__ import annotations

from typing import Any

from Qt import QtWidgets as qtw
from sqlalchemy import inspect
from sqlalchemy import select

from atlas_db.context import DbQueryContext
from atlas_db.models import Asset
from atlas_db.models import Base
from atlas_db_ui.models.entity import EntityTypeTableModel
from atlas_ui.rule_proxy_model import ActiveFilterRule
from atlas_ui.rule_proxy_model import RuleFilterProxyModel


def get_entities_row(entity_type: type[Base]):
    items = []
    with DbQueryContext() as db:
        columns = entity_type.__table__.columns.keys()
        cols = [getattr(entity_type, col) for col in columns]
        stmt = select(*cols)
        assets_list = db.execute(stmt).all()
        columns_names = [f"{entity_type.__name__}.{col}" for col in columns]

        for asset in assets_list:
            asset_row = dict(zip(columns_names, asset, strict=True))

            mapper = inspect(entity_type)
            for rel in mapper.relationships:
                model = rel.mapper.class_
                rl_columns = model.__table__.columns.keys()
                cols = [getattr(model, col) for col in rl_columns]
                stmt = (
                    select(*cols)
                    .join(entity_type)
                    .filter(entity_type.id == asset_row["Asset.id"])
                )
                header = [f"{model.__name__}.{c.name}" for c in cols]

                columns_values = db.execute(stmt).all()
                for value in columns_values:
                    for index, v in enumerate(value):
                        asset_row[header[index]] = v
            items.append(asset_row)

    return items


class AssetTable(qtw.QWidget):
    """Asset table widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Widgets
        # Menu
        self._menu = qtw.QMenuBar(self)

        act_add_asset = qtw.QAction("Add Asset", self)
        act_add_asset.triggered.connect(self._on_act_add_asset_clicked)
        self._menu.addAction(act_add_asset)

        men_filters = self._menu.addMenu("Filters")

        act_active_filter = qtw.QAction("Active Only", self)
        act_active_filter.setCheckable(True)
        act_active_filter.setChecked(True)

        men_filters.addAction(act_active_filter)

        men_group_by = self._menu.addMenu("Groups by")
        grp_asset_name = qtw.QAction("Asset name", self)
        grp_asset_type = qtw.QAction("Asset type", self)

        men_group_by.addAction(grp_asset_name)
        men_group_by.addAction(grp_asset_type)

        # View
        self._view = qtw.QTreeView(self)
        self._model = EntityTypeTableModel()
        self._model.set_entities(get_entities_row(Asset))

        self._prx_rule_model = RuleFilterProxyModel()
        self._prx_rule_model.setSourceModel(self._model)

        self.active_rule = ActiveFilterRule(EntityTypeTableModel.ActiveRole)
        self._prx_rule_model.add_filter_rule(self.active_rule)

        self._view.setModel(self._prx_rule_model)

        # Layout
        lay_main = qtw.QVBoxLayout(self)
        lay_main.addWidget(self._menu)
        lay_main.addWidget(self._view)

        # Connections
        act_active_filter.triggered.connect(self.active_rule.toggle)
        self.active_rule.modified.connect(self._prx_rule_model.invalidateFilter)

        # Init
        self.active_rule.set_active_only(act_active_filter.isChecked())
        self._model.SetActive.connect(self._prx_rule_model.invalidateFilter)
        self._get_fill_options()

    def _on_act_add_asset_clicked(self):
        print("Add asset !")

    def set_assets(self, entities: list[dict[str, Any]]):
        """Set assets to view model."""
        self._model.set_entities(entities)

    def _get_fill_options(self):
        men_fill = self._menu.addMenu("Fill")
        asset_menu = men_fill.addMenu("Asset")

        asset_columns = Asset.__table__.columns.keys()
        for column in asset_columns:
            act_col = qtw.QAction(column.capitalize(), self)
            act_col.setCheckable(True)
            act_col.setChecked("_id" not in column)

            asset_menu.addAction(act_col)
