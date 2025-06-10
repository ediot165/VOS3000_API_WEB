# Hệ Thống Quản Lý VOS3000 (VOS3000 Management System)

Đây là một ứng dụng web được xây dựng bằng Streamlit để quản lý và tương tác với nhiều server VOS3000, giúp đơn giản hóa các tác vụ quản trị VoIP.

## Tính Năng Chính

* **Cấu hình Server VOS3000:** Xem và cấu hình chi tiết Mapping Gateways (MG) và Routing Gateways (RG).
* **Quản lý Khách Hàng:** Tìm kiếm, xem chi tiết, cập nhật hạn mức, khóa/mở tài khoản khách hàng trên nhiều server.
* **Tra Cứu Thông Tin Số:** Tìm kiếm sự xuất hiện của một số điện thoại (và các biến thể) trong cấu hình MG/RG.
* **Dọn Dẹp Gateway:** Xóa các số điện thoại khỏi MG (CalloutCallerPrefixes) và RG (CallinCallerPrefixes, CallinCalleePrefixes, Rewrite Rules) trên nhiều server.
* **Quản lý Số Ảo (Rewrite Rules):** Tra cứu, sửa đổi, và thay thế số thật cho một Số ảo Đích trong RG.
* **Thêm Server VOS Mới (Trong Phiên):** Cho phép người dùng tạm thời thêm server VOS mới vào danh sách để thao tác trong phiên làm việc hiện tại.

## Yêu Cầu Hệ Thống

* Python 3.9 trở lên (khuyến nghị 3.10+)
* PIP (Python package installer)

## Hướng Dẫn Cài Đặt



1.  **Tạo Môi Trường Ảo (Khuyến Nghị):**
    Việc sử dụng môi trường ảo giúp quản lý các gói phụ thuộc tốt hơn.
    ```bash
    python -m venv venv
    ```
    Kích hoạt môi trường ảo:
    * Windows:
        ```bash
        venv\Scripts\activate
        ```
    * macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

2.  **Cài Đặt Các Gói Phụ Thuộc:**
    Ứng dụng này yêu cầu một số thư viện Python. Hãy tạo một file `requirements.txt` với nội dung sau (hoặc thêm các thư viện bạn đã dùng mà tôi có thể đã bỏ sót):

    ```txt
    streamlit
    streamlit-option-menu
    pandas
    requests


    Sau đó, cài đặt các gói này bằng pip:
    ```bash
    pip install -r requirements.txt
    ```
    Nếu bạn không có file `requirements.txt`, bạn có thể cài đặt từng gói một:
    ```bash
    pip install streamlit streamlit-option-menu pandas requests
    ```

3.  **Cấu Hình Server VOS:**
    Mở file `config.py` (nếu bạn đặt các file backend trong thư mục con như `backup`, đường dẫn sẽ là `backup/config.py`).
    Chỉnh sửa danh sách `VOS_SERVERS` để bao gồm thông tin (tên và URL API) của các server VOS3000 bạn muốn quản lý:
    ```python
    # Ví dụ trong config.py
    VOS_SERVERS = [
        {"name": "VOS-01 (IP: 171.244.56.166)", "url": "[http://171.244.56.166:3161/external_new/server/](http://171.244.56.166:3161/external_new/server/)"},
        {"name": "VOS-02 (IP: 171.244.56.167)", "url": "[http://171.244.56.167:2718/external/server/](http://171.244.56.167:2718/external/server/)"},
        # Thêm các server khác của bạn vào đây
    ]
    ```

4.  **Cấu Trúc Thư Mục (Quan trọng):**
    * **Cách 1 (Tất cả file ngang hàng):** Đặt tất cả các file Python (`app.py`, `config.py`, `api_client.py`, `utils.py`, `customer_management.py`, `mapping_gateway_management.py`, `routing_gateway_management.py`, `ui_utils.py`) trong cùng một thư mục. Nếu theo cách này, đảm bảo bạn đã **xóa** đoạn code thêm thư mục `backup` (hoặc tên thư mục con khác) vào `sys.path` ở đầu file `app.py`.
    * **Cách 2 (Sử dụng thư mục con cho backend, ví dụ `backup`):** Nếu bạn đặt các file backend (ngoại trừ `app.py`) vào một thư mục con (ví dụ: tên là `backup`), hãy đảm bảo rằng đoạn code sau có trong `app.py` để Python có thể tìm thấy các module đó:
        ```python
        # Ở đầu file app.py
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_modules_dir = os.path.join(current_dir, "backup") # Thay "backup" bằng tên thư mục con của bạn
        if backend_modules_dir not in sys.path:
            sys.path.insert(0, backend_modules_dir)
        ```
    * **Cách 3 (Sử dụng thư mục `pages_app` cho các trang con của `app.py`):** Nếu bạn đã tách các trang con của `app.py` (như `configure_server.py`, `customer_management_page.py`, v.v.) ra thư mục `pages_app` như tôi đã gợi ý, đảm bảo thư mục này tồn tại và các file trang con nằm trong đó.

## Cách Chạy Ứng Dụng

1.  Mở terminal hoặc command prompt.
2.  Điều hướng đến thư mục gốc của project (nơi chứa file `app.py`).
3.  Nếu bạn sử dụng môi trường ảo, hãy kích hoạt nó.
4.  Chạy lệnh sau:
    ```bash
    streamlit run app.py
    ```
5.  Streamlit sẽ tự động mở ứng dụng trong trình duyệt web của bạn. Nếu không, hãy mở trình duyệt và truy cập vào địa chỉ Local URL mà Streamlit hiển thị trên terminal (thường là `http://localhost:8501`).

## Các Module Backend

* `config.py`: Chứa các cấu hình chung như danh sách server VOS, timeout mặc định.
* `api_client.py`: Xử lý việc thực hiện các lời gọi API đến VOS3000 server.
* `utils.py`: Chứa các hàm tiện ích chung (phân loại số, biến đổi số, định dạng tiền, xử lý rewrite rules).
* `ui_utils.py`: Chứa các tiện ích hiển thị an toàn (hiện tại chủ yếu là `safe_display`).
* `customer_management.py`: Logic nghiệp vụ cho việc quản lý khách hàng.
* `mapping_gateway_management.py`: Logic nghiệp vụ cho việc quản lý Mapping Gateway.
* `routing_gateway_management.py`: Logic nghiệp vụ cho việc quản lý Routing Gateway và số ảo.

## Gỡ Lỗi (Troubleshooting)

* **Lỗi `ImportError`:**
    * Đảm bảo bạn đã cài đặt tất cả các gói trong `requirements.txt` (hoặc các gói được liệt kê).
    * Kiểm tra cấu trúc thư mục và `sys.path` trong `app.py` nếu bạn đặt các module backend vào thư mục con.
    * Đảm bảo tên các hàm được import trong `app.py` và giữa các module backend với nhau là chính xác (đặc biệt sau quá trình refactor đổi tên hàm sang tiếng Anh).
* **Không kết nối được VOS Server:**
    * Kiểm tra lại URL và port của các server VOS trong `config.py`.
    * Đảm bảo máy tính chạy ứng dụng Streamlit có thể kết nối mạng đến các server VOS đó.
    * Kiểm tra firewall trên server VOS hoặc trên máy tính của bạn.

