"""Load local audit references; customer photos never belong in this repository."""

from dataclasses import dataclass
from decimal import Decimal
import json
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class Sample:
    asset_id: str
    path: Path
    gateway: str
    group: str
    expected: Decimal | None
    labelled: bool
    baseline: float | None
    label_boxes: list[dict]
    baseline_available: bool = True


def load_samples(reference: Path, reviewed: Path, backup_root: Path) -> list[Sample]:
    manual = {r['asset_id']:r for r in json.loads(reviewed.read_text(encoding='utf-8'))}
    result = []
    root = backup_root.resolve()
    for row in json.loads(reference.read_text(encoding='utf-8')):
        # Relocate archived E:/backup-tramcan paths on another workstation.
        relative = row.get('relative_path')
        if relative is None:
            parts = row['path'].replace('\\','/').split('/backup-tramcan/',1)
            if len(parts)!=2:
                raise ValueError('Reference image must be relative to backup-tramcan')
            relative = parts[1]
        path = (root/relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Image path escapes the supplied backup root')
        expected = row.get('expected')
        group = 'legacy-readable' if expected is not None else 'legacy-negative' if row['source']=='reviewed-400' else 'unreviewed'
        if row['asset_id'] in manual:
            expected = manual[row['asset_id']]['expected']
            group = 'oct21-visual'
        result.append(Sample(row['asset_id'],path,row['gateway'],group,
            Decimal(str(expected)) if expected is not None else None,
            group!='unreviewed',row.get('scene',{}).get('weight'),(row.get('label') or {}).get('boxes',[]),
            'scene' in row))
    if len({r.asset_id for r in result}) != len(result):
        raise ValueError('Duplicate asset IDs in reference data')
    return result


def load_frame(sample: Sample) -> tuple[np.ndarray,np.ndarray]:
    original = cv2.imdecode(np.fromfile(sample.path,dtype=np.uint8),cv2.IMREAD_COLOR)
    if original is None:
        raise ValueError(f'Cannot decode image {sample.asset_id}')
    scene = original[:900] if original.shape[:2]==(1266,1600) else original
    return original,scene


def oracle_crop(original: np.ndarray, sample: Sample) -> np.ndarray | None:
    """Diagnostic upper bound using a label ROI, never the automatic pipeline."""
    if not sample.label_boxes:
        return None
    x1,y1,x2,y2 = sample.label_boxes[0]['xyxy']
    dx,dy = max(4,round((x2-x1)*.1)),max(4,round((y2-y1)*.2))
    return original[max(0,y1-dy):min(original.shape[0],y2+dy),max(0,x1-dx):min(original.shape[1],x2+dx)]
