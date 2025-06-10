# routing_gateway_management.py
import config
from api_client import call_api # Đã được refactor để trả về tuple (data, error_message)
from utils import (
    parse_vos_rewrite_rules,          
    is_six_digit_virtual_number_candidate,
)
# --- Routing Gateway Data Retrieval Functions ---

def get_all_routing_gateways(server_info: dict, filter_text: str = "") -> tuple[list[dict] | None, str | None]:
    if not server_info or "url" not in server_info or "name" not in server_info:
        return None, "Error: Server information is incomplete."
    base_url = server_info["url"]
    server_name = server_info["name"]

    api_data, error_msg_api = call_api(base_url, "GetGatewayRouting", {}, show_spinner=True, server_name_for_log=server_name)

    if error_msg_api:
        return None, f"Could not retrieve Routing Gateway list from server {server_name}: {error_msg_api}"
    if api_data is None: # Should ideally be caught by error_msg_api, but as a safeguard
        return None, f"Could not retrieve Routing Gateway list from server {server_name} (no data and no specific error)."

    routings_info_list = api_data.get("infoGatewayRoutings", [])
    if not routings_info_list:
        return [], None 

    if filter_text:
        filtered_routings = [
            rg for rg in routings_info_list if filter_text.lower() in rg.get("name", "").lower()
        ]
        if not filtered_routings:
            return [], f"No Routing Gateways found on server {server_name} matching filter: '{filter_text}'"
        return sorted(filtered_routings, key=lambda x: x.get("name", "Unnamed_RG")), None
    else:
        return sorted(routings_info_list, key=lambda x: x.get("name", "Unnamed_RG")), None

def get_routing_gateway_details(server_info: dict, rg_name: str) -> tuple[dict | None, str | None]:
    if not server_info or "url" not in server_info:
        return None, "Error: Server URL not provided."
    if not rg_name:
        return None, "Error: Routing Gateway name cannot be empty."

    base_url = server_info["url"]
    server_name = server_info.get("name", base_url)

    api_data, error_msg_api = call_api(base_url, "GetGatewayRouting", {}, show_spinner=False, server_name_for_log=server_name)

    if error_msg_api:
        return None, f"API call failed while fetching details for RG '{rg_name}' from server {server_name}: {error_msg_api}"
    
    if api_data and api_data.get("infoGatewayRoutings"):
        for rg_info_item in api_data.get("infoGatewayRoutings", []):
            if rg_info_item.get("name") == rg_name:
                return rg_info_item, None
        return None, f"Routing Gateway '{rg_name}' not found on server {server_name}."
    
    return None, f"No valid Routing Gateway data returned from server {server_name} when searching for RG '{rg_name}'."

# --- Routing Gateway Modification Functions ---

def update_routing_gateway(server_info: dict, rg_name_param: str, payload_update_data: dict) -> tuple[bool, str | None]:
    if not server_info or "url" not in server_info:
        return False, "Error: Server URL not provided for RG update."
    
    # rg_name_param là tên gốc, payload_update_data['name'] có thể là tên mới nếu đổi tên
    effective_rg_name = payload_update_data.get('name', rg_name_param)
    if not effective_rg_name:
        return False, "Error: Routing Gateway name cannot be empty for update (checked from param and payload)."
    if not payload_update_data:
        return False, "Error: Update payload cannot be empty."

    base_url = server_info["url"]
    server_name = server_info.get("name", base_url)

    api_data, error_msg_api = call_api(base_url, "ModifyGatewayRouting", payload_update_data, show_spinner=True, server_name_for_log=server_name)

    if error_msg_api:
        return False, f"Failed to update Routing Gateway '{effective_rg_name}' on {server_name}: {error_msg_api}"
    
    # call_api đã kiểm tra retCode == 0. Nếu error_msg_api là None, nghĩa là thành công.
    # api_data có thể là {} nếu API Modify không trả về body cụ thể khi thành công.
    return True, f"Routing Gateway '{effective_rg_name}' on server {server_name} updated successfully."


# --- Virtual Number and Rewrite Rule Management Functions ---

def get_all_virtual_number_definitions_backend() -> tuple[dict, str | None]: # Bỏ verbose
    all_virtuals_map = {}
    error_messages_list = []
    active_servers_list = config.VOS_SERVERS 

    for server_info_item in active_servers_list:
        server_name = server_info_item["name"]
        base_url = server_info_item["url"]
        
        response_rg_data, error_rg_api = call_api(base_url, "GetGatewayRouting", {}, show_spinner=False, server_name_for_log=server_name)
        
        if error_rg_api:
            error_messages_list.append(f"Failed to fetch RG data from {server_name}: {error_rg_api}")
            continue
        if not response_rg_data or not response_rg_data.get("infoGatewayRoutings"):
            continue

        for rg_data_item in response_rg_data.get("infoGatewayRoutings", []):
            rg_name_item = rg_data_item.get("name", f"Unnamed_RG_on_{server_name}")
            rewrite_rules_str_item = rg_data_item.get("rewriteRulesInCaller", "")
            parsed_rules_item = parse_vos_rewrite_rules(rewrite_rules_str_item)
            for virtual_key, real_list_values in parsed_rules_item.items():
                is_hetso = real_list_values == ["hetso"]
                count_reals = 0 if is_hetso or not real_list_values else len(real_list_values)
                definition_info = {
                    "server_name": server_name, "server_url": base_url, "rg_name": rg_name_item,
                    "reals": [] if is_hetso or not real_list_values else real_list_values,
                    "is_hetso": is_hetso, "real_numbers_count": count_reals,
                    "raw_rg_info": rg_data_item 
                }
                if virtual_key not in all_virtuals_map:
                    all_virtuals_map[virtual_key] = []
                all_virtuals_map[virtual_key].append(definition_info)
    
    final_error_message_summary = "; ".join(error_messages_list) if error_messages_list else None
    return all_virtuals_map, final_error_message_summary

def find_specific_virtual_number_definitions_backend(virtual_key_to_find: str) -> tuple[list[dict], str | None]:
    definitions_list = []
    error_messages_list = []
    if not virtual_key_to_find:
        return [], "Virtual number key to find cannot be empty."
    
    active_servers_list = config.VOS_SERVERS

    for server_info_item in active_servers_list:
        server_name = server_info_item["name"]
        base_url = server_info_item["url"]
        response_rg_data, error_rg_api = call_api(base_url, "GetGatewayRouting", {}, show_spinner=False, server_name_for_log=server_name)

        if error_rg_api:
            error_messages_list.append(f"Failed to fetch RG data from {server_name} for VN '{virtual_key_to_find}': {error_rg_api}")
            continue
        if not response_rg_data or not response_rg_data.get("infoGatewayRoutings"):
            continue 

        for rg_data_item in response_rg_data.get("infoGatewayRoutings", []):
            rg_name_current_item = rg_data_item.get("name", f"Unnamed_RG_on_{server_name}")
            rewrite_rules_str_item = rg_data_item.get("rewriteRulesInCaller", "")
            parsed_rules_item = parse_vos_rewrite_rules(rewrite_rules_str_item)
            if virtual_key_to_find in parsed_rules_item:
                reals_list_item = parsed_rules_item[virtual_key_to_find]
                is_hetso_val_item = reals_list_item == ["hetso"]
                reals_count_val_item = 0 if is_hetso_val_item or not reals_list_item else len(reals_list_item)
                definitions_list.append({
                    "virtual_key": virtual_key_to_find,
                    "server_name": server_name, "server_url": base_url,
                    "rg_name": rg_name_current_item,
                    "reals": reals_list_item, "real_numbers_count": reals_count_val_item,
                    "is_hetso": is_hetso_val_item, "raw_rg_info": rg_data_item,
                })
    final_error_message_summary = "; ".join(error_messages_list) if error_messages_list else None
    return definitions_list, final_error_message_summary

def find_rewrite_rule_keys_globally_backend(search_key_term_str: str) -> tuple[list[dict], str | None]:
    found_definitions_list = []
    error_messages_list = []
    if not search_key_term_str:
        return [], "Search term for rewrite rule keys cannot be empty."

    active_servers_list = config.VOS_SERVERS

    for server_info_item in active_servers_list:
        server_name = server_info_item["name"]
        base_url = server_info_item["url"]
        response_rg_data, error_rg_api = call_api(base_url, "GetGatewayRouting", {}, show_spinner=False, server_name_for_log=server_name)
        
        if error_rg_api:
            error_messages_list.append(f"Failed to fetch RG data from {server_name} for key search '{search_key_term_str}': {error_rg_api}")
            continue
        if not response_rg_data or not response_rg_data.get("infoGatewayRoutings"):
            continue

        for rg_data_item in response_rg_data.get("infoGatewayRoutings", []):
            rg_name_current_item = rg_data_item.get("name", f"Unnamed_RG_on_{server_name}")
            rewrite_rules_str_item = rg_data_item.get("rewriteRulesInCaller", "")
            parsed_rules_item = parse_vos_rewrite_rules(rewrite_rules_str_item)
            
            for current_key_in_rule_item, reals_list_values_item in parsed_rules_item.items():
                if search_key_term_str.lower() in current_key_in_rule_item.lower():
                    is_hetso_item = reals_list_values_item == ["hetso"]
                    reals_count_item = 0 if is_hetso_item or not reals_list_values_item else len(reals_list_values_item)
                    
                    found_definitions_list.append({
                        "found_key": current_key_in_rule_item,
                        "server_name": server_name, "server_url": base_url, "rg_name": rg_name_current_item,
                        "reals": reals_list_values_item, "real_numbers_count": reals_count_item,
                        "is_hetso": is_hetso_item, "raw_rg_info": rg_data_item,
                    })
    final_error_message_summary = "; ".join(error_messages_list) if error_messages_list else None
    return found_definitions_list, final_error_message_summary

# --- Routing Gateway Cleanup Support Functions (Multi-Server Backend) ---

def fetch_routings_for_server_backend(server_url: str, server_name: str) -> tuple[list[dict] | None, str | None]:
    api_data, error_msg = call_api(server_url, "GetGatewayRouting", {}, show_spinner=False, server_name_for_log=server_name)
    if error_msg:
        return None, error_msg
    if not api_data:
        return None, "No data returned from API for GetGatewayRouting."
    return api_data.get("infoGatewayRoutings", []), None

def identify_rgs_for_cleanup_backend(server_url: str, server_name: str, numbers_to_check_set: set[str]) -> tuple[list[dict] | None, str | None]:
    identified_rg_infos_list: list[dict] = []
    all_routings_on_server_list, error_fetch = fetch_routings_for_server_backend(server_url, server_name)
    
    if error_fetch:
        return None, f"Could not fetch RGs for cleanup from {server_name}: {error_fetch}"
    if all_routings_on_server_list is None: # Should be caught by error_fetch, but defensive
        return None, f"Received no RG list from {server_name} for cleanup."
    if not all_routings_on_server_list: # List is empty
        return [], None

    for rg_data_item in all_routings_on_server_list:
        rg_name = rg_data_item.get("name", f"Unnamed_RG_Cleanup_{server_name}")
        rg_name_lower = rg_name.lower()
        is_to_rg_flag = ("to" in rg_name_lower or "to-" in rg_name_lower or "to_" in rg_name_lower)
        
        callin_caller_str_val = rg_data_item.get("callinCallerPrefixes", "")
        original_callin_caller_list_val = [p.strip() for p in callin_caller_str_val.split(",") if p.strip()]
        common_in_callin_caller_val = sorted(list(set(original_callin_caller_list_val) & numbers_to_check_set))
        
        callin_callee_str_val = rg_data_item.get("callinCalleePrefixes", "")
        original_callin_callee_list_val = [p.strip() for p in callin_callee_str_val.split(",") if p.strip()]
        common_in_callin_callee_val = sorted(list(set(original_callin_callee_list_val) & numbers_to_check_set)) if is_to_rg_flag else []
        
        rewrite_str_val = rg_data_item.get("rewriteRulesInCaller", "")
        original_rewrite_parsed_val = parse_vos_rewrite_rules(rewrite_str_val)
        common_virtual_keys_as_keys_val = sorted([
            vk for vk in original_rewrite_parsed_val 
            if vk in numbers_to_check_set and is_six_digit_virtual_number_candidate(vk) # use refactored name
        ])
        
        common_real_values_map_val: dict[str, list[str]] = {}
        for vk_map, rv_list_map in original_rewrite_parsed_val.items():
            actual_reals_list = [r for r in rv_list_map if r.lower() != "hetso"]
            common_rv_for_this_key_list = sorted(list(set(actual_reals_list) & numbers_to_check_set))
            if common_rv_for_this_key_list: common_real_values_map_val[vk_map] = common_rv_for_this_key_list
                
        if common_in_callin_caller_val or common_in_callin_callee_val or common_virtual_keys_as_keys_val or bool(common_real_values_map_val):
            identified_rg_infos_list.append({
                "type": "RG", "server_url": server_url, "server_name": server_name, "name": rg_name, "is_to_rg": is_to_rg_flag,
                "original_callin_caller_prefixes_list": original_callin_caller_list_val, 
                "common_in_callin_caller": common_in_callin_caller_val,
                "original_callin_callee_prefixes_list": original_callin_callee_list_val, 
                "common_in_callin_callee": common_in_callin_callee_val,
                "original_rewrite_str": rewrite_str_val, 
                "original_rewrite_parsed": original_rewrite_parsed_val,
                "common_virtual_keys_to_delete": common_virtual_keys_as_keys_val, 
                "common_real_values_to_delete_map": common_real_values_map_val,
                "raw_rg_info": rg_data_item,
            })
    return identified_rg_infos_list, None

def apply_rg_update_for_cleanup_backend(server_url: str, server_name: str, rg_name: str, updated_rg_data_payload: dict) -> tuple[bool, str]:
    api_data, error_msg = call_api(server_url, "ModifyGatewayRouting", updated_rg_data_payload, show_spinner=False, server_name_for_log=server_name)
    
    if error_msg:
        return False, f"Error updating Routing Gateway '{rg_name}' on {server_name} for cleanup: {error_msg}"
    if api_data: # call_api already checked retCode
        return True, f"Routing Gateway '{rg_name}' on {server_name} updated successfully for cleanup."
    return False, f"Error updating Routing Gateway '{rg_name}' on {server_name} for cleanup: No data but no specific error."

# --- Functions related to finding linked Customers via MG (Backend) ---

def find_customers_linked_to_virtual_number_backend(virtual_number_key_str: str) -> tuple[list[dict] | None, str | None]:
    if not virtual_number_key_str:
        return None, "Virtual number key cannot be empty."

    linked_customers_info_list = []
    processed_customer_server_pairs_set = set() 
    error_messages_aggregated_list = []
    active_servers_list = config.VOS_SERVERS

    for server_info_mg_loop_item in active_servers_list:
        server_url_mg = server_info_mg_loop_item["url"]
        server_name_mg = server_info_mg_loop_item["name"]

        mg_list_api_data, mg_list_error = call_api(server_url_mg, "GetGatewayMapping", {}, show_spinner=False, timeout=20, server_name_for_log=server_name_mg)
        
        if mg_list_error:
            error_messages_aggregated_list.append(f"Could not fetch MGs from {server_name_mg} for VN link check: {mg_list_error}")
            continue
        if not mg_list_api_data or not mg_list_api_data.get("infoGatewayMappings"):
            continue

        for mg_item_data_val in mg_list_api_data.get("infoGatewayMappings", []):
            current_mg_prefixes_str_val = mg_item_data_val.get("calloutCallerPrefixes", "")
            if virtual_number_key_str in {p.strip() for p in current_mg_prefixes_str_val.split(",")}:
                mg_linked_customer_account_val = mg_item_data_val.get("account")
                mg_linked_customer_name_in_mg_val = mg_item_data_val.get("accountName")

                if mg_linked_customer_account_val and mg_linked_customer_name_in_mg_val:
                    customer_key_on_server_val = (mg_linked_customer_account_val, server_url_mg)
                    if customer_key_on_server_val in processed_customer_server_pairs_set:
                        continue 
                    processed_customer_server_pairs_set.add(customer_key_on_server_val)
                    
                    try:
                        # DELAYED IMPORT: Import customer_management here to avoid potential circular dependency at module load time
                        from customer_management import get_raw_customer_details 
                        customer_raw_data_val, cust_error_val = get_raw_customer_details(server_url_mg, server_name_mg, mg_linked_customer_account_val)
                    except ImportError: # Should not happen if structure is correct
                        error_messages_aggregated_list.append(f"Critical: Could not import customer_management for VN link check.")
                        continue # Skip this server or iteration

                    if cust_error_val:
                        error_messages_aggregated_list.append(f"Error fetching details for potential customer {mg_linked_customer_account_val} on {server_name_mg} (for VN link): {cust_error_val}")
                        continue
                    
                    if customer_raw_data_val and customer_raw_data_val.get("name", "").lower() == mg_linked_customer_name_in_mg_val.lower():
                        linked_customers_info_list.append({
                            "account_id": customer_raw_data_val.get("account"),
                            "customer_name_on_vos": customer_raw_data_val.get("name"),
                            "customer_name_in_mg": mg_linked_customer_name_in_mg_val,
                            "server_name": server_name_mg, "server_url": server_url_mg,
                            "linked_via_mg_name": mg_item_data_val.get("name"),
                        })
    
    final_error_message_summary = "; ".join(error_messages_aggregated_list) if error_messages_aggregated_list else None
    if not linked_customers_info_list and final_error_message_summary: # No results but there were errors
        return None, final_error_message_summary
    
    return linked_customers_info_list, final_error_message_summary