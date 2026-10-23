from tramcan_rapidocr.trial_state import TrialSession, Viewport


def test_drag_accounts_for_letterboxing_and_reverse_direction():
    # 1920x1080 image letterboxed in a square: visible y starts at 140.
    view = Viewport.fit(640, 640, 1920, 1080)
    assert view.y == 140
    assert view.region((320, 320), (160, 230)) == (480, 270, 960, 540)


def test_drag_clamps_to_real_image_and_rejects_tiny_or_outside_selection():
    view = Viewport.fit(640, 640, 1920, 1080)
    assert view.region((-10, 100), (100, 200)) == (0, 0, 300, 180)
    assert view.region((0, 0), (100, 100)) is None
    assert view.region((100, 200), (101, 201)) is None


def test_reconfiguration_discards_inflight_weight_and_region():
    session = TrialSession()
    session.change((10, 20, 110, 60))
    revision = session.revision
    assert session.accepts(revision, 100, 101)
    session.change()
    assert session.roi is None
    assert not session.accepts(revision, 100, 101)


def test_stale_or_future_frame_can_never_show_as_current_weight():
    session = TrialSession()
    assert not session.accepts(0, 100, 103)
    assert not session.accepts(0, 101, 100)
    assert session.accepts(0, 100, 102)
