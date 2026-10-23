"""Single OCR worker with bounded, in-memory queues."""
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Thread

import numpy as np

from .engine import ScaleReader


@dataclass
class Job:
    revision: int
    captured_at: float
    frame: np.ndarray
    roi: tuple | None
    fixed_two: bool


class ReaderWorker:
    def __init__(self, models: Path):
        self.jobs = Queue(maxsize=1)
        self.results = Queue(maxsize=2)
        self.models = models
        self.thread = Thread(target=self._run, daemon=True, name='TrialOCR')
        self.thread.start()

    def _run(self):
        try:
            reader = ScaleReader(self.models, decimal_policy='explicit')
            self.results.put(('ready', None))
        except Exception as error:
            self.results.put(('fatal', str(error)))
            return
        while (job := self.jobs.get()) is not None:
            try:
                reader.fixed_digits = job.fixed_two
                if job.roi:
                    x1, y1, x2, y2 = job.roi
                    result = reader.read_crop(job.frame[y1:y2, x1:x2])
                else:
                    result = reader.read(job.frame)
                self.results.put(('reading', (job, result)))
            except Exception as error:
                self.results.put(('error', (job, str(error))))

    def close(self):
        # Remove pending image references. Inference in flight may finish while exiting.
        try:
            self.jobs.get_nowait()
        except Empty:
            pass
        try:
            self.jobs.put_nowait(None)
        except Full:
            pass
