# Trạm Cân QR — RapidOCR + PP-OCRv6

Repo thử nghiệm riêng cho nhận diện số cân trên CPU Windows. Có **bộ cài chạy thử
camera tại xưởng 0.2.0-trial1**, CLI đọc ảnh, benchmark và báo cáo đối chứng.
Chưa phải bộ cài thay thế phần mềm vận hành tại xưởng.

Repo này độc lập với `tram-can-qr-render-pilot` và `digit_detection_new`.
Không đọc `.env`, DB hay cấu hình máy trạm; không có luồng ghi/sync dữ liệu.
Ảnh và nhãn xưởng dùng tại máy kiểm tra, không commit lên GitHub.

## Cài bản thử tại máy khách

Tải **TramCanOCRTrial-Setup-0.2.0-trial1.exe** tại
[Releases](https://github.com/huybitvvt/tram-can-qr-rapidocr/releases/tag/v0.2.0-trial1).
Repo riêng tư: tải ở máy có quyền truy cập rồi chép file sang máy khách.

Windows 10/11 x64; không cần cài Python, GPU hoặc tải model. Đóng phần mềm cân đang
dùng camera → cài → mở **Tram Can OCR - Ban thu** → Camera 0 → **Mở camera**.
Nếu tự chọn vùng sai, bấm **Chọn vùng số cân** rồi kéo bao trọn một dòng số.

**Bản thử không lưu phiếu, ảnh, lịch sử hay cấu hình; không kết nối dữ liệu vận hành.**
Vùng chọn và kết quả chỉ giữ trong RAM. Cài riêng, không ghi đè hai bản hiện tại.
Chưa có tự động cập nhật. [Hướng dẫn tại xưởng](docs/CAI-BAN-THU.md).

Chạy từ mã nguồn: `.venv\Scripts\python.exe -m tramcan_rapidocr.trial_app`.
Build: cài `requirements-build.txt`, tải model small bằng lệnh bên dưới,
cài Inno Setup 6 rồi chạy `powershell -File tools\build_trial.ps1`.

## Kết quả đã đo — 23/10/2026

Đã chạy 522 ảnh. Hai bộ có đối chiếu gồm 389 ảnh đọc được có nhãn cũ và
24 ảnh ngày 21/10 được Codex đối chiếu bằng mắt trước khi xem dự đoán.

| Bộ ảnh | Hệ nhận diện | Đúng | Sai | Từ chối |
|---|---|---:|---:|---:|
| 389 ảnh có nhãn | YOLO rc81 đối chứng | 231 | 21 | 137 |
| 389 ảnh có nhãn | PP-OCRv6 small + lọc kết quả | **311** | **6** | **72** |
| 24 ảnh 21/10 | YOLO rc81 đối chứng | 11 | 2 | 11 |
| 24 ảnh 21/10 | PP-OCRv6 small + lọc kết quả | **20** | **1** | **3** |

11 ảnh âm tính đều bị từ chối. 98 ảnh chưa có đối chiếu không được tính
độ đúng. Bản small dùng cấu hình cân **luôn có 2 số thập phân**, confidence
0,85 và từ chối khi các phương án đủ số bất đồng từ confidence 0,70.

Trên Intel Core i3-1215U, 2 thread OCR, p50 bản small khoảng 0,28–0,35 giây/ảnh.
Đây là lượt chạy có thêm phép đo crop theo nhãn; không phải tốc độ camera đã
nghiệm thu. Medium đã thử 24 ảnh, p50 khoảng 5,63 giây/ảnh trong lượt thử đó.

**Vẫn có lỗi đọc sai 7,00 → 2,00 và bỏ chữ số đầu. Chưa đạt để tự động
chấp nhận số cân tại xưởng.** Cần cải thiện và nghiệm thu thêm. Các số liệu
là kết quả của toàn bộ luồng cắt/đọc/lọc trên mẫu này; chưa xác minh bộ ảnh
độc lập với tập train.

[Chi tiết phép thử](docs/benchmark-2026-10-23.md) ·
[JSON kết quả](reports/2026-10-23-small.json)

## Cài môi trường phát triển

Python 3.12 x64 và `curl` (có sẵn trên Windows 10/11).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest
```

Dependency chính: RapidOCR **3.10.0**, ONNX Runtime **1.31.0**. Nguồn/model
PP-OCRv6 được cố định URL và SHA-256 trong
`src/tramcan_rapidocr/model_sources.json`. Môi trường không dùng Torch,
PaddlePaddle, Gemini hay API nhận diện từ xa.

## Tải model và đọc ảnh

Chỉ lệnh `download-models` tải model. Lệnh `read` kiểm tra checksum và dùng
đường dẫn model local; thiếu/sai model sẽ dừng.

```powershell
.\.venv\Scripts\tramcan-ocr.exe download-models --size small
.\.venv\Scripts\tramcan-ocr.exe read C:\anh-xuong\can.jpg --size small
```

Mặc định `--decimal-policy explicit`: cần OCR thấy dấu chấm/phẩy và đúng
2 chữ số sau dấu; `120` bị từ chối. Chỉ dùng cấu hình sau khi đã xác minh
thiết bị luôn hiển thị 2 số thập phân:

```powershell
.\.venv\Scripts\tramcan-ocr.exe read C:\anh-xuong\can.jpg --decimal-policy fixed-2
```

Trong `fixed-2`, chuỗi không dấu `120` được diễn giải thành `1.20` theo cấu
hình thiết bị. `1.20` giữ nguyên. Không thay chữ O/I thành số, không cắt bỏ
chữ số thừa, không sửa số dựa vào giá trị mong đợi.

Các lựa chọn:

- `--strategy red-roi`: tìm dòng LED đỏ, đọc ảnh gốc và kênh xanh tăng tương
  phản; giữ dòng Gross trên cùng khi có các dòng cân thẳng hàng.
- `--strategy text-det`: PP-OCRv6 tìm/chỉnh phối cảnh vùng chữ, lọc số LED
  đỏ. Đã đo riêng 24 ảnh; chưa benchmark toàn bộ 522 ảnh với phương án này.
- `--roi x1,y1,x2,y2`: đọc vùng chỉ định theo pixel, dùng chẩn đoán.
- `--archive-scene`: bỏ panel zoom phụ ở ảnh bằng chứng đúng kích thước
  1600×1266, dùng phần cảnh camera 1600×900 phía trên.
- `download-models --size medium`: tải model nhận diện medium, dùng chung
  detector small; bản medium có chi phí CPU cao hơn.

Kết quả JSON gồm số đọc, lý do từ chối, chuỗi OCR thô, confidence, vùng và
thời gian. Đây là công cụ thử nghiệm; người vận hành vẫn phải đối chiếu số.

## Chuẩn bị bộ đối chiếu trực tiếp từ backup

Không cần clone hai repo cũ. Script đọc ZIP nhãn và ảnh sẵn có; không sao
chép hay sửa ảnh gốc:

```powershell
.\.venv\Scripts\python.exe tools\import_backup_labels.py `
  --backup-root E:\backup-tramcan `
  --labels-zip E:\backup-tramcan\colab_upload_v001\labels_reviewed_v001.zip

.\.venv\Scripts\tramcan-ocr.exe benchmark --size small --decimal-policy fixed-2 `
  --backup-root E:\backup-tramcan `
  --reference .local\reference.json --reviewed .local\reviewed.json `
  --out artifacts\benchmark-local --oracle
```

Script trên tạo bộ 400 ảnh nhãn cũ. Bộ 522 ảnh và 24 nhãn đối chiếu mới của
lượt kiểm tra này được giữ local riêng. Có thể cung cấp chúng qua cùng
`--reference`/`--reviewed`; đối chứng YOLO được giữ khi reference có trường
`scene.weight`. Khi không có dữ liệu YOLO, báo cáo ghi `unavailable`.

`--oracle` đo thêm nhận diện trên crop theo nhãn, tách riêng scene/zoom;
không dùng nhãn để chọn vùng trong luồng tự động.

```powershell
.\.venv\Scripts\python.exe tools\offline_smoke.py `
  --reference .local\results.json --reviewed .local\blind-review.json `
  --backup-root E:\backup-tramcan --out artifacts\offline-smoke.json
```

Lệnh smoke cuối dùng bộ 522 ảnh đã có tại máy kiểm tra; chặn HTTP/socket
Python trong lúc chạy OCR thật. `tools/replay_decisions.py` cho phép so
sánh chính sách thập phân/lọc trên observations đã lưu, không chạy lại OCR;
báo cáo ghi rõ `postprocessing_only`.

## Giấy phép

Mã repo: Apache-2.0. Nguồn gốc và giấy phép thành phần/model được ghi trong
`NOTICE`, `licenses/` và file khóa model. Ảnh, nhãn, cấu hình và dữ liệu
xưởng không thuộc giấy phép mã nguồn này.
