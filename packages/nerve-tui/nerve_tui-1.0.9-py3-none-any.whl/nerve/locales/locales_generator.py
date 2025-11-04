#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import subprocess

def update_lang(*, file: str) -> None:
    print("Updating: " + file)
    path: str = os.path.dirname(p=file)

    subprocess.run(args=['msgmerge', '--quiet', '--no-location', '--width', '512', '--backup', 'none', '--update', file, 'base.pot'], check=True)
    subprocess.run(args=['msgfmt', '-o', os.path.join(path, 'base.mo'), file], check=True)

def generate_all() -> None:
    for (root, _, files) in os.walk(top=script_dir):
        if 'LC_MESSAGES' in root and 'base.po' in files:
            update_lang(file=os.path.join(root, 'base.po'))

def generate_single_lang(*, lang_code: str) -> None:
    lang_file: str = os.path.join(script_dir, lang_code + '/LC_MESSAGES/base.po')

    if not os.path.isfile(path=lang_file):
        print("Language files not found: " + lang_file)
        sys.exit(1)

    update_lang(file=lang_file)

def main() -> None:
    os.chdir(path=script_dir)

    if len(sys.argv) == 1:
        print("Usage: " + str(sys.argv[0]) + " <language_code>")
        print("Special case 'all' for <language_code> builds all languages.")

        sys.exit(1)

    lang:          str = sys.argv[1]
    base_pot_path: str = os.path.join(script_dir, 'base.pot')

    if not os.path.isfile(path=base_pot_path):
        open(file=base_pot_path, mode='w').close()

    subprocess.run(args=['xgettext', '--join-existing', '--no-location', '--omit-header', '--keyword=tr', '-d', 'base', '-o', base_pot_path, *find_python_files()], check=True)
    generate_all() if lang == 'all' else generate_single_lang(lang_code=lang)

def find_python_files() -> list[str]:
    return [os.path.join(root, file) for (root, _, files) in os.walk(top=script_dir) for file in files if file.endswith('.py')]

if __name__ == '__main__':
    script_dir: str = os.path.dirname(p=os.path.abspath(path=__file__))
    main()
