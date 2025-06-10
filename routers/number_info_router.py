# vos_api_fastapi/routers/number_info_router.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Set, Dict, Any
import re # Để parse input string

from pydantic import BaseModel

# Import các module cần thiết từ thư mục gốc
import config
import utils
import mapping_gateway_management
import routing_gateway_management

# --- Định nghĩa Khuôn Mẫu Dữ Liệu (Pydantic Models) ---

class SearchNumberRequest(BaseModel):
    # Người dùng sẽ gửi một chuỗi chứa các số/keys, cách nhau bằng dấu phẩy, cách, hoặc xuống dòng
    search_terms_raw: str
    # Ví dụ: "12345, 67890\nkey_ảo"

class FoundNumberInfoItem(BaseModel):
    Server: str
    Type: str  # "MG" hoặc "RG"
    GatewayName: str
    Field: str # Ví dụ: "CalloutCallerPrefixes", "RewriteRule (Key)", "RewriteRule (Real Numbers)"
    FoundValues: str # Các giá trị khớp, cách nhau bằng dấu phẩy
    MatchingOriginalInputs: str # Các input gốc đã tìm thấy, cách nhau bằng dấu phẩy
    RewriteKeyContext: Optional[str] = None # Khóa ảo liên quan (nếu Field là Real Numbers của một rule)

    class Config:
        from_attributes = True


# --- Khởi tạo "Khu Vực" (Router) cho Tìm Thông Tin Số ---
router = APIRouter(
    prefix="/number-info", # Tiền tố cho tất cả các "quầy" ở đây
    tags=["Tìm Thông Tin Số"]    # Nhóm API trên trang /docs
)

def _get_matching_original_inputs(matched_variants: Set[str], original_inputs_list: List[str]) -> str:
    """
    Từ các variant đã khớp, tìm ra những input gốc nào đã tạo ra chúng.
    """
    found_original_inputs = set()
    for original_input in original_inputs_list:
        # Tạo lại variants cho từng original_input để so sánh
        # Điều này có thể tối ưu hơn nếu variants của mỗi original_input được lưu lại
        # ngay từ đầu, nhưng để đơn giản thì tạo lại ở đây.
        variants_for_this_original = utils.generate_search_variants(original_input)
        if not matched_variants.isdisjoint(variants_for_this_original): # Nếu có phần tử chung
            found_original_inputs.add(original_input)
    return ", ".join(sorted(list(found_original_inputs)))

@router.post("/search/",
             response_model=List[FoundNumberInfoItem],
             summary="Tìm kiếm số hoặc khóa trên tất cả các server và gateway")
async def search_numbers_globally(request: SearchNumberRequest):
    """
    Nhận một chuỗi các số hoặc khóa (cách nhau bằng dấu phẩy, cách, hoặc xuống dòng)
    và quét toàn bộ hệ thống VOS để tìm chúng.
    """
    print(f"API Router (Tìm Số): Nhận yêu cầu tìm: '{request.search_terms_raw[:100]}...'") # Log một phần input

    if not request.search_terms_raw.strip():
        raise HTTPException(status_code=400, detail="Chuỗi tìm kiếm không được để trống.")

    # 1. Xử lý input: tách thành list các số/khóa gốc
    original_inputs = [term.strip() for term in re.split(r'[,\s\n]+', request.search_terms_raw) if term.strip()]
    if not original_inputs:
        raise HTTPException(status_code=400, detail="Không có số/khóa hợp lệ nào trong chuỗi tìm kiếm.")

    # 2. Tạo tập hợp tất cả các biến thể tìm kiếm từ input gốc
    all_search_variants: Set[str] = set()
    for item_input in original_inputs:
        all_search_variants.update(utils.generate_search_variants(item_input))

    if not all_search_variants:
        return [] # Không có biến thể nào để tìm

    print(f"API Router (Tìm Số): Sẽ tìm kiếm {len(all_search_variants)} biến thể từ {len(original_inputs)} input gốc.")

    aggregated_findings: List[Dict[str, Any]] = [] # Dùng Dict để dễ tạo FoundNumberInfoItem

    # 3. Duyệt qua từng server trong config
    for server_info in config.VOS_SERVERS:
        server_name = server_info.get("name", "Unknown Server")
        print(f"API Router (Tìm Số): Đang quét server: {server_name}...")

        # --- Quét Mapping Gateways (MG) ---
        try:
            mg_list, mg_error = mapping_gateway_management.get_all_mapping_gateways(server_info, "")
            if mg_error:
                print(f"Lỗi khi lấy MG từ {server_name}: {mg_error}")
                # Có thể thêm lỗi này vào một danh sách lỗi chung để trả về nếu muốn
            elif mg_list:
                for mg_data in mg_list:
                    mg_name_item = mg_data.get("name", "Unnamed_MG")
                    mg_prefixes_str = mg_data.get("calloutCallerPrefixes", "")
                    if mg_prefixes_str:
                        mg_prefixes_set = {p.strip() for p in mg_prefixes_str.split(",") if p.strip()}
                        matched_in_mg = all_search_variants.intersection(mg_prefixes_set)
                        if matched_in_mg:
                            aggregated_findings.append({
                                "Server": server_name, "Type": "MG", "GatewayName": mg_name_item,
                                "Field": "CalloutCallerPrefixes",
                                "FoundValues": ", ".join(sorted(list(matched_in_mg))),
                                "MatchingOriginalInputs": _get_matching_original_inputs(matched_in_mg, original_inputs),
                                "RewriteKeyContext": None
                            })
        except Exception as e_mg:
            print(f"Lỗi ngoại lệ khi xử lý MG trên {server_name}: {e_mg}")


        # --- Quét Routing Gateways (RG) ---
        try:
            rg_list, rg_error = routing_gateway_management.get_all_routing_gateways(server_info, "")
            if rg_error:
                print(f"Lỗi khi lấy RG từ {server_name}: {rg_error}")
            elif rg_list:
                for rg_data in rg_list:
                    rg_name_item = rg_data.get("name", "Unnamed_RG")

                    # Kiểm tra CallinCallerPrefixes
                    caller_prefixes_str = rg_data.get("callinCallerPrefixes", "")
                    if caller_prefixes_str:
                        caller_prefixes_set = {p.strip() for p in caller_prefixes_str.split(",") if p.strip()}
                        matched_in_rg_caller = all_search_variants.intersection(caller_prefixes_set)
                        if matched_in_rg_caller:
                            aggregated_findings.append({
                                "Server": server_name, "Type": "RG", "GatewayName": rg_name_item,
                                "Field": "CallinCallerPrefixes",
                                "FoundValues": ", ".join(sorted(list(matched_in_rg_caller))),
                                "MatchingOriginalInputs": _get_matching_original_inputs(matched_in_rg_caller, original_inputs),
                                "RewriteKeyContext": None
                            })

                    # Kiểm tra CallinCalleePrefixes
                    callee_prefixes_str = rg_data.get("callinCalleePrefixes", "")
                    if callee_prefixes_str:
                        callee_prefixes_set = {p.strip() for p in callee_prefixes_str.split(",") if p.strip()}
                        matched_in_rg_callee = all_search_variants.intersection(callee_prefixes_set)
                        if matched_in_rg_callee:
                            aggregated_findings.append({
                                "Server": server_name, "Type": "RG", "GatewayName": rg_name_item,
                                "Field": "CallinCalleePrefixes",
                                "FoundValues": ", ".join(sorted(list(matched_in_rg_callee))),
                                "MatchingOriginalInputs": _get_matching_original_inputs(matched_in_rg_callee, original_inputs),
                                "RewriteKeyContext": None
                            })

                    # Kiểm tra RewriteRulesInCaller
                    rewrite_rules_str = rg_data.get("rewriteRulesInCaller", "")
                    if rewrite_rules_str:
                        parsed_rules = utils.parse_vos_rewrite_rules(rewrite_rules_str)
                        for key_rw, reals_list_rw in parsed_rules.items():
                            # Kiểm tra key ảo
                            if key_rw in all_search_variants:
                                aggregated_findings.append({
                                    "Server": server_name, "Type": "RG", "GatewayName": rg_name_item,
                                    "Field": "RewriteRule (Key)", "FoundValues": key_rw,
                                    "MatchingOriginalInputs": _get_matching_original_inputs({key_rw}, original_inputs),
                                    "RewriteKeyContext": key_rw # Chính nó là context
                                })
                            # Kiểm tra các số thực trong rule (trừ "hetso")
                            reals_set_rw = {r.strip() for r in reals_list_rw if r.strip().lower() != "hetso"}
                            matched_reals_rw = all_search_variants.intersection(reals_set_rw)
                            if matched_reals_rw:
                                aggregated_findings.append({
                                    "Server": server_name, "Type": "RG", "GatewayName": rg_name_item,
                                    "Field": "RewriteRule (Real Numbers)",
                                    "FoundValues": ", ".join(sorted(list(matched_reals_rw))),
                                    "MatchingOriginalInputs": _get_matching_original_inputs(matched_reals_rw, original_inputs),
                                    "RewriteKeyContext": key_rw # Key ảo là context
                                })
        except Exception as e_rg:
            print(f"Lỗi ngoại lệ khi xử lý RG trên {server_name}: {e_rg}")

    print(f"API Router (Tìm Số): Tìm thấy tổng cộng {len(aggregated_findings)} kết quả.")
    return aggregated_findings # FastAPI sẽ validate với List[FoundNumberInfoItem]