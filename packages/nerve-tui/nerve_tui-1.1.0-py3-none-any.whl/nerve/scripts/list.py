# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

from glob import glob
from pathlib import Path

print("The following are viable --script options:")

for script in [Path(x) for x in glob(str(Path(__file__).parent) + "/*.py")]:
    if script.stem in {'__init__', 'list'}:
        continue

    print((' ' * 4) + script.stem)
