# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from pathlib import Path
from shutil import copy2

from nerve.lib.models.packages import Repository

class PacmanConfig:
    def __init__(self, target: Path | None) -> None:
        self._config_path: Path = Path("/etc") / "pacman.conf"
        self._config_remote_path: Path | None = target / "etc" / "pacman.conf" if target else None

        self._repositories: list[Repository] = []

    def enable(self, repo: Repository | list[Repository]) -> None:
        if not isinstance(repo, list):
            repo = [repo]

        self._repositories += repo

    def apply(self) -> None:
        if not self._repositories:
            return

        repos_to_enable: list[str] = []

        for repo in self._repositories:
            repos_to_enable.extend(['core-testing', 'extra-testing', 'multilib-testing']) if repo == Repository.Testing else repos_to_enable.append(repo.value)  # type: ignore

        content: list[str] = self._config_path.read_text().splitlines(keepends=True)

        for (row, line) in enumerate(content):
            # Check if this is a commented repository section that needs to be enabled
            match: re.Match[str] = re.match(pattern=r'^#\s*\[(.*)\]', string=line)  # type: ignore

            if match and match.group(1) in repos_to_enable:
                # uncomment the repository section line, properly removing # and any spaces
                content[row] = re.sub(pattern=r'^#\s*', repl='', string=line)

                # also uncomment the next line (Include statement) if it exists and is commented
                if ((row + 1) < len(content)) and content[row + 1].lstrip().startswith('#'):
                    content[row + 1] = re.sub(pattern=r'^#\s*', repl='', string=content[row + 1])

        # Write the modified content back to the file
        with open(file=self._config_path, mode='w') as f:
            f.writelines(content)

    def persist(self) -> None:
        if self._repositories and self._config_remote_path:
            copy2(src=self._config_path, dst=self._config_remote_path)
