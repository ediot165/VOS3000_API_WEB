# vos_api_fastapi/routers/cleanup_router.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Set, Dict, Any
import re # Để parse input string
from enum import Enum # Để tạo Enum cho scope

from pydantic import BaseModel

# Import các module cần thiết từ thư mục gốc
import config
import utils
import mapping_gateway_management
import routing_gateway_management

# --- Định nghĩa Khuôn Mẫu Dữ Liệu (Pydantic Models) ---

class CleanupScope(str, Enum): # Enum cho phạm vi quét
    MG = "MG"
    RG = "RG"
    BOTH = "Both"

class CleanupScanRequest(BaseModel):
    numbers_raw: str # Chuỗi các số cần tìm để xóa, cách nhau bằng dấu phẩy, cách, hoặc xuống dòng
    scope: CleanupScope = CleanupScope.BOTH # Mặc định là quét cả MG và RG

# Model mô tả một vị trí cụ thể tìm thấy số khớp để có thể dọn dẹp
class IdentifiedMatchLocation(BaseModel):
    field_name: str # Ví dụ: "CalloutCallerPrefixes", "CallinCallerPrefixes", "RewriteRuleKey", "RewriteRuleReal"
    virtual_key_context: Optional[str] = None # Nếu field_name là "RewriteRuleReal", đây là virtual_key chứa nó
    found_numbers_to_remove: List[str] # Các số cụ thể (biến thể đã chuẩn hóa) tìm thấy trong trường này khớp với input

# Model cho một "ứng viên" gateway có thể được dọn dẹp
class CleanupCandidateItem(BaseModel):
    server_name: str
    gateway_type: str  # "MG" hoặc "RG"
    gateway_name: str
    # Thông tin chi tiết về các vị trí khớp và số cần xóa trong gateway này
    matches: List[IdentifiedMatchLocation]
    # Chúng ta sẽ gửi kèm thông tin thô của gateway để client có thể hiển thị
    # và sau này client có thể gửi lại chính xác item này cho API thực thi xóa.
    # Điều này giúp API thực thi không cần phải quét lại.
    raw_gateway_info: Dict[str, Any]
class CleanupExecuteRequest(BaseModel):
    # Client sẽ gửi lại danh sách các CleanupCandidateItem mà họ muốn thực thi dọn dẹp
    # Đây là những item đã được trả về từ API /scan/
    items_to_clean: List[CleanupCandidateItem]
    # Chuỗi các số gốc mà người dùng đã nhập ban đầu để quét,
    # dùng để tạo lại các biến thể cần xóa một cách chính xác.
    original_numbers_to_remove_raw: str

# --- Model MỚI cho Kết Quả Thực Thi của Từng Item ---
class CleanupExecutionResultItem(BaseModel):
    server_name: str
    gateway_type: str # "MG" hoặc "RG"
    gateway_name: str
    field_cleaned: Optional[str] = None # Mô tả các trường đã được xử lý, ví dụ: "CalloutCallerPrefixes, RewriteRuleKey_DELETE(some_key)"
    status: str  # Ví dụ: "Success", "Failed", "NoActionNeeded"
    message: str

# --- Khởi tạo "Khu Vực" (Router) cho Dọn Dẹp Gateway ---
router = APIRouter(
    prefix="/cleanup",
    tags=["Dọn Dẹp Gateway"]
)

# vos_api_fastapi/routers/cleanup_router.py
# ... (code Pydantic models và khởi tạo router đã có ở trên) ...

# --- Helper function nhỏ để tìm original inputs (tương tự logic trong app.py cũ) ---
# (Bạn có thể đã có hàm này ở number_info_router.py, có thể chuyển nó vào utils.py)
def _get_matching_original_inputs_for_cleanup(matched_variants: Set[str], original_inputs_list: List[str]) -> str:
    found_original_inputs = set()
    for original_input in original_inputs_list:
        variants_for_this_original = utils.generate_search_variants(original_input)
        if not matched_variants.isdisjoint(variants_for_this_original):
            found_original_inputs.add(original_input)
    return ", ".join(sorted(list(found_original_inputs)))


@router.post("/scan/",
             response_model=List[CleanupCandidateItem],
             summary="Quét các gateway để tìm số cần dọn dẹp")
async def scan_gateways_for_cleanup(request: CleanupScanRequest):
    """
    Nhận một chuỗi các số cần dọn dẹp và phạm vi quét (MG, RG, hoặc Both).
    Trả về danh sách các gateway "ứng viên" có chứa các số đó, cùng chi tiết
    về vị trí tìm thấy và thông tin gateway gốc.
    """
    print(f"API Router (Cleanup Scan): Yêu cầu quét với scope '{request.scope}', numbers: '{request.numbers_raw[:100]}...'")

    if not request.numbers_raw.strip():
        raise HTTPException(status_code=400, detail="Chuỗi số cần dọn dẹp không được để trống.")

    original_numbers_to_scan = [term.strip() for term in re.split(r'[,\s\n]+', request.numbers_raw) if term.strip()]
    if not original_numbers_to_scan:
        raise HTTPException(status_code=400, detail="Không có số hợp lệ nào trong chuỗi đầu vào.")

    # Tạo tất cả các biến thể tìm kiếm (nên là các dạng đã chuẩn hóa VOS hay dùng)
    all_variants_for_cleanup: Set[str] = set()
    for num_original_scan in original_numbers_to_scan:
        all_variants_for_cleanup.update(utils.generate_search_variants(num_original_scan))

    if not all_variants_for_cleanup:
        return [] # Không có gì để quét

    print(f"API Router (Cleanup Scan): Sẽ quét {len(all_variants_for_cleanup)} biến thể từ {len(original_numbers_to_scan)} input gốc.")

    candidate_items: List[CleanupCandidateItem] = []

    scan_mg = request.scope in [CleanupScope.MG, CleanupScope.BOTH]
    scan_rg = request.scope in [CleanupScope.RG, CleanupScope.BOTH]

    for server_info in config.VOS_SERVERS:
        server_name = server_info.get("name", "Unknown Server")
        print(f"API Router (Cleanup Scan): Đang quét server: {server_name}...")

        # --- Quét Mapping Gateways (MG) ---
        if scan_mg:
            # Giả sử hàm identify_mg_for_cleanup_backend đã được refactor
            # trong mapping_gateway_management.py và trả về cấu trúc phù hợp
            # Hoặc chúng ta sẽ tái tạo logic đó ở đây.
            # Tạm thời, tái tạo logic tương tự như trong app.py gốc:
            try:
                mg_list_data, err_mg_list = mapping_gateway_management.get_all_mapping_gateways(server_info, "")
                if err_mg_list:
                    print(f"Lỗi khi lấy MG từ {server_name} cho cleanup: {err_mg_list}")
                elif mg_list_data:
                    for mg_data_item in mg_list_data:
                        matches_in_this_mg: List[IdentifiedMatchLocation] = []
                        mg_name_item = mg_data_item.get("name", f"Unnamed_MG_Cleanup_{server_name}")

                        # Kiểm tra calloutCallerPrefixes
                        prefixes_str_item = mg_data_item.get("calloutCallerPrefixes", "")
                        if prefixes_str_item:
                            original_prefixes_list_item = [p.strip() for p in prefixes_str_item.split(",") if p.strip()]
                            common_numbers_found_list = sorted(list(set(original_prefixes_list_item) & all_variants_for_cleanup))
                            if common_numbers_found_list:
                                matches_in_this_mg.append(IdentifiedMatchLocation(
                                    field_name="CalloutCallerPrefixes",
                                    found_numbers_to_remove=common_numbers_found_list
                                ))

                        if matches_in_this_mg:
                            candidate_items.append(CleanupCandidateItem(
                                server_name=server_name,
                                gateway_type="MG",
                                gateway_name=mg_name_item,
                                matches=matches_in_this_mg,
                                raw_gateway_info=mg_data_item
                            ))
            except Exception as e_mg_scan:
                print(f"Lỗi ngoại lệ khi quét MG trên {server_name}: {e_mg_scan}")


        # --- Quét Routing Gateways (RG) ---
        if scan_rg:
            # Tương tự, giả sử có hàm identify_rgs_for_cleanup_backend
            # hoặc tái tạo logic ở đây.
            try:
                rg_list_data, err_rg_list = routing_gateway_management.get_all_routing_gateways(server_info, "")
                if err_rg_list:
                    print(f"Lỗi khi lấy RG từ {server_name} cho cleanup: {err_rg_list}")
                elif rg_list_data:
                    for rg_data_item in rg_list_data:
                        matches_in_this_rg: List[IdentifiedMatchLocation] = []
                        rg_name_item = rg_data_item.get("name", f"Unnamed_RG_Cleanup_{server_name}")
                        # is_to_rg_flag = ("to" in rg_name_item.lower() or "to-" in rg_name_item.lower() or "to_" in rg_name_item.lower())

                        # Kiểm tra callinCallerPrefixes
                        caller_prefixes_str = rg_data_item.get("callinCallerPrefixes", "")
                        if caller_prefixes_str:
                            original_caller_list = [p.strip() for p in caller_prefixes_str.split(",") if p.strip()]
                            common_in_caller = sorted(list(set(original_caller_list) & all_variants_for_cleanup))
                            if common_in_caller:
                                matches_in_this_rg.append(IdentifiedMatchLocation(
                                    field_name="CallinCallerPrefixes",
                                    found_numbers_to_remove=common_in_caller
                                ))

                        # Kiểm tra callinCalleePrefixes
                        callee_prefixes_str = rg_data_item.get("callinCalleePrefixes", "")
                        if callee_prefixes_str: # Chỉ kiểm tra nếu có giá trị
                            original_callee_list = [p.strip() for p in callee_prefixes_str.split(",") if p.strip()]
                            common_in_callee = sorted(list(set(original_callee_list) & all_variants_for_cleanup))
                            if common_in_callee:
                                matches_in_this_rg.append(IdentifiedMatchLocation(
                                    field_name="CallinCalleePrefixes",
                                    found_numbers_to_remove=common_in_callee
                                ))

                        # Kiểm tra RewriteRulesInCaller
                        rewrite_str = rg_data_item.get("rewriteRulesInCaller", "")
                        if rewrite_str:
                            original_rewrite_parsed = utils.parse_vos_rewrite_rules(rewrite_str)
                            # Kiểm tra key ảo trùng với số cần xóa
                            for vk_del in list(original_rewrite_parsed.keys()): # list() để tránh lỗi thay đổi dict khi duyệt
                                # Chỉ xóa key nếu nó là dạng số ảo (ví dụ 6 số) và nằm trong danh sách cần xóa
                                # Điều kiện is_six_digit_virtual_number_candidate có thể cần thiết ở đây
                                if vk_del in all_variants_for_cleanup: # and utils.is_six_digit_virtual_number_candidate(vk_del)
                                    matches_in_this_rg.append(IdentifiedMatchLocation(
                                        field_name="RewriteRuleKey_DELETE", # Đánh dấu để biết là xóa cả key
                                        virtual_key_context=vk_del,
                                        found_numbers_to_remove=[vk_del]
                                    ))

                            # Kiểm tra số thực trong rule trùng với số cần xóa
                            for vk_map, rv_list_map in original_rewrite_parsed.items():
                                actual_reals_list = [r for r in rv_list_map if r.lower() != "hetso"]
                                common_rv_for_this_key = sorted(list(set(actual_reals_list) & all_variants_for_cleanup))
                                if common_rv_for_this_key:
                                    matches_in_this_rg.append(IdentifiedMatchLocation(
                                        field_name="RewriteRuleReal_MODIFY", # Đánh dấu để biết là sửa real numbers trong key
                                        virtual_key_context=vk_map,
                                        found_numbers_to_remove=common_rv_for_this_key
                                    ))

                        if matches_in_this_rg:
                            candidate_items.append(CleanupCandidateItem(
                                server_name=server_name,
                                gateway_type="RG",
                                gateway_name=rg_name_item,
                                matches=matches_in_this_rg,
                                raw_gateway_info=rg_data_item
                            ))
            except Exception as e_rg_scan:
                print(f"Lỗi ngoại lệ khi quét RG trên {server_name}: {e_rg_scan}")

    print(f"API Router (Cleanup Scan): Hoàn thành quét, tìm thấy {len(candidate_items)} ứng viên.")
    return candidate_items

@router.post("/execute/",
             response_model=List[CleanupExecutionResultItem],
             summary="Thực thi việc dọn dẹp các số đã chọn khỏi gateway")
async def execute_gateway_cleanup(request: CleanupExecuteRequest):
    """
    Nhận một danh sách các "ứng viên" gateway (items_to_clean) đã được chọn
    từ kết quả của API /scan/, và chuỗi số gốc cần xóa.
    API sẽ thực hiện việc xóa các số/quy tắc tương ứng khỏi các gateway đó.
    """
    print(f"API Router (Cleanup Execute): Nhận yêu cầu thực thi dọn dẹp cho {len(request.items_to_clean)} item(s).")

    if not request.items_to_clean:
        raise HTTPException(status_code=400, detail="Danh sách 'items_to_clean' không được để trống.")
    if not request.original_numbers_to_remove_raw.strip():
        raise HTTPException(status_code=400, detail="'original_numbers_to_remove_raw' không được để trống.")

    # Tạo lại các biến thể cần xóa chính xác từ input gốc của người dùng
    original_numbers_input_list = [term.strip() for term in re.split(r'[,\s\n]+', request.original_numbers_to_remove_raw) if term.strip()]
    variants_to_remove_exactly: Set[str] = set()
    for num_original in original_numbers_input_list:
        variants_to_remove_exactly.update(utils.generate_search_variants(num_original))

    if not variants_to_remove_exactly:
        raise HTTPException(status_code=400, detail="Không tạo được biến thể nào từ 'original_numbers_to_remove_raw'.")

    execution_results: List[CleanupExecutionResultItem] = []

    for item_to_clean in request.items_to_clean:
        server_name = item_to_clean.server_name
        gateway_type = item_to_clean.gateway_type
        gateway_name = item_to_clean.gateway_name
        current_gateway_payload = item_to_clean.raw_gateway_info.copy() # Làm việc trên bản sao

        server_info_found = next((s_info for s_info in config.VOS_SERVERS if s_info.get("name") == server_name), None)
        if not server_info_found:
            execution_results.append(CleanupExecutionResultItem(
                server_name=server_name, gateway_type=gateway_type, gateway_name=gateway_name,
                status="Failed", message=f"Server '{server_name}' không tìm thấy trong cấu hình."
            ))
            continue # Chuyển sang item tiếp theo

        changes_made_to_this_gateway = False
        fields_processed_log: List[str] = []

        # Duyệt qua các "match" mà API /scan/ đã tìm thấy cho item này
        for match_info in item_to_clean.matches:
            field_to_act_on = match_info.field_name
            # numbers_found_by_scan là các số mà scan đã thấy khớp,
            # chúng ta cần giao với variants_to_remove_exactly để đảm bảo chỉ xóa những gì người dùng thực sự muốn xóa
            # dựa trên original_numbers_to_remove_raw.
            numbers_in_this_match_to_remove = variants_to_remove_exactly.intersection(set(match_info.found_numbers_to_remove))

            if not numbers_in_this_match_to_remove:
                print(f"Không có số nào trong match này ({field_to_act_on} của {gateway_name}) cần xóa sau khi đối chiếu với variants_to_remove_exactly.")
                continue


            # --- Xử lý cho từng loại trường ---
            if gateway_type == "MG":
                if field_to_act_on == "CalloutCallerPrefixes":
                    current_prefixes_str = current_gateway_payload.get("calloutCallerPrefixes", "")
                    prefix_set = {p.strip() for p in current_prefixes_str.split(',') if p.strip()}
                    original_size = len(prefix_set)
                    prefix_set.difference_update(numbers_in_this_match_to_remove)
                    if len(prefix_set) < original_size:
                        changes_made_to_this_gateway = True
                        current_gateway_payload["calloutCallerPrefixes"] = ",".join(sorted(list(prefix_set)))
                        fields_processed_log.append(f"CalloutCallerPrefixes (removed: {', '.join(numbers_in_this_match_to_remove)})")
                        # TODO: Logic MG lockType (rất quan trọng!)
                        # new_prefix_list = list(prefix_set)
                        # callout_callee_exists = current_gateway_payload.get("calloutCalleePrefixes","").strip()
                        # if not new_prefix_list and not callout_callee_exists: current_gateway_payload["lockType"] = "3"
                        # elif len(new_prefix_list) <= 1 and not callout_callee_exists: ...

            elif gateway_type == "RG":
                if field_to_act_on == "CallinCallerPrefixes":
                    current_prefixes_str = current_gateway_payload.get("callinCallerPrefixes", "")
                    prefix_set = {p.strip() for p in current_prefixes_str.split(',') if p.strip()}
                    original_size = len(prefix_set)
                    prefix_set.difference_update(numbers_in_this_match_to_remove)
                    if len(prefix_set) < original_size:
                        changes_made_to_this_gateway = True
                        current_gateway_payload["callinCallerPrefixes"] = ",".join(sorted(list(prefix_set)))
                        fields_processed_log.append(f"CallinCallerPrefixes (removed: {', '.join(numbers_in_this_match_to_remove)})")

                elif field_to_act_on == "CallinCalleePrefixes":
                    current_prefixes_str = current_gateway_payload.get("callinCalleePrefixes", "")
                    prefix_set = {p.strip() for p in current_prefixes_str.split(',') if p.strip()}
                    original_size = len(prefix_set)
                    prefix_set.difference_update(numbers_in_this_match_to_remove)
                    if len(prefix_set) < original_size:
                        changes_made_to_this_gateway = True
                        current_gateway_payload["callinCalleePrefixes"] = ",".join(sorted(list(prefix_set)))
                        fields_processed_log.append(f"CallinCalleePrefixes (removed: {', '.join(numbers_in_this_match_to_remove)})")

                elif field_to_act_on == "RewriteRuleKey_DELETE":
                    # numbers_in_this_match_to_remove sẽ chứa virtual_key cần xóa
                    vk_to_delete = match_info.virtual_key_context
                    if vk_to_delete and vk_to_delete in variants_to_remove_exactly:
                        rules_str = current_gateway_payload.get("rewriteRulesInCaller", "")
                        rules_dict = utils.parse_vos_rewrite_rules(rules_str)
                        if vk_to_delete in rules_dict:
                            del rules_dict[vk_to_delete]
                            changes_made_to_this_gateway = True
                            current_gateway_payload["rewriteRulesInCaller"] = utils.format_rewrite_rules_for_vos(rules_dict)
                            fields_processed_log.append(f"RewriteRuleKey_DELETE (key: {vk_to_delete})")

                elif field_to_act_on == "RewriteRuleReal_MODIFY":
                    vk_context = match_info.virtual_key_context
                    reals_to_remove_from_this_key = numbers_in_this_match_to_remove
                    if vk_context and reals_to_remove_from_this_key:
                        rules_str = current_gateway_payload.get("rewriteRulesInCaller", "")
                        rules_dict = utils.parse_vos_rewrite_rules(rules_str)
                        if vk_context in rules_dict:
                            current_reals_in_key = {r.strip() for r in rules_dict[vk_context] if r.strip().lower() != "hetso"}
                            original_size = len(current_reals_in_key)
                            current_reals_in_key.difference_update(reals_to_remove_from_this_key)
                            if len(current_reals_in_key) < original_size:
                                changes_made_to_this_gateway = True
                                # Nếu key ảo là dạng 6 số và list số thực rỗng, VOS thường yêu cầu "hetso"
                                if not current_reals_in_key and utils.is_six_digit_virtual_number_candidate(vk_context):
                                    rules_dict[vk_context] = ["hetso"]
                                elif not current_reals_in_key: # Nếu rỗng và không phải số ảo 6 số, có thể xóa key hoặc để rỗng
                                    rules_dict[vk_context] = [] # Hoặc del rules_dict[vk_context] nếu muốn
                                else:
                                    rules_dict[vk_context] = sorted(list(current_reals_in_key))
                                current_gateway_payload["rewriteRulesInCaller"] = utils.format_rewrite_rules_for_vos(rules_dict)
                                fields_processed_log.append(f"RewriteRuleReal_MODIFY (key: {vk_context}, removed: {', '.join(reals_to_remove_from_this_key)})")
                # Sau khi xử lý tất cả các match cho RG, áp dụng logic lockType tổng thể
                if gateway_type == "RG" and changes_made_to_this_gateway:
                    # TODO: Áp dụng logic RG lockType (rất quan trọng!)
                    # rules_dict_final = utils.parse_vos_rewrite_rules(current_gateway_payload.get("rewriteRulesInCaller", ""))
                    # apply_rg_locktype_logic(current_gateway_payload, rules_dict_final)
                    # Bạn cần tạo hàm apply_rg_locktype_logic dựa trên logic cũ
                    print(f"LOGIC LOCKTYPE (RG Cleanup Execute): Cần áp dụng logic cập nhật lockType cho RG {gateway_name}.")


        # --- Gọi API cập nhật nếu có thay đổi ---
        if changes_made_to_this_gateway:
            success_update = False
            message_update = "Không có hành động cập nhật nào được thực hiện."
            try:
                if gateway_type == "MG":
                    # Giả sử bạn có hàm apply_mg_update_for_cleanup_backend trong mapping_gateway_management
                    # Hàm này nên nhận server_info, mg_name, và current_gateway_payload (đã chỉnh sửa)
                    success_update, message_update = mapping_gateway_management.apply_mg_update_for_cleanup_backend(
                        server_url=server_info_found["url"],
                        server_name=server_name,
                        mg_name=gateway_name,
                        updated_mg_data_payload=current_gateway_payload
                    )
                elif gateway_type == "RG":
                    # Tương tự cho RG
                    success_update, message_update = routing_gateway_management.apply_rg_update_for_cleanup_backend(
                        server_url=server_info_found["url"],
                        server_name=server_name,
                        rg_name=gateway_name,
                        updated_rg_data_payload=current_gateway_payload
                    )

                if success_update:
                    execution_results.append(CleanupExecutionResultItem(
                        server_name=server_name, gateway_type=gateway_type, gateway_name=gateway_name,
                        field_cleaned = "; ".join(fields_processed_log),
                        status="Success", message=message_update
                    ))
                else:
                    execution_results.append(CleanupExecutionResultItem(
                        server_name=server_name, gateway_type=gateway_type, gateway_name=gateway_name,
                        field_cleaned = "; ".join(fields_processed_log),
                        status="Failed", message=message_update
                    ))
            except Exception as e_update:
                print(f"Lỗi khi thực thi cập nhật cho {gateway_name} trên {server_name}: {e_update}")
                execution_results.append(CleanupExecutionResultItem(
                    server_name=server_name, gateway_type=gateway_type, gateway_name=gateway_name,
                    field_cleaned = "; ".join(fields_processed_log),
                    status="Failed", message=f"Lỗi ngoại lệ khi cập nhật: {str(e_update)}"
                ))
        else:
            execution_results.append(CleanupExecutionResultItem(
                server_name=server_name, gateway_type=gateway_type, gateway_name=gateway_name,
                status="NoActionNeeded", message="Không có thay đổi nào được thực hiện cho gateway này dựa trên các match và số cần xóa."
            ))

    return execution_results