from decimal import Decimal
from queue import Empty
import time

import numpy as np

from tramcan_rapidocr.decision import Reading
from tramcan_rapidocr.trial_worker import Job, ReaderWorker


def test_worker_reads_only_selected_pixels_and_changes_decimal_policy(monkeypatch, tmp_path):
    calls = []

    class Reader:
        def __init__(self, root, **kwargs):
            assert root == tmp_path
            self.fixed_digits = False

        def read_crop(self, image):
            calls.append((image.shape, image.copy(), self.fixed_digits))
            return Reading(Decimal('1.20'), 'complete-reading', [])

        def read(self, image):
            calls.append((image.shape, image.copy(), self.fixed_digits))
            return Reading(None, 'display-region-not-found', [])

    monkeypatch.setattr('tramcan_rapidocr.trial_worker.ScaleReader', Reader)
    worker = ReaderWorker(tmp_path)
    assert worker.results.get(timeout=2) == ('ready', None)
    frame = np.arange(20*30*3, dtype=np.uint8).reshape(20, 30, 3)
    worker.jobs.put(Job(4, time.monotonic(), frame, (3, 4, 13, 12), True))
    kind, (job, reading) = worker.results.get(timeout=2)
    assert kind == 'reading' and job.revision == 4
    assert reading.value == Decimal('1.20')
    assert calls[0][0] == (8, 10, 3) and calls[0][2] is True
    assert np.array_equal(calls[0][1], frame[4:12, 3:13])
    worker.jobs.put(Job(5, time.monotonic(), frame, None, False))
    assert worker.results.get(timeout=2)[0] == 'reading'
    assert calls[1][0] == frame.shape and calls[1][2] is False
    worker.close()
    worker.thread.join(timeout=2)
    assert not worker.thread.is_alive()
    assert list(tmp_path.iterdir()) == []  # no settings, frames, or history


def test_model_error_is_reported_without_attempting_camera_or_persistence(monkeypatch, tmp_path):
    def missing(*args, **kwargs):
        raise FileNotFoundError('Missing model')

    monkeypatch.setattr('tramcan_rapidocr.trial_worker.ScaleReader', missing)
    worker = ReaderWorker(tmp_path)
    kind, message = worker.results.get(timeout=2)
    assert kind == 'fatal' and 'Missing model' in message
    worker.close()
    worker.thread.join(timeout=2)
    assert list(tmp_path.iterdir()) == []
