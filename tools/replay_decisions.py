"""Compare explicit/fixed scale profiles on saved, immutable OCR observations."""
import argparse
from decimal import Decimal
import json
from pathlib import Path

from tramcan_rapidocr.benchmark import classify,summarize
from tramcan_rapidocr.decision import Observation,decide
from tramcan_rapidocr.engine import sha256


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--decimal-policy',choices=['explicit','fixed-2'],required=True)
    parser.add_argument('--confidence',type=float,default=.85)
    args=parser.parse_args()
    target=args.out/'results.jsonl'
    if target.exists():raise FileExistsError(target)
    args.out.mkdir(parents=True,exist_ok=True)
    records=[]
    for line in args.source.read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        expected=Decimal(row['expected']) if row.get('expected') is not None else None
        for field in ('auto','oracle'):
            if field not in row:continue
            observations=[Observation(**o) for o in row[field]['observations']]
            reading=decide(observations,min_confidence=args.confidence,fixed_digits=args.decimal_policy=='fixed-2')
            reading.elapsed_ms=row[field]['elapsed_ms']
            row[field]=reading.as_dict()
            row['outcome' if field=='auto' else 'oracle_outcome']=classify(reading.value,expected,row['group']!='unreviewed')
        records.append(row)
    target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    summary=summarize(records)
    summary.update({'postprocessing_only':True,'ocr_observations_sha256':sha256(args.source),
                    'parser':args.decimal_policy,'confidence':args.confidence,
                    'conflict_confidence':min(.70,args.confidence),
                    'latency_note':'Inference timings retained from original OCR run; no new inference was run.'})
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
