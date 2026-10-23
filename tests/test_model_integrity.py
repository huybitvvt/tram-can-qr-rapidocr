import json

import pytest

from tramcan_rapidocr.engine import ScaleReader


def test_inference_never_downloads_a_missing_model(tmp_path):
    with pytest.raises(FileNotFoundError,match='download-models'):
        ScaleReader(tmp_path)
    assert list(tmp_path.iterdir())==[]


def test_modified_manifest_cannot_substitute_a_different_checkpoint(tmp_path):
    info={'ocr_version':'PP-OCRv6','rec_size':'small','models':{
        'rec':{'file':'other.onnx','sha256':'0'*64}}}
    (tmp_path/'manifest-small.json').write_text(json.dumps(info))
    with pytest.raises(ValueError,match='pinned upstream'):
        ScaleReader(tmp_path)
