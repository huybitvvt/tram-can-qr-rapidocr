import json
from pathlib import Path

import pytest

from tramcan_rapidocr.dataset import load_samples


def test_old_absolute_paths_relocate_without_reading_other_directories(tmp_path):
    reference = tmp_path/'ref.json'
    reference.write_text(json.dumps([{'path':'E:/backup-tramcan/folder/image.jpg','asset_id':'a',
        'gateway':'g','source':'reviewed-400','expected':1.2,'scene':{'weight':12.}}]))
    reviewed = tmp_path/'reviewed.json'
    reviewed.write_text('[]')
    sample = load_samples(reference,reviewed,tmp_path/'backup')[0]
    assert sample.path==(tmp_path/'backup/folder/image.jpg').resolve()
    assert str(sample.expected)=='1.2' and sample.baseline==12.


def test_cannot_escape_backup_directory(tmp_path):
    reference = tmp_path/'ref.json'
    reference.write_text(json.dumps([{'path':'E:/backup-tramcan/../private.env'}]))
    reviewed = tmp_path/'reviewed.json'
    reviewed.write_text('[]')
    with pytest.raises(ValueError,match='escapes'):
        load_samples(reference,reviewed,tmp_path/'backup')


def test_independent_reference_does_not_invent_a_yolo_baseline(tmp_path):
    reference=tmp_path/'ref.json'
    reference.write_text(json.dumps([{'relative_path':'folder/image.jpg','asset_id':'a',
        'gateway':'g','source':'reviewed-400','expected':1.2}]))
    reviewed=tmp_path/'reviewed.json'
    reviewed.write_text('[]')
    sample=load_samples(reference,reviewed,tmp_path/'backup')[0]
    assert not sample.baseline_available
    assert sample.path==(tmp_path/'backup/folder/image.jpg').resolve()
