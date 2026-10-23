"""Reproducible benchmark against the previous read-only factory audit."""

from collections import Counter,defaultdict
import csv
from decimal import Decimal
import json
import platform
from pathlib import Path
import time

import numpy as np

from .dataset import load_frame,load_samples,oracle_crop
from .engine import ScaleReader,sha256


def classify(value: Decimal | None, expected: Decimal | None, labelled: bool) -> str:
    if not labelled:
        return 'unreviewed'
    if expected is None:
        return 'true_negative' if value is None else 'false_accept'
    return 'rejected' if value is None else 'correct' if value==expected else 'wrong'


def run_benchmark(args) -> dict:
    samples = load_samples(args.reference,args.reviewed,args.backup_root)
    if args.group!='all':
        samples = [s for s in samples if s.group==args.group]
    if args.limit:
        samples = samples[:args.limit]
    if not samples:
        raise ValueError('No images selected')
    args.out.mkdir(parents=True,exist_ok=True)
    results_path = args.out/'results.jsonl'
    if results_path.exists():
        raise FileExistsError(f'{results_path} already exists; choose a new output directory')
    started = time.perf_counter()
    reader = ScaleReader(args.models,args.size,threads=args.threads,min_confidence=args.confidence,decimal_policy=args.decimal_policy)
    reader.read_crop(np.zeros((64,256,3),dtype=np.uint8))
    startup_ms = (time.perf_counter()-started)*1000
    records = []
    with results_path.open('w',encoding='utf-8') as stream:
        for index,sample in enumerate(samples):
            try:
                original,frame = load_frame(sample)
                reading = reader.read_text_detector(frame) if args.strategy=='text-det' else reader.read(frame)
                record = {'asset_id':sample.asset_id,'gateway':sample.gateway,'group':sample.group,
                          'expected':str(sample.expected) if sample.expected is not None else None,
                          'source_path':str(sample.path),'image_sha256':sha256(sample.path),
                          'auto':reading.as_dict(),
                          'outcome':classify(reading.value,sample.expected,sample.labelled),
                          'baseline':sample.baseline,
                          'baseline_outcome':classify(Decimal(str(sample.baseline)) if sample.baseline is not None else None,sample.expected,sample.labelled) if sample.baseline_available else 'unavailable'}
                if args.oracle:
                    crop = oracle_crop(original,sample)
                    if crop is not None:
                        answer = reader.read_crop(crop)
                        record['oracle'] = answer.as_dict()
                        record['oracle_outcome'] = classify(answer.value,sample.expected,sample.labelled)
                        record['oracle_view'] = sample.label_boxes[0].get('view_kind','unknown')
            except Exception as error:
                record = {'asset_id':sample.asset_id,'group':sample.group,'outcome':'error','error':str(error)}
            records.append(record)
            stream.write(json.dumps(record,ensure_ascii=False)+'\n')
            stream.flush()
            if (index+1)%10==0 or index+1==len(samples):
                print(f'{index+1}/{len(samples)} {dict(Counter(r["outcome"] for r in records))}',flush=True)
    summary = summarize(records)
    summary.update({'model':reader.model_info,'strategy':args.strategy,'confidence':args.confidence,'cpu_threads':args.threads,
                    'startup_and_warmup_ms':startup_ms,'platform':platform.platform(),
                    'python':platform.python_version(),
                    'reference_sha256':sha256(args.reference),'reviewed_sha256':sha256(args.reviewed),
                    'scene_policy':'1600x1266 evidence -> top 1600x900 camera scene',
                    'parser':args.decimal_policy,'decimal_places':2,'digit_substitutions':False,
                    'conflict_confidence':min(.70,args.confidence),
                    'note':'Existing labels are not a verified training holdout; visual24 labels were produced by Codex before viewing predictions.'})
    (args.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    with (args.out/'results.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['asset_id','group','gateway','expected','rapidocr','outcome','baseline_yolo','baseline_outcome','latency_ms','observations'])
        for r in records:
            writer.writerow([r['asset_id'],r['group'],r.get('gateway'),r.get('expected'),r.get('auto',{}).get('weight'),r['outcome'],r.get('baseline'),r.get('baseline_outcome'),r.get('auto',{}).get('elapsed_ms'),json.dumps(r.get('auto',{}).get('observations',[]),ensure_ascii=False)])
    return summary


def summarize(records: list[dict]) -> dict:
    groups = defaultdict(list)
    for row in records:
        groups[row['group']].append(row)
    summary = {'images':len(records),'groups':{},'errors':sum(r['outcome']=='error' for r in records)}
    for group,rows in sorted(groups.items()):
        ms = [r['auto']['elapsed_ms'] for r in rows if 'auto' in r]
        info = {'images':len(rows),'rapidocr':dict(Counter(r['outcome'] for r in rows)),
                'baseline_yolo':dict(Counter(r.get('baseline_outcome','error') for r in rows))}
        if ms:
            info['latency_ms'] = {'p50':float(np.percentile(ms,50)),'p95':float(np.percentile(ms,95)),'mean':float(np.mean(ms))}
        for view in ('scene','zoom'):
            oracle = [r for r in rows if r.get('oracle_view')==view]
            if oracle:
                info['oracle_'+view] = dict(Counter(r['oracle_outcome'] for r in oracle))
        summary['groups'][group] = info
    return summary
