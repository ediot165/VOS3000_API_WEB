# vos_api_fastapi/routers/gateways_router.py

from fastapi import APIRouter, HTTPException, Path
from typing import List, Optional, Dict, Any
from routers.qvn_router import _get_server_info_by_name
import routing_gateway_management 
import utils
# Pydantic dùng để định nghĩa cấu trúc dữ liệu (khuôn mẫu)
from pydantic import BaseModel, Field

# Import các module cần thiết từ thư mục gốc của dự án
# (Cách import này hoạt động khi bạn chạy uvicorn từ thư mục gốc vos_api_fastapi)
import config  # Để lấy thông tin server từ VOS_SERVERS
import mapping_gateway_management # "Bộ não" xử lý MG

# --- Định nghĩa Khuôn Mẫu Dữ Liệu (Pydantic Models) ---

class MappingGatewayBase(BaseModel):
    # Các trường này nên khớp với những gì hàm backend của bạn trả về cho một MG.
    # Hãy điều chỉnh cho đúng với cấu trúc dữ liệu thực tế của bạn.
    name: Optional[str] = None
    account: Optional[str] = None
    # Ví dụ thêm các trường khác bạn có thể muốn (lấy từ file app.py gốc của bạn)
    calloutCallerPrefixes: Optional[str] = None
    calloutCalleePrefixes: Optional[str] = None
    capacity: Optional[int] = None
    lockType: Optional[Any] = None # Có thể là số hoặc chuỗi tùy theo VOS API trả về
    registerType: Optional[Any] = None
    remoteIps: Optional[str] = None
    # Thêm các trường khác nếu cần...

    class Config:
        # Cho phép Pydantic đọc dữ liệu từ các thuộc tính của đối tượng
        # hoặc nếu hàm backend trả về dict thì cũng không sao.
        # orm_mode = True # Nếu hàm backend trả về đối tượng ORM
        from_attributes = True # Cho Pydantic v2


class MGPrefixesUpdateRequest(BaseModel):
    action: str  # Sẽ là "add" (thêm) hoặc "delete" (xóa)
    prefixes_to_modify: List[str] # Danh sách các số cần thêm hoặc xóa

class RoutingGatewayBase(BaseModel):
    # Các trường này nên khớp với dữ liệu RG mà backend của bạn trả về
    name: Optional[str] = None
    callinCallerPrefixes: Optional[str] = None
    callinCalleePrefixes: Optional[str] = None
    rewriteRulesInCaller: Optional[str] = None # Chuỗi rewrite rules gốc từ VOS
    lockType: Optional[Any] = None # Có thể là số hoặc chuỗi
    registerType: Optional[Any] = None
    remoteIps: Optional[str] = None
    # Thêm các trường khác nếu cần...

    class Config:
        from_attributes = True

# Model MỚI cho yêu cầu cập nhật Rewrite Rule của RG
class RGRewriteRuleItem(BaseModel): # Một item trong danh sách rule để cập nhật
    virtual_key: str
    real_numbers: List[str] # Danh sách các số thực, hoặc ["hetso"]

class RGRewriteRuleUpdateRequest(BaseModel):
    action: str  # "add_update" (thêm hoặc cập nhật key) hoặc "delete" (xóa key)
    virtual_key: str
    # real_numbers chỉ cần thiết khi action là "add_update"
    real_numbers: Optional[List[str]] = None # Ví dụ: ["1000", "1001"] hoặc ["hetso"]

# Model MỚI cho yêu cầu cập nhật Prefixes của RG (tương tự MG)
class RGPrefixUpdateRequest(BaseModel):
    action: str  # "add" hoặc "delete"
    prefixes_to_modify: List[str]
# --- Khởi tạo "Khu Vực" (Router) cho Gateway ---
router = APIRouter(
    prefix="/gateways",      # Tất cả "quầy" ở đây sẽ bắt đầu bằng /gateways
    tags=["Quản Lý Gateway"] # Nhóm các API này lại trên trang /docs
)

class ManualGatewayLockRequest(BaseModel):
    lock_type_value: str = Field(..., description="Giá trị lockType mới muốn đặt. Ví dụ: '0' (Mở), '1' (Khóa bởi người dùng), '3' (Khóa hệ thống - nếu muốn).")
# --- Các "Quầy Giao Dịch" (Endpoints) ---

@router.get("/{server_name}/mapping-gateways/",
            response_model=List[MappingGatewayBase],
            summary="Lấy danh sách Mapping Gateway của một server")
async def list_mapping_gateways_for_server(
    # FastAPI sẽ tự động lấy server_name từ URL path
    server_name: str = Path(..., title="Tên Server", description="Tên của VOS server (ví dụ: 'VOS-01 (171.244.56.166)')")
):
    """
    Lấy danh sách tất cả Mapping Gateways cho một **server_name** được chỉ định.
    Tên server phải khớp với một trong các tên đã được định nghĩa trong `config.VOS_SERVERS`.
    """
    print(f"API Router: Yêu cầu lấy MG cho server: {server_name}")

    server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
    if not server_info_found:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy server với tên '{server_name}' trong cấu hình."
        )

    try:
        list_mg, error_msg = mapping_gateway_management.get_all_mapping_gateways(
            server_info=server_info_found
        )
        if error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"Lỗi khi lấy danh sách MG từ server '{server_name}': {error_msg}"
            )
        if list_mg is None:
            raise HTTPException(
                status_code=500,
                detail=f"Không nhận được dữ liệu MG hợp lệ từ server '{server_name}'."
            )
        return list_mg
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router: Lỗi nghiêm trọng khi lấy MG cho server '{server_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server. Chi tiết: {str(e)}")


@router.get("/{server_name}/mapping-gateways/{mg_name}/details/",
            response_model=MappingGatewayBase, # Hoặc một model chi tiết hơn nếu cần
            summary="Lấy thông tin chi tiết của một Mapping Gateway")
async def get_mapping_gateway_detail(
    server_name: str = Path(..., title="Tên Server", description="Tên của VOS server"),
    mg_name: str = Path(..., title="Tên Mapping Gateway", description="Tên chính xác của MG cần xem chi tiết")
):
    """
    Lấy thông tin chi tiết cho một Mapping Gateway (`mg_name`) cụ thể
    trên một **server_name** được chỉ định.
    """
    print(f"API Router: Yêu cầu lấy chi tiết MG '{mg_name}' trên server '{server_name}'")

    server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy server '{server_name}'.")

    try:
        mg_details, error_msg = mapping_gateway_management.get_mapping_gateway_details(
            server_info=server_info_found,
            mg_name=mg_name
        )
        if error_msg:
            raise HTTPException(status_code=400, detail=f"Lỗi khi lấy chi tiết MG '{mg_name}': {error_msg}")
        if not mg_details:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy Mapping Gateway '{mg_name}' trên server '{server_name}'.")
        return mg_details
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router: Lỗi nghiêm trọng khi lấy chi tiết MG '{mg_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server. Chi tiết: {str(e)}")


@router.put("/{server_name}/mapping-gateways/{mg_name}/prefixes/",
            response_model=MappingGatewayBase, # Trả về thông tin MG đã cập nhật
            summary="Thêm hoặc xóa các số trong calloutCallerPrefixes của MG")
async def update_mg_prefixes(
    server_name: str,
    mg_name: str,
    update_request: MGPrefixesUpdateRequest
):
    """
    Thêm hoặc xóa một danh sách các số (prefixes) vào/khỏi trường `calloutCallerPrefixes`
    của một Mapping Gateway (`mg_name`) trên **server_name** được chỉ định.

    Nếu `calloutCallerPrefixes` trở nên rỗng sau khi xóa, `lockType` của MG sẽ được đặt thành "3" (khóa).
    (Cần kiểm tra lại giá trị "3" có đúng là giá trị khóa cho VOS API của bạn không).

    Trong request body, cần cung cấp:
    - **action**: "add" (để thêm số) hoặc "delete" (để xóa số).
    - **prefixes_to_modify**: Một danh sách các chuỗi số cần thêm/xóa.
    """
    print(f"API Router: Yêu cầu cập nhật prefixes cho MG '{mg_name}' trên server '{server_name}'. Action: {update_request.action}")

    server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy server '{server_name}'.")

    try:
        current_mg_details, error_msg_detail = mapping_gateway_management.get_mapping_gateway_details(
            server_info=server_info_found,
            mg_name=mg_name
        )
        if error_msg_detail:
            raise HTTPException(status_code=400, detail=f"Không thể lấy thông tin MG '{mg_name}' hiện tại để cập nhật: {error_msg_detail}")
        if not current_mg_details:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy MG '{mg_name}' để cập nhật.")

        current_prefixes_str = current_mg_details.get("calloutCallerPrefixes", "")
        prefix_set = {p.strip() for p in current_prefixes_str.split(',') if p.strip()}
        prefixes_to_modify_set = {p.strip() for p in update_request.prefixes_to_modify if p.strip()}

        if update_request.action.lower() == "add":
            prefix_set.update(prefixes_to_modify_set)
        elif update_request.action.lower() == "delete":
            prefix_set.difference_update(prefixes_to_modify_set)
        else:
            raise HTTPException(status_code=400, detail="Giá trị 'action' không hợp lệ. Phải là 'add' hoặc 'delete'.")

        updated_prefixes_str = ",".join(sorted(list(prefix_set)))
        payload_for_update = current_mg_details.copy()
        payload_for_update["calloutCallerPrefixes"] = updated_prefixes_str

        # --- LOGIC CẬP NHẬT lockType CHO MG THEO RULE MỚI ---
        # Rule: Nếu calloutCallerPrefixes bị xóa hết (rỗng) thì lockType = "3" (khóa MG).
        # (Giả sử "3" là giá trị khóa. Hãy xác nhận lại với VOS API của bạn).
        
        # Lấy danh sách prefix mới sau khi đã cập nhật
        new_prefix_list = [p for p in prefix_set if p] # Lọc bỏ chuỗi rỗng một lần nữa cho chắc

        callout_callee_exists_and_has_value = payload_for_update.get("calloutCalleePrefixes", "").strip()

        if not new_prefix_list and not callout_callee_exists_and_has_value:
            # Nếu cả calloutCallerPrefixes rỗng VÀ calloutCalleePrefixes cũng rỗng (hoặc không có)
            payload_for_update["lockType"] = "3" # Đặt là chuỗi "3", VOS API có thể cần số 3
            print(f"LOGIC MG LOCKTYPE: Đặt lockType thành '3' cho MG '{mg_name}' vì calloutCallerPrefixes và calloutCalleePrefixes đều rỗng.")
        elif not new_prefix_list and callout_callee_exists_and_has_value:
            payload_for_update["lockType"] = "3"
            print(f"LOGIC MG LOCKTYPE: Đặt lockType thành '3' cho MG '{mg_name}' vì calloutCallerPrefixes đã bị xóa hết (theo rule mới).")


        # --- Kết thúc logic lockType ---

        success, message = mapping_gateway_management.update_mapping_gateway(
            server_info=server_info_found,
            mg_name=mg_name,
            payload_update_data=payload_for_update
        )

        if not success:
            raise HTTPException(status_code=400, detail=message or "Không thể cập nhật prefixes cho MG.")

        updated_mg_details_after_save, _ = mapping_gateway_management.get_mapping_gateway_details(
            server_info=server_info_found,
            mg_name=payload_for_update.get("name", mg_name)
        )
        if not updated_mg_details_after_save:
             print(f"API Router: Không lấy lại được chi tiết MG '{mg_name}' sau khi cập nhật. Trả về payload đã gửi đi.")
             return payload_for_update
        return updated_mg_details_after_save

    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router: Lỗi nghiêm trọng khi cập nhật prefixes cho MG '{mg_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server. Chi tiết: {str(e)}")

    
@router.get("/{server_name}/routing-gateways/",
            response_model=List[RoutingGatewayBase],
            summary="Lấy danh sách Routing Gateway của một server")
async def list_routing_gateways_for_server(
    server_name: str = Path(..., title="Tên Server")
):
    """Lấy danh sách tất cả Routing Gateways cho một **server_name** được chỉ định."""
    print(f"API Router: Yêu cầu lấy RG cho server: {server_name}")
    server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy server '{server_name}'.")

    try:
        list_rg, error_msg = routing_gateway_management.get_all_routing_gateways(
            server_info=server_info_found
        )
        if error_msg:
            raise HTTPException(status_code=400, detail=f"Lỗi khi lấy danh sách RG: {error_msg}")
        if list_rg is None:
            raise HTTPException(status_code=500, detail="Không nhận được dữ liệu RG hợp lệ.")
        return list_rg
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router: Lỗi nghiêm trọng khi lấy RG cho server '{server_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")


@router.get("/{server_name}/routing-gateways/{rg_name}/details/",
            response_model=RoutingGatewayBase,
            summary="Lấy thông tin chi tiết của một Routing Gateway")
async def get_routing_gateway_detail(
    server_name: str = Path(..., title="Tên Server"),
    rg_name: str = Path(..., title="Tên Routing Gateway")
):
    """Lấy thông tin chi tiết cho một Routing Gateway (`rg_name`) cụ thể trên một **server_name**."""
    print(f"API Router: Yêu cầu lấy chi tiết RG '{rg_name}' trên server '{server_name}'")
    server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy server '{server_name}'.")

    try:
        rg_details, error_msg = routing_gateway_management.get_routing_gateway_details(
            server_info=server_info_found, rg_name=rg_name
        )
        if error_msg:
            raise HTTPException(status_code=400, detail=f"Lỗi khi lấy chi tiết RG: {error_msg}")
        if not rg_details:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy RG '{rg_name}'.")
        return rg_details
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router: Lỗi nghiêm trọng khi lấy chi tiết RG '{rg_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")

@router.put("/{server_name}/routing-gateways/{rg_name}/rewrite-rules/",
            response_model=RoutingGatewayBase, # Trả về RG đã cập nhật
            summary="Cập nhật (thêm/sửa/xóa) một Rewrite Rule cho RG")
async def update_rg_rewrite_rule(
    server_name: str,
    rg_name: str,
    rule_update: RGRewriteRuleUpdateRequest # Dữ liệu từ request body
):
    """
    Thêm/cập nhật hoặc xóa một rewrite rule cho Routing Gateway.
    - **action**: "add_update" hoặc "delete".
    - **virtual_key**: Khóa ảo của rule.
    - **real_numbers**: Danh sách số thực (chỉ cần cho "add_update"). Ví dụ: `["123", "456"]` hoặc `["hetso"]`.
    """
    print(f"API Router: Yêu cầu cập nhật rewrite rule cho RG '{rg_name}', action: {rule_update.action}")
    server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' không tìm thấy.")

    try:
        current_rg_details, error_detail = routing_gateway_management.get_routing_gateway_details(server_info_found, rg_name)
        if error_detail:
            raise HTTPException(status_code=400, detail=f"Không thể lấy thông tin RG '{rg_name}': {error_detail}")
        if not current_rg_details:
            raise HTTPException(status_code=404, detail=f"RG '{rg_name}' không tìm thấy.")

        # Parse rewrite rules hiện tại từ chuỗi sang dict
        current_rules_str = current_rg_details.get("rewriteRulesInCaller", "")
        rules_dict = utils.parse_vos_rewrite_rules(current_rules_str)

        if rule_update.action.lower() == "add_update":
            if rule_update.real_numbers is None: # Phải có real_numbers khi add/update
                raise HTTPException(status_code=400, detail="Cần cung cấp 'real_numbers' cho hành động 'add_update'.")
            # Đảm bảo số ảo được chuẩn hóa (nếu cần, ví dụ: utils.transform_real_number_for_vos_storage)
            # Tạm thời dùng trực tiếp
            transformed_reals = [utils.transform_real_number_for_vos_storage(r) for r in rule_update.real_numbers if r.lower() != "hetso"]
            if "hetso" in [r.lower() for r in rule_update.real_numbers]:
                rules_dict[rule_update.virtual_key.strip()] = ["hetso"]
            elif transformed_reals:
                 rules_dict[rule_update.virtual_key.strip()] = list(set(transformed_reals)) # Loại bỏ trùng lặp
            else: # Nếu real_numbers rỗng và không phải hetso
                rules_dict[rule_update.virtual_key.strip()] = []


        elif rule_update.action.lower() == "delete":
            if rule_update.virtual_key.strip() in rules_dict:
                del rules_dict[rule_update.virtual_key.strip()]
            else:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy virtual key '{rule_update.virtual_key}' để xóa.")
        else:
            raise HTTPException(status_code=400, detail="Giá trị 'action' không hợp lệ. Phải là 'add_update' hoặc 'delete'.")

        # Format lại rules dict thành chuỗi
        updated_rules_str = utils.format_rewrite_rules_for_vos(rules_dict)
        payload_for_update = current_rg_details.copy()
        payload_for_update["rewriteRulesInCaller"] = updated_rules_str

        # --- Logic cập nhật lockType cho RG ---
        # Đây là nơi bạn cần áp dụng logic tương tự như hàm apply_locktype_logic_qvn_helper
        # trong file app.py cũ của bạn, hoặc một phiên bản đã được điều chỉnh.
        # Ví dụ đơn giản: nếu không còn rule nào có giá trị thực (chỉ còn key rỗng hoặc hetso)
        # và không có caller/callee prefix nào, thì lockType = 3
        # Tạm thời để một TODO ở đây, bạn cần hoàn thiện logic này cho đúng.
        # TODO: Áp dụng logic cập nhật lockType dựa trên rules_dict và các prefix khác.
        # Ví dụ:
        meaningful_rules = any(r_list and r_list != ["hetso"] for r_list in rules_dict.values() if r_list)
        current_callin_caller = [p.strip() for p in payload_for_update.get("callinCallerPrefixes", "").split(',') if p.strip()]
        current_callin_callee = [p.strip() for p in payload_for_update.get("callinCalleePrefixes", "").split(',') if p.strip()]

        if not current_callin_caller and not current_callin_callee and not meaningful_rules:
            payload_for_update["lockType"] = "3" # Hoặc 3 nếu API VOS nhận số
            print(f"LOGIC LOCKTYPE (RG Rewrite): Đặt lockType thành 3 cho RG {rg_name} vì không còn rule/prefix nào.")
        # --- Kết thúc logic lockType (cần hoàn thiện) ---


        success, message = routing_gateway_management.update_routing_gateway(
            server_info_found, rg_name, payload_for_update
        )
        if not success:
            raise HTTPException(status_code=400, detail=message or "Không thể cập nhật Rewrite Rule.")

        updated_rg_details, _ = routing_gateway_management.get_routing_gateway_details(server_info_found, rg_name)
        return updated_rg_details if updated_rg_details else payload_for_update

    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router: Lỗi nghiêm trọng khi cập nhật rewrite rule cho RG '{rg_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")

@router.put("/{server_name}/routing-gateways/{rg_name}/caller-prefixes/",
            response_model=RoutingGatewayBase,
            summary="Cập nhật Callin Caller Prefixes cho RG")
async def update_rg_caller_prefixes(
    server_name: str,
    rg_name: str,
    update_request: RGPrefixUpdateRequest
):
    # --- TƯƠNG TỰ NHƯ update_mg_prefixes ---
    # 1. Tìm server_info
    # 2. Lấy current_rg_details
    # 3. Xử lý prefix_set dựa trên update_request.action và update_request.prefixes_to_modify
    #    cho trường "callinCallerPrefixes"
    # 4. Tạo payload_for_update, cập nhật "callinCallerPrefixes"
    # 5. TODO: Áp dụng logic cập nhật lockType cho RG (quan trọng!)
    #    (Dựa trên rules_dict, callinCallerPrefixes mới, callinCalleePrefixes hiện tại)
    # 6. Gọi routing_gateway_management.update_routing_gateway
    # 7. Trả về kết quả (updated_rg_details)
    # --- VÍ DỤ SƠ LƯỢC ---
    server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' không tìm thấy.")

    current_rg_details, error_detail = routing_gateway_management.get_routing_gateway_details(server_info_found, rg_name)
    if error_detail or not current_rg_details:
        raise HTTPException(status_code=400, detail=f"Không thể lấy thông tin RG '{rg_name}'.")

    current_prefixes_str = current_rg_details.get("callinCallerPrefixes", "")
    prefix_set = {p.strip() for p in current_prefixes_str.split(',') if p.strip()}
    # ... (logic add/delete tương tự MG) ...
    if update_request.action.lower() == "add":
        prefix_set.update(p.strip() for p in update_request.prefixes_to_modify if p.strip())
    elif update_request.action.lower() == "delete":
        prefix_set.difference_update(p.strip() for p in update_request.prefixes_to_modify if p.strip())
    else:
        raise HTTPException(status_code=400, detail="Action không hợp lệ.")

    updated_prefixes_str = ",".join(sorted(list(prefix_set)))
    payload_for_update = current_rg_details.copy()
    payload_for_update["callinCallerPrefixes"] = updated_prefixes_str

    # TODO: Gọi hàm logic cập nhật lockType ở đây
    # Ví dụ: apply_rg_locktype_logic(payload_for_update, utils.parse_vos_rewrite_rules(payload_for_update.get("rewriteRulesInCaller", "")))
    # Bạn cần định nghĩa hàm apply_rg_locktype_logic dựa trên logic cũ trong app.py

    success, message = routing_gateway_management.update_routing_gateway(server_info_found, rg_name, payload_for_update)
    if not success:
        raise HTTPException(status_code=400, detail=message or "Lỗi cập nhật caller prefixes.")

    updated_details, _ = routing_gateway_management.get_routing_gateway_details(server_info_found, rg_name)
    return updated_details if updated_details else payload_for_update

@router.put("/{server_name}/routing-gateways/{rg_name}/callee-prefixes/",
            response_model=RoutingGatewayBase, # Trả về RG đã cập nhật
            summary="Cập nhật Callin Callee Prefixes cho RG")
async def update_rg_callee_prefixes(
    server_name: str,
    rg_name: str,
    update_request: RGPrefixUpdateRequest # Dữ liệu từ request body
):
    """
    Thêm hoặc xóa một danh sách các số (prefixes) vào/khỏi trường `callinCalleePrefixes`
    của một Routing Gateway (`rg_name`) trên **server_name** được chỉ định.

    Trong request body, cần cung cấp:
    - **action**: "add" (để thêm số) hoặc "delete" (để xóa số).
    - **prefixes_to_modify**: Một danh sách các chuỗi số cần thêm/xóa.

    Lưu ý: Việc cập nhật callinCalleePrefixes thường chỉ có ý nghĩa với các RG loại "TO".
    API này không tự kiểm tra loại RG, việc này sẽ do VOS hoặc logic backend xử lý.
    """
    print(f"API Router: Yêu cầu cập nhật CALLEE prefixes cho RG '{rg_name}' trên server '{server_name}'. Action: {update_request.action}")

    server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' không tìm thấy.")

    try:
        # 1. Lấy thông tin RG hiện tại để có payload gốc
        current_rg_details, error_detail = routing_gateway_management.get_routing_gateway_details(
            server_info=server_info_found,
            rg_name=rg_name
        )
        if error_detail:
            raise HTTPException(status_code=400, detail=f"Không thể lấy thông tin RG '{rg_name}' hiện tại để cập nhật: {error_detail}")
        if not current_rg_details:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy RG '{rg_name}' để cập nhật.")

        # 2. Xử lý logic thêm/xóa prefixes cho callinCalleePrefixes
        current_prefixes_str = current_rg_details.get("callinCalleePrefixes", "")
        prefix_set = {p.strip() for p in current_prefixes_str.split(',') if p.strip()}
        prefixes_to_modify_set = {p.strip() for p in update_request.prefixes_to_modify if p.strip()}

        if update_request.action.lower() == "add":
            prefix_set.update(prefixes_to_modify_set)
        elif update_request.action.lower() == "delete":
            prefix_set.difference_update(prefixes_to_modify_set)
        else:
            raise HTTPException(status_code=400, detail="Giá trị 'action' không hợp lệ. Phải là 'add' hoặc 'delete'.")

        updated_prefixes_str = ",".join(sorted(list(prefix_set)))

        # 3. Tạo payload đầy đủ để gửi lên VOS API
        payload_for_update = current_rg_details.copy()
        payload_for_update["callinCalleePrefixes"] = updated_prefixes_str

        # 4. QUAN TRỌNG: Logic cập nhật lockType cho RG
        # Bạn cần áp dụng logic tương tự như hàm apply_locktype_logic_qvn_helper
        # hoặc một phiên bản đã được điều chỉnh cho phù hợp.
        # Logic này xem xét cả callinCallerPrefixes, callinCalleePrefixes (mới cập nhật),
        # và rewriteRulesInCaller để quyết định lockType.
        # Tạm thời để một TODO ở đây, bạn cần hoàn thiện logic này cho đúng.
        # Ví dụ:
        # current_rules_dict = utils.parse_vos_rewrite_rules(payload_for_update.get("rewriteRulesInCaller", ""))
        # apply_rg_locktype_logic(payload_for_update, current_rules_dict)
        # (Trong đó apply_rg_locktype_logic là hàm bạn tự định nghĩa dựa trên logic cũ)
        print(f"LOGIC LOCKTYPE (RG CalleePrefix): Cần áp dụng logic cập nhật lockType cho RG {rg_name} sau khi thay đổi callee prefixes.")
        # --- Ví dụ logic đơn giản hóa (cần xem xét kỹ): ---
        rules_dict = utils.parse_vos_rewrite_rules(payload_for_update.get("rewriteRulesInCaller", ""))
        meaningful_rules = any(r_list and r_list != ["hetso"] for r_list in rules_dict.values() if r_list)
        current_callin_caller = [p.strip() for p in payload_for_update.get("callinCallerPrefixes", "").split(',') if p.strip()]
        # new_callee_list là prefix_set đã được cập nhật
        new_callee_list = [p for p in prefix_set if p]

        if not current_callin_caller and not new_callee_list and not meaningful_rules:
            payload_for_update["lockType"] = "3" # Hoặc 3 nếu API VOS nhận số
            print(f"LOGIC LOCKTYPE (RG CalleePrefix): Đặt lockType thành 3 cho RG {rg_name}.")
        # --- Kết thúc logic lockType (cần hoàn thiện) ---


        # 5. Gọi hàm backend để cập nhật RG
        success, message = routing_gateway_management.update_routing_gateway(
            server_info=server_info_found,
            rg_name=rg_name,
            payload_update_data=payload_for_update
        )

        if not success:
            raise HTTPException(status_code=400, detail=message or "Không thể cập nhật Callin Callee Prefixes cho RG.")

        # 6. Trả về thông tin RG đã được cập nhật (lấy lại thông tin mới nhất)
        updated_rg_details_after_save, _ = routing_gateway_management.get_routing_gateway_details(
            server_info=server_info_found,
            rg_name=payload_for_update.get("name", rg_name) # Dùng tên mới nếu có thể đã đổi tên
        )
        if not updated_rg_details_after_save:
             print(f"API Router: Không lấy lại được chi tiết RG '{rg_name}' sau khi cập nhật callee prefixes. Trả về payload đã gửi đi.")
             return payload_for_update

        return updated_rg_details_after_save

    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router: Lỗi nghiêm trọng khi cập nhật callee prefixes cho RG '{rg_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server. Chi tiết: {str(e)}")

# vos_api_fastapi/routers/gateways_router.py
# ... (các import và model đã có) ...

# --- Endpoint MỚI: Khóa/Mở khóa thủ công cho Routing Gateway ---
@router.put("/{server_name}/routing-gateways/{rg_name}/manual-lock/",
            response_model=RoutingGatewayBase, # Trả về thông tin RG đã cập nhật
            summary="Khóa hoặc mở khóa thủ công một Routing Gateway")
async def manually_set_rg_lock_status(
    # Đưa tham số request body (không có default) lên trước
    lock_request: ManualGatewayLockRequest,
    # Các path parameters (có default là Path(...)) theo sau
    server_name: str = Path(..., title="Tên Server"),
    rg_name: str = Path(..., title="Tên Routing Gateway")
):
    """
    Cho phép đặt trực tiếp giá trị `lockType` cho một Routing Gateway.
    Hãy cẩn thận khi sử dụng chức năng này.

    - **lock_type_value**: Giá trị `lockType` mới (chuỗi), ví dụ: "0", "1", "3".
    Bạn cần kiểm tra giá trị chính xác mà VOS API của bạn chấp nhận.
    """
    print(f"API Router: Yêu cầu khóa/mở khóa thủ công RG '{rg_name}' trên server '{server_name}' thành lockType '{lock_request.lock_type_value}'")

    server_info_found = _get_server_info_by_name(server_name) # Giả sử bạn có hàm helper này
    if not server_info_found:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy server '{server_name}'.")

    try:
        current_rg_details, error_msg_detail = routing_gateway_management.get_routing_gateway_details(
            server_info=server_info_found,
            rg_name=rg_name
        )
        if error_msg_detail:
            raise HTTPException(status_code=400, detail=f"Không thể lấy thông tin RG '{rg_name}' hiện tại: {error_msg_detail}")
        if not current_rg_details:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy RG '{rg_name}'.")

        payload_for_update = current_rg_details.copy()
        payload_for_update["lockType"] = lock_request.lock_type_value

        success, message = routing_gateway_management.update_routing_gateway(
            server_info=server_info_found,
            rg_name=rg_name,
            payload_update_data=payload_for_update
        )

        if not success:
            raise HTTPException(status_code=400, detail=message or "Không thể cập nhật lockType cho RG.")

        updated_rg_details_after_save, _ = routing_gateway_management.get_routing_gateway_details(
            server_info=server_info_found,
            rg_name=payload_for_update.get("name", rg_name)
        )
        if not updated_rg_details_after_save:
            if success: # Nếu VOS báo thành công nhưng không lấy lại được detail
                 # Trả về payload đã gửi có thể không khớp response_model nếu tên RG thay đổi
                 # hoặc cấu trúc payload_for_update không hoàn toàn là RoutingGatewayBase
                 # Cân nhắc trả về một thông báo đơn giản hoặc lấy lại chi tiết một lần nữa.
                 # Để đơn giản, nếu thành công, ta có thể giả định payload_for_update có cấu trúc gần đúng.
                 # Tuy nhiên, tốt nhất là lấy lại được detail.
                 # Nếu không, có thể trả về một dict thông báo thành công.
                 # response_model=Dict[str, str] cho trường hợp này có thể phù hợp hơn.
                 # Hoặc, nếu payload_for_update khớp RoutingGatewayBase thì có thể trả về nó.
                 return payload_for_update # CẨN THẬN: có thể không khớp response_model nếu tên thay đổi
            else:
                 raise HTTPException(status_code=500, detail=f"Cập nhật lockType có vẻ thành công nhưng không thể lấy lại chi tiết RG '{rg_name}'.")
        
        return updated_rg_details_after_save

    except HTTPException:
        raise
    except Exception as e:
        print(f"API Router: Lỗi nghiêm trọng khi cập nhật lockType thủ công cho RG '{rg_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server khi cập nhật lockType RG. Chi tiết: {str(e)}")