"""Prepare local references directly from the user's backup, without another code repo."""
import argparse
import csv
import io
import json
from pathlib import Path
import zipfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--backup-root',type=Path,required=True)
    parser.add_argument('--labels-zip',type=Path,required=True)
    parser.add_argument('--snapshot',default='cloudinary_backup_2026-09-27')
    parser.add_argument('--out',type=Path,default=Path('.local/reference.json'))
    args=parser.parse_args()
    with zipfile.ZipFile(args.labels_zip) as archive:
        index={r['asset_id']:r for r in csv.DictReader(io.StringIO(archive.read('index.csv').decode('utf-8-sig')))}
        labels=[json.loads(s) for s in archive.read('annotations.jsonl').decode('utf-8').splitlines()]
    rows=[]
    root=args.backup_root.resolve()
    for label in labels:
        relative=Path(args.snapshot)/index[label['asset_id']]['local_file']
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'Missing or invalid image for {label["asset_id"]}')
        texts={b['text'] for b in label.get('boxes',[])}
        expected=float(next(iter(texts))) if label['readability']=='readable' and len(texts)==1 else None
        rows.append({'relative_path':relative.as_posix(),'asset_id':label['asset_id'],
                     'gateway':index[label['asset_id']]['gateway'],'expected':expected,
                     'source':'reviewed-400','label':label})
    reviewed=args.out.with_name('reviewed.json')
    if args.out.exists() or reviewed.exists():
        raise FileExistsError('Reference output exists; choose a new output directory')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    reviewed.write_text('[]',encoding='utf-8')
    print(f'Prepared {len(rows)} local references, no photos copied: {args.out}')


if __name__=='__main__':main()
