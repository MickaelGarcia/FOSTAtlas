"""Database constant module."""

from __future__ import annotations

import re


# Uppercase, number after first character.
project_code_str = r"[A-Z](?:[A-Z0-9])*"
project_code_grp = rf"(?P<project_code>{project_code_str})"
project_code_grp_re = re.compile(rf"^{project_code_grp}$")

project_root_path_str = rf".*/{project_code_str}"
project_root_path_grp = rf".*/{project_code_grp}"
project_root_path_grp_re = re.compile(project_root_path_grp)

# lowercase only, three character strict.
asset_type_code_str = r"[a-z][a-z][a-z]"
asset_type_code_grp = rf"(?P<asset_type_code>{asset_type_code_str})"
asset_type_code_grp_re = re.compile(rf"^{asset_type_code_grp}$")

# lower_snake_case, number after first word.
asset_code_str = r"[a-z]+(?:_[a-z0-9]+)+"
asset_code_grp = rf"(?P<asset_code>{asset_code_str})"
asset_code_grp_re = re.compile(rf"^{asset_code_grp}$")

# lower_snake_case only.
task_code_str = r"[a-z]+(?:_[a-z]+)*"
task_code_grp = rf"(?P<task_code>{task_code_str})"
task_code_grp_re = re.compile(rf"^{task_code_grp}$")

# camelCase, number after first word.
publish_code_str = r"[a-z]+(?:[A-Z][a-z0-9]*)*"
publish_code_grp = rf"(?P<publish_code>{publish_code_str})"
publish_code_grp_re = re.compile(rf"^{publish_code_grp}$")


# lowercase only.
file_desc_str = r"[a-z]+"
file_desc_grp = rf"(?P<file_desc>{file_desc_str})"
file_desc_grp_re = rf"^{file_desc_grp}$"
