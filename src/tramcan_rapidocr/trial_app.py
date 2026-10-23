"""Standalone factory trial. No database, captures, settings, or network service."""
import argparse
import multiprocessing as mp
from pathlib import Path
from queue import Empty
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from .trial_camera import Camera
from .parsing import parse_weight
from .trial_state import TrialSession, Viewport
from .trial_worker import Job, ReaderWorker

VERSION = '0.2.0-trial1'
BG, INK, MUTED = '#f1f5f9', '#0f172a', '#475569'
BLUE, AMBER = '#075985', '#92400e'


def bundled_models():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)/'models'
    return Path(__file__).resolve().parents[2]/'models'


class TrialApp:
    def __init__(self, root, models=None):
        self.root = root
        root.title(f'Trạm Cân OCR — Chạy thử {VERSION}')
        root.geometry('1260x790')
        root.minsize(1000, 680)
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.closed = False
        self.session = TrialSession()
        self.camera = None
        self.frame = None
        self.frame_at = 0.
        self.frame_number = 0
        self.submitted_number = -1
        self.last_submit = 0.
        self.last_result_at = 0.
        self.last_job = None
        self.auto_regions = []
        self.source = None
        self.ready = self.busy = self.selecting = False
        self.drag_start = self.drag_end = None
        self.viewport = None
        self.preview_image = self.crop_image = None
        self.reading_details = 'Chưa có kết quả'
        self._build()
        self.worker = ReaderWorker(models or bundled_models())
        root.after(50, self._tick)

    def _build(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10))
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=INK)
        style.configure('TButton', padding=(12, 8), background='#ffffff')
        style.configure('Primary.TButton', background=BLUE, foreground='white')
        style.map('Primary.TButton', background=[('active', '#0c4a6e')])
        style.configure('TCheckbutton', background=BG)
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill='both', expand=True)
        ttk.Label(container, text='TRẠM CÂN OCR  /  CHẠY THỬ TẠI XƯỞNG',
                  font=('Segoe UI', 19, 'bold')).pack(anchor='w')
        tk.Label(container, text='CHỈ THỬ NHẬN DIỆN  ·  Có thể đọc sai  ·  Không lưu phiếu, ảnh hay dữ liệu cân',
                 font=('Segoe UI', 11, 'bold'), bg='#fef3c7', fg=AMBER,
                 padx=12, pady=10, anchor='w').pack(fill='x', pady=(10, 14))

        controls = ttk.Frame(container)
        controls.pack(fill='x')
        ttk.Label(controls, text='Camera').pack(side='left', padx=(0, 6))
        self.camera_index = tk.StringVar(value='0')
        ttk.Combobox(controls, textvariable=self.camera_index,
                     values=[str(i) for i in range(10)], width=3,
                     state='readonly').pack(side='left')
        self.backend = tk.StringVar(value='DirectShow')
        ttk.Combobox(controls, textvariable=self.backend,
                     values=['DirectShow', 'Media Foundation'], width=17,
                     state='readonly').pack(side='left', padx=8)
        self.open_button = ttk.Button(controls, text='Mở camera', style='Primary.TButton',
                                      command=self.open_camera, state='disabled')
        self.open_button.pack(side='left')
        ttk.Button(controls, text='Dừng', command=self.stop).pack(side='left', padx=8)
        self.file_button = ttk.Button(controls, text='Mở ảnh thử…', command=self.open_file,
                                      state='disabled')
        self.file_button.pack(side='left')
        ttk.Button(controls, text='Hướng dẫn', command=self.help).pack(side='right')

        options = ttk.Frame(container)
        options.pack(fill='x', pady=(12, 12))
        ttk.Button(options, text='Chọn vùng số cân', command=self.select_region).pack(side='left')
        ttk.Button(options, text='Tự tìm LED đỏ', command=self.auto_region).pack(side='left', padx=8)
        self.fixed_two = tk.BooleanVar(value=True)
        ttk.Checkbutton(options, text='Cân luôn có 2 số thập phân', variable=self.fixed_two,
                        command=self.policy_changed).pack(side='left', padx=(8, 0))
        self.region_text = tk.StringVar(value='Vùng đọc: tự tìm LED đỏ')
        ttk.Label(options, textvariable=self.region_text, foreground=MUTED).pack(side='right')

        body = ttk.Frame(container)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0, minsize=320)
        body.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(body, bg='#111827', highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew', padx=(0, 16))
        self.canvas.bind('<ButtonPress-1>', self.drag_begin)
        self.canvas.bind('<B1-Motion>', self.drag_move)
        self.canvas.bind('<ButtonRelease-1>', self.drag_finish)
        panel = tk.Frame(body, bg='white', padx=14, pady=12, width=320)
        panel.grid(row=0, column=1, sticky='nsew')
        panel.grid_propagate(False)
        panel.columnconfigure(0, weight=1)
        tk.Label(panel, text='SỐ CÂN ĐỌC THỬ', bg='white', fg=MUTED,
                 font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, sticky='w')
        self.weight_text = tk.StringVar(value='—')
        tk.Label(panel, textvariable=self.weight_text, bg='white', fg=INK,
                 font=('Segoe UI', 44, 'bold')).grid(row=1, column=0, sticky='w', pady=(6, 0))
        self.unit_text = tk.StringVar(value='kg · cần đối chiếu với cân')
        tk.Label(panel, textvariable=self.unit_text, bg='white', fg=AMBER,
                 font=('Segoe UI', 10)).grid(row=2, column=0, sticky='w')
        self.result_text = tk.StringVar(value='Đang nạp bộ nhận diện…')
        tk.Label(panel, textvariable=self.result_text, bg='white', fg=BLUE,
                 font=('Segoe UI', 11, 'bold'), wraplength=280, justify='left',
                 anchor='w').grid(row=3, column=0, sticky='ew', pady=(8, 8))
        tk.Label(panel, text='VÙNG ẢNH VỪA ĐỌC', bg='white', fg=MUTED,
                 font=('Segoe UI', 9, 'bold')).grid(row=4, column=0, sticky='w')
        self.crop_canvas = tk.Canvas(panel, bg='#e2e8f0', height=70,
                                     width=280, highlightthickness=0)
        self.crop_canvas.grid(row=5, column=0, sticky='ew', pady=(6, 6))
        self.details = tk.StringVar(value='Chưa có kết quả')
        tk.Label(panel, textvariable=self.details, bg='white', fg=MUTED,
                 font=('Segoe UI', 10), wraplength=280, justify='left',
                 anchor='nw').grid(row=6, column=0, sticky='new')
        panel.rowconfigure(7, weight=1)
        ttk.Button(panel, text='Xem chuỗi OCR', command=lambda: messagebox.showinfo(
            'Chi tiết lần đọc thử', self.reading_details, parent=self.root)).grid(
                row=8, column=0, sticky='ew', pady=(8, 0))

        self.status_text = tk.StringVar(value='Đang nạp model offline. Không cần API key.')
        ttk.Label(container, textvariable=self.status_text, wraplength=1150,
                  foreground=MUTED).pack(fill='x', pady=(12, 3))
        ttk.Label(container, text=f'RapidOCR + PP-OCRv6 small · CPU · {VERSION}  |  '
                  'Đóng phần mềm cân khác trước khi mở cùng camera.',
                  foreground=MUTED, font=('Segoe UI', 9)).pack(anchor='w')

    def invalidate(self, roi=None):
        self.session.change(roi)
        self.submitted_number = -1
        self.last_job = None
        self.auto_regions = []
        self.last_result_at = 0
        self.weight_text.set('—')
        self.details.set('Chưa có kết quả cho vùng đọc này')
        self.reading_details = 'Chưa có kết quả cho vùng đọc này'
        self.crop_canvas.delete('all')
        self.crop_image = None

    def stop(self):
        if self.camera:
            self.camera.close()
            self.camera = None
        self.source = None
        self.frame = None
        self.frame_at = 0.
        self.selecting = False
        self.drag_start = self.drag_end = None
        self.canvas.configure(cursor='')
        self.invalidate()
        self.region_text.set('Vùng đọc: tự tìm LED đỏ')
        self.result_text.set('Đã dừng')
        self.status_text.set('Camera đã đóng. Không lưu ảnh hay kết quả cân.')

    def open_camera(self):
        if not self.ready:
            return
        self.stop()
        try:
            backend = cv2.CAP_DSHOW if self.backend.get() == 'DirectShow' else cv2.CAP_MSMF
            self.camera = Camera(int(self.camera_index.get()), backend)
            self.source = 'camera'
            self.result_text.set('Đang mở camera…')
            self.status_text.set('Nếu không có hình, thử Camera 1/2 hoặc đổi sang Media Foundation.')
        except Exception as error:
            self.result_text.set('Không mở được camera')
            self.status_text.set(f'Thử đóng ứng dụng đang dùng camera rồi mở lại. {error}')

    def open_file(self):
        path = filedialog.askopenfilename(title='Chọn ảnh thử (chỉ đọc)', filetypes=[
            ('Ảnh', '*.jpg *.jpeg *.png *.bmp *.webp'), ('Tất cả', '*.*')])
        if path:
            self.load_image(Path(path))

    def load_image(self, path):
        try:
            frame = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError('File không phải ảnh được hỗ trợ')
            # Bounded memory and the same pixel scale as the live camera.
            height, width = frame.shape[:2]
            scale = min(1, 1920/width, 1440/height)
            if scale < 1:
                frame = cv2.resize(frame, (int(width*scale), int(height*scale)))
        except Exception as error:
            messagebox.showerror('Không đọc được ảnh', str(error), parent=self.root)
            return
        self.stop()
        self.source = 'image'
        self.frame, self.frame_at = frame, time.monotonic()
        self.frame_number += 1
        self.result_text.set('Đang đọc ảnh thử…')
        self.status_text.set(f'Ảnh thử: {path.name}. File gốc chỉ được đọc; không tạo bản sao hay kết quả.')

    def select_region(self):
        if self.frame is None:
            self.status_text.set('Mở camera hoặc ảnh thử trước, sau đó chọn vùng số cân.')
            return
        self.selecting = True
        self.invalidate(self.session.roi)
        self.canvas.configure(cursor='crosshair')
        self.result_text.set('Đang chọn vùng…')
        self.status_text.set('Kéo chuột bao trọn một dòng số cân, gồm dấu thập phân. Esc để hủy.')
        self.root.bind('<Escape>', self.cancel_selection)

    def cancel_selection(self, _event=None):
        self.selecting = False
        self.drag_start = self.drag_end = None
        self.canvas.configure(cursor='')
        self.status_text.set('Đã hủy thao tác chọn vùng.')

    def drag_begin(self, event):
        if self.selecting and self.viewport:
            self.drag_start = self.drag_end = (event.x, event.y)

    def drag_move(self, event):
        if self.selecting and self.drag_start:
            self.drag_end = (event.x, event.y)

    def drag_finish(self, event):
        if not self.selecting or not self.drag_start or not self.viewport:
            return
        region = self.viewport.region(self.drag_start, (event.x, event.y))
        if region:
            self.invalidate(region)
            self.region_text.set('Vùng đọc: chọn bằng chuột')
            self.result_text.set('Đang đọc vùng đã chọn…')
            self.cancel_selection()
            self.status_text.set('Vùng màu xanh là vùng đọc. Bao đủ mọi chữ số, tránh đèn báo và dòng Tare/Net.')
        else:
            self.drag_start = self.drag_end = None
            self.status_text.set('Vùng quá nhỏ. Kéo lại để bao trọn một dòng số cân.')

    def auto_region(self):
        self.cancel_selection()
        self.invalidate()
        self.region_text.set('Vùng đọc: tự tìm LED đỏ')
        self.status_text.set('Đang tự tìm LED đỏ. Nếu chọn sai dòng, dùng “Chọn vùng số cân”.')

    def policy_changed(self):
        self.invalidate(self.session.roi)
        self.status_text.set('Đã đổi cách đọc dấu thập phân. Chỉ bật tùy chọn nếu cân luôn có đúng 2 số sau dấu.')

    def _show_reading(self, job, reading):
        now = time.monotonic()
        if not self.session.accepts(job.revision, job.captured_at, now,
                                    max_age=2.5 if self.source == 'camera' else float('inf')):
            return
        self.last_job = job
        self.last_result_at = job.captured_at
        self.weight_text.set(f'{reading.value:.2f}' if reading.value is not None else '—')
        self.result_text.set({
            'complete-reading': 'Đọc được · hãy đối chiếu với cân',
            'conflicting-readings': 'Các lần đọc bất đồng · chưa lấy số',
            'display-region-not-found': 'Chưa tìm thấy LED đỏ · thử chọn vùng',
            'no-complete-confident-reading': 'Chưa đọc đủ số · chỉnh vùng hoặc góc camera',
        }.get(reading.reason, 'Chưa đọc được'))
        lines = [f'Thời gian đọc: {reading.elapsed_ms:.0f} ms',
                 f'Ảnh đã đọc: {job.frame.shape[1]} × {job.frame.shape[0]}', 'Chuỗi OCR / điểm model:']
        for observation in reading.observations[:6]:
            lines.append(f'  {observation.text[:24]!r}  /  {observation.confidence:.2f}')
        self.reading_details = '\n'.join(lines)
        self.details.set(f'{reading.elapsed_ms:.0f} ms · {len(reading.observations)} chuỗi OCR')
        self.auto_regions = list(dict.fromkeys(o.region for o in reading.observations if o.region))
        region = job.roi
        if not region:
            matches = [o for o in reading.observations if o.region and reading.value is not None
                       and parse_weight(o.text, fixed_digits=job.fixed_two) == reading.value]
            regions = [o.region for o in sorted(matches, key=lambda o: o.confidence, reverse=True)]
            regions += self.auto_regions
            region = regions[0] if regions else None
        self.crop_canvas.delete('all')
        if region:
            x1, y1, x2, y2 = region
            crop = job.frame[y1:y2, x1:x2]
            if crop.size:
                image = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                scale = min(280/image.width, 70/image.height)
                image = image.resize((max(1, round(image.width*scale)), max(1, round(image.height*scale))),
                                     Image.Resampling.LANCZOS)
                self.crop_image = ImageTk.PhotoImage(image)
                self.crop_canvas.create_image(140, 35, image=self.crop_image)

    def _draw(self):
        canvas = self.canvas
        canvas.delete('all')
        width, height = max(1, canvas.winfo_width()), max(1, canvas.winfo_height())
        if self.frame is None:
            canvas.create_text(width/2, height/2, text='Mở camera hoặc chọn ảnh để thử nhận diện',
                               fill='#cbd5e1', font=('Segoe UI', 14), width=width-40)
            self.viewport = None
            return
        h, w = self.frame.shape[:2]
        self.viewport = view = Viewport.fit(width, height, w, h)
        image = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
        image = image.resize((max(1, round(view.width)), max(1, round(view.height))), Image.Resampling.BILINEAR)
        self.preview_image = ImageTk.PhotoImage(image)
        canvas.create_image(view.x, view.y, image=self.preview_image, anchor='nw')
        if self.session.roi:
            x1, y1, x2, y2 = self.session.roi
            canvas.create_rectangle(view.x+x1/w*view.width, view.y+y1/h*view.height,
                                    view.x+x2/w*view.width, view.y+y2/h*view.height,
                                    outline='#38bdf8', width=3)
        elif self.auto_regions and (self.source == 'image' or time.monotonic()-self.last_result_at < 2.5):
            for x1, y1, x2, y2 in self.auto_regions:
                canvas.create_rectangle(view.x+x1/w*view.width, view.y+y1/h*view.height,
                                        view.x+x2/w*view.width, view.y+y2/h*view.height,
                                        outline='#fbbf24', width=2)
        if self.selecting and self.drag_start and self.drag_end:
            canvas.create_rectangle(*self.drag_start, *self.drag_end, outline='#fbbf24', width=3)
        canvas.create_text(view.x+12, view.y+12, anchor='nw',
                           text=f'{w} × {h}  ·  ' + ('CAMERA' if self.source == 'camera' else 'ẢNH THỬ'),
                           fill='white', font=('Segoe UI', 10, 'bold'))

    def _tick(self):
        if self.closed:
            return
        now = time.monotonic()
        try:
            while True:
                kind, payload = self.worker.results.get_nowait()
                if kind == 'ready':
                    self.ready = True
                    self.open_button.configure(state='normal')
                    self.file_button.configure(state='normal')
                    self.result_text.set('Sẵn sàng thử')
                    self.status_text.set('Chọn Camera 0 rồi bấm Mở camera. Chương trình chỉ đọc thử, không lưu dữ liệu.')
                elif kind == 'fatal':
                    self.result_text.set('Không nạp được model')
                    self.status_text.set(f'Cài lại bộ thử nghiệm đầy đủ. Lỗi: {payload}')
                elif kind == 'reading':
                    self.busy = False
                    self._show_reading(*payload)
                elif kind == 'error':
                    self.busy = False
                    job, error = payload
                    if job.revision == self.session.revision:
                        self.weight_text.set('—')
                        self.result_text.set('Lỗi đọc ảnh · thử mở lại camera')
                        self.details.set(error[:300])
        except Empty:
            pass
        if self.camera:
            latest = self.camera.latest()
            if latest:
                frame, timestamp = latest
                if self.frame is not None and frame.shape != self.frame.shape:
                    self.invalidate()
                    self.region_text.set('Vùng đọc: tự tìm LED đỏ')
                self.frame, self.frame_at = frame, timestamp
                self.frame_number += 1
            age = now - (self.frame_at or self.camera.started_at)
            if self.camera.failed() or age > (3 if self.frame is not None else 12):
                self.stop()
                self.result_text.set('Mất hình / không mở được camera')
                self.status_text.set('Đóng ứng dụng khác đang dùng camera; thử Camera 1/2 hoặc Media Foundation rồi Mở camera.')
            elif self.last_result_at and now-self.last_result_at > 2.5:
                self.weight_text.set('—')
                self.result_text.set('Kết quả đã cũ · chờ ảnh mới')
                self.crop_canvas.delete('all')
                self.auto_regions = []
        if (self.ready and not self.busy and not self.selecting and self.frame is not None
                and self.frame_number != self.submitted_number and now-self.last_submit >= .45
                and (self.source == 'image' or now-self.frame_at < 1)):
            self.worker.jobs.put_nowait(Job(self.session.revision,
                self.frame_at if self.source == 'camera' else now,
                self.frame.copy(), self.session.roi, self.fixed_two.get()))
            self.busy = True
            self.submitted_number = self.frame_number
            self.last_submit = now
        self._draw()
        self.root.after(80, self._tick)

    def help(self):
        messagebox.showinfo('Cách thử tại xưởng',
            '1. Đóng phần mềm cân đang dùng cùng camera.\n'
            '2. Chọn Camera 0 → Mở camera. Nếu thiếu hình, thử Camera 1/2 hoặc Media Foundation.\n'
            '3. Kéo “Chọn vùng số cân” bao trọn đúng một dòng số, gồm dấu thập phân.\n'
            '4. Chỉ bật “Cân luôn có 2 số thập phân” nếu đúng cấu hình cân tại xưởng.\n'
            '5. Đối chiếu số đọc với cân thật ở nhiều mức tải. Số có thể sai dù điểm model cao.\n\n'
            'Không lưu phiếu, ảnh, lịch sử hay cấu hình. Không kết nối DB/cloud/API. '
            'Đóng ứng dụng sẽ xóa vùng chọn và kết quả trong RAM.', parent=self.root)

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.camera:
            self.camera.close()
            self.camera = None
        self.worker.close()
        self.frame = self.last_job = self.preview_image = self.crop_image = None
        self.root.destroy()


def main():
    mp.freeze_support()
    parser = argparse.ArgumentParser(description='Trạm Cân OCR — bản chạy thử không lưu dữ liệu')
    parser.add_argument('--models', type=Path, default=None, help='Chỉ dùng khi phát triển')
    parser.add_argument('--self-test', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--expect-weight', default='1.20', help=argparse.SUPPRESS)
    args = parser.parse_args()
    cv2.setNumThreads(2)
    root = tk.Tk()
    if args.self_test:
        # Explicit packaging check, with no report/capture written by the application.
        from unittest.mock import patch
        guards = [patch('requests.sessions.Session.request', side_effect=RuntimeError('Network forbidden')),
                  patch('urllib.request.urlopen', side_effect=RuntimeError('Network forbidden')),
                  patch('socket.create_connection', side_effect=RuntimeError('Network forbidden'))]
        for guard in guards:
            guard.start()
    app = TrialApp(root, args.models)
    if args.self_test:
        deadline, finished_at, loaded, success = time.monotonic()+30, 0., False, False
        probe = None

        def verify():
            nonlocal loaded, finished_at, success, probe
            if app.ready and not loaded:
                loaded = True
                app.load_image(args.self_test)
            if app.last_job and not finished_at:
                success = app.weight_text.get() == args.expect_weight
                finished_at = time.monotonic()
            if finished_at and time.monotonic()-finished_at > 3 and probe is None:
                # Exercise Windows frozen multiprocessing without touching a real camera.
                probe = Camera(99, cv2.CAP_DSHOW)
            if time.monotonic() > deadline or (finished_at and time.monotonic()-finished_at > 6):
                if probe:
                    started = time.monotonic()
                    probe.close()
                    success = success and time.monotonic()-started < 2
                # Source/ROI changes must immediately remove the old displayed weight.
                app.invalidate((0, 0, 50, 30))
                success = success and app.weight_text.get() == '—'
                app.stop()
                success = success and app.frame is None and app.session.roi is None
                app.close()
            else:
                root.after(100, verify)

        root.after(100, verify)
    root.mainloop()
    if args.self_test:
        for guard in guards:
            guard.stop()
        raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
