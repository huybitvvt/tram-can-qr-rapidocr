"""Windows packaging smoke: real offline OCR + window-only screenshot.

Developer tool; reports/screenshots go only to an explicitly supplied output directory.
The installed app's --self-test path never writes a capture or a report.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
import hashlib
import os
from pathlib import Path
import subprocess
import time

from PIL import ImageGrab


def window_for_pid(pid):
    user32 = ctypes.windll.user32
    found = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]

    @callback_type
    def visit(hwnd, _):
        window_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if window_pid.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    user32.EnumWindows(visit, 0)
    return found[0] if found else None


def snapshot(root):
    return {str(p.relative_to(root)): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()} if root.exists() else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--expect', default='1.20')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sandbox = args.out/'isolated-user'
    for folder in ('Local', 'Roaming', 'Profile', 'work'):
        (sandbox/folder).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, LOCALAPPDATA=str(sandbox/'Local'), APPDATA=str(sandbox/'Roaming'),
               USERPROFILE=str(sandbox/'Profile'), PYTHONDONTWRITEBYTECODE='1')
    command = [str(args.exe.resolve())]
    command += ['--self-test', str(args.image.resolve()), '--expect-weight', args.expect]
    before = snapshot(sandbox)
    app_before = snapshot(args.exe.resolve().parent)
    def input_hash():
        with args.image.open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    original_hash = input_hash()
    process = subprocess.Popen(command, cwd=sandbox/'work', env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    captured = False
    deadline = time.monotonic()+40
    while process.poll() is None and time.monotonic() < deadline:
        hwnd = window_for_pid(process.pid)
        if hwnd:
            # Replace an early loading screenshot with the fully rendered reading.
            ImageGrab.grab(window=hwnd).save(args.out/'window.png')
            captured = True
        time.sleep(.5)
    try:
        stdout, stderr = process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        raise RuntimeError('GUI failed to exit within 40s')
    after = snapshot(sandbox)
    app_unchanged = app_before == snapshot(args.exe.resolve().parent)
    input_unchanged = original_hash == input_hash()
    report = {'exit_code': process.returncode, 'screenshot': captured,
              'application_created_or_modified_user_files': before != after,
              'new_or_modified': [k for k in after if before.get(k) != after[k]],
              'deleted': [k for k in before if k not in after],
              'stdout': stdout.decode('utf-8', 'replace')[-2000:],
              'stderr': stderr.decode('utf-8', 'replace')[-2000:],
              'offline_python_guard': True, 'expected_weight': args.expect}
    report.update(install_files_unmodified=app_unchanged, input_image_unmodified=input_unchanged)
    (args.out/'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if process.returncode == 0 and before == after and captured and app_unchanged and input_unchanged else 1


if __name__ == '__main__':
    raise SystemExit(main())
