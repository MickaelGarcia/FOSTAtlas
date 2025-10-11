"""Db Error module."""

from __future__ import annotations


class MissingDbProjectError(Exception):
    """Raised when project do not exist in database."""

class MissingDbAssetTypeError(Exception):
    """Raised when asset type do not exist in database."""

class MissingDbAssetError(Exception):
    """Raised when asset do not exist in project."""

class MissingDbTaskTypeError(Exception):
    """Raised when task type do not exist in database."""

class MissingDbTaskError(Exception):
    """Raised when task do not exist in database."""

class MissingDbPublishTypeError(Exception):
    """Raised when publish type do not exist in database."""


class MissingDbPublishError(Exception):
    """Raised when publish do not exist in database."""

class DbProjectAlreadyExistError(Exception):
    """Raised when trying to create project that already exist."""

class DbAssetTypeAlreadyExistError(Exception):
    """Raised when trying to create asset type that already exist."""

class DbAssetAlreadyExistError(Exception):
    """Raised when trying to create asset that already exist."""

class DbTaskTypeAlreadyExistError(Exception):
    """Raised when trying to create task type that already exist."""

class DbTaskAlreadyExistError(Exception):
    """Raised when trying to create task that already exist."""

class DbPublishTypeAlreadyExistError(Exception):
    """Raised when trying to create publish type that already exist."""
