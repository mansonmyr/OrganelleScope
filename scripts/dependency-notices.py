"""Collect licence notices for declared runtime dependencies and the actual frozen module graph.

Run after freezing, using the same Python environment as PyInstaller. Generated files
stay outside Git and are included in each platform's installer and build artifact.
"""
import ast
import importlib.metadata as md
import json
from pathlib import Path
import re
import sysconfig
import tomllib
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]

def normalized(name):
    return re.sub(r'[-_.]+', '-', name).lower()

def collect_python():
    graph = ROOT / 'backend/build/organellescope-backend/PYZ-00.toc'
    if not graph.is_file():
        raise SystemExit('Freeze the backend before generating its dependency notices.')
    modules = {row[0].split('.')[0] for row in ast.literal_eval(graph.read_text())[1]}
    providers = md.packages_distributions()
    pending = list(tomllib.loads((ROOT/'backend/pyproject.toml').read_text())['project']['dependencies'])
    pending.extend(name for module in modules for name in providers.get(module, []))
    seen, inventory, sections = set(), [], []
    while pending:
        requirement = Requirement(pending.pop())
        if requirement.marker and not requirement.marker.evaluate({'extra': ''}):
            continue
        name = normalized(requirement.name)
        if name in seen or name == 'organellescope-backend':
            continue
        seen.add(name)
        dist = md.distribution(requirement.name)
        pending.extend(dist.requires or [])
        texts = []
        for item in dist.files or []:
            path = Path(item)
            if '.dist-info' not in str(path) or not any(t in str(path).lower() for t in ('license','copying','notice')):
                continue
            file = dist.locate_file(item)
            if file.is_file() and file.stat().st_size < 4*1024**2:
                try:
                    text = file.read_text(encoding='utf-8')
                except UnicodeError:
                    continue
                texts.append((str(path), text))
        license_name = dist.metadata.get('License-Expression') or dist.metadata.get('License') or 'See upstream project and notices'
        inventory.append({'name':dist.metadata['Name'], 'version':dist.version, 'license':license_name, 'notice_files':[n for n,_ in texts]})
        sections.append(f"\n===== {dist.metadata['Name']} {dist.version} =====\nLicence metadata: {license_name}\n" + ''.join(f'\n--- {n} ---\n{t}\n' for n,t in texts))
    stdlib = Path(sysconfig.get_path('stdlib'))/'LICENSE.txt'
    if not stdlib.is_file():
        import sys
        stdlib = Path(sys.base_prefix)/'LICENSE.txt'
    if not stdlib.is_file():
        raise SystemExit('Python runtime licence not found; do not publish an incomplete notice bundle.')
    sections.insert(0, '\n===== Python runtime =====\n'+stdlib.read_text(encoding='utf-8'))
    return sorted(inventory, key=lambda d:d['name'].lower()), sections

def collect_javascript():
    packages = json.loads((ROOT/'frontend/package-lock.json').read_text())['packages']
    inventory, sections = [], []
    for relative, info in sorted(packages.items()):
        if not relative or info.get('dev') or info.get('link'):
            continue
        folder = ROOT/'frontend'/relative
        if not folder.is_dir():
            if info.get('optional'): continue
            raise SystemExit(f'Install frontend dependencies before collecting notices: {relative}')
        manifest = json.loads((folder/'package.json').read_text())
        name, version = manifest['name'], manifest['version']
        texts=[]
        for file in sorted(folder.iterdir()):
            if file.is_file() and file.name.lower().startswith(('license','licence','copying','notice')):
                texts.append((file.name,file.read_text(encoding='utf-8',errors='replace')))
        inventory.append({'name':name, 'version':version, 'license':manifest.get('license',info.get('license','See upstream project')), 'notice_files':[n for n,_ in texts]})
        sections.append(f'\n===== {name} {version} =====\nLicence metadata: {inventory[-1]["license"]}\n' + ''.join(f'\n--- {n} ---\n{t}\n' for n,t in texts))
    return inventory, sections

def main():
    out=ROOT/'build/notices';out.mkdir(parents=True,exist_ok=True)
    python, ptexts=collect_python();javascript,jtexts=collect_javascript()
    header='Generated per native build. Python includes declared runtime dependencies, actual frozen module providers and their dependencies (a conservative closure); JavaScript includes installed production frontend dependencies. This inventory is not a claim every package is used by every workflow. Electron supplies its own LICENSE and Chromium notices.\n'
    (out/'PYTHON_DEPENDENCY_NOTICES.txt').write_text(header+''.join(ptexts),encoding='utf-8')
    (out/'JAVASCRIPT_DEPENDENCY_NOTICES.txt').write_text(header+''.join(jtexts),encoding='utf-8')
    (out/'DEPENDENCIES.json').write_text(json.dumps({'scope':header.strip(),'python':python,'frontend':javascript},indent=2)+'\n',encoding='utf-8')
    print(f'Collected notices: {len(python)} Python distributions; {len(javascript)} frontend packages.')

if __name__=='__main__':main()
