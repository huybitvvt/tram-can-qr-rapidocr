"""Command line tools; no production config, database or cloud integrations."""

import argparse
import json
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description='RapidOCR + PP-OCRv6 factory scale experiment')
    commands = root.add_subparsers(dest='command',required=True)
    for name in ('download-models','read','benchmark'):
        sub = commands.add_parser(name)
        sub.add_argument('--size',choices=['small','medium'],default='small')
        sub.add_argument('--models',type=Path,default=Path('models'))
        sub.add_argument('--threads',type=int,default=2)
        if name in {'read','benchmark'}:
            sub.add_argument('--confidence',type=float,default=.85)
            sub.add_argument('--strategy',choices=['red-roi','text-det'],default='red-roi')
            sub.add_argument('--decimal-policy',choices=['explicit','fixed-2'],default='explicit',help='fixed-2 is only for a scale verified to always show two decimal places')
        if name=='read':
            sub.add_argument('image',type=Path)
            sub.add_argument('--roi',help='Pixel coordinates x1,y1,x2,y2; diagnostic manual crop')
            sub.add_argument('--archive-scene',action='store_true')
        elif name=='benchmark':
            sub.add_argument('--reference',type=Path,required=True)
            sub.add_argument('--reviewed',type=Path,required=True)
            sub.add_argument('--backup-root',type=Path,required=True)
            sub.add_argument('--out',type=Path,required=True)
            sub.add_argument('--group',choices=['all','legacy-readable','legacy-negative','oct21-visual'],default='all')
            sub.add_argument('--limit',type=int)
            sub.add_argument('--oracle',action='store_true',help='Also measure labelled crop recognition separately')
    return root


def main():
    args = parser().parse_args()
    from .engine import ScaleReader,prepare_models
    if args.command=='download-models':
        result = prepare_models(args.models,args.size,args.threads)
    elif args.command=='benchmark':
        from .benchmark import run_benchmark
        result = run_benchmark(args)
    else:
        import cv2
        import numpy as np
        frame = cv2.imdecode(np.fromfile(args.image,dtype=np.uint8),cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError(f'Cannot read {args.image}')
        if args.archive_scene and frame.shape[:2]==(1266,1600):
            frame = frame[:900]
        reader = ScaleReader(args.models,args.size,threads=args.threads,min_confidence=args.confidence,decimal_policy=args.decimal_policy)
        if args.roi:
            x1,y1,x2,y2 = map(int,args.roi.split(','))
            if not (0<=x1<x2<=frame.shape[1] and 0<=y1<y2<=frame.shape[0]):
                raise ValueError('ROI must be inside the image')
            result = reader.read_crop(frame[y1:y2,x1:x2]).as_dict()
        else:
            result = (reader.read_text_detector(frame) if args.strategy=='text-det' else reader.read(frame)).as_dict()
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
