# Cài bản thử OCR tại xưởng — 0.2.0-trial1

File cần mang sang máy khách: **TramCanOCRTrial-Setup-0.2.0-trial1.exe**.

1. Đóng phần mềm đang sử dụng camera cân.
2. Chạy file cài → Next → Install. Cài cho tài khoản Windows hiện tại, không cần quyền admin.
3. Mở shortcut **Tram Can OCR - Ban thu** trên Desktop.
4. Chọn **Camera 0 → Mở camera**. Nếu không có hình, thử Camera 1/2;
   hoặc đổi DirectShow sang Media Foundation rồi mở lại.
5. Bấm **Chọn vùng số cân**, kéo bao trọn đúng một dòng số, gồm cả dấu thập phân.
   Tránh cắt mất chữ số đầu hoặc lấy lẫn dòng Tare/Net. Có thể bấm **Tự tìm LED đỏ** để so sánh.
6. Tùy chọn **Cân luôn có 2 số thập phân** mặc định bật cho cân đang thử.
   Khi bật, OCR `120` được diễn giải là `1.20 kg`. Tắt nếu cân không cố định hai số sau dấu.
7. Thay đổi tải, thử số 0, số nhỏ/lớn, các chữ số 1/2/3/7/8 và nhiều góc/ánh sáng.
   Đối chiếu trực tiếp với cân thật. Nếu sai, chỉnh vùng/camera và thử lại.
8. Đóng cửa sổ sau khi thử; mở lại phần mềm cân cũ để làm việc bình thường.

**Chỉ thử nhận diện.** Model vẫn có lỗi nhầm 7 thành 2 và bỏ chữ số đầu trên một số ảnh đã kiểm tra.
Điểm model cao không bảo đảm đọc đúng. Bản này không có nút lưu/chốt phiếu.

- Camera, vùng chọn và kết quả chỉ nằm trong RAM; đóng ứng dụng sẽ xóa.
- Không ghi DB, phiếu cân, ảnh chụp, lịch sử hoặc cấu hình người dùng.
- Không đọc `.env`, không dùng chung dữ liệu/cấu hình của hai bản hiện tại.
- Không gọi Gemini/API, không tải model khi chạy; model đã kèm trong bộ cài.
- Cài riêng ở `%LOCALAPPDATA%\Programs\TramCanOCRTrial`; gỡ trong Windows Apps.
  Việc cài/gỡ chỉ quản lý file ứng dụng, không đụng thư mục dữ liệu Trạm Cân QR.
- Không cần Python, CUDA, GPU hoặc Internet để nhận diện. Yêu cầu Windows 10/11 x64.
- Chưa có tự động cập nhật trong bản thử này.

Nếu Windows hiện SmartScreen: bộ cài chưa ký số. Chỉ tiếp tục khi file nhận trực tiếp
từ người triển khai và khớp SHA256SUMS.txt đi kèm. Không cần tắt Defender.

Nếu không có camera: kiểm tra cáp, Windows Settings → Privacy → Camera → cho phép
desktop apps; đóng ứng dụng khác đang chiếm camera. Bản này hỗ trợ camera USB/thiết bị
video Windows theo số thứ tự, chưa có RTSP. **Mở ảnh thử…** chỉ đọc file ảnh có sẵn.
