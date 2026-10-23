"""Write an offline HTML report; keep all customer-specific rows local."""
import argparse
import base64
import html
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--results',type=Path,default=Path('artifacts/small-final522'))
    parser.add_argument('--out',type=Path,default=Path('artifacts/report.html'))
    args=parser.parse_args()
    summary=json.loads((args.results/'summary.json').read_text(encoding='utf-8'))
    records=[json.loads(line) for line in (args.results/'results.jsonl').read_text(encoding='utf-8').splitlines()]
    rows=[]
    for r in records:
        observations=' | '.join(o['text']+' ['+f'{o["confidence"]:.3f}'+']' for o in r.get('auto',{}).get('observations',[]))
        values=[r['asset_id'][:12],r['group'],r.get('expected') or '—',r.get('auto',{}).get('weight') or '—',r['outcome'],observations]
        rows.append('<tr data-outcome="'+html.escape(r['outcome'])+'">'+''.join('<td>'+html.escape(str(v))+'</td>' for v in values)+'</tr>')
    summary_rows=[]
    for name in ('legacy-readable','oct21-visual'):
        group=summary['groups'][name]
        for key in ('baseline_yolo','rapidocr'):
            counts=group[key]
            summary_rows.append(f'<tr><td>{name}</td><td>{key}</td><td>{counts.get("correct",0)}</td><td>{counts.get("wrong",0)}</td><td>{counts.get("rejected",0)}</td></tr>')
    image=''
    wrong=args.out.parent/'wrong-readings.jpg'
    if wrong.exists():
        image='<img alt="7 ca đọc sai đã đối chiếu" src="data:image/jpeg;base64,'+base64.b64encode(wrong.read_bytes()).decode()+'">'
    page='''<!doctype html><html lang="vi"><meta charset="utf-8"><title>RapidOCR — ảnh xưởng</title>
<style>body{font:16px/1.5 system-ui;margin:28px;color:#17202a;background:#f6f7f8}h1{font-size:28px}table{border-collapse:collapse;width:100%;background:white;margin:16px 0}th,td{padding:8px;border:1px solid #ccd3da;text-align:left}td:last-child{overflow-wrap:anywhere}img{max-width:100%;height:auto}.warning{color:#9e1a1a}select{padding:8px}</style>
<h1>RapidOCR + PP-OCRv6 small — 23/10/2026</h1>
<p>Đã chạy 522 ảnh. Profile: red-roi, fixed-2, confidence 0,85, veto bất đồng từ 0,70. Không sửa dữ liệu gốc hay hai repo ứng dụng.</p>
<p class="warning"><strong>Chưa đạt để tự động chấp nhận số cân tại xưởng.</strong> Vẫn có 7 ca sai trên 413 ảnh có số đối chiếu.</p>
<table><tr><th>Bộ ảnh</th><th>Pipeline</th><th>Đúng</th><th>Sai</th><th>Từ chối</th></tr>'''+''.join(summary_rows)+'''</table>
<p>11 ảnh âm tính đều bị từ chối. 98 ảnh chưa có đối chiếu không tính độ đúng. Nhãn cũ chưa được xác minh độc lập với tập train; 24 nhãn mới do Codex đối chiếu bằng mắt.</p>
<p>Ảnh lỗi lấy trực tiếp từ backup, lưu local:</p>'''+image+'''
<p><a href="small-final522/results.csv">CSV 522 ảnh</a> · <a href="small-final522/summary.json">Summary JSON</a> · <a href="offline-smoke.json">Smoke chặn HTTP/socket</a></p>
<label>Lọc <select id="filter"><option value="">Tất cả</option><option value="wrong">Đọc sai</option><option value="rejected">Từ chối</option><option value="correct">Đúng</option><option value="unreviewed">Chưa đối chiếu</option></select></label>
<table id="details"><thead><tr><th>Ảnh</th><th>Bộ</th><th>Đối chiếu kg</th><th>OCR kg</th><th>Kết quả</th><th>OCR thô [confidence]</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table>
<script>const f=document.getElementById('filter');f.onchange=()=>{for(const r of document.querySelectorAll('#details tbody tr'))r.hidden=Boolean(f.value&&r.dataset.outcome!==f.value)};</script></html>'''
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(page,encoding='utf-8')
    print(args.out)


if __name__=='__main__':main()
