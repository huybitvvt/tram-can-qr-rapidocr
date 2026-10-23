import multiprocessing as mp
import time

from tramcan_rapidocr.trial_camera import Camera


def test_stop_does_not_wait_for_a_blocked_capture_driver():
    # A sleeping child stands in for a camera driver blocked in open/read.
    camera = Camera.__new__(Camera)
    camera.process = mp.get_context('spawn').Process(target=time.sleep, args=(30,))
    camera.process.start()
    camera_pid = camera.process.pid
    started = time.monotonic()
    camera.close()
    assert time.monotonic()-started < 2
    assert camera_pid not in [child.pid for child in mp.active_children()]
