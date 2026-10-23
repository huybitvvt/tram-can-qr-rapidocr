# Kiểm thử PP-OCRv6 — 23/10/2026

Kết quả chính ở `reports/2026-10-23-small.json`. Lượt thực nghiệm được chạy
tại `E:\tram-can-qr-rapidocr` trong venv riêng; không sửa hai repo ứng dụng
cũ và không mở DB/config máy trạm.

## Thiết kế phép thử

- Dùng 522 ảnh và kết quả đối chứng đã ghi ở lượt kiểm tra rc81 trước đó.
- 389 ảnh đọc được có nhãn OCR có duyệt từ bộ 400 ảnh; 11 ảnh âm tính.
- 122 ảnh lấy mẫu có seed 81 từ backup 21/10. Trong đó 24 ảnh được Codex
  đối chiếu từ cảnh/inset trước khi xem kết quả; 98 ảnh chưa có nhãn mới.
- Các bộ này không phải tập test được xác minh độc lập với dữ liệu train.
- Luồng tự động chỉ nhận cảnh gốc. Với bằng chứng 1600×1266, cắt phần
  1600×900 phía trên; panel zoom phía dưới không tham gia nhận diện.
- Nhãn chỉ dùng so kết quả; luồng tự động không biết số cân mong đợi.
- Cả hai hệ được so ở mức pipeline: bộ tìm vùng, nhận diện và ngưỡng lọc
  khác nhau. Confidence của hai hệ không được coi là xác suất đã hiệu chuẩn.
- Profile cuối: `small`, `red-roi`, confidence 0,85; veto bất đồng đủ số
  từ 0,70; `fixed-2` theo thiết bị luôn có 2 số thập phân.
- Bộ OCR gốc và phép thử không thay ký tự/số bằng quy tắc dựa vào nhãn.

## Kết quả chính — chạy thật 522 ảnh, không có lỗi thực thi

| Bộ đối chiếu | Pipeline | Đúng | Sai | Từ chối |
|---|---|---:|---:|---:|
| 389 nhãn cũ | YOLO rc81 | 231 | 21 | 137 |
| 389 nhãn cũ | RapidOCR PP-OCRv6 small | 311 | 6 | 72 |
| 24 ảnh 21/10 | YOLO rc81 | 11 | 2 | 11 |
| 24 ảnh 21/10 | RapidOCR PP-OCRv6 small | 20 | 1 | 3 |

Cả 11 ảnh âm tính bị từ chối. 98 ảnh chưa đối chiếu không tham gia tính độ
đúng. Tổng 413 ảnh có số đối chiếu: 331 đúng, 7 sai, 75 từ chối.

Các lỗi còn lại đã xem lại trực tiếp từ ảnh backup:

| Asset ID | Nhãn | RapidOCR small |
|---|---:|---:|
| `03cc08d45a56c1a768e43e576a89f8b7` | 13,12 | 3,12 |
| `38b035ecdab44d4de468b7545522a7dc` | 7,01 | 1,01 |
| `4ee8c24a5aa5acbc2fa77d88242c12ef` | 7,32 | 1,32 |
| `73853ca61f0dfa415d83b804a381796a` | 7,76 | 2,76 |
| `b5e8e9ce93d2045aa0414f00f550ea45` | 7,02 | 2,02 |
| `f39cc34a8e0e09c9561602c2ad57048c` | 7,02 | 2,02 |
| `4546676515e67e0ab3aeb73df5e1db96` | 7,00 | 2,00 |

Lỗi nhầm 7/1/2 và bỏ số đầu vẫn hiện diện; confidence cao không đảm bảo
đọc đúng. Chưa đạt để tự động chấp nhận số tại xưởng.

## Các phương án đã đo thêm

| Phương án | Mẫu | Đúng | Sai | Từ chối | Cách đo |
|---|---:|---:|---:|---:|---|
| Small, text detector PP-OCRv6, fixed-2 | 24 | 21 | 2 | 1 | OCR thực tế |
| Medium, red ROI, dấu thập phân explicit | 24 | 9 | 0 | 15 | OCR thực tế |
| Medium, red ROI, fixed-2 và veto 0,70 | 24 | 21 | 1 | 2 | Lọc lại cùng observations đã ghi, không chạy lại OCR |

Kết quả medium sau cùng là phép replay được đánh dấu rõ trong
`reports/2026-10-23-medium-replay.json`; timing giữ từ lượt OCR gốc. Không
có số liệu medium trên toàn bộ 389 ảnh. Text-det chưa thử đủ 522 ảnh.

## Tốc độ CPU

Intel Core i3-1215U, Python 3.12.10 x64, ONNX Runtime CPU, intra-op 2 thread,
inter-op 1 thread. Lượt cuối small đồng thời có phép đo oracle theo nhãn;
các thời gian này là số đo trên máy kiểm tra, không phải cam kết tại máy khách.

| Profile/mẫu | p50 | p95 |
|---|---:|---:|
| Small red-roi, 389 ảnh | 353,8 ms | 594,6 ms |
| Small red-roi, 24 ảnh mới | 282,3 ms | 442,6 ms |
| Small text-det, 24 ảnh mới | 1004,5 ms | 1218,4 ms |
| Medium red-roi, 24 ảnh mới | 5627,0 ms | 8753,0 ms |

Startup/hash/warmup ghi riêng trong JSON; không gộp vào thời gian mỗi ảnh.
Không suy tốc độ camera live từ benchmark ảnh tĩnh.

## Kiểm chứng khác

- Model từ RapidOCR tag `v3.10.0`, commit
  `bd941dae09da793e76c6ba15c7aaf40f8424232a`; SHA-256 khớp nguồn upstream.
- Tải model có resume và checksum; inference bắt buộc có model/manifest
  local hợp lệ, không tự tải model thay thế.
- `offline_smoke.py` chạy OCR thật trên 4 ca với HTTP/socket Python bị chặn,
  telemetry ONNX Runtime tắt. Đọc đúng 1,20 và 6,86; từ chối ca 7,06 bị bất
  đồng; tái hiện lỗi chưa sửa 7,00→2,00.
- 31 unit tests kiểm tra parser, bất đồng, số âm/zero, vùng Gross, dữ liệu
  đối chiếu, đường dẫn và nhận dạng/checksum model. Không dùng mock OCR để
  tính các số liệu độ đúng trong bảng.
- Đọc nhãn trực tiếp từ ZIP backup được thử trên đủ 400 ảnh, không cần repo
  ứng dụng cũ. Ảnh gốc không bị sửa hay sao chép vào Git.
- Venv chỉ chứa dependencies riêng, không trỏ site-packages vào repo cũ.
  Một số wheel có sẵn tại máy được sao chép vào venv để tránh tải chậm.
  ONNX Runtime được tải và kiểm tra SHA-256 theo metadata PyPI; RapidOCR
  được build từ tag chính thức. `pip check` không phát hiện dependency lỗi.

## Artifacts riêng tại máy kiểm tra

`artifacts/small-final522/`: JSONL chi tiết, CSV 522 ảnh, summary đầy đủ.
`artifacts/report.html`: ảnh lỗi, kết quả và liên kết file.
`artifacts/wrong-readings.jpg`: 7 ca đọc sai đã xem lại.
`artifacts/offline-smoke.json`: kết quả smoke thật.

Ảnh, đường dẫn ảnh, observations từng ảnh và nhãn mới giữ local; GitHub chỉ
có code, giấy phép và báo cáo tổng hợp. Cần nghiệm thu camera USB thật và
nhãn đối chiếu trước khi làm bộ cài vận hành.
