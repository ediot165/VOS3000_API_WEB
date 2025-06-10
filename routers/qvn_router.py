# vos_api_fastapi/routers/qvn_router.py
from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional, Dict, Any, Union # Thêm Union cho response_model

from pydantic import BaseModel, Field
from enum import Enum

# Import các module cần thiết
import config
import utils # Sẽ chứa hàm apply_rg_locktype_logic và các hàm parse/format rule
import routing_gateway_management

# --- Định nghĩa Enums cho các lựa chọn ---
class QVNSourceType(str, Enum):
    AUTO_BACKUP = "auto_backup_in_target_rg"
    MANUAL_KEY = "manual_key"

class QVNTargetAction(str, Enum):
    ADD = "add"
    REPLACE = "replace"

class QVNEmptySourceAction(str, Enum):
    HETSO = "hetso"
    EMPTY = "empty"
    DELETE_KEY = "delete_key"

# --- Định nghĩa Khuôn Mẫu Dữ Liệu (Pydantic Models) ---

class RewriteKeyDefinition(BaseModel):
    virtual_key: str # Key tìm thấy (target_vn hoặc source_key)
    server_name: str
    server_url: str
    rg_name: str
    reals: List[str]
    real_numbers_count: int
    is_hetso: bool
    raw_rg_info: Dict[str, Any]

    class Config:
        from_attributes = True

class QVNTargetVNInfo(BaseModel):
    virtual_key: str = Field(..., description="Khóa ảo của Target VN.")
    server_name: str = Field(..., description="Tên server chứa Target VN (phải có trong config.VOS_SERVERS).")
    rg_name: str = Field(..., description="Tên Routing Gateway chứa Target VN.")

class QVNSourceInfo(BaseModel):
    type: QVNSourceType = Field(..., description="Loại nguồn: 'auto_backup_in_target_rg' hoặc 'manual_key'.")
    virtual_key: str = Field(..., description="Khóa ảo của nguồn (tên key backup nếu là auto, tên key nguồn nếu là manual).")
    # server_name và rg_name của nguồn chỉ cần nếu type='manual_key' VÀ nguồn khác RG/server với Target.
    # Nếu type='manual_key' và các trường này là None, API hiểu là nguồn cùng RG với Target.
    server_name: Optional[str] = Field(None, description="Tên server chứa Source VN (nếu khác Target Server và type='manual_key').")
    rg_name: Optional[str] = Field(None, description="Tên RG chứa Source VN (nếu khác Target RG và type='manual_key').")

class QVNExecutionRequest(BaseModel):
    target_vn: QVNTargetVNInfo
    source_info: QVNSourceInfo
    numbers_to_take_from_source: int = Field(..., gt=0, description="Số lượng số thực muốn lấy từ nguồn (phải > 0).")
    action_on_target_vn_reals: QVNTargetAction = Field(..., description="Hành động với số thực của Target VN: 'add' hoặc 'replace'.")
    action_on_empty_source_key: Optional[QVNEmptySourceAction] = Field(None, description="Hành động với Source Key nếu nó rỗng sau khi lấy số: 'hetso', 'empty', 'delete_key'. Bắt buộc nếu source có thể trở nên rỗng.")
    dry_run: bool = Field(False, description="True để xem trước thay đổi, False để thực thi.")

class QVNChangeDetail(BaseModel):
    gateway_type: str = "RG"
    server_name: str
    rg_name: str
    virtual_key_affected: str
    old_reals: Optional[List[str]] = None
    new_reals: Optional[List[str]] = None
    action_taken: str
    old_lock_type: Optional[Any] = None
    new_lock_type: Optional[Any] = None
    message: Optional[str] = None

class QVNPreviewResponse(BaseModel):
    target_vn_changes: QVNChangeDetail
    source_vn_changes: Optional[QVNChangeDetail] = None
    summary: str
    warnings: List[str] = []

class QVNExecutionResultItem(BaseModel):
    server_name: str
    rg_name: str
    virtual_key_affected: str
    status: str  # "Success", "Failed", "Skipped", "NoChangeNeeded"
    message: str
    changed_reals: Optional[List[str]] = None
    changed_lock_type: Optional[Any] = None

class QVNExecutionResponse(BaseModel):
    target_rg_result: QVNExecutionResultItem
    source_rg_result: Optional[QVNExecutionResultItem] = None
    overall_status: str # "Completed", "CompletedWithErrors", "Failed"
    final_message: str

# --- Khởi tạo "Khu Vực" (Router) cho QVN ---
router = APIRouter(
    prefix="/qvn",
    tags=["Quản Lý Số Ảo (QVN)"]
)

# --- Helper Functions (có thể đặt trong utils.py nếu muốn) ---
def _get_server_info_by_name(server_name: str) -> Optional[Dict[str, str]]:
    return next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)

# --- Các "Quầy Giao Dịch" (Endpoints) ---

@router.get("/target-vn-definitions/{virtual_key}",
            response_model=List[RewriteKeyDefinition],
            summary="Tìm tất cả các định nghĩa của một Target VN mục tiêu")
async def find_target_vn_definitions_api(
    virtual_key: str = Path(..., description="Khóa ảo của Target VN cần tìm, ví dụ: '500555'")
):
    print(f"API Router (QVN): Tìm Target VN definitions cho key: '{virtual_key}'")
    if not virtual_key.strip():
        raise HTTPException(status_code=400, detail="Virtual key không được để trống.")
    try:
        definitions_found, error_msg = routing_gateway_management.find_specific_virtual_number_definitions_backend(virtual_key_to_find=virtual_key)
        if error_msg:
            raise HTTPException(status_code=503, detail=f"Lỗi khi truy vấn backend để tìm Target VN: {error_msg}")
        if definitions_found is None:
             raise HTTPException(status_code=500, detail="Lỗi không mong muốn từ backend khi tìm Target VN.")
        return definitions_found
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router (QVN): Lỗi nghiêm trọng khi tìm Target VN '{virtual_key}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")

@router.get("/source-key-definitions/",
            response_model=List[RewriteKeyDefinition],
            summary="Tìm các Rewrite Rule Key có thể dùng làm nguồn số thực")
async def find_source_key_definitions_api(
    search_term: str = Query(..., min_length=1, description="Từ khóa để tìm Rewrite Rule Key (có thể là một phần tên)")
):
    print(f"API Router (QVN): Tìm Source Key definitions với từ khóa: '{search_term}'")
    try:
        definitions_found, error_msg = routing_gateway_management.find_rewrite_rule_keys_globally_backend(search_key_term_str=search_term)
        if error_msg:
            raise HTTPException(status_code=503, detail=f"Lỗi khi truy vấn backend để tìm Source Key: {error_msg}")
        if definitions_found is None:
             raise HTTPException(status_code=500, detail="Lỗi không mong muốn từ backend khi tìm Source Key.")
        
        processed_definitions = []
        for item_dict in definitions_found:
            item_dict_copy = item_dict.copy()
            if "found_key" in item_dict_copy and "virtual_key" not in item_dict_copy:
                item_dict_copy["virtual_key"] = item_dict_copy.pop("found_key")
            processed_definitions.append(item_dict_copy)
        return processed_definitions
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router (QVN): Lỗi nghiêm trọng khi tìm Source Key '{search_term}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")


@router.post("/execute-operation/",
             response_model=Union[QVNPreviewResponse, QVNExecutionResponse], # Trả về 1 trong 2 model này
             summary="Thực thi hoặc xem trước nghiệp vụ QVN")
async def execute_qvn_operation(request: QVNExecutionRequest):
    print(f"API Router (QVN Execute): Yêu cầu QVN cho target '{request.target_vn.virtual_key}', dry_run: {request.dry_run}")

    # --- PHẦN 1: THU THẬP DỮ LIỆU BAN ĐẦU ---
    target_server_info = _get_server_info_by_name(request.target_vn.server_name)
    if not target_server_info:
        raise HTTPException(status_code=404, detail=f"Target server '{request.target_vn.server_name}' không tìm thấy.")

    target_rg_details_raw, err_target_rg = routing_gateway_management.get_routing_gateway_details(target_server_info, request.target_vn.rg_name)
    if err_target_rg or not target_rg_details_raw:
        raise HTTPException(status_code=404, detail=f"Không thể lấy thông tin Target RG '{request.target_vn.rg_name}': {err_target_rg}")

    target_rules_dict_initial = utils.parse_vos_rewrite_rules(target_rg_details_raw.get("rewriteRulesInCaller", ""))
    target_current_reals_from_vos = target_rules_dict_initial.get(request.target_vn.virtual_key, [])

    source_server_info = None
    source_rg_details_raw = None
    source_current_reals_from_vos = []
    source_key_to_find = request.source_info.virtual_key # Key nguồn, ví dụ "VN_BK" hoặc key manual
    source_rules_dict_initial_for_source_rg = {} # Dùng nếu source RG khác target RG

    if request.source_info.type == QVNSourceType.AUTO_BACKUP:
        source_server_info = target_server_info
        source_rg_details_raw = target_rg_details_raw
        source_current_reals_from_vos = target_rules_dict_initial.get(source_key_to_find, [])
    elif request.source_info.type == QVNSourceType.MANUAL_KEY:
        source_server_name_actual = request.source_info.server_name or request.target_vn.server_name
        source_rg_name_actual = request.source_info.rg_name or request.target_vn.rg_name

        if source_server_name_actual == target_server_info["name"] and source_rg_name_actual == target_rg_details_raw["name"]:
            source_server_info = target_server_info
            source_rg_details_raw = target_rg_details_raw
            source_current_reals_from_vos = target_rules_dict_initial.get(source_key_to_find, [])
        else:
            source_server_info = _get_server_info_by_name(source_server_name_actual)
            if not source_server_info:
                raise HTTPException(status_code=404, detail=f"Source server '{source_server_name_actual}' không tìm thấy.")
            source_rg_details_raw, err_source_rg = routing_gateway_management.get_routing_gateway_details(source_server_info, source_rg_name_actual)
            if err_source_rg or not source_rg_details_raw:
                raise HTTPException(status_code=404, detail=f"Không thể lấy thông tin Source RG '{source_rg_name_actual}': {err_source_rg}")
            source_rules_dict_initial_for_source_rg = utils.parse_vos_rewrite_rules(source_rg_details_raw.get("rewriteRulesInCaller", ""))
            source_current_reals_from_vos = source_rules_dict_initial_for_source_rg.get(source_key_to_find, [])
    
    source_current_reals_clean = [r for r in source_current_reals_from_vos if r.lower() != "hetso"]
    if not source_current_reals_clean and request.numbers_to_take_from_source > 0:
        raise HTTPException(status_code=400, detail=f"Source VN '{source_key_to_find}' rỗng hoặc chỉ chứa 'hetso', không thể lấy số.")
    if request.numbers_to_take_from_source > len(source_current_reals_clean):
        raise HTTPException(status_code=400, detail=f"Yêu cầu lấy {request.numbers_to_take_from_source} số nhưng nguồn chỉ có {len(source_current_reals_clean)} số thực.")

    numbers_actually_taken = source_current_reals_clean[:request.numbers_to_take_from_source]
    remaining_reals_in_source = source_current_reals_clean[request.numbers_to_take_from_source:]

    # --- PHẦN 2: TÍNH TOÁN CÁC THAY ĐỔI DỰ KIẾN ---
    target_current_reals_clean = [r for r in target_current_reals_from_vos if r.lower() != "hetso"]
    new_reals_for_target_calculated = []
    target_action_taken_msg = ""

    if request.action_on_target_vn_reals == QVNTargetAction.ADD:
        new_reals_for_target_calculated = list(dict.fromkeys(target_current_reals_clean + numbers_actually_taken))
        target_action_taken_msg = f"Đã thêm {len(numbers_actually_taken)} số vào Target VN."
    elif request.action_on_target_vn_reals == QVNTargetAction.REPLACE:
        new_reals_for_target_calculated = numbers_actually_taken
        target_action_taken_msg = f"Đã thay thế số của Target VN bằng {len(numbers_actually_taken)} số từ Source."
    
    if not new_reals_for_target_calculated and utils.is_six_digit_virtual_number_candidate(request.target_vn.virtual_key):
        new_reals_for_target_calculated = ["hetso"]
        target_action_taken_msg += " Target VN rỗng sau đó, được đặt thành 'hetso'."

    new_reals_for_source_calculated = remaining_reals_in_source
    source_action_taken_msg = f"Source VN còn lại {len(remaining_reals_in_source)} số."
    if not remaining_reals_in_source:
        if not request.action_on_empty_source_key:
            raise HTTPException(status_code=400, detail="Source VN đã rỗng sau khi lấy số nhưng 'action_on_empty_source_key' không được cung cấp.")
        if request.action_on_empty_source_key == QVNEmptySourceAction.HETSO:
            new_reals_for_source_calculated = ["hetso"]
            source_action_taken_msg = "Source VN rỗng, được đặt thành 'hetso'."
        elif request.action_on_empty_source_key == QVNEmptySourceAction.EMPTY:
            new_reals_for_source_calculated = []
            source_action_taken_msg = "Source VN rỗng, được để trống (xóa hết số thực)."
        elif request.action_on_empty_source_key == QVNEmptySourceAction.DELETE_KEY:
            new_reals_for_source_calculated = [] # Sẽ bị xóa key
            source_action_taken_msg = "Source VN rỗng, KEY SẼ BỊ XÓA."


    # --- PHẦN 3: CHUẨN BỊ PAYLOAD CẬP NHẬT VÀ ÁP DỤNG LOCKTYPE ---
    # TARGET RG PAYLOAD
    target_rg_payload_final = target_rg_details_raw.copy()
    target_rules_dict_for_update = utils.parse_vos_rewrite_rules(target_rg_payload_final.get("rewriteRulesInCaller", ""))
    original_target_locktype_str = str(target_rg_payload_final.get("lockType", "0"))

    target_rules_dict_for_update[request.target_vn.virtual_key] = new_reals_for_target_calculated

    is_source_in_same_rg_as_target = (source_server_info["name"] == target_server_info["name"] and \
                                   source_rg_details_raw["name"] == target_rg_details_raw["name"])

    if is_source_in_same_rg_as_target:
        if source_action_taken_msg.startswith("KEY SẼ BỊ XÓA") and source_key_to_find in target_rules_dict_for_update:
            del target_rules_dict_for_update[source_key_to_find]
        elif not source_action_taken_msg.startswith("KEY SẼ BỊ XÓA"): # chỉ cập nhật nếu không phải xóa key
            target_rules_dict_for_update[source_key_to_find] = new_reals_for_source_calculated
        
    target_rg_payload_final["rewriteRulesInCaller"] = utils.format_rewrite_rules_for_vos(target_rules_dict_for_update)
    # QUAN TRỌNG: Gọi hàm logic lockType
    # Hàm này được kỳ vọng sẽ chỉnh sửa target_rg_payload_final["lockType"]
    try:
        utils.apply_rg_locktype_logic(target_rg_payload_final, target_rules_dict_for_update)
    except AttributeError: # Nếu hàm utils.apply_rg_locktype_logic chưa có
        print("CẢNH BÁO QVN: Hàm utils.apply_rg_locktype_logic chưa được định nghĩa hoặc import! Bỏ qua cập nhật lockType.")
        # Giữ nguyên lockType gốc nếu hàm không tồn tại để tránh lỗi
        target_rg_payload_final["lockType"] = original_target_locktype_str

    final_target_locktype_str = str(target_rg_payload_final.get("lockType"))

    # SOURCE RG PAYLOAD (nếu khác target và không bị xóa key ở bước trên)
    source_rg_payload_final = None
    original_source_locktype_str = None
    final_source_locktype_str = None
    if not is_source_in_same_rg_as_target and not source_action_taken_msg.startswith("KEY SẼ BỊ XÓA"):
        source_rg_payload_final = source_rg_details_raw.copy()
        source_rules_dict_for_update = utils.parse_vos_rewrite_rules(source_rg_payload_final.get("rewriteRulesInCaller", ""))
        original_source_locktype_str = str(source_rg_payload_final.get("lockType", "0"))

        source_rules_dict_for_update[source_key_to_find] = new_reals_for_source_calculated
            
        source_rg_payload_final["rewriteRulesInCaller"] = utils.format_rewrite_rules_for_vos(source_rules_dict_for_update)
        try:
            utils.apply_rg_locktype_logic(source_rg_payload_final, source_rules_dict_for_update)
        except AttributeError:
            print("CẢNH BÁO QVN: Hàm utils.apply_rg_locktype_logic chưa được định nghĩa hoặc import! Bỏ qua cập nhật lockType cho source.")
            source_rg_payload_final["lockType"] = original_source_locktype_str
        final_source_locktype_str = str(source_rg_payload_final.get("lockType"))
    elif not is_source_in_same_rg_as_target and source_action_taken_msg.startswith("KEY SẼ BỊ XÓA"):
        # Source RG khác, và key nguồn cần bị xóa khỏi Source RG đó
        source_rg_payload_final = source_rg_details_raw.copy()
        source_rules_dict_for_update = utils.parse_vos_rewrite_rules(source_rg_payload_final.get("rewriteRulesInCaller", ""))
        original_source_locktype_str = str(source_rg_payload_final.get("lockType", "0"))
        if source_key_to_find in source_rules_dict_for_update:
            del source_rules_dict_for_update[source_key_to_find]
        source_rg_payload_final["rewriteRulesInCaller"] = utils.format_rewrite_rules_for_vos(source_rules_dict_for_update)
        try:
            utils.apply_rg_locktype_logic(source_rg_payload_final, source_rules_dict_for_update)
        except AttributeError:
            print("CẢNH BÁO QVN: Hàm utils.apply_rg_locktype_logic chưa được định nghĩa hoặc import! Bỏ qua cập nhật lockType cho source (khi xóa key).")
            source_rg_payload_final["lockType"] = original_source_locktype_str
        final_source_locktype_str = str(source_rg_payload_final.get("lockType"))


    # --- PHẦN 4: DRY RUN HOẶC THỰC THI ---
    if request.dry_run:
        preview_target_changes = QVNChangeDetail(
            server_name=target_server_info["name"], rg_name=target_rg_details_raw["name"],
            virtual_key_affected=request.target_vn.virtual_key,
            old_reals=target_current_reals_from_vos, new_reals=new_reals_for_target_calculated,
            action_taken=f"Target VN: {target_action_taken_msg}",
            old_lock_type=original_target_locktype_str, new_lock_type=final_target_locktype_str
        )
        preview_source_changes = None
        if source_key_to_find:
            old_s_reals = []
            old_s_lock = None
            if is_source_in_same_rg_as_target:
                old_s_reals = utils.parse_vos_rewrite_rules(target_rg_details_raw.get("rewriteRulesInCaller", "")).get(source_key_to_find, []) # Lấy lại reals gốc của source từ target RG ban đầu
                old_s_lock = original_target_locktype_str # Locktype gốc của RG chứa cả hai
                msg_s = f"Source VN (cùng RG Target): {source_action_taken_msg}"
                new_s_lock = final_target_locktype_str # Locktype mới của RG chứa cả hai
            elif source_rg_details_raw: # Source RG khác
                old_s_reals = utils.parse_vos_rewrite_rules(source_rg_details_raw.get("rewriteRulesInCaller", "")).get(source_key_to_find, [])
                old_s_lock = original_source_locktype_str
                msg_s = f"Source VN (RG khác): {source_action_taken_msg}"
                new_s_lock = final_source_locktype_str
            
            preview_source_changes = QVNChangeDetail(
                server_name=source_server_info["name"], rg_name=source_rg_details_raw["name"],
                virtual_key_affected=source_key_to_find,
                old_reals=old_s_reals,
                new_reals=new_reals_for_source_calculated if not source_action_taken_msg.startswith("KEY SẼ BỊ XÓA") else None,
                action_taken=msg_s,
                old_lock_type=old_s_lock, new_lock_type=new_s_lock
            )

        return QVNPreviewResponse(
            target_vn_changes=preview_target_changes,
            source_vn_changes=preview_source_changes,
            summary="Xem trước các thay đổi cho nghiệp vụ QVN. KHÔNG có thay đổi nào được áp dụng lên VOS.",
            warnings=["QUAN TRỌNG: Hãy đảm bảo hàm utils.apply_rg_locktype_logic đã được bạn triển khai và kiểm tra kỹ lưỡng trong file utils.py!"]
        )

    # --- THỰC THI THAY ĐỔI (dry_run = False) ---
    target_op_success = False
    target_op_message = "N/A"
    source_op_success = True # Mặc định True, chỉ False nếu có update source RG riêng và thất bại
    source_op_message = "Không cần cập nhật Source RG riêng biệt hoặc Source RG đã được xử lý cùng Target RG."

    try:
        target_op_success, target_op_message = routing_gateway_management.update_routing_gateway(
            target_server_info, target_rg_payload_final["name"], target_rg_payload_final
        )
        if not target_op_success:
            target_op_message = f"Lỗi cập nhật Target RG: {target_op_message}"
    except Exception as e_target_exec:
        target_op_success = False
        target_op_message = f"Ngoại lệ khi cập nhật Target RG: {str(e_target_exec)}"

    target_result = QVNExecutionResultItem(
        server_name=target_server_info["name"], rg_name=target_rg_payload_final["name"],
        virtual_key_affected=request.target_vn.virtual_key,
        status="Success" if target_op_success else "Failed", message=target_op_message,
        changed_reals=new_reals_for_target_calculated, changed_lock_type=final_target_locktype_str
    )
    
    source_result = None
    if source_rg_payload_final: # Chỉ khi source RG khác target VÀ có payload để update (tức là không bị xóa key ở target RG)
        try:
            source_op_success, source_op_message = routing_gateway_management.update_routing_gateway(
                source_server_info, source_rg_payload_final["name"], source_rg_payload_final
            )
            if not source_op_success:
                source_op_message = f"Lỗi cập nhật Source RG: {source_op_message}"
        except Exception as e_source_exec:
            source_op_success = False
            source_op_message = f"Ngoại lệ khi cập nhật Source RG: {str(e_source_exec)}"
        
        source_result = QVNExecutionResultItem(
            server_name=source_server_info["name"], rg_name=source_rg_payload_final["name"],
            virtual_key_affected=source_key_to_find,
            status="Success" if source_op_success else "Failed", message=source_op_message,
            changed_reals=new_reals_for_source_calculated if not source_action_taken_msg.startswith("KEY SẼ BỊ XÓA") else None,
            changed_lock_type=final_source_locktype_str
        )
    elif is_source_in_same_rg_as_target and source_key_to_find: # Source đã được xử lý cùng Target
        source_result = QVNExecutionResultItem(
            server_name=target_server_info["name"], rg_name=target_rg_payload_final["name"],
            virtual_key_affected=source_key_to_find,
            status=target_result.status, # Trạng thái của source phụ thuộc vào target khi cùng RG
            message="Source VN được xử lý cùng Target RG. " + ("Thành công." if target_op_success else "Thất bại/Bỏ qua do Target RG."),
            changed_reals=new_reals_for_source_calculated if not source_action_taken_msg.startswith("KEY SẼ BỊ XÓA") else None,
            changed_lock_type=final_target_locktype_str
        )

    overall_status_str = "Failed"
    final_msg_str = "Đã xảy ra lỗi trong quá trình thực thi QVN."
    if target_op_success and source_op_success:
        overall_status_str = "Completed"
        final_msg_str = "Nghiệp vụ QVN hoàn thành thành công."
    elif target_op_success and not source_op_success: # source_op_success=False chỉ khi source RG riêng bị lỗi
        overall_status_str = "CompletedWithErrors"
        final_msg_str = "Cập nhật Target RG thành công, nhưng cập nhật Source RG (nếu có) thất bại."
        
    return QVNExecutionResponse(
        target_rg_result=target_result,
        source_rg_result=source_result,
        overall_status=overall_status_str,
        final_message=final_msg_str
    )