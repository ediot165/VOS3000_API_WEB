# vos_api_fastapi/routers/customers_router.py

from fastapi import APIRouter, HTTPException, Path
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

# Import các module cần thiết
import config
import customer_management # "Bộ não" xử lý khách hàng
# import utils # (Nếu bạn cần)

# --- Pydantic Models (Giữ nguyên như trước) ---
class CustomerBase(BaseModel):
    AccountID: Optional[str] = None
    CustomerName: Optional[str] = None
    BalanceRaw: Optional[float] = None
    CreditLimitRaw: Optional[float] = None
    Status: Optional[str] = None
    ServerName: Optional[str] = None
    agentAccount: Optional[str] = None
    feeRateGroup: Optional[str] = None
    todayConsumption: Optional[float] = None
    type: Optional[str] = None
    category: Optional[str] = None
    startTime: Optional[Any] = None
    validTime: Optional[Any] = None
    memo: Optional[str] = None
    lockType: Optional[str] = None
    _server_url: Optional[str] = None

    class Config:
        from_attributes = True

class CustomerCreditLimitUpdateRequest(BaseModel):
    new_credit_limit: str

class CustomerLockStatusUpdateRequest(BaseModel):
    lock_status: str

# --- Helper Function (Có thể đã có hoặc chuyển vào utils.py) ---
def _get_server_info_by_name(server_name: str) -> Optional[Dict[str, str]]:
    return next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)

# --- Router Setup (Giữ nguyên) ---
router = APIRouter(
    prefix="/customers",
    tags=["Chăm Sóc Khách Hàng"]
)

# --- Endpoint Tìm Kiếm (Giữ nguyên như đã sửa) ---
@router.get("/search/",
            response_model=List[CustomerBase],
            summary="Tìm kiếm khách hàng trên tất cả server")
async def search_customers_api(filter_type: str, filter_text: str ):
    # ... (code của hàm search_customers_api giữ nguyên) ...
    print(f"API Router (Customer Search): filter_type='{filter_type}', filter_text='{filter_text}'")
    try:
        danh_sach_khach_hang = customer_management.find_customers_across_all_servers(
            filter_type=filter_type,
            filter_text=filter_text
        )
        if not danh_sach_khach_hang:
            return []
        return danh_sach_khach_hang
    except Exception as e:
        print(f"API Router (Customer Search): Lỗi khi tìm kiếm: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server khi tìm kiếm khách hàng: {str(e)}")

# --- Endpoint Lấy Chi Tiết Khách Hàng (VIẾT LẠI ĐẦY ĐỦ VÀ CHÍNH XÁC) ---
@router.get("/{server_name}/{customer_account_id}/details/",
            response_model=CustomerBase,
            summary="Lấy thông tin chi tiết của một khách hàng")
async def get_customer_detail_api(
    server_name: str,
    customer_account_id: str
):
    print(f"API Router (Customer Detail): Yêu cầu chi tiết KH '{customer_account_id}' trên server '{server_name}'")

    server_info_found = _get_server_info_by_name(server_name)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy server với tên '{server_name}'.")

    try:
        # 1. Gọi hàm từ customer_management để lấy dữ liệu
        # Hàm này trả về: (dữ liệu thô từ VOS, danh sách đã format cho Streamlit, thông báo lỗi)
        raw_details_from_vos, display_list_ignore, error_msg = customer_management.get_customer_details_for_display(
            base_url=server_info_found["url"],
            server_name=server_name, # Hoặc server_info_found["name"]
            customer_account=customer_account_id
        )

        # 2. Kiểm tra lỗi hoặc không có dữ liệu thô
        if error_msg:
            if "not found" in error_msg.lower() or "không tìm thấy" in error_msg.lower():
                 raise HTTPException(status_code=404, detail=f"KH '{customer_account_id}' không tồn tại trên server '{server_name}' hoặc có lỗi: {error_msg}")
            # Các lỗi khác từ backend (ví dụ: không kết nối được VOS)
            raise HTTPException(status_code=400, detail=f"Lỗi khi lấy chi tiết KH '{customer_account_id}': {error_msg}")

        if not raw_details_from_vos: # Nếu không có lỗi nhưng cũng không có dữ liệu thô
            raise HTTPException(status_code=404, detail=f"Không tìm thấy thông tin chi tiết thô cho KH '{customer_account_id}' trên server '{server_name}'.")

        # DEBUG: In ra dữ liệu thô nhận được từ VOS (qua hàm get_customer_details_for_display)
        print(f"DEBUG API Endpoint (get_customer_detail_api) - Dữ liệu thô gốc từ VOS: {raw_details_from_vos}")

        # 3. Ánh xạ và xử lý dữ liệu từ `raw_details_from_vos` sang các trường của `CustomerBase`
        # Đây là bước quan trọng để đảm bảo các trường như AccountID, CustomerName, Status có giá trị.
        
        lock_type_from_vos = raw_details_from_vos.get("lockType") # VOS có thể trả về số hoặc chuỗi, hoặc None
        status_val = "Locked" if str(lock_type_from_vos) == "1" else "Active"

        credit_limit_raw_val = 0.0 # Giá trị mặc định nếu không có hoặc không hợp lệ
        limit_money_from_vos = raw_details_from_vos.get("limitMoney")
        if limit_money_from_vos is not None:
            limit_money_str = str(limit_money_from_vos).strip().lower()
            if limit_money_str in ["-1", "-1.0", "infinity", "unlimited", "không giới hạn"]:
                credit_limit_raw_val = -1.0
            else:
                try:
                    credit_limit_raw_val = float(limit_money_from_vos)
                except (ValueError, TypeError):
                    # Giữ giá trị mặc định 0.0 nếu không parse được
                    pass
        
        balance_raw_val = None # Mặc định là None nếu không có hoặc không hợp lệ
        money_from_vos = raw_details_from_vos.get("money")
        if money_from_vos is not None:
            try:
                balance_raw_val = float(money_from_vos)
            except (ValueError, TypeError):
                pass # Giữ None

        # Tạo dictionary kết quả để trả về, đảm bảo khớp với CustomerBase
        processed_details_for_response = {
            "AccountID": raw_details_from_vos.get("account", customer_account_id), # Ưu tiên key "account" từ VOS
            "CustomerName": raw_details_from_vos.get("name"), # Ưu tiên key "name" từ VOS
            "BalanceRaw": balance_raw_val,
            "CreditLimitRaw": credit_limit_raw_val,
            "Status": status_val,
            "ServerName": server_name, # Lấy từ path param
            "_server_url": server_info_found["url"],

            # Các trường chi tiết khác, lấy trực tiếp từ raw_details_from_vos nếu có
            "agentAccount": raw_details_from_vos.get("agentAccount"),
            "feeRateGroup": raw_details_from_vos.get("feeRateGroup"),
            "todayConsumption": raw_details_from_vos.get("todayConsumption"),
            "type": str(raw_details_from_vos.get("type")) if raw_details_from_vos.get("type") is not None else None,
            "category": str(raw_details_from_vos.get("category")) if raw_details_from_vos.get("category") is not None else None,
            "startTime": raw_details_from_vos.get("startTime"),
            "validTime": raw_details_from_vos.get("validTime"),
            "memo": raw_details_from_vos.get("memo"),
            "lockType": str(lock_type_from_vos) if lock_type_from_vos is not None else "0" # Đảm bảo trả về "0" (Active) nếu VOS không có hoặc null
        }
        
        print(f"DEBUG API Endpoint (get_customer_detail_api) - Dữ liệu đã xử lý để trả về: {processed_details_for_response}")
        
        # FastAPI sẽ dùng Pydantic model CustomerBase để validate và serialize dict này
        return processed_details_for_response

    except HTTPException: # Để các HTTPException đã raise được trả về đúng
        raise
    except Exception as e:
        print(f"API Router (Customer Detail): Lỗi nghiêm trọng khi lấy chi tiết KH '{customer_account_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server khi lấy chi tiết KH. Chi tiết: {str(e)}")


# --- Endpoint Cập Nhật Hạn Mức (Giữ nguyên) ---
@router.put("/{server_name}/{customer_account_id}/credit-limit/",
            response_model=Dict[str, str],
            summary="Cập nhật hạn mức tín dụng cho khách hàng")
async def update_customer_credit_limit_api(
    server_name: str,
    customer_account_id: str,
    request_data: CustomerCreditLimitUpdateRequest
):
    # ... (code của hàm update_customer_credit_limit_api giữ nguyên) ...
    print(f"API Router (Update Credit Limit): KH '{customer_account_id}' on '{server_name}' to '{request_data.new_credit_limit}'")
    server_info_found = _get_server_info_by_name(server_name)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy server '{server_name}'.")
    try:
        success, message = customer_management.update_customer_credit_limit(
            server_url=server_info_found["url"],
            customer_account=customer_account_id,
            new_credit_limit_str=request_data.new_credit_limit
        )
        if not success:
            raise HTTPException(status_code=400, detail=message or "Không thể cập nhật hạn mức tín dụng.")
        return {"message": message or "Cập nhật hạn mức tín dụng thành công."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router (Update Credit Limit): Lỗi: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")


# --- Endpoint Khóa/Mở Khóa (Giữ nguyên) ---
@router.put("/{server_name}/{customer_account_id}/lock-status/",
            response_model=Dict[str, str],
            summary="Khóa hoặc mở khóa tài khoản khách hàng")
async def update_customer_lock_status_api(
    server_name: str,
    customer_account_id: str,
    request_data: CustomerLockStatusUpdateRequest
):
    # ... (code của hàm update_customer_lock_status_api giữ nguyên) ...
    print(f"API Router (Update Lock Status): KH '{customer_account_id}' on '{server_name}' to '{request_data.lock_status}'")
    if request_data.lock_status not in ["0", "1"]:
        raise HTTPException(status_code=422, detail="Giá trị 'lock_status' không hợp lệ. Phải là '0' (Active) hoặc '1' (Locked).")

    server_info_found = _get_server_info_by_name(server_name)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy server '{server_name}'.")
    try:
        success, message = customer_management.update_customer_lock_status(
            server_url=server_info_found["url"],
            customer_account=customer_account_id,
            new_lock_status_str=request_data.lock_status
        )
        if not success:
            raise HTTPException(status_code=400, detail=message or "Không thể cập nhật trạng thái khóa.")
        return {"message": message or "Cập nhật trạng thái khóa thành công."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router (Update Lock Status): Lỗi: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")