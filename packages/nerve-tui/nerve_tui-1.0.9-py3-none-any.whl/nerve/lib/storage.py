# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

# There are a few scenarios of execution:
#   1. In the git repository, where ./profiles_bck/ exist
#   2. When executing from a remote directory, but targeted a script that starts from git repository
#   3. When executing as a python -m nerve module, where profiles_bck exists one step back for library reasons.
#   (4. Add the ~/.config directory as an additional option for future reasons),
#
# And Keeping this in dict ensures that variables are shared across imports.
from typing import (TYPE_CHECKING, NotRequired, TypedDict)

if TYPE_CHECKING:
	from nerve.lib.boot import Boot  # pylint: disable=unused-import
	from nerve.lib.installer import Installer

class _StorageDict(TypedDict):
	active_boot:          NotRequired['Boot | None']
	installation_session: NotRequired['Installer']

storage: _StorageDict = {}
