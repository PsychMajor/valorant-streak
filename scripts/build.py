"""Build an Anki package with explicitly supplied local assets; no downloads."""
import argparse
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    args = parser.parse_args()
    assets = args.assets.resolve()
    addon = ROOT / 'addon'
    catalog = json.loads((addon / 'catalog.json').read_text())
    files = {}
    for pack in catalog['packs']:
        if len(pack['sounds']) != 5:
            parser.error(f"{pack['id']}: exactly five sounds are required")
        for entry in [pack['banner']] + [s['file'] for s in pack['sounds']]:
            relative = PurePosixPath(entry)
            if relative.is_absolute() or '..' in relative.parts or relative.parts[0] != 'assets':
                parser.error(f'Invalid asset path: {entry}')
            source = assets.joinpath(*relative.parts[1:]).resolve()
            if not source.is_relative_to(assets) or not source.is_file():
                parser.error(f'Missing or unsafe asset: {entry}')
            files[str(relative)] = source
    destination = ROOT / 'dist' / 'Valorant-Streak.ankiaddon'
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED) as package:
        for name in ('__init__.py', 'core.py', 'config.json', 'config.md', 'catalog.json', 'manifest.json'):
            package.write(addon / name, name)
        package.write(ROOT / 'LICENSE', 'LICENSE')
        for name, source in sorted(files.items()):
            package.write(source, name)
    print(destination)

if __name__ == '__main__':
    main()
