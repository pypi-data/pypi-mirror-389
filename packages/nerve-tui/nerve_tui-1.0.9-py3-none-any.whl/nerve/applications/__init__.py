# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import (ABC, abstractmethod)
from typing import Any

class Application(ABC):
    @abstractmethod
    def install(self, *args: Any, **kwargs: Any) -> None:
        pass
