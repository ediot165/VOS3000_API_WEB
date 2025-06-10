# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# KHÔNG CẦN import HTTPException, List, BaseModel ở đây nữa nếu đã chuyển hết sang router
# KHÔNG CẦN import customer_management ở đây nữa nếu chỉ dùng trong router

import config
from routers import (
    customers_router,
    gateways_router,
    number_info_router,
    cleanup_router,
    qvn_router  # <--- THÊM DÒNG NÀY: Import "khu vực khách hàng"
)
    

# 1. Khởi tạo "trụ sở chính" của API (giữ nguyên)
app = FastAPI(
    title="VOS Management API (Triển Khai Với FastAPI)",
    description="API để quản lý các chức năng của hệ thống VOS3000, được giải thích từng bước.",
    version="0.1.0"
)
origins = [
    "http://localhost:5173", # Port mặc định của Vite cho React
    "http://localhost:3000", # Port phổ biến khác cho React dev server
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Cho phép các origin này
    allow_credentials=True,    # Cho phép gửi cookie
    allow_methods=["*"],       # Cho phép tất cả các phương thức GET, POST, PUT, etc.
    allow_headers=["*"],       # Cho phép tất cả các header
)

# 2. "Quầy lễ tân" (giữ nguyên)
@app.get("/")
async def trang_chu_api():
    return {"thong_bao": "Chào mừng bạn đến với VOS Management API phiên bản FastAPI! Chúng ta đang đi từng bước."}

# 3. "Quầy Giao Dịch": Lấy danh sách server (giữ nguyên)
@app.get("/servers/")
async def lay_danh_sach_server():
    danh_sach_server = config.VOS_SERVERS
    return {"cac_server_da_cau_hinh": danh_sach_server}

# 4. "Lắp ráp" khu vực quản lý khách hàng vào "trụ sở chính"
app.include_router(customers_router.router) # <--- THÊM DÒNG NÀY
app.include_router(gateways_router.router)
app.include_router(number_info_router.router)
app.include_router(cleanup_router.router)
app.include_router(qvn_router.router)
# (Nếu có các khu vực khác, ví dụ cho gateways, bạn cũng sẽ include_router tương tự)