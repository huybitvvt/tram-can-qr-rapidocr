"""Run real PP-OCRv6 with Python HTTP/socket connections denied."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from tramcan_rapidocr.dataset import load_frame,load_samples
from tramcan_rapidocr.engine import ScaleReader


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--reviewed',type=Path,required=True)
    parser.add_argument('--backup-root',type=Path,required=True)
    parser.add_argument('--models',type=Path,default=Path('models'))
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    selected_prefixes={'9765b53baf','8e10c56ad6','9324e60e0d','4546676515'}
    samples=[s for s in load_samples(args.reference,args.reviewed,args.backup_root)
             if any(s.asset_id.startswith(key) for key in selected_prefixes)]
    assert len(samples)==4
    records=[]
    with patch('requests.sessions.Session.request',side_effect=AssertionError('Unexpected HTTP request')), \
         patch('urllib.request.urlopen',side_effect=AssertionError('Unexpected URL request')), \
         patch('socket.create_connection',side_effect=AssertionError('Unexpected socket connection')):
        reader=ScaleReader(args.models,decimal_policy='fixed-2')
        for sample in samples:
            _,frame=load_frame(sample)
            result=reader.read(frame)
            records.append({'asset_id':sample.asset_id,'expected':str(sample.expected),**result.as_dict()})
            print(sample.asset_id[:10],sample.expected,'->',result.value,result.reason,flush=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({'python_network_guard':'passed','native_ort_telemetry':'disabled',
                                   'records':records},indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
