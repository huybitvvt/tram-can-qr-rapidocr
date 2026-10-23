# Build only the standalone trial; no production backend, secrets, or data.
from pathlib import Path
from importlib.metadata import distribution
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH).parent
datas = collect_data_files('rapidocr') + collect_data_files('tramcan_rapidocr')
datas += copy_metadata('rapidocr') + copy_metadata('onnxruntime')
# Preserve license texts shipped in the runtime wheels, including transitive packages.
for name in ['numpy', 'opencv-python-headless', 'Pillow', 'onnxruntime', 'rapidocr',
             'omegaconf', 'pyclipper', 'shapely', 'PyYAML', 'requests', 'tqdm', 'six',
             'colorlog', 'colorama', 'certifi', 'charset-normalizer', 'idna', 'urllib3',
             'protobuf', 'flatbuffers', 'packaging']:
    dist = distribution(name)
    for entry in dist.files or []:
        path = Path(dist.locate_file(entry))
        if path.is_file() and any(x in path.name.lower() for x in ['license', 'copying', 'notice']):
            datas.append((str(path), f'licenses/{name}/{entry.parent}'))
python_license = Path(sys.base_prefix)/'LICENSE.txt'
if python_license.is_file():
    datas.append((str(python_license), 'licenses/Python'))
for name in ['PP-OCRv6_det_small.onnx', 'PP-OCRv6_rec_small.onnx', 'manifest-small.json']:
    datas.append((str(root/'models'/name), 'models'))
datas += [(str(root/'LICENSE'), 'licenses'), (str(root/'NOTICE'), 'licenses'),
          (str(root/'licenses'), 'licenses'),
          (str(root/'docs'/'CAI-BAN-THU.md'), '.')]
a = Analysis([str(root/'packaging'/'trial_entry.py')], pathex=[str(root/'src')],
    binaries=[], datas=datas,
    hiddenimports=collect_submodules('rapidocr') + ['PIL.ImageTk', 'onnxruntime'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['torch', 'paddle', 'tensorflow', 'openvino', 'tensorrt', 'pytest', 'matplotlib',
              'IPython', 'notebook', 'pandas', 'scipy', 'sympy'],
    noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='TramCanOCRTrial',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='TramCanOCRTrial')
