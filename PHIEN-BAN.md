# Nhật ký phiên bản website lhcviet.com

Mỗi lần cập nhật lớn ghi một dòng: ngày, commit đã đưa lên web, mã SHA-256 của thư mục `docs/` (trừ CNAME; cách tính: `cd docs && find . -type f ! -name CNAME -print0 | sort -z | xargs -0 sha256sum | sha256sum`), và bản lưu Internet Archive. Lịch sử commit trên GitHub ghi thời điểm đăng; mã SHA-256 chứng minh nội dung không bị sửa sau đó.

| Ngày | Phiên bản | Commit | SHA-256 thư mục docs/ | Internet Archive | Nội dung thay đổi |
| --- | --- | --- | --- | --- | --- |
| 10/11/2026 | web-2026.11.10 | 054d8f0 | 0f5de26905c44417372d9346a8861f463e8307954720090f283d52dc866c4e39 | https://web.archive.org/web/2026*/lhcviet.com* | Thêm trang Điều khoản sử dụng, dòng bản quyền ở footer, LICENSE |
