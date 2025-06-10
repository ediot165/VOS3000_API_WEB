# customer_management.py
from datetime import datetime, timezone
import sys # Cần import sys để dùng sys.modules
import config
from api_client import call_api # Đã refactor để trả về tuple (data, error_msg)
from utils import format_amount_vietnamese_style # Đảm bảo utils.py có hàm này với tên đúng

# --- Customer Information Retrieval and Update Functions (Backend) ---

def get_raw_customer_details(base_url: str, server_name: str, customer_account: str) -> tuple[dict | None, str | None]:
    payload = {"accounts": [customer_account]}
    api_data, error_msg_api = call_api(base_url, "GetCustomer", payload, show_spinner=False, server_name_for_log=server_name)

    if error_msg_api:
        return None, f"Failed to get customer details for {customer_account} on {server_name}: {error_msg_api}"
    if not api_data: 
        return None, f"No data returned for customer {customer_account} on {server_name} (and no specific error)."
    
    info_customers_list = api_data.get("infoCustomers", [])
    if not info_customers_list:
        return None, f"Customer {customer_account} not found or no data in infoCustomers list on {server_name}."
        
    return info_customers_list[0], None

def get_customer_details_for_display(base_url: str, server_name: str, customer_account: str) -> tuple[dict | None, list[dict] | None, str | None]:
    raw_details_data, error_fetch_raw = get_raw_customer_details(base_url, server_name, customer_account)
    
    if error_fetch_raw:
        return None, None, error_fetch_raw
    if not raw_details_data: 
        return None, None, f"No raw details found for customer {customer_account} on {server_name} to display."

    fields_to_display_list = [
        "account", "name", "agentAccount", "feeRateGroup",
        "money", "limitMoney", "todayConsumption",
        "lockType", "type", "category", "startTime", "validTime", "memo"
    ]
    
    display_data_key_value_list = []
    for key_item in fields_to_display_list:
        value_item = raw_details_data.get(key_item)
        display_value_item_str = "N/A"

        if value_item is not None:
            if key_item in ["money", "limitMoney", "todayConsumption"]:
                display_value_item_str = format_amount_vietnamese_style(value_item)
            elif key_item == "lockType":
                display_value_item_str = "Locked" if str(value_item) == "1" else "Active"
            elif key_item in ["startTime", "validTime"]:
                try:
                    timestamp_ms = int(value_item)
                    if -62135596800000 <= timestamp_ms <= 253402300799999 :
                        timestamp_s = timestamp_ms / 1000.0
                        dt_object = datetime.fromtimestamp(timestamp_s, tz=timezone.utc) 
                        display_value_item_str = dt_object.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        display_value_item_str = f"Invalid Timestamp ({value_item})"
                except (ValueError, TypeError, OverflowError):
                    display_value_item_str = str(value_item) 
            else:
                display_value_item_str = str(value_item)
            
        display_data_key_value_list.append({"field": key_item.replace("_", " ").title(), "value": display_value_item_str})
    
    return raw_details_data, display_data_key_value_list, None


def get_current_customer_limit_money(base_url: str, customer_account: str, server_name: str) -> tuple[float | str | None, str | None]:
    raw_details_data, error_fetch_raw = get_raw_customer_details(base_url, server_name, customer_account)

    if error_fetch_raw:
        return None, error_fetch_raw
    if not raw_details_data:
        return None, f"Could not retrieve customer information for '{customer_account}' to check credit limit."

    limit_money_value_data = raw_details_data.get("limitMoney")
    if limit_money_value_data is not None:
        val_str_data = str(limit_money_value_data).strip().lower()
        if val_str_data in ["-1", "infinity", "unlimited", "không giới hạn"]:
            return "Unlimited", None
        try:
            return float(limit_money_value_data), None
        except ValueError:
            return None, f"Invalid credit limit value ('{limit_money_value_data}') for customer {customer_account}."
    else: 
        return 0.0, f"Credit limit field ('limitMoney') not found for customer {customer_account}, assuming 0.0."


def _update_customer_api_call(base_url: str, payload_to_modify: dict, server_name: str) -> tuple[dict | None, str | None]:
    return call_api(
        base_url, 
        "ModifyCustomer",
        payload_to_modify, 
        show_spinner=False,
        server_name_for_log=server_name
    )

def update_customer_credit_limit(server_url: str, customer_account: str, new_credit_limit_str: str) -> tuple[bool, str | None]:
    if not server_url or not customer_account or new_credit_limit_str is None:
        return False, "Invalid input (server URL, customer account, or new credit limit value)."

    # Lấy danh sách server đang hoạt động một cách an toàn
    active_servers_list_update = config.VOS_SERVERS 
    streamlit_module_ref = sys.modules.get('streamlit')
    if streamlit_module_ref and hasattr(streamlit_module_ref, 'session_state') and 'vos_servers_list' in streamlit_module_ref.session_state:
        active_servers_list_update = streamlit_module_ref.session_state.vos_servers_list
    
    server_name_val_update = config.get_server_name_from_url(server_url, active_servers_list_update) # Truyền danh sách server đã lấy
    
    payload = {"account": customer_account, "limitMoney": str(new_credit_limit_str)}
    api_data, error_msg_api = _update_customer_api_call(server_url, payload, server_name_val_update)

    if error_msg_api:
        return False, f"Failed to update credit limit for {customer_account}: {error_msg_api}"
    
    formatted_limit_disp_update = new_credit_limit_str
    if str(new_credit_limit_str) == "-1": formatted_limit_disp_update = "Unlimited"
    else:
        try: formatted_limit_disp_update = format_amount_vietnamese_style(new_credit_limit_str)
        except Exception: pass 
    return True, f"Successfully updated credit limit for customer {customer_account} to {formatted_limit_disp_update}."


def update_customer_lock_status(server_url: str, customer_account: str, new_lock_status_str: str) -> tuple[bool, str | None]:
    if not server_url or not customer_account or new_lock_status_str not in ["0", "1"]:
        return False, "Invalid input (server URL, customer account, or lock status - must be '0' or '1')."

    # Lấy danh sách server đang hoạt động một cách an toàn
    active_servers_list_lock = config.VOS_SERVERS
    streamlit_module_ref_lock = sys.modules.get('streamlit')
    if streamlit_module_ref_lock and hasattr(streamlit_module_ref_lock, 'session_state') and 'vos_servers_list' in streamlit_module_ref_lock.session_state:
        active_servers_list_lock = streamlit_module_ref_lock.session_state.vos_servers_list

    server_name_val_lock = config.get_server_name_from_url(server_url, active_servers_list_lock) # Truyền danh sách server đã lấy
    
    payload = {"account": customer_account, "lockType": str(new_lock_status_str)}
    api_data, error_msg_api = _update_customer_api_call(server_url, payload, server_name_val_lock)

    if error_msg_api:
        return False, f"Failed to update lock status for {customer_account}: {error_msg_api}"

    action_desc_str_lock = "Locked" if new_lock_status_str == "1" else "Unlocked"
    return True, f"Successfully {action_desc_str_lock.lower()} account {customer_account}."


def fetch_all_customer_details_on_server(base_url: str, server_name: str, customer_accounts_list: list[str]) -> tuple[list[dict] | None, str | None]:
    if not customer_accounts_list:
        return [], None

    customer_details_compiled_list = []
    errors_collated_list = []

    for i, acc_item in enumerate(customer_accounts_list):
        raw_detail_item, error_item = get_raw_customer_details(base_url, server_name, acc_item)

        if error_item:
            errors_collated_list.append(f"Error for account {acc_item}: {error_item}")
            customer_details_compiled_list.append({
                "account": acc_item, "name": "[Error Loading Data]",
                "money": "0", "limitMoney": "0", "lockType": "0",
                "_error_fetching_details": error_item,
                "_server_name_source": server_name, "_server_url_source": base_url
            })
        elif raw_detail_item:
            raw_detail_item["_server_name_source"] = server_name
            raw_detail_item["_server_url_source"] = base_url
            raw_detail_item.setdefault("account", acc_item)
            raw_detail_item.setdefault("name", f"[Name data missing for {acc_item}]")
            raw_detail_item.setdefault("money", "0")
            raw_detail_item.setdefault("limitMoney", "0")
            raw_detail_item.setdefault("lockType", "0")
            customer_details_compiled_list.append(raw_detail_item)
    
    final_error_message = "; ".join(errors_collated_list) if errors_collated_list else None
    if not customer_details_compiled_list and final_error_message:
        return None, final_error_message
        
    return customer_details_compiled_list, final_error_message


def find_customers_across_all_servers(filter_type: str | None = None, filter_text: str = "") -> list[dict]:
    active_servers_find = config.VOS_SERVERS 
    if 'streamlit' in sys.modules:
        streamlit_module_find = sys.modules['streamlit']
        if hasattr(streamlit_module_find, 'session_state') and 'vos_servers_list' in streamlit_module_find.session_state:
            active_servers_find = streamlit_module_find.session_state.vos_servers_list
    
    if not active_servers_find:
        return [] 

    all_found_customers_list_find = []

    for server_info_find in active_servers_find:
        server_url_find = server_info_find["url"]
        server_name_find = server_info_find["name"]

        all_accounts_api_data_find, error_get_all_accounts_find = call_api(
            server_url_find, "GetAllCustomers", {}, 
            show_spinner=False, timeout=45, server_name_for_log=server_name_find
        )

        if error_get_all_accounts_find:
            print(f"Debug: Error fetching all accounts from {server_name_find}: {error_get_all_accounts_find}") 
            continue 
        if not all_accounts_api_data_find or not all_accounts_api_data_find.get("accounts"):
            continue

        accounts_on_server_list_find = all_accounts_api_data_find.get("accounts", [])
        accounts_to_fetch_details_list_find = []

        if filter_type == "account_id":
            accounts_to_fetch_details_list_find = [acc_f for acc_f in accounts_on_server_list_find if filter_text.lower() in acc_f.lower()] if filter_text else accounts_on_server_list_find
        elif filter_type == "account_name":
            accounts_to_fetch_details_list_find = accounts_on_server_list_find 
        elif filter_type is None or filter_type == "all":
            accounts_to_fetch_details_list_find = accounts_on_server_list_find
        else: 
            accounts_to_fetch_details_list_find = accounts_on_server_list_find
            
        if not accounts_to_fetch_details_list_find:
            continue

        detailed_customers_list_find, error_fetch_details_find = fetch_all_customer_details_on_server(
            server_url_find, server_name_find, accounts_to_fetch_details_list_find
        )
        
        if error_fetch_details_find:
            print(f"Debug: Error fetching customer details from {server_name_find}: {error_fetch_details_find}")
            continue
        if not detailed_customers_list_find:
            continue

        for cust_item_detail_find in detailed_customers_list_find:
            account_id_val_find = cust_item_detail_find.get("account")
            customer_name_val_find = cust_item_detail_find.get("name", "N/A")

            if "_error_fetching_details" in cust_item_detail_find and filter_type == "account_name":
                if filter_type == "account_id" and account_id_val_find and filter_text.lower() in account_id_val_find.lower():
                     pass 
                else:
                    continue 

            if filter_type == "account_name" and filter_text:
                if filter_text.lower() not in customer_name_val_find.lower():
                    continue
            
            balance_raw_val_find = 0.0
            try: balance_raw_val_find = float(cust_item_detail_find.get("money", 0.0))
            except (ValueError, TypeError): pass
            
            credit_limit_raw_val_str_find = cust_item_detail_find.get("limitMoney", "0")
            credit_limit_raw_val_find = 0.0
            if str(credit_limit_raw_val_str_find).strip().lower() in ["-1", "infinity", "unlimited", "không giới hạn"]:
                 credit_limit_raw_val_find = -1.0 
            else:
                try: credit_limit_raw_val_find = float(credit_limit_raw_val_str_find)
                except (ValueError, TypeError): pass

            all_found_customers_list_find.append({
                "No": 0, 
                "AccountID": account_id_val_find, "CustomerName": customer_name_val_find,
                "BalanceRaw": balance_raw_val_find, "CreditLimitRaw": credit_limit_raw_val_find, 
                "Status": "Locked" if str(cust_item_detail_find.get("lockType", "0")) == "1" else "Active",
                "ServerName": cust_item_detail_find.get("_server_name_source", server_name_find),
                "_server_url": cust_item_detail_find.get("_server_url_source", server_url_find),
                "_raw_details": cust_item_detail_find if "_error_fetching_details" not in cust_item_detail_find else None
            })

    if not all_found_customers_list_find:
        return []

    sorted_customers_list_final = sorted(all_found_customers_list_find, key=lambda x_sort: (x_sort["ServerName"].lower(), str(x_sort.get("AccountID","")).lower()))
    for i_sort, item_sorted_final in enumerate(sorted_customers_list_final, 1):
        item_sorted_final["No"] = i_sort
    return sorted_customers_list_final