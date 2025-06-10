# app.py
import streamlit as st
from streamlit_option_menu import option_menu # Đảm bảo bạn đã cài đặt: pip install streamlit-option-menu
import sys
import os
import pandas as pd # Sẽ cần cho việc hiển thị bảng dữ liệu sau này
import re
# --- Cấu hình trang (Nên là lệnh Streamlit đầu tiên) ---
st.set_page_config(layout="wide", page_title="VOS3000 Management", page_icon="️🎯")
st.markdown("""
    <style>
    /* Áp dụng font Cambria cho toàn bộ body và các thành phần cơ bản */
    html, body, [class*="st-"] { 
        font-family: 'Cambria', 'Georgia', serif !important;
        color: #000001 !important; /* Màu chữ mặc định */ 
    }
    
    /* Bạn cũng có thể nhắm mục tiêu cụ thể hơn nếu cần */
    /* Ví dụ: cho các nút bấm */
    .stButton>button {
        font-family: 'Cambria', 'Georgia', serif !important;
        color: #4A55A2 !important; /* Màu chữ cho nút bấm */
        background-color: #ABB5EA !important; /* Màu nền cho nút bấm */
    }
    /* Style cho nút bấm KHI HOVER (ĐƯA CHUỘT TỚI) */
    .stButton>button:hover {
    border-color: white !important; /* << VIỀN MÀU ĐỎ KHI HOVER */
    font-weight: bold !important; /* Làm đậm chữ khi hover */
    }
            
    /* Ví dụ: cho các text input */
    .stTextInput input {
        font-family: 'Cambria', 'Georgia', serif !important;
        color: #4A55A2 !important; /* Màu chữ cho text input */
    }

    /* Ví dụ: cho các text area */
    .stTextArea>textarea {
        font-family: 'Cambria', 'Georgia', serif !important;
        color: #4A55A2 !important; /* Màu chữ cho text input */
        font-size: 14px !important; /* Kích thước chữ cho text area */
    }

    /* Ví dụ: cho các selectbox */
    .stSelectbox div[data-baseweb="select"] > div {
        font-family: 'Cambria', 'Georgia', serif !important;
        color: #4A55A2 !important; /* Màu chữ cho selectbox */
    }
    
    /* Ví dụ: cho các radio button label */
    .stRadio label {
        font-family: 'Cambria', 'Georgia', serif !important;
        color: #4A55A2 !important; /* Màu chữ cho text input */
    }

    /* Tiêu đề markdown (h1, h2, h3, etc.) */
    h1, h2, h3 {
        font-family: 'Cambria', 'Georgia', serif !important;
        color: #333F98 !important; /* Màu chữ cho tiêu đề */
    }
    h4, h5, h6 {
        font-family: 'Cambria', 'Georgia', serif !important;
        
    }
            
    /* Bảng dữ liệu (Pandas DataFrame) */
    .stDataFrame { /* Hoặc các class cụ thể hơn bên trong stDataFrame */
        font-family: 'Cambria', 'Georgia', serif !important;
        color: #4A55A2 !important; /* Màu chữ cho bảng dữ liệu */
        font-size: 14px !important; /* Kích thước chữ cho bảng dữ liệu */
    }

    /* Chữ trong option_menu (cần kiểm tra lại class nếu không ăn) */
    /* Dựa trên style bạn cung cấp cho option_menu, bạn có thể cần thêm vào đây */
    div[data-testid="stOptionMenu"] div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stOptionMenu"] .nav-link { /* Nhắm cả vào nav-link nếu text nằm trong đó */
        font-family: 'Cambria', 'Georgia', serif !important;
    }
    .streamlit-radio-selected-label p { 
        color: #FF4B4B !important;
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* --- Font Chữ Cambria cho Toàn Bộ Ứng Dụng (nếu chưa có) --- */
    html, body, [class*="st-"], .stDataFrame, .stTable { 
        font-family: 'Cambria', 'Georgia', serif !important; 
    }

    /* --- Tùy Chỉnh Bảng Kết Quả Tìm Kiếm Khách Hàng --- */
    /* Áp dụng cho DataFrame có key là customer_search_results_df_global (hoặc key bạn đặt) */
    /* Để nhắm mục tiêu cụ thể hơn, bạn có thể bọc DataFrame này trong một st.container() */
    /* và style cho container đó, ví dụ: .customer-search-results-container .stDataFrame */

    /* Container của DataFrame (nếu bạn muốn style cả khung bao quanh) */
    /* div[data-testid="stDataFrame"] { */
        /* border: 1px solid #4A55A2 !important; */ /* Ví dụ: thêm viền cho toàn bộ DataFrame */
        /* border-radius: 8px !important; */
    /* } */

    /* Header của bảng */
    .stDataFrame [data-testid="stDataFrameVacantScroll"] > div > div > div[role="columnheader"] > div > div,
    .stDataFrame [data-testid="stDataFrameFixedScroll"] > div > div > div[role="columnheader"] > div > div {
        background-color: #6c757d !important; /* Ví dụ: Màu xám tối cho header */
        color: white !important;
        font-weight: 600 !important;       /* Hơi đậm hơn chút */
        font-size: 15px !important;         /* Kích thước font chữ header */
        text-transform: none !important;    /* Bỏ uppercase nếu không muốn */
        border-bottom: 2px solid #495057 !important; /* Đường kẻ dưới header */
    }
    
    /* Chữ trong các ô dữ liệu của bảng */
    .stDataFrame [data-testid="stDataFrameCells"] [role="cell"] > div {
        color: #343a40 !important; /* Màu chữ đậm hơn một chút */
        font-size: 14px !important; /* Kích thước font trong ô */
    }

    /* Màu nền cho các dòng xen kẽ */
    .stDataFrame [data-testid="stDataFrameCells"] [role="row"]:nth-child(even) > [role="cell"] {
        background-color: #f8f9fa !important; 
    }
    .stDataFrame [data-testid="stDataFrameCells"] [role="row"]:nth-child(odd) > [role="cell"] {
        background-color: #ffffff !important; 
    }

    /* Màu khi hover qua dòng */
    .stDataFrame [data-testid="stDataFrameCells"] [role="row"]:hover > [role="cell"] {
        background-color: #CFD8DC !important; /* Màu xanh xám nhạt khi hover */
        color: black !important;
    }
    
    /* Màu cho dòng được chọn (Phần này có thể cần tùy chỉnh sâu hơn) */
    /* Streamlit sử dụng một lớp hoặc thuộc tính để đánh dấu dòng được chọn. */
    /* Bạn cần "Inspect Element" để tìm đúng selector cho phiên bản Streamlit của bạn. */
    /* Dưới đây là một ví dụ cố gắng nhắm mục tiêu dòng được chọn: */
    .stDataFrame [data-testid="stDataFrameContainer"] .data sécrétion-enabled.focusedin.row-selected {
        background-color: #FFC107 !important; /* Ví dụ: Màu vàng cho dòng được chọn */
        color: black !important; 
        font-weight: bold !important;
    }
    /* Hoặc một selector khác có thể hoạt động: */
    .stDataFrame [data-testid="stDataFrameCells"] [role="row"][aria-selected="true"] > [role="cell"] {
        background-color: #FFC107 !important; /* Ví dụ: Màu vàng */
        color: black !important;
        font-weight: bold !important;
    }
    /* Hoặc class mà Streamlit thường dùng cho row được select */
    .streamlit-data-frame tr.row-selected td,
    .streamlit-data-frame tr.row-selected:hover td {
        background-color: #FFC107 !important; 
        color: black !important;
        font-weight: bold !important;
    }

    </style>
    """, unsafe_allow_html=True)

if 'current_vos_server_info' not in st.session_state:
    st.session_state.current_vos_server_info = None
# 'vos_servers_list' sẽ được khởi tạo sau khi 'config' được import thành công

# --- Import các Module Backend ---
# Khối này cố gắng import các module backend cần thiết.
# Giả định các file module này nằm CÙNG THƯ MỤC với app.py
try:
    import config # Import config trước để có thể truy cập VOS_SERVERS

    # Khởi tạo 'vos_servers_list' trong session state SAU KHI config đã được import thành công
    if 'vos_servers_list' not in st.session_state:
        st.session_state.vos_servers_list = list(config.VOS_SERVERS) # Tạo một bản sao có thể thay đổi

    from api_client import call_api

    # Import các hàm từ các module backend đã được refactor (phiên bản tiếng Anh)
    # Các import này sẽ được mở rộng khi chúng ta refactor các trang khác.
    from customer_management import (
        find_customers_across_all_servers,
        get_customer_details_for_display,
        get_current_customer_limit_money,
        update_customer_credit_limit,
        update_customer_lock_status,
        # ... các hàm quản lý khách hàng khác nếu có ...
    )
    from mapping_gateway_management import (
        get_all_mapping_gateways,
        get_mapping_gateway_details, 
        update_mapping_gateway,
        identify_mg_for_cleanup_backend,
        apply_mg_update_for_cleanup_backend,
        # ... các hàm quản lý MG khác ...
    )
    from routing_gateway_management import (
        get_all_routing_gateways,
        get_routing_gateway_details,
        update_routing_gateway,
        identify_rgs_for_cleanup_backend,
        apply_rg_update_for_cleanup_backend,
        find_specific_virtual_number_definitions_backend,
        find_rewrite_rule_keys_globally_backend

        # ... các hàm quản lý RG khác ...
    )
    from utils import (
        format_amount_vietnamese_style,
        parse_vos_rewrite_rules,
        transform_real_number_for_vos_storage,
        format_rewrite_rules_for_vos,
        generate_search_variants,
        is_six_digit_virtual_number_candidate
    )

except ImportError as e:
    st.error(f"Lỗi Import: {e}. Vui lòng đảm bảo các file module backend (ví dụ: config.py, api_client.py, utils.py, v.v.) nằm CÙNG THƯ MỤC với file app.py và không có lỗi cú pháp.")
    st.error(f"Chi tiết lỗi: {e.name} - {e.msg}")
    st.error("Hãy kiểm tra xem tên file và tên hàm/lớp bạn đang cố import có chính xác không, đặc biệt là sau quá trình refactor đổi tên.")
    st.error(f"Đường dẫn sys.path hiện tại bao gồm: {sys.path}")
    st.stop() # Dừng ứng dụng nếu các import quan trọng bị lỗi


# --- Các Hàm Helper cho Giao diện Streamlit ---
def display_status_message(message: str, level: str = "INFO", server_name: str | None = None):
    """Hiển thị thông báo trạng thái trong Streamlit với định dạng phù hợp."""
    prefix = f"[{server_name}] " if server_name else ""
    full_message = f"{prefix}{message}"
    if level.upper() == "SUCCESS":
        st.success(full_message)
    elif level.upper() == "ERROR":
        st.error(full_message)
    elif level.upper() == "WARNING":
        st.warning(full_message)
    else: # INFO hoặc khác
        st.info(full_message)

def reset_source_states_qvn_helper_vnm():
    st.session_state.qvn_source_reals_to_use_original = []
    st.session_state.qvn_num_to_take_from_source = 0
    st.session_state.qvn_selected_manual_source_obj = None
    st.session_state.qvn_selected_manual_source_idx = None
    st.session_state.qvn_manual_source_search_input = ""
    st.session_state.qvn_manual_source_keys_found = []
    st.session_state.qvn_remaining_reals_in_source_key = []
    st.session_state.qvn_empty_source_key_action = None

def get_qvn_source_details_helper_vnm():
    source_key_name_h = "N/A"; source_rg_name_h = "N/A"; source_server_name_h = "N/A"
    if st.session_state.qvn_source_type == "auto_backup":
        source_key_name_h = st.session_state.qvn_auto_backup_key_in_target
        if st.session_state.qvn_selected_target_definition_obj:
            source_rg_name_h = st.session_state.qvn_selected_target_definition_obj['rg_name']
            source_server_name_h = st.session_state.qvn_selected_target_definition_obj['server_name']
    elif st.session_state.qvn_source_type == "manual_source_key" and st.session_state.qvn_selected_manual_source_obj:
        manual_src_obj_h = st.session_state.qvn_selected_manual_source_obj
        source_key_name_h = manual_src_obj_h['found_key']
        source_rg_name_h = manual_src_obj_h['rg_name']
        source_server_name_h = manual_src_obj_h['server_name']
    return source_key_name_h, source_rg_name_h, source_server_name_h

def get_qvn_source_details_for_execution_helper_vnm():
    key_h, rg_name_h, server_name_h = get_qvn_source_details_helper_vnm()
    server_url_h, raw_rg_info_h = None, None
    if st.session_state.qvn_source_type == "auto_backup" and st.session_state.qvn_selected_target_definition_obj:
        server_url_h = st.session_state.qvn_selected_target_definition_obj['server_url']
        raw_rg_info_h = st.session_state.qvn_selected_target_definition_obj['raw_rg_info']
    elif st.session_state.qvn_source_type == "manual_source_key" and st.session_state.qvn_selected_manual_source_obj:
        server_url_h = st.session_state.qvn_selected_manual_source_obj['server_url']
        raw_rg_info_h = st.session_state.qvn_selected_manual_source_obj['raw_rg_info']
    return key_h, rg_name_h, server_name_h, server_url_h, raw_rg_info_h, rg_name_h, server_name_h # Return rg_name, server_name again for consistency with how it was used

def apply_locktype_logic_qvn_helper(payload_rg_dict, rules_dict_to_check):
    current_callin_list_lock = [p.strip() for p in payload_rg_dict.get("callinCallerPrefixes", "").split(',') if p.strip()]
    meaningful_rules_lock = any(r_list_lock and r_list_lock != ["hetso"] for r_list_lock in rules_dict_to_check.values() if r_list_lock)
    original_lock_type_val = payload_rg_dict.get("lockType", 0) 

    if len(current_callin_list_lock) == 0 and not meaningful_rules_lock and not payload_rg_dict.get("callinCalleePrefixes","").strip():
        payload_rg_dict["lockType"] = 3 
    elif len(current_callin_list_lock) <= 1 and not meaningful_rules_lock:
        if original_lock_type_val not in [0, 1]: payload_rg_dict["lockType"] = 3
        else: payload_rg_dict["lockType"] = original_lock_type_val
    else: payload_rg_dict["lockType"] = original_lock_type_val

# --- Cấu hình Menu Chính ---
# (internal_key, display_label_english, icon_name_from_bootstrap_icons_or_similar)
main_menu_config = [
    ("HomePage", "Home", "house-door-fill"),
    ("ConfigureVOSTServer", "Configure Server", "server"),
    ("CustomerManagement", "Customer Information", "people-fill"),
    ("SearchNumberInfo", "Number Information", "search"),
    ("GatewayCleanup", "Gateway Cleanup", "trash2-fill"),
    ("VirtualNumberManagement", "Virtual Number ", "telephone-forward"),
    # ("AddNewVOSTServer", "Add New VOS Server", "plus-circle-dotted"), # Bỏ comment nếu trang này cần thiết
]

# --- Sidebar và Điều Hướng ---
with st.sidebar:
    # Phần markdown header trong sidebar của bạn (cho branding)
  

    st.markdown(    
    """
    <style>
        /* Nhúng font Bebas Neue từ Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Audiowide&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Scramento&display=swap');

        /* CSS cho tiêu đề VOS3000 */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 0.95; transform: translateY(0); }
        }
        .vos-container {
            font-family: 'Cambria', 'Inter', sans-serif; 
            text-align: center; 
            padding: 30px 20px;
            margin: 25px 15px; 
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(200, 220, 255, 0.3));
            backdrop-filter: blur(12px) saturate(180%); 
            -webkit-backdrop-filter: blur(12px) saturate(180%);
            border-radius: 20px; 
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15); 
            animation: fadeInUp 0.8s ease-out;
        }
        .vos-title {
            font-family: 'Audiowide', sans-serif; /* Font mạnh mẽ thay cho Boxing/Sigma One */
            font-size: 35px; /* Tăng kích thước để nổi bật */
            font-weight: 500; /* Bebas Neue không cần font-weight cao vì đã rất đậm */
            color: #4A55A2; /* Màu xanh đậm thay vì gradient */
            text-transform: uppercase; 
            letter-spacing: 1px; /* Tăng khoảng cách chữ để mạnh mẽ hơn */
            margin-bottom: 5px; 
            opacity: 0.95; 
            transition: transform 0.3s ease;
        }
        .vos-title:hover {
            transform: scale(1.05);
        }
        .vos-subtitle {
            font-family: 'Scramento', sans-serif;
            font-size: 20px; 
            font-weight: 400; 
            color: #333333; 
            font-style: italic; 
            letter-spacing: 1.5px; 
            text-shadow: 0 1px 4px rgba(0, 0, 0, 0.15); 
            background: linear-gradient(45deg, #666, #999); 
            -webkit-background-clip: text; 
            background-clip: text;
            transition: color 0.3s ease;
        }
        .vos-subtitle:hover {
            color: #4A55A2;
        }

        /* CSS cho sidebar (streamlit-option-menu) */
        div[data-testid="stSidebar"] a.nav-link {
            transition: all 0.3s ease !important;
        }
        div[data-testid="stSidebar"] a.nav-link:hover {
            background: linear-gradient(45deg, #F1F3F4, #E5E7EB) !important; /* Gradient cho hover */
            color: #202124 !important;
            transform: scale(1.05) !important; /* Phóng to nhẹ */
            border-radius: 20px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important; /* Bóng đổ */
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important; /* Bóng chữ */
        }
    </style>

    <!-- Tiêu đề VOS3000 -->
    <div class="vos-container">
        <div class="vos-title">VOS3000</div>
        <div class="vos-subtitle">Management System</div>
    </div>
    """,
    unsafe_allow_html=True
)

    # Menu điều hướng sử dụng streamlit-option-menu
    selected_page_label = option_menu(
        menu_title=None,  # Không có tiêu đề cho menu
        options=[item[1] for item in main_menu_config],  # Sử dụng nhãn tiếng Anh để hiển thị
        icons=None,  # Giữ None để ẩn icon mặc định
        menu_icon=None,  # Không có icon menu chính
        default_index=0,  # Mặc định chọn mục đầu tiên (Home)
        orientation="vertical",
        styles={
             "container": {
                "padding": "10px 5px",
                #"background-color": "#0E0E0D",
                "background-color": "transparent",
                "border-radius": "16px",
                "backdrop-filter": "blur(10px)",
                "-webkit-backdrop-filter": "blur(10px)",
                "margin": "0px",
                "box-shadow": "none" 
            },
            "icon": {
                "visibility": "hidden",
                "font-size": "0px",
                "width": "0px",
                "height": "0px",
                "padding": "0px",
                "margin": "0px 10px 0px 0px",
                "display": "none"
            },
            "nav-link": {
                "font-family": "'Cambria', sans-serif",
                "font-size": "18px",
                "font-weight": "500",
                "color": "#000000",
                "background-color": "transparent",
                "padding": "10px 15px 10px 15px",
                "margin": "4px 8px",
                "border-radius": "20px",
                "text-align": "left",
                "transition": "background-color 0.2s ease, color 0.2s ease",
                "border": "none",
                "box-shadow": "none"
            },
            "nav-link-selected": {
                "background-color": "#ABB5EA",
                "color": "#333F98",
                "font-weight": "600",
                "border-radius": "20px",
                "box-shadow": "none"
            }
        }
    )  

    # Ánh xạ nhãn hiển thị đã chọn về key nội bộ để định tuyến trang
    page_key_map = {label: key for key, label, _ in main_menu_config}
    current_page_key = page_key_map.get(selected_page_label)

# --- Logic Render Trang (Thiết lập ban đầu) ---
if current_page_key == "HomePage":
    st.markdown("""
        <style>
        /* General Page Styles (if not already global) */
        .main .block-container { 
            padding-top: 2rem; /* Add some padding at the top */
        }

        /* Homepage Specific Styles */
        .homepage-hero-title {
            font-family: 'Cambria', 'Inter', sans-serif;
            font-size: 3.2em; /* Slightly larger title */
            font-weight: 700;
            color: #4A55A2; /* A strong, professional blue/purple */
            text-align: center;
            margin-bottom: 0.5em;
            line-height: 1.2;
        }
        .homepage-subtitle {
            font-family: 'Cambria', 'Inter', sans-serif;
            font-size: 1.3em;
            color: #4A5568; /* A softer, secondary text color */
            text-align: center;
            margin-bottom: 2.5em;
            margin-left: auto;
            margin-right: auto;
        }
        .feature-section {
            padding: 2em 0;
        }
        .feature-col {
            text-align: center;
            padding: 1em;
        }
        .feature-icon {
            font-size: 3em; /* Larger icons */
            margin-bottom: 0.5em;
            color: #667eea; /* Icon color, can be same as title or accent */
        }
        .feature-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #2D3748; /* Darker text for feature titles */
            margin-bottom: 0.5em;
        }
        .feature-description {
            font-size: 1em;
            color: #718096; /* Lighter text for descriptions */
            line-height: 1.6;
        }
        .homepage-cta {
            font-family: 'Cambria', 'Inter', sans-serif;
            font-size: 1.2em;
            color: #4A55A2;
            text-align: center;
            margin-top: 3em;
            margin-bottom: 3em;
            font-weight: 500;
            padding: 1.5em; /* More padding for CTA */
            background-color: rgba(102, 126, 234, 0.08);
            border-radius: 12px; /* Softer border radius */
            border: 1px solid rgba(102, 126, 234, 0.2); /* Subtle border */
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Homepage Content ---
    st.markdown("<div class='homepage-hero-title'>VOS3000 Management System</div>", unsafe_allow_html=True)
    st.markdown("<p class='homepage-subtitle'>Streamline your VoIP service operations with this intuitive and powerful central dashboard. Effortlessly manage servers, customers, and configurations.</p>", unsafe_allow_html=True)
    
    st.markdown("---")

    st.markdown("<div class='feature-section'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='feature-col'>", unsafe_allow_html=True)
        st.markdown("<div class='feature-icon'>🔧</div>", unsafe_allow_html=True) # Wrench icon
        st.markdown("<div class='feature-title'>Server Configuration</div>", unsafe_allow_html=True)
        st.markdown("<p class='feature-description'>View and fine-tune Mapping & Routing Gateways with detailed controls and overview.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='feature-col'>", unsafe_allow_html=True)
        st.markdown("<div class='feature-icon'>👥</div>", unsafe_allow_html=True) # People icon
        st.markdown("<div class='feature-title'>Customer Management</div>", unsafe_allow_html=True)
        st.markdown("<p class='feature-description'>Search, manage credit limits, and update account statuses across all your VOS servers.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='feature-col'>", unsafe_allow_html=True)
        st.markdown("<div class='feature-icon'>📞</div>", unsafe_allow_html=True) # Phone icon
        st.markdown("<div class='feature-title'>Number & Rule Control</div>", unsafe_allow_html=True)
        st.markdown("<p class='feature-description'>Efficiently manage virtual numbers, rewrite rules, and perform gateway cleanups.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


    st.markdown("<p class='homepage-cta'>🚀 Select a function from the sidebar to begin exploring and managing your VOS3000 system!</p>", unsafe_allow_html=True)

elif current_page_key == "ConfigureVOSTServer":
    st.markdown(
        "<h1 style='text-align: center; color: #1E88E5;'>VOS3000 Server Configuration</h1>",
        unsafe_allow_html=True
    )

    if not st.session_state.vos_servers_list:
        st.warning("No VOS servers defined. Please add servers or check config.py.")
    else:
        with st.container():
            st.markdown("### Select Server to Configure")
            server_names_for_config_display = [s["name"] for s in st.session_state.vos_servers_list]
            default_idx_cfg_server = 0
            if st.session_state.current_vos_server_info and st.session_state.current_vos_server_info.get('name') in server_names_for_config_display:
                try:
                    default_idx_cfg_server = server_names_for_config_display.index(st.session_state.current_vos_server_info['name'])
                except ValueError:
                    default_idx_cfg_server = 0

            selected_server_name_cfg_page = st.selectbox(
                "Select VOS Server:",
                options=server_names_for_config_display,
                index=default_idx_cfg_server,
                key="config_page_server_selector",
                help="Choose a server to view and edit its configuration."
            )

            active_server_details_cfg = next(
                (s for s in st.session_state.vos_servers_list if s["name"] == selected_server_name_cfg_page), None
            )

        if active_server_details_cfg:
            if st.session_state.current_vos_server_info != active_server_details_cfg:
                st.session_state.current_vos_server_info = active_server_details_cfg
                st.info(f"Switched to server: {active_server_details_cfg['name']}")
                st.rerun()

            server_key_suffix_cfg = active_server_details_cfg['name'].replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")

            mg_list_ss_key = f"mg_list_data_{server_key_suffix_cfg}"
            mg_selected_info_ss_key = f"mg_selected_info_{server_key_suffix_cfg}"
            mg_operation_ss_key = f"mg_operation_choice_{server_key_suffix_cfg}"
            mg_filter_ss_key = f"mg_filter_input_{server_key_suffix_cfg}"
            mg_action_result_ss_key = f"mg_action_result_{server_key_suffix_cfg}"
            mg_current_detail_cache_key_pattern = f"mg_detail_cache_{{mg_name_safe}}_{server_key_suffix_cfg}"
            mg_last_selected_name_ss_key = f"mg_last_selected_name_{server_key_suffix_cfg}"
            mg_tab_server_tracker = f"mg_tab_active_server_{server_key_suffix_cfg}"
            if st.session_state.get(mg_tab_server_tracker) != active_server_details_cfg['name']:
                st.session_state[mg_list_ss_key] = []
                st.session_state[mg_selected_info_ss_key] = None
                st.session_state[mg_operation_ss_key] = "VIEW_MG_DETAILS"
                st.session_state[mg_filter_ss_key] = ""
                st.session_state[mg_action_result_ss_key] = None
                st.session_state[mg_last_selected_name_ss_key] = None
                st.session_state[mg_tab_server_tracker] = active_server_details_cfg['name']

            rg_list_ss_key = f"rg_list_data_{server_key_suffix_cfg}"
            rg_selected_info_ss_key = f"rg_selected_info_{server_key_suffix_cfg}"
            rg_operation_ss_key = f"rg_operation_choice_{server_key_suffix_cfg}"
            rg_filter_ss_key = f"rg_filter_input_{server_key_suffix_cfg}"
            rg_action_result_ss_key = f"rg_action_result_{server_key_suffix_cfg}"
            rg_current_detail_cache_key_pattern = f"rg_detail_cache_{{rg_name_safe}}_{server_key_suffix_cfg}"
            rg_last_selected_name_ss_key = f"rg_last_selected_name_{server_key_suffix_cfg}"
            rg_tab_server_tracker = f"rg_tab_active_server_{server_key_suffix_cfg}"
            rg_detail_cache_key_pattern = f"rg_detail_cache_tab_{{rg_name_safe}}_{server_key_suffix_cfg}"
            if st.session_state.get(rg_tab_server_tracker) != active_server_details_cfg['name']:
                st.session_state[rg_list_ss_key] = []
                st.session_state[rg_selected_info_ss_key] = None
                st.session_state[rg_operation_ss_key] = "VIEW_RG_DETAILS"
                st.session_state[rg_filter_ss_key] = ""
                st.session_state[rg_action_result_ss_key] = None
                st.session_state[rg_last_selected_name_ss_key] = None
                st.session_state[rg_tab_server_tracker] = active_server_details_cfg['name']

            tab_titles_cfg = ["Mapping Gateway Configuration", "Routing Gateway Configuration"]
            tab_mg, tab_rg = st.tabs(tab_titles_cfg)

            with tab_mg:
                st.markdown(f"### Mapping Gateways on {active_server_details_cfg['name']}")
                with st.container():
                    st.session_state[mg_filter_ss_key] = st.text_input(
                        "Filter Mapping Gateway by name (leave empty to list all):",
                        value=st.session_state.get(mg_filter_ss_key, ""),
                        key=f"mg_filter_input_widget_{server_key_suffix_cfg}",
                        help="Enter a name to filter the Mapping Gateway list."
                    ).strip()

                    if st.button("List / Find MGs", key=f"mg_find_button_{server_key_suffix_cfg}"):
                        st.session_state[mg_selected_info_ss_key] = None
                        st.session_state[mg_operation_ss_key] = "VIEW_MG_DETAILS"
                        st.session_state[mg_action_result_ss_key] = None
                        filter_val = st.session_state.get(mg_filter_ss_key, "")
                        with st.spinner("Loading Mapping Gateways..."):
                            mg_list_data, error_msg = get_all_mapping_gateways(active_server_details_cfg, filter_val)
                            if error_msg:
                                st.error(f"Error: {error_msg} (Server: {active_server_details_cfg['name']})")
                                st.session_state[mg_list_ss_key] = []
                            elif mg_list_data is not None:
                                st.session_state[mg_list_ss_key] = mg_list_data
                                if not mg_list_data:
                                    st.info(f"No Mapping Gateways found {('matching: ' + filter_val) if filter_val else ''}.")
                                else:
                                    st.success(f"Found {len(mg_list_data)} Mapping Gateway(s). Click a row to select.")
                            else:
                                st.session_state[mg_list_ss_key] = []
                                st.error(f"Failed to load MGs (Server: {active_server_details_cfg['name']}).")
                        st.rerun()

                    mg_list_current = st.session_state.get(mg_list_ss_key, [])
                    mg_df_widget_key = f"mg_list_df_{server_key_suffix_cfg}"

                    if mg_list_current:
                        st.markdown("#### Mapping Gateway List")
                        st.caption("Click a row to select a Mapping Gateway")
                        mg_df_data = [{"Name": mg.get('name', 'N/A'), 
                                       "Account": mg.get('account', 'N/A')} for mg in mg_list_current]
                        df_mg_display = pd.DataFrame(mg_df_data)

                        if not df_mg_display.empty:
                            st.dataframe(
                                df_mg_display,
                                use_container_width=True,
                                hide_index=True,
                                key=mg_df_widget_key,
                                on_select="rerun",
                                selection_mode="single-row",
                                column_config={
                                    "Name": st.column_config.TextColumn("MG Name", width="large"),
                                    "Account": st.column_config.TextColumn("Account", width="medium"),
                                }
                            )
                            if mg_df_widget_key in st.session_state and \
                               st.session_state[mg_df_widget_key].selection and \
                               st.session_state[mg_df_widget_key].selection.get("rows"):
                                selected_mg_idx = st.session_state[mg_df_widget_key].selection["rows"][0]
                                if 0 <= selected_mg_idx < len(mg_list_current):
                                    newly_selected_mg = mg_list_current[selected_mg_idx]
                                    if st.session_state.get(mg_selected_info_ss_key) != newly_selected_mg:
                                        st.session_state[mg_selected_info_ss_key] = newly_selected_mg
                                        st.session_state[mg_operation_ss_key] = "VIEW_MG_DETAILS"
                                        st.session_state[mg_action_result_ss_key] = None
                                        mg_name_safe_selected = newly_selected_mg.get("name", "").replace(" ", "_")
                                        detail_cache_key_to_clear = mg_current_detail_cache_key_pattern.format(mg_name_safe=mg_name_safe_selected)
                                        if detail_cache_key_to_clear in st.session_state:
                                            del st.session_state[detail_cache_key_to_clear]
                                        st.session_state[mg_last_selected_name_ss_key] = newly_selected_mg.get("name")
                            elif mg_df_widget_key in st.session_state and \
                                 st.session_state[mg_df_widget_key].selection and \
                                 not st.session_state[mg_df_widget_key].selection.get("rows") and \
                                 st.session_state.get(mg_selected_info_ss_key) is not None:
                                st.session_state[mg_selected_info_ss_key] = None
                                st.session_state[mg_operation_ss_key] = "VIEW_MG_DETAILS"
                                st.session_state[mg_action_result_ss_key] = None
                                st.session_state[mg_last_selected_name_ss_key] = None

                    selected_mg_object = st.session_state.get(mg_selected_info_ss_key)
                    if selected_mg_object:
                        st.divider()
                        selected_mg_name_for_ops = selected_mg_object.get('name', 'N/A')
                        st.markdown(f"### Operating on MG: {selected_mg_name_for_ops}")

                        mg_name_safe_ops = selected_mg_name_for_ops.replace(" ", "_")
                        detail_cache_key_ops = mg_current_detail_cache_key_pattern.format(mg_name_safe=mg_name_safe_ops)

                        if detail_cache_key_ops not in st.session_state or \
                           st.session_state.get(mg_last_selected_name_ss_key) != selected_mg_name_for_ops:
                            with st.spinner(f"Loading details for MG: {selected_mg_name_for_ops}..."):
                                mg_detail_data, err_msg_detail = get_mapping_gateway_details(active_server_details_cfg, selected_mg_name_for_ops)
                                if err_msg_detail:
                                    st.error(f"Error loading MG details: {err_msg_detail} (Server: {active_server_details_cfg['name']})")
                                    st.session_state[detail_cache_key_ops] = None
                                else:
                                    st.session_state[detail_cache_key_ops] = mg_detail_data
                            st.session_state[mg_last_selected_name_ss_key] = selected_mg_name_for_ops
                            st.rerun()

                        current_mg_detail_for_ops = st.session_state.get(detail_cache_key_ops)
                        if current_mg_detail_for_ops:
                            mg_detail_col, mg_action_col = st.columns([3, 2])

                            with mg_detail_col:
                                st.markdown("#### Mapping Gateway Details")
                                fields_to_show_mg = ["name", "account", "calloutCallerPrefixes", "calloutCalleePrefixes", 
                                                     "capacity", "lockType", "registerType", "remoteIps"]
                                detail_df_rows = []
                                for field in fields_to_show_mg:
                                    value = current_mg_detail_for_ops.get(field)
                                    display_val = str(value) if value is not None else "N/A"
                                    if field == "lockType": 
                                        display_val = "Locked" if str(value) == "1" else "Active"
                                    elif field == "registerType": 
                                        display_val = {"0": "Static", "1": "Dynamic"}.get(str(value), str(value))
                                    elif field in ["calloutCallerPrefixes", "calloutCalleePrefixes", "remoteIps"] and value and len(str(value)) > 40:
                                        display_val = str(value)[:40] + "..."
                                    detail_df_rows.append({"Field": field, "Value": display_val})
                                st.table(pd.DataFrame(detail_df_rows).set_index("Field"))

                            with mg_action_col:
                                st.markdown("#### Actions")
                                current_mg_op_choice = st.session_state.get(mg_operation_ss_key, "VIEW_MG_DETAILS")
                                op_suffix_form_key = f"{mg_name_safe_ops}_{server_key_suffix_cfg}"

                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    if st.button("Count Prefixes", key=f"mg_count_btn_{op_suffix_form_key}", use_container_width=True):
                                        st.session_state[mg_operation_ss_key] = "COUNT_PREFIXES"
                                        st.session_state[mg_action_result_ss_key] = None
                                        st.rerun()
                                with col2:
                                    if st.button("Add Prefixes", key=f"mg_add_form_btn_{op_suffix_form_key}", use_container_width=True):
                                        st.session_state[mg_operation_ss_key] = "ADD_PREFIXES_FORM"
                                        st.session_state[mg_action_result_ss_key] = None
                                        st.rerun()
                                with col3:
                                    if st.button("Delete Prefixes", key=f"mg_delete_form_btn_{op_suffix_form_key}", use_container_width=True):
                                        st.session_state[mg_operation_ss_key] = "DELETE_PREFIXES_FORM"
                                        st.session_state[mg_action_result_ss_key] = None
                                        st.rerun()

                                if current_mg_op_choice == "COUNT_PREFIXES":
                                    st.subheader("Prefix Count")
                                    prefixes_str = current_mg_detail_for_ops.get("calloutCallerPrefixes", "")
                                    prefixes_list = [p.strip() for p in prefixes_str.split(',') if p.strip()]
                                    st.markdown(f"Number of CalloutCallerPrefixes: **{len(prefixes_list)}**")
                                    if prefixes_list:
                                        with st.expander("View current prefixes"):
                                            st.json(prefixes_list)

                                elif current_mg_op_choice in ["ADD_PREFIXES_FORM", "DELETE_PREFIXES_FORM"]:
                                    action_verb = "Add" if current_mg_op_choice == "ADD_PREFIXES_FORM" else "Delete"
                                    st.subheader(f"{action_verb} Numbers in CalloutCallerPrefixes")
                                    with st.form(key=f"mg_prefix_op_form_{action_verb.lower()}_{op_suffix_form_key}"):
                                        current_prefixes_display = current_mg_detail_for_ops.get("calloutCallerPrefixes", "")
                                        st.caption(f"Current prefixes: {current_prefixes_display[:100]}{'...' if len(current_prefixes_display)>100 else ''}")
                                        numbers_input_mg = st.text_area(
                                            "Enter numbers (comma, space, or newline separated):",
                                            key=f"mg_numbers_input_{action_verb.lower()}_{op_suffix_form_key}",
                                            height=100
                                        )
                                        submitted_mg_op = st.form_submit_button(f"Confirm {action_verb}")

                                        if submitted_mg_op:
                                            if not numbers_input_mg.strip():
                                                st.warning("Please enter numbers to process.")
                                            else:
                                                input_numbers = [n.strip() for n in re.split(r'[,\s\n]+', numbers_input_mg) if n.strip()]
                                                payload_mg_op = current_mg_detail_for_ops.copy()
                                                original_list = [p.strip() for p in current_prefixes_display.split(',') if p.strip()]
                                                original_set = set(original_list)
                                                changed_flag = False
                                                success_op_text = ""

                                                if current_mg_op_choice == "ADD_PREFIXES_FORM":
                                                    to_add_list = [n for n in input_numbers if n not in original_set]
                                                    if to_add_list:
                                                        payload_mg_op["calloutCallerPrefixes"] = ",".join(original_list + to_add_list)
                                                        changed_flag = True
                                                        success_op_text = f"Prepared to add {len(to_add_list)} number(s)."
                                                    else:
                                                        st.info("No new numbers to add.")
                                                elif current_mg_op_choice == "DELETE_PREFIXES_FORM":
                                                    to_remove_set = {n for n in input_numbers if n in original_set}
                                                    if to_remove_set:
                                                        new_list = [p for p in original_list if p not in to_remove_set]
                                                        payload_mg_op["calloutCallerPrefixes"] = ",".join(new_list)
                                                        if len(new_list) == 0 and not payload_mg_op.get("calloutCalleePrefixes"):
                                                            payload_mg_op["lockType"] = 3
                                                        elif len(new_list) <= 1 and "lockType" not in payload_mg_op:
                                                            payload_mg_op["lockType"] = payload_mg_op.get("lockType", 3)
                                                        changed_flag = True
                                                        success_op_text = f"Prepared to delete {len(to_remove_set)} number(s)."
                                                    else:
                                                        st.info("No matching numbers found to delete.")

                                                if changed_flag:
                                                    with st.spinner(f"Processing {action_verb.lower()} prefixes..."):
                                                        update_success, update_msg = update_mapping_gateway(
                                                            active_server_details_cfg, 
                                                            selected_mg_name_for_ops, 
                                                            payload_mg_op
                                                        )
                                                        if update_success:
                                                            st.success(f"{success_op_text} {update_msg or 'Operation successful!'}")
                                                            with st.spinner(f"Refreshing details for MG: {selected_mg_name_for_ops}..."):
                                                                refreshed_detail, err_refresh = get_mapping_gateway_details(active_server_details_cfg, selected_mg_name_for_ops)
                                                                if err_refresh:
                                                                    st.error(f"Error refreshing MG details: {err_refresh}")
                                                                else:
                                                                    st.session_state[detail_cache_key_ops] = refreshed_detail
                                                            st.session_state[mg_operation_ss_key] = "VIEW_MG_DETAILS"
                                                            st.session_state[mg_action_result_ss_key] = None
                                                            st.rerun()
                                                        else:
                                                            st.error(update_msg or "Operation failed.")
                        else:
                            st.warning("MG details not available. Cannot perform operations.")

            with tab_rg:
                st.markdown(f"### Routing Gateways on {active_server_details_cfg['name']}")
                with st.container():
                    st.session_state[rg_filter_ss_key] = st.text_input(
                        "Filter Routing Gateway by name (leave empty for all):",
                        value=st.session_state.get(rg_filter_ss_key, ""),
                        key=f"rg_filter_input_widget_tab_{server_key_suffix_cfg}",
                        help="Enter a name to filter the Routing Gateway list."
                    ).strip()

                    if st.button("List / Find RGs", key=f"rg_find_button_tab_{server_key_suffix_cfg}"):
                        st.session_state[rg_selected_info_ss_key] = None
                        st.session_state[rg_operation_ss_key] = "VIEW_RG_DETAILS"
                        filter_val_rg_tab = st.session_state.get(rg_filter_ss_key, "")
                        with st.spinner("Loading Routing Gateways..."):
                            rg_list_data_tab, error_msg_rg_tab = get_all_routing_gateways(active_server_details_cfg, filter_val_rg_tab)
                            if error_msg_rg_tab:
                                st.error(f"Error: {error_msg_rg_tab} (Server: {active_server_details_cfg['name']})")
                                st.session_state[rg_list_ss_key] = []
                            elif rg_list_data_tab is not None:
                                st.session_state[rg_list_ss_key] = rg_list_data_tab
                                if not rg_list_data_tab:
                                    st.info(f"No RGs found {('matching: ' + filter_val_rg_tab) if filter_val_rg_tab else ''}.")
                                else:
                                    st.success(f"Found {len(rg_list_data_tab)} RG(s). Click a row to select.")
                            else:
                                st.session_state[rg_list_ss_key] = []
                                st.error("Failed to load RGs.")
                        st.rerun()

                    rg_list_current_tab = st.session_state.get(rg_list_ss_key, [])
                    rg_df_widget_key_tab = f"rg_list_df_tab_{server_key_suffix_cfg}"

                    if rg_list_current_tab:
                        st.markdown("#### Routing Gateway List")
                        st.caption("Click a row to select a Routing Gateway")
                        rg_df_data_tab = [{"Name": rg.get('name', 'N/A'),
                                           "Type": "TO" if any(x in rg.get('name', '').lower() for x in ['to', 'to-', 'to_']) else "FROM/OTHER"} 
                                          for rg in rg_list_current_tab]
                        df_rg_display_tab = pd.DataFrame(rg_df_data_tab)

                        if not df_rg_display_tab.empty:
                            st.dataframe(
                                df_rg_display_tab,
                                use_container_width=True,
                                hide_index=True,
                                key=rg_df_widget_key_tab,
                                on_select="rerun",
                                selection_mode="single-row",
                                column_config={
                                    "Name": st.column_config.TextColumn("RG Name", width="large"),
                                    "Type": st.column_config.TextColumn("Type", width="small"),
                                }
                            )
                            if rg_df_widget_key_tab in st.session_state and \
                               st.session_state[rg_df_widget_key_tab].selection and \
                               st.session_state[rg_df_widget_key_tab].selection.get("rows"):
                                selected_rg_idx_tab = st.session_state[rg_df_widget_key_tab].selection["rows"][0]
                                if 0 <= selected_rg_idx_tab < len(rg_list_current_tab):
                                    newly_selected_rg_tab = rg_list_current_tab[selected_rg_idx_tab]
                                    if st.session_state.get(rg_selected_info_ss_key) != newly_selected_rg_tab:
                                        st.session_state[rg_selected_info_ss_key] = newly_selected_rg_tab
                                        st.session_state[rg_operation_ss_key] = "VIEW_RG_DETAILS"
                                        rg_name_safe_sel_tab = newly_selected_rg_tab.get("name", "").replace(" ", "_")
                                        detail_cache_key_rg_clear_tab = rg_detail_cache_key_pattern.format(rg_name_safe=rg_name_safe_sel_tab)
                                        if detail_cache_key_rg_clear_tab in st.session_state:
                                            del st.session_state[detail_cache_key_rg_clear_tab]
                                        st.session_state[rg_last_selected_name_ss_key] = newly_selected_rg_tab.get("name")
                            elif rg_df_widget_key_tab in st.session_state and \
                                 st.session_state[rg_df_widget_key_tab].selection and \
                                 not st.session_state[rg_df_widget_key_tab].selection.get("rows") and \
                                 st.session_state.get(rg_selected_info_ss_key) is not None:
                                st.session_state[rg_selected_info_ss_key] = None
                                st.session_state[rg_operation_ss_key] = "VIEW_RG_DETAILS"
                                st.session_state[rg_last_selected_name_ss_key] = None

                    selected_rg_object_tab = st.session_state.get(rg_selected_info_ss_key)
                    if selected_rg_object_tab:
                        st.divider()
                        selected_rg_name_ops_tab = selected_rg_object_tab.get('name', 'N/A')
                        st.markdown(f"### Operating on RG: {selected_rg_name_ops_tab}")

                        rg_name_safe_ops_key_tab = selected_rg_name_ops_tab.replace(" ", "_")
                        detail_cache_key_rg_ops_tab = rg_detail_cache_key_pattern.format(rg_name_safe=rg_name_safe_ops_key_tab)

                        if detail_cache_key_rg_ops_tab not in st.session_state or \
                           st.session_state.get(rg_last_selected_name_ss_key) != selected_rg_name_ops_tab:
                            with st.spinner(f"Loading details for RG: {selected_rg_name_ops_tab}..."):
                                rg_detail_data_ops_tab, err_msg_rg_detail_tab = get_routing_gateway_details(active_server_details_cfg, selected_rg_name_ops_tab)
                                if err_msg_rg_detail_tab:
                                    st.error(f"Error loading RG details: {err_msg_rg_detail_tab}")
                                    st.session_state[detail_cache_key_rg_ops_tab] = None
                                else:
                                    st.session_state[detail_cache_key_rg_ops_tab] = rg_detail_data_ops_tab
                            st.session_state[rg_last_selected_name_ss_key] = selected_rg_name_ops_tab
                            st.rerun()

                        current_rg_detail_ops_tab = st.session_state.get(detail_cache_key_rg_ops_tab)
                        if current_rg_detail_ops_tab:
                            rg_detail_col_disp_tab, rg_action_col_disp_tab = st.columns([3, 2])
                            with rg_detail_col_disp_tab:
                                st.markdown("#### Routing Gateway Details")
                                fields_rg_disp = ["name", "callinCallerPrefixes", "callinCalleePrefixes", "rewriteRulesInCaller", "lockType", "registerType", "remoteIps"]
                                rows_rg_disp = []
                                expander_content = {}
                                for field in fields_rg_disp:
                                    val = current_rg_detail_ops_tab.get(field)
                                    disp_val = str(val) if val is not None else "N/A"
                                    if field == "lockType":
                                        disp_val = "Locked" if str(val) == "1" else "Active"
                                    elif field == "registerType":
                                        disp_val = {"0": "Static", "1": "Dynamic"}.get(str(val), str(val))
                                    elif field == "rewriteRulesInCaller":
                                        parsed = parse_vos_rewrite_rules(str(val))
                                        if parsed:
                                            disp_val = f"{len(parsed)} rule(s)"
                                            expander_content[f"Rewrite Rules Details##{rg_name_safe_ops_key_tab}"] = parsed
                                        else:
                                            disp_val = "No rules / Empty"
                                    elif field in ["callinCallerPrefixes", "callinCalleePrefixes", "remoteIps"] and val and len(str(val)) > 40:
                                        expander_content[f"Full {field}##{rg_name_safe_ops_key_tab}"] = str(val)
                                        disp_val = str(val)[:40] + "..."
                                    rows_rg_disp.append({"Field": field, "Value": disp_val})
                                st.table(pd.DataFrame(rows_rg_disp).set_index("Field"))
                                for title, content in expander_content.items():
                                    with st.expander(title.split("##")[0]):
                                        if isinstance(content, dict):
                                            for k_r, v_r_list in content.items():
                                                st.text(f"  {k_r}: {';'.join(v_r_list)}")
                                        else:
                                            st.text(content)

                            with rg_action_col_disp_tab:
                                st.markdown("#### Actions")
                                current_rg_op_choice_val_tab = st.session_state.get(rg_operation_ss_key, "VIEW_RG_DETAILS")
                                op_suffix_rg_form_key_tab = f"{rg_name_safe_ops_key_tab}_{server_key_suffix_cfg}"
                                is_to_rg_type_tab = any(x in selected_rg_name_ops_tab.lower() for x in ['to', 'to-', 'to_'])

                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    if st.button("Manage Rewrite Rules", key=f"rg_btn_rules_tab_{op_suffix_rg_form_key_tab}", use_container_width=True):
                                        st.session_state[rg_operation_ss_key] = "MANAGE_REWRITE_RULES"
                                        st.rerun()
                                with col2:
                                    if st.button("Manage Callin Caller Prefixes", key=f"rg_btn_caller_tab_{op_suffix_rg_form_key_tab}", use_container_width=True):
                                        st.session_state[rg_operation_ss_key] = "MANAGE_CALLER_PREFIXES"
                                        st.rerun()
                                with col3:
                                    if st.button("Manage Callin Callee Prefixes", key=f"rg_btn_callee_tab_{op_suffix_rg_form_key_tab}", use_container_width=True, disabled=not is_to_rg_type_tab):
                                        st.session_state[rg_operation_ss_key] = "MANAGE_CALLEE_PREFIXES"
                                        st.rerun()

                                if current_rg_op_choice_val_tab == "MANAGE_REWRITE_RULES":
                                    st.subheader("Manage Rewrite Rules")
                                    rules_str_form_rw = current_rg_detail_ops_tab.get("rewriteRulesInCaller", "")
                                    rules_dict_form_rw = parse_vos_rewrite_rules(rules_str_form_rw)

                                    with st.form(key=f"rg_rewrite_form_tab_{op_suffix_rg_form_key_tab}"):
                                        rw_virtual_key = st.text_input("Virtual Key (e.g., 6-digit):")
                                        rw_real_numbers_str = st.text_area("Real Numbers (comma-separated, or 'hetso'):", height=100)
                                        rw_action = st.radio("Action:", ["Add/Update Key", "Delete Key"], horizontal=True, key=f"rw_action_{op_suffix_rg_form_key_tab}")
                                        rw_submitted = st.form_submit_button("Execute Rewrite Rule Action")

                                        if rw_submitted:
                                            if not rw_virtual_key.strip() and rw_action != "Delete Key":
                                                st.warning("Virtual Key is required for Add/Update.")
                                            else:
                                                temp_rules_rw = rules_dict_form_rw.copy()
                                                vk_clean_rw = rw_virtual_key.strip()
                                                if rw_action == "Add/Update Key":
                                                    if not rw_real_numbers_str.strip():
                                                        st.warning("Real numbers are required for Add/Update.")
                                                    elif rw_real_numbers_str.strip().lower() == "hetso":
                                                        temp_rules_rw[vk_clean_rw] = ["hetso"]
                                                    else:
                                                        reals_raw_list = [r.strip() for r in rw_real_numbers_str.split(',') if r.strip()]
                                                        reals_transformed_list = [transform_real_number_for_vos_storage(r) for r in reals_raw_list if transform_real_number_for_vos_storage(r)]
                                                        temp_rules_rw[vk_clean_rw] = list(set(reals_transformed_list))
                                                elif rw_action == "Delete Key":
                                                    if vk_clean_rw in temp_rules_rw:
                                                        del temp_rules_rw[vk_clean_rw]
                                                    else:
                                                        st.info(f"Key '{vk_clean_rw}' not found for deletion.")
                                                        st.stop()

                                                payload_rg_rw_update = current_rg_detail_ops_tab.copy()
                                                payload_rg_rw_update["rewriteRulesInCaller"] = format_rewrite_rules_for_vos(temp_rules_rw)
                                                if not any(temp_rules_rw.values()):
                                                    payload_rg_rw_update["lockType"] = 3

                                                with st.spinner("Updating Rewrite Rules..."):
                                                    success_rw_op, msg_rw_op = update_routing_gateway(active_server_details_cfg, selected_rg_name_ops_tab, payload_rg_rw_update)
                                                    if success_rw_op:
                                                        st.success(msg_rw_op or "Rewrite Rules updated successfully!")
                                                        refreshed_rg_detail, err_ref_rg = get_routing_gateway_details(active_server_details_cfg, selected_rg_name_ops_tab)
                                                        if not err_ref_rg:
                                                            st.session_state[detail_cache_key_rg_ops_tab] = refreshed_rg_detail
                                                        st.session_state[rg_operation_ss_key] = "VIEW_RG_DETAILS"
                                                        st.rerun()
                                                    else:
                                                        st.error(msg_rw_op or "Failed to update Rewrite Rules.")

                                elif current_rg_op_choice_val_tab in ["MANAGE_CALLER_PREFIXES", "MANAGE_CALLEE_PREFIXES"]:
                                    prefix_type_key = "callinCallerPrefixes" if current_rg_op_choice_val_tab == "MANAGE_CALLER_PREFIXES" else "callinCalleePrefixes"
                                    prefix_display_name = "Callin Caller Prefixes" if prefix_type_key == "callinCallerPrefixes" else "Callin Callee Prefixes"
                                    st.subheader(f"Manage {prefix_display_name}")
                                    current_prefixes_str_form = current_rg_detail_ops_tab.get(prefix_type_key, "")
                                    prefix_list_form = [p.strip() for p in current_prefixes_str_form.split(',') if p.strip()]
                                    st.caption(f"Current prefixes: {current_prefixes_str_form[:100]}{'...' if len(current_prefixes_str_form)>100 else ''}")

                                    with st.form(key=f"rg_prefix_form_{prefix_type_key}_{op_suffix_rg_form_key_tab}"):
                                        numbers_prefix_input_str = st.text_area(
                                            "Enter numbers (comma, space, or newline separated):",
                                            height=100
                                        )
                                        action_prefix_form = st.radio("Action:", ["Add", "Delete"], horizontal=True, key=f"rg_prefix_action_{prefix_type_key}_{op_suffix_rg_form_key_tab}")
                                        submitted_prefix_op = st.form_submit_button(f"Execute {prefix_display_name} Action")

                                        if submitted_prefix_op:
                                            if not numbers_prefix_input_str.strip():
                                                st.warning("Please enter numbers.")
                                            else:
                                                input_numbers_list_prefix = [n.strip() for n in re.split(r'[,\s\n]+', numbers_prefix_input_str) if n.strip()]
                                                new_prefix_list_final = list(prefix_list_form)
                                                changed_prefix_flag = False

                                                if action_prefix_form == "Add":
                                                    added_count_prefix = 0
                                                    for num_add_p in input_numbers_list_prefix:
                                                        if num_add_p not in new_prefix_list_final:
                                                            new_prefix_list_final.append(num_add_p)
                                                            added_count_prefix += 1
                                                    if added_count_prefix > 0:
                                                        changed_prefix_flag = True
                                                    else:
                                                        st.info("No new prefixes to add.")
                                                elif action_prefix_form == "Delete":
                                                    removed_count_prefix = 0
                                                    temp_list_after_delete = [p for p in new_prefix_list_final if p not in input_numbers_list_prefix]
                                                    if len(temp_list_after_delete) != len(new_prefix_list_final):
                                                        new_prefix_list_final = temp_list_after_delete
                                                        changed_prefix_flag = True
                                                    else:
                                                        st.info("No matching prefixes found to delete.")

                                                if changed_prefix_flag:
                                                    payload_rg_prefix_update = current_rg_detail_ops_tab.copy()
                                                    payload_rg_prefix_update[prefix_type_key] = ",".join(new_prefix_list_final)

                                                    with st.spinner(f"Updating {prefix_display_name}..."):
                                                        success_prefix_op, msg_prefix_op = update_routing_gateway(active_server_details_cfg, selected_rg_name_ops_tab, payload_rg_prefix_update)
                                                        if success_prefix_op:
                                                            st.success(msg_prefix_op or f"{prefix_display_name} updated successfully!")
                                                            refreshed_rg_detail_p, err_ref_rg_p = get_routing_gateway_details(active_server_details_cfg, selected_rg_name_ops_tab)
                                                            if not err_ref_rg_p:
                                                                st.session_state[detail_cache_key_rg_ops_tab] = refreshed_rg_detail_p
                                                            st.session_state[rg_operation_ss_key] = "VIEW_RG_DETAILS"
                                                            st.rerun()
                                                        else:
                                                            st.error(msg_prefix_op or f"Failed to update {prefix_display_name}.")
                        else:
                            st.error(f"Details for RG '{selected_rg_name_ops_tab}' could not be loaded. Cannot perform operations.")

elif current_page_key == "SearchNumberInfo":
    st.header("Search Number Information")

    if 'search_num_input_text' not in st.session_state:
        st.session_state.search_num_input_text = ""
    if 'search_num_results_data' not in st.session_state:
        st.session_state.search_num_results_data = None
    if 'search_num_original_inputs_list' not in st.session_state:
        st.session_state.search_num_original_inputs_list = []
    if 'search_num_all_variants_set' not in st.session_state:
        st.session_state.search_num_all_variants_set = set()

    st.session_state.search_num_input_text = st.text_area(
        "Enter numbers or keys to search (comma, space, or newline separated):",
        value=st.session_state.search_num_input_text,
        height=70,
        key="search_num_info_input_area"
    )

    if st.button("Search Numbers/Keys", key="search_num_info_button"):
        st.session_state.search_num_results_data = None
        st.session_state.search_num_original_inputs_list = []
        st.session_state.search_num_all_variants_set = set()

        raw_input_str = st.session_state.search_num_input_text
        if not raw_input_str.strip():
            display_status_message("Please enter numbers or keys to search.", "WARNING")
        else:
            original_inputs = [n.strip() for n in re.split(r'[,\s\n]+', raw_input_str) if n.strip()]
            if not original_inputs:
                display_status_message("Processed input list is empty.", "WARNING")
            else:
                st.session_state.search_num_original_inputs_list = original_inputs
                
                all_variants = set()
                for item_input in original_inputs:
                    all_variants.update(generate_search_variants(item_input))
                
                if not all_variants:
                    display_status_message("Could not generate any search variants from the input.", "INFO")
                else:
                    st.session_state.search_num_all_variants_set = all_variants
                    display_status_message(f"Searching for {len(all_variants)} variants (derived from {len(original_inputs)} original inputs) across all servers...", "INFO")

                    with st.spinner("Scanning all servers... This might take a while."):
                        active_servers_search = st.session_state.get('vos_servers_list', config.VOS_SERVERS)
                        aggregated_findings_for_search = []

                        for server_info_search in active_servers_search:
                            s_url, s_name = server_info_search["url"], server_info_search["name"]

                            mg_list_data_search, err_mg_list = get_all_mapping_gateways(server_info_search, "")
                            if err_mg_list:
                                display_status_message(f"Error fetching MGs from {s_name}: {err_mg_list}", "ERROR")
                            elif mg_list_data_search:
                                for mg_data_item in mg_list_data_search:
                                    mg_name_item = mg_data_item.get("name", "Unnamed_MG")
                                    mg_prefixes_str = mg_data_item.get("calloutCallerPrefixes", "")
                                    if mg_prefixes_str:
                                        mg_prefixes_set = {p.strip() for p in mg_prefixes_str.split(",") if p.strip()}
                                        matched_in_mg = all_variants.intersection(mg_prefixes_set)
                                        if matched_in_mg:
                                            aggregated_findings_for_search.append({
                                                "Server": s_name, "Type": "MG", "Gateway Name": mg_name_item,
                                                "Field": "CalloutCallerPrefixes", "Found Values": ", ".join(sorted(list(matched_in_mg))),
                                                "Matching Original Inputs": ", ".join(sorted(list(set(orig for var in matched_in_mg for orig in original_inputs if var in generate_search_variants(orig))))),
                                                "Rewrite Key Context": "N/A"
                                            })
                            
                            rg_list_data_search, err_rg_list = get_all_routing_gateways(server_info_search, "")
                            if err_rg_list:
                                display_status_message(f"Error fetching RGs from {s_name}: {err_rg_list}", "ERROR")
                            elif rg_list_data_search:
                                for rg_data_item in rg_list_data_search:
                                    rg_name_item = rg_data_item.get("name", "Unnamed_RG")
                                    
                                    caller_prefixes_str = rg_data_item.get("callinCallerPrefixes", "")
                                    if caller_prefixes_str:
                                        caller_prefixes_set = {p.strip() for p in caller_prefixes_str.split(",") if p.strip()}
                                        matched_in_rg_caller = all_variants.intersection(caller_prefixes_set)
                                        if matched_in_rg_caller:
                                            aggregated_findings_for_search.append({
                                                "Server": s_name, "Type": "RG", "Gateway Name": rg_name_item,
                                                "Field": "CallinCallerPrefixes", "Found Values": ", ".join(sorted(list(matched_in_rg_caller))),
                                                "Matching Original Inputs": ", ".join(sorted(list(set(orig for var in matched_in_rg_caller for orig in original_inputs if var in generate_search_variants(orig))))),
                                                "Rewrite Key Context": "N/A"
                                            })

                                    callee_prefixes_str = rg_data_item.get("callinCalleePrefixes", "")
                                    if callee_prefixes_str:
                                        callee_prefixes_set = {p.strip() for p in callee_prefixes_str.split(",") if p.strip()}
                                        matched_in_rg_callee = all_variants.intersection(callee_prefixes_set)
                                        if matched_in_rg_callee:
                                            aggregated_findings_for_search.append({
                                                "Server": s_name, "Type": "RG", "Gateway Name": rg_name_item,
                                                "Field": "CallinCalleePrefixes", "Found Values": ", ".join(sorted(list(matched_in_rg_callee))),
                                                "Matching Original Inputs": ", ".join(sorted(list(set(orig for var in matched_in_rg_callee for orig in original_inputs if var in generate_search_variants(orig))))),
                                                "Rewrite Key Context": "N/A"
                                            })
                                    
                                    rewrite_rules_str_val = rg_data_item.get("rewriteRulesInCaller", "")
                                    if rewrite_rules_str_val:
                                        parsed_rules_val = parse_vos_rewrite_rules(rewrite_rules_str_val)
                                        for key_rw, reals_list_rw in parsed_rules_val.items():
                                            if key_rw in all_variants:
                                                aggregated_findings_for_search.append({
                                                    "Server": s_name, "Type": "RG", "Gateway Name": rg_name_item,
                                                    "Field": "RewriteRule (Key)", "Found Values": key_rw,
                                                    "Matching Original Inputs": ", ".join(sorted(list(set(orig for var in {key_rw} for orig in original_inputs if var in generate_search_variants(orig))))),
                                                    "Rewrite Key Context": key_rw
                                                })
                                            
                                            reals_set_rw = {r.strip() for r in reals_list_rw if r.strip().lower() != "hetso"}
                                            matched_reals_rw = all_variants.intersection(reals_set_rw)
                                            if matched_reals_rw:
                                                aggregated_findings_for_search.append({
                                                    "Server": s_name, "Type": "RG", "Gateway Name": rg_name_item,
                                                    "Field": "RewriteRule (Real Numbers)", "Found Values": ", ".join(sorted(list(matched_reals_rw))),
                                                    "Matching Original Inputs": ", ".join(sorted(list(set(orig for var in matched_reals_rw for orig in original_inputs if var in generate_search_variants(orig))))),
                                                    "Rewrite Key Context": key_rw
                                                })
                        st.session_state.search_num_results_data = aggregated_findings_for_search
                        if not aggregated_findings_for_search:
                            display_status_message("No occurrences found for the given numbers/keys or their variants.", "INFO")
                        else:
                            display_status_message(f"Search complete. Found {len(aggregated_findings_for_search)} occurrences.", "SUCCESS")
                    st.rerun()

    if st.session_state.search_num_results_data is not None:
        if not st.session_state.search_num_results_data:
            pass
        else:
            st.markdown("##### Search Results:")
            df_search_results_display = pd.DataFrame(st.session_state.search_num_results_data)
            
            column_config_search_num = {
                "Server": st.column_config.TextColumn("Server", width="medium"),
                "Type": st.column_config.TextColumn("GW Type", width="small"),
                "Gateway Name": st.column_config.TextColumn("Gateway/Routing Name", width="large"),
                "Field": st.column_config.TextColumn("Field / Rule Type", width="medium"),
                "Found Values": st.column_config.TextColumn("Matching Value(s) Found", width="large"),
                "Matching Original Inputs": st.column_config.TextColumn("Original Input(s) Matched", width="large"),
                "Rewrite Key Context": st.column_config.TextColumn("Context (Rewrite Key)", width="medium"),
            }
            
            df_height_search = (len(df_search_results_display) + 1) * 35 + 3 if len(df_search_results_display) < 15 else 530
            
            st.dataframe(
                df_search_results_display,
                use_container_width=True,
                hide_index=True,
                column_config=column_config_search_num,
                height=df_height_search
            )

elif current_page_key == "GatewayCleanup": # Using the English internal key
    st.header("Gateway Cleanup (Remove Numbers from MG/RG)")

    # --- Session State Initialization for Gateway Cleanup Page ---
    if 'cleanup_input_numbers_text' not in st.session_state:
        st.session_state.cleanup_input_numbers_text = ""
    if 'cleanup_scope_selection' not in st.session_state:
        st.session_state.cleanup_scope_selection = "Both" # Default scope
    if 'cleanup_scan_results_list' not in st.session_state: # Stores combined MG and RG items found
        st.session_state.cleanup_scan_results_list = []
    if 'cleanup_items_for_editor' not in st.session_state: # For st.data_editor
        st.session_state.cleanup_items_for_editor = pd.DataFrame()
    if 'cleanup_execution_log_messages' not in st.session_state:
        st.session_state.cleanup_execution_log_messages = []
    if 'cleanup_current_step' not in st.session_state:
        st.session_state.cleanup_current_step = "input_numbers" # Steps: input_numbers, show_results, execute_cleanup, show_log

    # --- Step 1: Input Numbers and Scope ---
    if st.session_state.cleanup_current_step == "input_numbers":
        st.subheader("Step 1: Enter Numbers and Select Scope for Cleanup")
        st.session_state.cleanup_input_numbers_text = st.text_area(
            "Enter numbers to remove (comma, space, or newline separated):",
            value=st.session_state.cleanup_input_numbers_text,
            height=150,
            key="cleanup_numbers_input_area_widget"
        )
        st.session_state.cleanup_scope_selection = st.radio(
            "Cleanup Scope:",
            options=["Mapping Gateway", "Routing Gateway", "Both"],
            index=["Mapping Gateway", "Routing Gateway", "Both"].index(st.session_state.cleanup_scope_selection),
            horizontal=True,
            key="cleanup_scope_radio_widget"
        )

        if st.button("Scan for Numbers", key="cleanup_scan_button_widget"):
            raw_numbers_input_str = st.session_state.cleanup_input_numbers_text
            if not raw_numbers_input_str.strip():
                display_status_message("Please enter numbers to scan.", "WARNING")
            else:
                original_numbers_to_scan = [n.strip() for n in re.split(r'[,\s\n]+', raw_numbers_input_str) if n.strip()]
                if not original_numbers_to_scan:
                    display_status_message("Number list is empty after processing input.", "WARNING")
                else:
                    # Generate all search variants for the input numbers
                    all_variants_for_cleanup_scan = set()
                    for num_original_scan in original_numbers_to_scan:
                        # Assuming generate_search_variants is imported from utils
                        all_variants_for_cleanup_scan.update(generate_search_variants(num_original_scan))
                    
                    if not all_variants_for_cleanup_scan:
                        display_status_message("Could not generate any search variants from the input numbers.", "WARNING")
                    else:
                        st.session_state.cleanup_variants_to_remove = all_variants_for_cleanup_scan # Store for later use in actual deletion
                        st.session_state.cleanup_scan_results_list = [] # Reset previous results
                        st.session_state.cleanup_items_for_editor = pd.DataFrame()
                        st.session_state.cleanup_execution_log_messages = []
                        
                        with st.spinner("Scanning all servers for specified numbers... This may take a while."):
                            active_servers_list_cleanup = st.session_state.get('vos_servers_list', config.VOS_SERVERS)
                            found_items_list_cleanup = []
                            
                            scan_mg = "MG" in st.session_state.cleanup_scope_selection or "Both" in st.session_state.cleanup_scope_selection
                            scan_rg = "RG" in st.session_state.cleanup_scope_selection or "Both" in st.session_state.cleanup_scope_selection

                            for server_info_cleanup in active_servers_list_cleanup:
                                s_url, s_name = server_info_cleanup["url"], server_info_cleanup["name"]
                                if scan_mg:
                                    # Use refactored identify_mg_for_cleanup which returns (list | None, error_msg | None)
                                    mg_items_found_list, err_mg_scan = identify_mg_for_cleanup_backend(s_url, s_name, all_variants_for_cleanup_scan)
                                    if err_mg_scan:
                                        display_status_message(f"Error scanning MGs on {s_name}: {err_mg_scan}", "ERROR")
                                    elif mg_items_found_list:
                                        found_items_list_cleanup.extend(mg_items_found_list)
                                if scan_rg:
                                    # Use refactored identify_rgs_for_cleanup
                                    rg_items_found_list, err_rg_scan = identify_rgs_for_cleanup_backend(s_url, s_name, all_variants_for_cleanup_scan)
                                    if err_rg_scan:
                                        display_status_message(f"Error scanning RGs on {s_name}: {err_rg_scan}", "ERROR")
                                    elif rg_items_found_list:
                                        found_items_list_cleanup.extend(rg_items_found_list)
                        
                        st.session_state.cleanup_scan_results_list = found_items_list_cleanup
                        if not found_items_list_cleanup:
                            display_status_message("No matching numbers found in any gateways based on the selected scope.", "INFO")
                            # Stay in input step or allow rescan
                        else:
                            display_status_message(f"Scan complete. Found {len(found_items_list_cleanup)} potential items for cleanup.", "SUCCESS")
                            st.session_state.cleanup_current_step = "show_results"
                        st.rerun()

    # --- Step 2: Display Scan Results and Allow Selection ---
    elif st.session_state.cleanup_current_step == "show_results":
        st.subheader("Step 2: Scan Results - Select Items for Number Removal")
        scan_results = st.session_state.get("cleanup_scan_results_list", [])

        if not scan_results:
            display_status_message("No items found in the scan. Please try different numbers or scope.", "INFO")
            if st.button("Back to Input Numbers", key="cleanup_back_to_input_btn_no_results"):
                st.session_state.cleanup_current_step = "input_numbers"
                st.rerun()
        else:
            # Prepare data for st.data_editor
            editor_data_list = []
            for idx, item_data in enumerate(scan_results):
                item_id = f"item_cleanup_{idx}" # Unique ID for the editor
                item_type_disp = item_data.get("type", "N/A")
                details_summary_list = []
                if item_type_disp == "MG":
                    details_summary_list.append(f"CalloutCaller: {', '.join(item_data.get('common_numbers_in_calloutCaller', []))}")
                elif item_type_disp == "RG":
                    if item_data.get("common_in_callin_caller"): details_summary_list.append(f"CallinCaller: {', '.join(item_data['common_in_callin_caller'])}")
                    if item_data.get("is_to_rg") and item_data.get("common_in_callin_callee"): details_summary_list.append(f"CallinCallee: {', '.join(item_data['common_in_callin_callee'])}")
                    if item_data.get("common_virtual_keys_to_delete"): details_summary_list.append(f"Delete VN Key(s): {', '.join(item_data['common_virtual_keys_to_delete'])}")
                    if item_data.get("common_real_values_to_delete_map"):
                        for vk_map_del, reals_map_del in item_data["common_real_values_to_delete_map"].items(): details_summary_list.append(f"In Key '{vk_map_del}' remove reals: [{', '.join(reals_map_del)}]")
                
                editor_data_list.append({
                    "ID_Cleanup": item_id,
                    "Select": False, # Default to not selected
                    "Type": item_type_disp,
                    "Server": item_data.get("server_name", "N/A"),
                    "Gateway Name": item_data.get("name", "N/A"),
                    "Numbers/Keys to be Removed": "; ".join(details_summary_list) if details_summary_list else "Review details"
                })
            
            # Initialize or update editor state
            if st.session_state.cleanup_items_for_editor.empty or list(st.session_state.cleanup_items_for_editor["ID_Cleanup"]) != [d["ID_Cleanup"] for d in editor_data_list]:
                 st.session_state.cleanup_items_for_editor = pd.DataFrame(editor_data_list)


            st.info("Review the items found. Check the 'Select' box for items you want to process for number removal.")
            
            col_sel_all_cleanup, col_desel_all_cleanup, _ = st.columns([1,1,3])
            with col_sel_all_cleanup:
                if st.button("Select All", key="cleanup_editor_select_all"):
                    if not st.session_state.cleanup_items_for_editor.empty:
                        st.session_state.cleanup_items_for_editor["Select"] = True
                        st.rerun()
            with col_desel_all_cleanup:
                if st.button(" Deselect All", key="cleanup_editor_deselect_all"):
                    if not st.session_state.cleanup_items_for_editor.empty:
                        st.session_state.cleanup_items_for_editor["Select"] = False
                        st.rerun()

            edited_df_cleanup = st.data_editor(
                st.session_state.cleanup_items_for_editor,
                use_container_width=True,
                hide_index=True,
                key="cleanup_data_editor_widget",
                column_config={
                    "ID_Cleanup": None, # Hide ID column
                    "Select": st.column_config.CheckboxColumn("Select", width="small", help="Select to include in cleanup operation"),
                    "Type": st.column_config.TextColumn("Type", width="small", disabled=True),
                    "Server": st.column_config.TextColumn("Server", width="medium", disabled=True),
                    "Gateway Name": st.column_config.TextColumn("Gateway Name", width="large", disabled=True),
                    "Numbers/Keys to be Removed": st.column_config.TextColumn("Summary of Numbers/Keys to be Removed", width="xlarge", disabled=True),
                },
                num_rows="fixed" 
            )
            st.session_state.cleanup_items_for_editor = edited_df_cleanup # Update session state with user's selections

            col_action_cleanup1, col_action_cleanup2 = st.columns(2)
            with col_action_cleanup1:
                if st.button("Proceed to Remove Selected Numbers", type="primary", key="cleanup_proceed_to_delete_btn"):
                    selected_items_df = edited_df_cleanup[edited_df_cleanup["Select"]]
                    if selected_items_df.empty:
                        display_status_message("Please select at least one item to proceed with cleanup.", "WARNING")
                    else:
                        # Map selected IDs back to raw data from scan_results
                        selected_ids_for_action = selected_items_df["ID_Cleanup"].tolist()
                        # We need to map these IDs back to the original full dicts stored in scan_results
                        # This requires scan_results to be structured in a way that items can be retrieved by an ID
                        # or by re-filtering scan_results. Simpler: store index or use a dict map for raw data.
                        
                        # For now, let's assume scan_results can be indexed or we find items by ID
                        # This part needs to be robust based on how scan_results is structured
                        final_items_for_action = []
                        for item_id_action in selected_ids_for_action:
                            # Find original item in scan_results based on item_id_action
                            # This assumes item_id_action was created like "mg_idx" or "rg_idx"
                            try:
                                original_item_index = int(item_id_action.split("_")[-1]) # Simplistic way to get index
                                if item_id_action.startswith("mg_") and original_item_index < len(st.session_state.cleanup_scan_results_list): # Simplified: check if item is from combined list
                                     retrieved_item = st.session_state.cleanup_scan_results_list[original_item_index] # This needs careful indexing if list is mixed
                                     # A better way is to have a map: item_id -> original_item_data
                                     # For now, we assume cleanup_scan_results_list matches the order that IDs were generated
                                     # This is a simplification and might need a more robust ID-to-data mapping
                                     is_match = False
                                     for res_item in scan_results: # Brute-force find by some unique properties if ID direct map is not good
                                         if res_item.get("type")+str(original_item_index) == item_id_action: # Placeholder matching
                                             final_items_for_action.append(res_item)
                                             is_match = True
                                             break
                                     # Fallback / Simplification: Get directly from scan_results using original index if IDs are just indices
                                     if not is_match and 0 <= original_item_index < len(scan_results) :
                                          final_items_for_action.append(scan_results[original_item_index])


                            except (ValueError, IndexError):
                                display_status_message(f"Error retrieving data for selected item ID {item_id_action}.", "ERROR")
                        
                        # A more robust way: use the full scan_results and filter by selected IDs from editor_data_list
                        final_items_for_action = []
                        original_scan_map = {f"item_cleanup_{i}": data for i, data in enumerate(scan_results)}
                        for selected_id_str in selected_ids_for_action:
                            if selected_id_str in original_scan_map:
                                final_items_for_action.append(original_scan_map[selected_id_str])


                        if not final_items_for_action:
                             display_status_message("Could not retrieve data for selected items. Please try re-scanning.", "ERROR")
                        else:
                            st.session_state.cleanup_items_to_execute = final_items_for_action
                            st.session_state.cleanup_current_step = "execute_cleanup"
                            st.rerun()
            with col_action_cleanup2:
                if st.button("Back to Input Numbers", key="cleanup_back_to_input_btn_results_page"):
                    st.session_state.cleanup_current_step = "input_numbers"; st.rerun()
    
    # --- Step 3: Execute Cleanup ---
    elif st.session_state.cleanup_current_step == "execute_cleanup":
        st.subheader("Step 3: Executing Cleanup Operation")
        items_to_execute_on = st.session_state.get("cleanup_items_to_execute", [])
        variants_to_remove_exec = st.session_state.get("cleanup_variants_to_remove", set())
        st.session_state.cleanup_execution_log_messages = [] # Clear previous logs

        if not items_to_execute_on:
            display_status_message("No items selected for cleanup execution.", "WARNING")
            st.session_state.cleanup_current_step = "show_results"; st.rerun()
        else:
            st.session_state.cleanup_execution_log_messages.append(f"Starting cleanup for {len(items_to_execute_on)} selected item(s)...")
            st.session_state.cleanup_execution_log_messages.append(f"Target numbers/variants for removal: {', '.join(list(variants_to_remove_exec)[:5])}{'...' if len(variants_to_remove_exec)>5 else ''}")

            with st.spinner(f"Removing numbers from {len(items_to_execute_on)} gateways... This may take time."):
                for item_exec_data in items_to_execute_on:
                    server_url_exec = item_exec_data["server_url"]
                    server_name_exec = item_exec_data["server_name"]
                    gw_name_exec = item_exec_data["name"]
                    item_type_exec = item_exec_data["type"]
                    log_prefix = f"[{item_type_exec}] {gw_name_exec} ({server_name_exec}): "
                    
                    raw_gw_info_exec = item_exec_data.get("raw_rg_info") if item_type_exec == "RG" else item_exec_data.get("raw_mg_info")
                    if not raw_gw_info_exec:
                        st.session_state.cleanup_execution_log_messages.append(log_prefix + "ERROR: Missing raw gateway info. Skipping.")
                        continue
                    
                    payload_update_exec = raw_gw_info_exec.copy() # Work on a copy
                    changed_in_gw = False

                    if item_type_exec == "MG":
                        numbers_to_remove_mg_item = item_exec_data.get("common_numbers_in_calloutCaller", [])
                        if numbers_to_remove_mg_item:
                            original_prefixes_mg = [p.strip() for p in raw_gw_info_exec.get("calloutCallerPrefixes", "").split(',') if p.strip()]
                            new_prefixes_mg = [p for p in original_prefixes_mg if p not in numbers_to_remove_mg_item]
                            if len(new_prefixes_mg) != len(original_prefixes_mg):
                                payload_update_exec["calloutCallerPrefixes"] = ",".join(new_prefixes_mg)
                                if len(new_prefixes_mg) == 0 and not payload_update_exec.get("calloutCalleePrefixes"): payload_update_exec["lockType"] = 3
                                elif len(new_prefixes_mg) <=1 : payload_update_exec["lockType"] = payload_update_exec.get("lockType",3)

                                success_apply_mg, msg_apply_mg = apply_mg_update_for_cleanup_backend(server_url_exec, server_name_exec, gw_name_exec, payload_update_exec)
                                if success_apply_mg: st.session_state.cleanup_execution_log_messages.append(log_prefix + f"SUCCESS - Removed {len(numbers_to_remove_mg_item)} number(s) from CalloutCallerPrefixes. {msg_apply_mg}")
                                else: st.session_state.cleanup_execution_log_messages.append(log_prefix + f"ERROR - Failed to remove numbers from CalloutCallerPrefixes: {msg_apply_mg}")
                            else: st.session_state.cleanup_execution_log_messages.append(log_prefix + "No changes needed for CalloutCallerPrefixes.")
                        else: st.session_state.cleanup_execution_log_messages.append(log_prefix + "No common numbers identified in CalloutCallerPrefixes to remove.")

                    elif item_type_exec == "RG":
                        # Caller Prefixes
                        caller_to_remove = item_exec_data.get("common_in_callin_caller", [])
                        if caller_to_remove:
                            original_caller = [p.strip() for p in raw_gw_info_exec.get("callinCallerPrefixes", "").split(',') if p.strip()]
                            new_caller = [p for p in original_caller if p not in caller_to_remove]
                            if len(new_caller) != len(original_caller): payload_update_exec["callinCallerPrefixes"] = ",".join(new_caller); changed_in_gw = True
                        
                        # Callee Prefixes (if TO RG)
                        if item_exec_data.get("is_to_rg"):
                            callee_to_remove = item_exec_data.get("common_in_callin_callee", [])
                            if callee_to_remove:
                                original_callee = [p.strip() for p in raw_gw_info_exec.get("callinCalleePrefixes", "").split(',') if p.strip()]
                                new_callee = [p for p in original_callee if p not in callee_to_remove]
                                if len(new_callee) != len(original_callee): payload_update_exec["callinCalleePrefixes"] = ",".join(new_callee); changed_in_gw = True

                        # Rewrite Rules
                        current_rules_parsed = item_exec_data.get("original_rewrite_parsed", {})
                        new_rules_parsed = {k: list(v) for k, v in current_rules_parsed.items()} # Deep copy
                        
                        vkeys_to_delete = item_exec_data.get("common_virtual_keys_to_delete", [])
                        for vk_del in vkeys_to_delete:
                            if vk_del in new_rules_parsed: del new_rules_parsed[vk_del]; changed_in_gw = True
                        
                        reals_map_to_delete = item_exec_data.get("common_real_values_to_delete_map", {})
                        for vk_map, reals_val_map_del in reals_map_to_delete.items():
                            if vk_map in new_rules_parsed:
                                original_reals_in_key = list(new_rules_parsed[vk_map])
                                temp_new_reals_for_key = [r for r in original_reals_in_key if r not in reals_val_map_del]
                                if len(temp_new_reals_for_key) != len(original_reals_in_key):
                                    new_rules_parsed[vk_map] = temp_new_reals_for_key; changed_in_gw = True
                                if is_six_digit_virtual_number_candidate(vk_map) and not new_rules_parsed.get(vk_map):
                                    new_rules_parsed[vk_map] = ["hetso"]; changed_in_gw = True 
                        
                        if changed_in_gw: # Only update if any part of RG was modified
                            payload_update_exec["rewriteRulesInCaller"] = format_rewrite_rules_for_vos(new_rules_parsed)
                            # Simplified lockType logic
                            if not any(new_rules_parsed.values()) and not payload_update_exec.get("callinCallerPrefixes") and not payload_update_exec.get("callinCalleePrefixes"):
                                payload_update_exec["lockType"] = 3
                            
                            success_apply_rg, msg_apply_rg = apply_rg_update_for_cleanup_backend(server_url_exec, server_name_exec, gw_name_exec, payload_update_exec)
                            if success_apply_rg: st.session_state.cleanup_execution_log_messages.append(log_prefix + f"SUCCESS - RG updated. {msg_apply_rg}")
                            else: st.session_state.cleanup_execution_log_messages.append(log_prefix + f"ERROR - Failed to update RG: {msg_apply_rg}")
                        else:
                            st.session_state.cleanup_execution_log_messages.append(log_prefix + "No changes needed for this RG.")
                
            st.session_state.cleanup_execution_log_messages.append("--- Cleanup process finished ---")
            st.session_state.cleanup_current_step = "show_log"
            st.rerun()

    # --- Step 4: Display Execution Log ---
    elif st.session_state.cleanup_current_step == "show_log":
        st.subheader("Step 4: Cleanup Execution Log")
        log_messages_cleanup_done = st.session_state.get("cleanup_execution_log_messages", [])
        if log_messages_cleanup_done:
            st.text_area("Execution Log:", value="\n".join(log_messages_cleanup_done), height=400, disabled=True, key="cleanup_final_log_display_widget")
        else:
            display_status_message("No execution log available.", "INFO")
        
        if st.button("Perform Another Cleanup Operation", key="cleanup_start_new_op_btn_final"):
            st.session_state.cleanup_current_step = "input_numbers"
            st.session_state.cleanup_input_numbers_text = "" # Reset input
            st.session_state.cleanup_scan_results_list = []
            st.session_state.cleanup_items_for_editor = pd.DataFrame()
            st.session_state.cleanup_execution_log_messages = []
            st.rerun()

elif current_page_key == "CustomerManagement": # Using the English internal key
    st.header("Customer Management Across All Servers")

    # --- Session State Initialization for Customer Management Page ---
    if 'customer_search_type_label_global' not in st.session_state:
        st.session_state.customer_search_type_label_global = "By Account ID"
    if 'customer_filter_text_global' not in st.session_state:
        st.session_state.customer_filter_text_global = ""
    if 'customer_search_results_global_list' not in st.session_state: # Stores list of dicts from backend
        st.session_state.customer_search_results_global_list = []
    if 'customer_selected_for_details_global' not in st.session_state: # Stores the full dict of the selected customer
        st.session_state.customer_selected_for_details_global = None
    if 'customer_current_details_display_global' not in st.session_state: # Stores {'raw':..., 'display_list':...}
        st.session_state.customer_current_details_display_global = None
    if 'customer_operation_choice_global' not in st.session_state:
        st.session_state.customer_operation_choice_global = None # e.g., "SET_LIMIT", "TOGGLE_LOCK"

    # --- Search Interface ---
    search_options_customer_map = {
        "By Account ID": "account_id",
        "By Customer Name": "account_name",
    }
    st.session_state.customer_search_type_label_global = st.radio(
        "Search by:", # Translated
        options=list(search_options_customer_map.keys()),
        index=list(search_options_customer_map.keys()).index(st.session_state.customer_search_type_label_global),
        horizontal=True,
        key="customer_global_search_type_radio"
    )
    selected_filter_type_customer = search_options_customer_map[st.session_state.customer_search_type_label_global]

    st.session_state.customer_filter_text_global = st.text_input(
        f"Enter {st.session_state.customer_search_type_label_global.split('By ')[-1].lower()}:", # Dynamic prompt
        value=st.session_state.customer_filter_text_global,
        key="customer_global_filter_text_input"
    ).strip()

    if st.button("Search Customers", key="customer_global_search_button"):
        st.session_state.customer_selected_for_details_global = None
        st.session_state.customer_current_details_display_global = None
        st.session_state.customer_operation_choice_global = None
        
        current_filter_text_customer = st.session_state.customer_filter_text_global
        if not current_filter_text_customer:
            display_status_message("Please enter search criteria.", "WARNING")
            st.session_state.customer_search_results_global_list = []
        else:
            with st.spinner("Searching for customers across all servers..."):
                # Use refactored backend function
                # find_customers_across_all_servers expects filter_type and filter_text
                # It now returns a list of dicts with English keys and raw numbers for Balance/Limit
                results_customer_list = find_customers_across_all_servers(
                    filter_type=selected_filter_type_customer,
                    filter_text=current_filter_text_customer
                )
            st.session_state.customer_search_results_global_list = results_customer_list
            if not results_customer_list:
                display_status_message("No customers found matching your criteria.", "INFO")
            else:
                display_status_message(f"Found {len(results_customer_list)} customer(s). Click a row to view details and actions.", "SUCCESS")
        st.rerun()

    # --- Display Search Results in a Selectable DataFrame ---
    customer_results_df_key = "customer_search_results_df_global"
    customer_list_for_display = st.session_state.get("customer_search_results_global_list", [])

    if customer_list_for_display:
        st.markdown("##### Search Results (click a row to select):")
        
        df_customer_data_display = []
        for cust_item in customer_list_for_display:
            df_customer_data_display.append({
                "Account ID": cust_item.get('AccountID', 'N/A'),
                "Customer Name": cust_item.get('CustomerName', 'N/A'),
                "Balance": format_amount_vietnamese_style(cust_item.get('BalanceRaw', 0.0)),
                "Credit Limit": format_amount_vietnamese_style(cust_item.get('CreditLimitRaw', 0.0)),
                "Status": cust_item.get('Status', 'N/A'),
                "Server": cust_item.get('ServerName', 'N/A')
            })
        
        
        df_customer_display_final = pd.DataFrame(df_customer_data_display)

        if not df_customer_display_final.empty:
            st.dataframe(
                df_customer_display_final,
                use_container_width=True, 
                hide_index=True,
                key=customer_results_df_key, # Key này quan trọng để nhắm mục tiêu nếu cần CSS phức tạp hơn
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Account ID": st.column_config.TextColumn("Account ID", width="medium"),
                    "Customer Name": st.column_config.TextColumn("Customer Name", width="large"),
                    "Balance": st.column_config.TextColumn("Balance", width="medium"),
                    "Credit Limit": st.column_config.TextColumn("Credit Limit", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Server": st.column_config.TextColumn("Server", width="medium"),
                }
            )

            # Handle selection from DataFrame
            if customer_results_df_key in st.session_state and \
               st.session_state[customer_results_df_key].selection and \
               st.session_state[customer_results_df_key].selection.get("rows"):
                
                selected_cust_idx = st.session_state[customer_results_df_key].selection["rows"][0]
                if 0 <= selected_cust_idx < len(customer_list_for_display): # Use original list for full data
                    newly_selected_customer_full_data = customer_list_for_display[selected_cust_idx]
                    if st.session_state.get('customer_selected_for_details_global') != newly_selected_customer_full_data:
                        st.session_state.customer_selected_for_details_global = newly_selected_customer_full_data
                        st.session_state.customer_current_details_display_global = None # Clear old details
                        st.session_state.customer_operation_choice_global = None # Reset operation
                        # No immediate rerun here, let the detail display section handle it or trigger it.
            elif customer_results_df_key in st.session_state and \
                 st.session_state[customer_results_df_key].selection and \
                 not st.session_state[customer_results_df_key].selection.get("rows") and \
                 st.session_state.get('customer_selected_for_details_global') is not None: # Deselection
                st.session_state.customer_selected_for_details_global = None
                st.session_state.customer_current_details_display_global = None
                st.session_state.customer_operation_choice_global = None

    # --- Customer Detail View and Operations Section ---
    selected_customer_data_global = st.session_state.get("customer_selected_for_details_global")

    if selected_customer_data_global:
        st.divider()
        selected_account_id = selected_customer_data_global.get('AccountID', 'N/A')
        selected_server_name = selected_customer_data_global.get('ServerName', 'N/A')
        selected_server_url = selected_customer_data_global.get('_server_url') # Key from backend

        st.subheader(f"Details & Actions for Customer:")
        st.subheader(f" {selected_account_id} (Server: {selected_server_name})")
        customer_detail_col, customer_action_col = st.columns([3, 2])

        with customer_detail_col:
            st.markdown("###### Customer Information")
            # Fetch and display details if not already fetched or selection changed
            if st.session_state.get("customer_current_details_display_global") is None:
                if selected_server_url and selected_account_id != 'N/A':
                    with st.spinner(f"Loading details for customer {selected_account_id}..."):
                        # Use refactored backend function
                        raw_detail_data, display_list_data, error_msg_cust_detail = get_customer_details_for_display(
                            base_url=selected_server_url,
                            server_name=selected_server_name, 
                            customer_account=selected_account_id
                        )
                        if error_msg_cust_detail:
                            display_status_message(f"Error loading customer details: {error_msg_cust_detail}", "ERROR", server_name=selected_server_name)
                            st.session_state.customer_current_details_display_global = {"raw": None, "display_list": None, "error": error_msg_cust_detail}
                        elif display_list_data is not None:
                             st.session_state.customer_current_details_display_global = {"raw": raw_detail_data, "display_list": display_list_data, "error": None}
                        else: # Should not happen if error_msg is None
                             st.session_state.customer_current_details_display_global = {"raw": None, "display_list": None, "error": "Unknown error fetching details."}

            current_customer_display_info = st.session_state.get("customer_current_details_display_global")
            if current_customer_display_info and current_customer_display_info.get("display_list"):
                df_cust_details = pd.DataFrame(current_customer_display_info["display_list"])
                st.table(df_cust_details.set_index("field")) # field and value are from get_customer_details_for_display
            elif current_customer_display_info and current_customer_display_info.get("error"):
                # Error already displayed by the fetch logic using display_status_message
                pass
            else:
                st.info("Select a customer from the search results to view details.")

        with customer_action_col:
            st.markdown("###### Available Actions")
            raw_customer_data_for_action = current_customer_display_info.get("raw") if current_customer_display_info else None

            if raw_customer_data_for_action and selected_server_url:
                op_unique_suffix_cust = f"_cust_global_{selected_account_id.replace('.','_')}_{selected_server_name.replace(' ','_')}"
                
                action_cols = st.columns(2)
                with action_cols[0]:
                    if st.button("Set Credit Limit", key=f"cust_set_limit_btn{op_unique_suffix_cust}", use_container_width=True):
                        st.session_state.customer_operation_choice_global = "SET_LIMIT"; st.rerun()
                    if st.button("Add to Credit Limit", key=f"cust_add_limit_btn{op_unique_suffix_cust}", use_container_width=True):
                        st.session_state.customer_operation_choice_global = "ADD_LIMIT"; st.rerun()
                with action_cols[1]:
                    if st.button("Subtract from Credit Limit", key=f"cust_sub_limit_btn{op_unique_suffix_cust}", use_container_width=True):
                        st.session_state.customer_operation_choice_global = "SUB_LIMIT"; st.rerun()
                    current_lock_status = str(raw_customer_data_for_action.get('lockType', "0"))
                    toggle_button_label = "Unlock Account" if current_lock_status == "1" else "Lock Account"
                    if st.button(toggle_button_label, key=f"cust_lock_btn{op_unique_suffix_cust}", use_container_width=True):
                        st.session_state.customer_operation_choice_global = "TOGGLE_LOCK"; st.rerun()
                
                st.markdown("---")
                chosen_customer_op = st.session_state.get("customer_operation_choice_global")

                if chosen_customer_op == "SET_LIMIT":
                    st.subheader("Set Absolute Credit Limit")
                    with st.form(key=f"form_set_limit_cust{op_unique_suffix_cust}"):
                        # Get current limit for display (optional, but good UX)
                        current_limit_val_set, err_get_limit = get_current_customer_limit_money(selected_server_url, selected_account_id, selected_server_name)
                        if err_get_limit: st.caption(f"Current limit: Error ({err_get_limit})")
                        else: st.caption(f"Current limit: {current_limit_val_set if isinstance(current_limit_val_set, str) else format_amount_vietnamese_style(current_limit_val_set)}")
                        
                        new_limit_input_set = st.text_input("New Credit Limit (-1 for unlimited):", key=f"input_set_limit_cust{op_unique_suffix_cust}")
                        submitted_set_limit = st.form_submit_button("Update Credit Limit")
                        if submitted_set_limit:
                            if not new_limit_input_set.strip(): display_status_message("Please enter a value.", "WARNING")
                            else:
                                try:
                                    if new_limit_input_set != "-1": float(new_limit_input_set) # Validate if not unlimited
                                    success_set_op, msg_set_op = update_customer_credit_limit(selected_server_url, selected_account_id, new_limit_input_set)
                                    if success_set_op:
                                        display_status_message(msg_set_op or "Credit limit set successfully!", "SUCCESS")
                                        st.session_state.customer_current_details_display_global = None # Force refresh details
                                        st.session_state.customer_operation_choice_global = None; st.rerun()
                                    else: display_status_message(msg_set_op or "Failed to set credit limit.", "ERROR")
                                except ValueError: display_status_message("Invalid credit limit value.", "ERROR")
                
                # (Tương tự, thêm form và logic cho ADD_LIMIT, SUB_LIMIT)
                # ...
                # Ví dụ cho ADD_LIMIT:
                elif chosen_customer_op == "ADD_LIMIT":
                    st.subheader("Add to Credit Limit")
                    with st.form(key=f"form_add_limit_cust{op_unique_suffix_cust}"):
                        current_limit_val_add, err_get_limit_add = get_current_customer_limit_money(selected_server_url, selected_account_id, selected_server_name)
                        can_proceed_add = False
                        if err_get_limit_add: st.caption(f"Current limit: Error ({err_get_limit_add})")
                        elif current_limit_val_add == "Unlimited": st.warning("Cannot add to an unlimited credit limit.")
                        elif current_limit_val_add is not None:
                            st.caption(f"Current limit: {format_amount_vietnamese_style(current_limit_val_add)}")
                            try: float(current_limit_val_add); can_proceed_add = True
                            except ValueError: st.error("Current credit limit is not a valid number.")
                        
                        amount_to_add_input = st.number_input("Amount to add:", min_value=0.01, format="%.2f", key=f"input_add_amount_cust{op_unique_suffix_cust}", disabled=not can_proceed_add)
                        submitted_add_limit = st.form_submit_button("Confirm Add", disabled=not can_proceed_add)
                        if submitted_add_limit and can_proceed_add:
                            new_total_limit_add = float(current_limit_val_add) + amount_to_add_input
                            success_add_op, msg_add_op = update_customer_credit_limit(selected_server_url, selected_account_id, str(new_total_limit_add))
                            if success_add_op:
                                display_status_message(msg_add_op or "Credit limit increased successfully!", "SUCCESS")
                                st.session_state.customer_current_details_display_global = None; st.session_state.customer_operation_choice_global = None; st.rerun()
                            else: display_status_message(msg_add_op or "Failed to increase credit limit.", "ERROR")

                # Ví dụ cho SUB_LIMIT:
                elif chosen_customer_op == "SUB_LIMIT":
                    st.subheader("Subtract from Credit Limit")
                    with st.form(key=f"form_sub_limit_cust{op_unique_suffix_cust}"):
                        current_limit_val_sub, err_get_limit_sub = get_current_customer_limit_money(selected_server_url, selected_account_id, selected_server_name)
                        can_proceed_sub = False
                        if err_get_limit_sub: st.caption(f"Current limit: Error ({err_get_limit_sub})")
                        elif current_limit_val_sub == "Unlimited": st.warning("Cannot subtract from an unlimited credit limit.")
                        elif current_limit_val_sub is not None:
                            st.caption(f"Current limit: {format_amount_vietnamese_style(current_limit_val_sub)}")
                            try: float(current_limit_val_sub); can_proceed_sub = True
                            except ValueError: st.error("Current credit limit is not a valid number.")
                        
                        amount_to_sub_input = st.number_input("Amount to subtract:", min_value=0.01, format="%.2f", key=f"input_sub_amount_cust{op_unique_suffix_cust}", disabled=not can_proceed_sub)
                        submitted_sub_limit = st.form_submit_button("Confirm Subtract", disabled=not can_proceed_sub)
                        if submitted_sub_limit and can_proceed_sub:
                            new_total_limit_sub = float(current_limit_val_sub) - amount_to_sub_input
                            if new_total_limit_sub < 0: display_status_message("New credit limit cannot be negative after subtraction.", "ERROR")
                            else:
                                success_sub_op, msg_sub_op = update_customer_credit_limit(selected_server_url, selected_account_id, str(new_total_limit_sub))
                                if success_sub_op:
                                    display_status_message(msg_sub_op or "Credit limit decreased successfully!", "SUCCESS")
                                    st.session_state.customer_current_details_display_global = None; st.session_state.customer_operation_choice_global = None; st.rerun()
                                else: display_status_message(msg_sub_op or "Failed to decrease credit limit.", "ERROR")


                elif chosen_customer_op == "TOGGLE_LOCK":
                    st.subheader(f"{toggle_button_label}") # Label from button
                    new_lock_status_val = "0" if current_lock_status == "1" else "1" # Toggle
                    if st.button(f"Confirm {toggle_button_label}", key=f"confirm_toggle_lock_btn{op_unique_suffix_cust}", type="primary"):
                        success_lock_op, msg_lock_op = update_customer_lock_status(selected_server_url, selected_account_id, new_lock_status_val)
                        if success_lock_op:
                            display_status_message(msg_lock_op or "Account lock status updated successfully!", "SUCCESS")
                            st.session_state.customer_current_details_display_global = None # Force refresh details
                            st.session_state.customer_operation_choice_global = None; st.rerun()
                        else: display_status_message(msg_lock_op or "Failed to update account lock status.", "ERROR")
            else:
                st.caption("Select a customer and load details to perform actions.")

elif current_page_key == "VirtualNumberManagement":
    st.header(" Virtual Number & Rewrite Rule Management")

    if 'qvn_step' not in st.session_state: st.session_state.qvn_step = "1_input_target_vn"
    if 'qvn_target_vn_input' not in st.session_state: st.session_state.qvn_target_vn_input = ""
    if 'qvn_target_vn_definitions_found' not in st.session_state: st.session_state.qvn_target_vn_definitions_found = []
    if 'qvn_selected_target_definition_idx' not in st.session_state: st.session_state.qvn_selected_target_definition_idx = None
    if 'qvn_selected_target_definition_obj' not in st.session_state: st.session_state.qvn_selected_target_definition_obj = None
    if 'qvn_main_action_choice' not in st.session_state: st.session_state.qvn_main_action_choice = None
    if 'qvn_source_type' not in st.session_state: st.session_state.qvn_source_type = None
    if 'qvn_auto_backup_key_in_target' not in st.session_state: st.session_state.qvn_auto_backup_key_in_target = None
    if 'qvn_auto_backup_reals_in_target' not in st.session_state: st.session_state.qvn_auto_backup_reals_in_target = []
    if 'qvn_manual_source_search_input' not in st.session_state: st.session_state.qvn_manual_source_search_input = ""
    if 'qvn_manual_source_keys_found' not in st.session_state: st.session_state.qvn_manual_source_keys_found = []
    if 'qvn_selected_manual_source_idx' not in st.session_state: st.session_state.qvn_selected_manual_source_idx = None
    if 'qvn_selected_manual_source_obj' not in st.session_state: st.session_state.qvn_selected_manual_source_obj = None
    if 'qvn_source_reals_to_use_original' not in st.session_state: st.session_state.qvn_source_reals_to_use_original = []
    if 'qvn_num_to_take_from_source' not in st.session_state: st.session_state.qvn_num_to_take_from_source = 0
    if 'qvn_final_numbers_for_target_vn' not in st.session_state: st.session_state.qvn_final_numbers_for_target_vn = []
    if 'qvn_remaining_reals_in_source_key' not in st.session_state: st.session_state.qvn_remaining_reals_in_source_key = []
    if 'qvn_target_vn_action_on_reals' not in st.session_state: st.session_state.qvn_target_vn_action_on_reals = None
    if 'qvn_empty_source_key_action' not in st.session_state: st.session_state.qvn_empty_source_key_action = None
    if 'qvn_execution_log' not in st.session_state: st.session_state.qvn_execution_log = []
    if 'qvn_exec_status_target' not in st.session_state: st.session_state.qvn_exec_status_target = False
    if 'qvn_exec_status_source' not in st.session_state: st.session_state.qvn_exec_status_source = True

    def reset_qvn_states_full_flow_function_final_vnm():
        keys_to_reset_qvn_list_final_vnm = [k_qvn_final_vnm for k_qvn_final_vnm in st.session_state if k_qvn_final_vnm.startswith('qvn_')]
        for key_to_reset_qvn_final_vnm in keys_to_reset_qvn_list_final_vnm:
            del st.session_state[key_to_reset_qvn_final_vnm]
        st.session_state.qvn_step = "1_input_target_vn"
        st.rerun()


    if st.session_state.qvn_step == "1_input_target_vn":
        st.subheader("Step 1: Input Target Virtual Number Key")
        st.session_state.qvn_target_vn_input = st.text_input(
            "Enter the Target Virtual Number key to manage (e.g., 500555):",
            value=st.session_state.qvn_target_vn_input,
            key="qvn_target_vn_input_widget_s1_vnm"
        )
        if st.button(" Search Target Virtual Number", key="qvn_find_target_vn_button_s1_vnm"):
            if not st.session_state.qvn_target_vn_input.strip():
                display_status_message("Please enter a Target Virtual Number key.", "WARNING")
            else:
                target_key_search_s1_vnm = st.session_state.qvn_target_vn_input.strip()
                with st.spinner(f"Searching for definitions of Target VN '{target_key_search_s1_vnm}'..."):
                    definitions_found_s1_vnm, err_find_vn_s1_vnm = find_specific_virtual_number_definitions_backend(target_key_search_s1_vnm)
                
                if err_find_vn_s1_vnm:
                    display_status_message(f"Error finding Target VN: {err_find_vn_s1_vnm}", "ERROR")
                    st.session_state.qvn_target_vn_definitions_found = []
                elif definitions_found_s1_vnm is None :
                    display_status_message(f"Failed to search for Target VN '{target_key_search_s1_vnm}' (no data returned).", "ERROR")
                    st.session_state.qvn_target_vn_definitions_found = []
                elif not definitions_found_s1_vnm:
                    display_status_message(f"No definitions found for Target VN '{target_key_search_s1_vnm}'. Please try again or enter a different key.", "ERROR")
                    st.session_state.qvn_target_vn_definitions_found = []
                elif len(definitions_found_s1_vnm) == 1:
                    st.session_state.qvn_target_vn_definitions_found = definitions_found_s1_vnm
                    st.session_state.qvn_selected_target_definition_obj = definitions_found_s1_vnm[0]
                    st.session_state.qvn_selected_target_definition_idx = 0
                    display_status_message(f"Found 1 definition for '{definitions_found_s1_vnm[0]['virtual_key']}' on Server: {definitions_found_s1_vnm[0]['server_name']}, RG: {definitions_found_s1_vnm[0]['rg_name']}.", "SUCCESS")
                    st.session_state.qvn_step = "3_select_main_action"
                    st.rerun()
                else:
                    st.session_state.qvn_target_vn_definitions_found = definitions_found_s1_vnm
                    display_status_message(f"Found {len(definitions_found_s1_vnm)} definitions for '{target_key_search_s1_vnm}'. Please select one to proceed.", "INFO")
                    st.session_state.qvn_step = "2_select_target_definition"
                    st.rerun()
        
        if st.button("Reset Flow", key="qvn_reset_step1_button_s1_action_vnm", type="secondary"):
            reset_qvn_states_full_flow_function_final_vnm()

    elif st.session_state.qvn_step == "2_select_target_definition":
        st.subheader("Step 2: Select Specific Definition for Target Virtual Number")
        target_definitions_list_s2_vnm = st.session_state.get('qvn_target_vn_definitions_found', [])
        if not target_definitions_list_s2_vnm:
            display_status_message("Error: No definitions to select. Returning to input.", "ERROR")
            st.session_state.qvn_step = "1_input_target_vn"; st.rerun()
        else:
            target_vn_key_disp_s2_vnm = st.session_state.get('qvn_target_vn_input', 'N/A')
            options_target_def_map_s2_vnm = {
                i_s2_vnm: f"Server: {d_s2_vnm['server_name']}, RG: {d_s2_vnm['rg_name']} (Reals: {'hetso' if d_s2_vnm['is_hetso'] else d_s2_vnm.get('real_numbers_count',0)} num(s))"
                for i_s2_vnm, d_s2_vnm in enumerate(target_definitions_list_s2_vnm)
            }
            default_idx_target_s2_vnm = st.session_state.get('qvn_selected_target_definition_idx', 0)
            if not (isinstance(default_idx_target_s2_vnm, int) and 0 <= default_idx_target_s2_vnm < len(options_target_def_map_s2_vnm)):
                default_idx_target_s2_vnm = 0
            
            selected_idx_target_def_s2_vnm = st.radio(
                f"Multiple definitions found for Target VN '{target_vn_key_disp_s2_vnm}'. Please choose one:",
                options=list(options_target_def_map_s2_vnm.keys()),
                format_func=lambda x_idx_s2_vnm: options_target_def_map_s2_vnm[x_idx_s2_vnm],
                index=default_idx_target_s2_vnm,
                key="qvn_select_target_def_radio_main_widget_s2_vnm"
            )
            st.session_state.qvn_selected_target_definition_idx = selected_idx_target_def_s2_vnm

            if st.button("Confirm This Target Definition", key="qvn_confirm_target_def_button_s2_vnm"):
                st.session_state.qvn_selected_target_definition_obj = target_definitions_list_s2_vnm[selected_idx_target_def_s2_vnm]
                sel_def_obj_disp_s2_vnm = st.session_state.qvn_selected_target_definition_obj
                display_status_message(f"Target VN selected: '{sel_def_obj_disp_s2_vnm['virtual_key']}' on Server: {sel_def_obj_disp_s2_vnm['server_name']}, RG: {sel_def_obj_disp_s2_vnm['rg_name']}.", "INFO")
                st.session_state.qvn_step = "3_select_main_action"
                st.rerun()
            
            if st.button("Back to Search Target VN", key="qvn_back_to_step1_button_s2_vnm", type="secondary"):
                st.session_state.qvn_target_vn_definitions_found = []
                st.session_state.qvn_selected_target_definition_idx = None
                st.session_state.qvn_selected_target_definition_obj = None
                st.session_state.qvn_step = "1_input_target_vn"; st.rerun()
    
    elif st.session_state.qvn_step == "3_select_main_action":
        st.subheader("Step 3: Select Main Action for Target Virtual Number")
        selected_target_def_s3_vnm = st.session_state.get('qvn_selected_target_definition_obj')
        if not selected_target_def_s3_vnm:
            display_status_message("Error: Target VN definition not selected. Please start over.", "ERROR")
            reset_qvn_states_full_flow_function_final_vnm(); st.stop()

        st.markdown(f"**Operating on Target VN:** `{selected_target_def_s3_vnm['virtual_key']}`")
        st.markdown(f"**Server:** `{selected_target_def_s3_vnm['server_name']}`, **RG:** `{selected_target_def_s3_vnm['rg_name']}`")
        current_reals_disp_s3_vnm = "hetso" if selected_target_def_s3_vnm['is_hetso'] else \
                                      (f"{selected_target_def_s3_vnm.get('real_numbers_count',0)} number(s): {'; '.join(selected_target_def_s3_vnm.get('reals',[])[:3])}{'...' if selected_target_def_s3_vnm.get('real_numbers_count',0) > 3 else ''}" 
                                       if selected_target_def_s3_vnm.get('reals') else "(Empty)")
        st.markdown(f"**Current Real Numbers:** `{current_reals_disp_s3_vnm}`")
        
        action_options_qvn_s3_vnm = {
            "instruct_edit_reals": "1. Edit Real Numbers (Note: Please use 'Configure Server' > 'Routing Gateway' tab for detailed editing)",
            "replace_from_other_source": "2. Replace/Get Real Numbers from another Source (Backup/Different Key)"
        }
        default_action_key_qvn_s3_vnm = st.session_state.get('qvn_main_action_choice', "replace_from_other_source")
        if default_action_key_qvn_s3_vnm == "edit_reals_directly": default_action_key_qvn_s3_vnm = "instruct_edit_reals" # Map old state if exists

        chosen_main_action_key_s3_vnm = st.radio(
            "What action would you like to perform?",
            options=list(action_options_qvn_s3_vnm.keys()),
            format_func=lambda x_key_s3_vnm: action_options_qvn_s3_vnm[x_key_s3_vnm],
            index=list(action_options_qvn_s3_vnm.keys()).index(default_action_key_qvn_s3_vnm) if default_action_key_qvn_s3_vnm in action_options_qvn_s3_vnm else 0,
            key="qvn_main_action_radio_widget_s3_vnm"
        )
        st.session_state.qvn_main_action_choice = chosen_main_action_key_s3_vnm

        if chosen_main_action_key_s3_vnm == "instruct_edit_reals":
             st.info(f"To directly edit Rewrite Rules for RG '{selected_target_def_s3_vnm['rg_name']}' on server '{selected_target_def_s3_vnm['server_name']}', please navigate to the 'Configure Server' page, select the appropriate server and Routing Gateway, then use the 'Manage Rewrite Rules' option there. This 'Virtual Number Management' page is now focused on replacing numbers from a source.")

        if st.button("Proceed", key="qvn_confirm_main_action_button_s3_vnm"):
            if chosen_main_action_key_s3_vnm == "replace_from_other_source":
                target_rg_info_s3_vnm_val = selected_target_def_s3_vnm.get('raw_rg_info', {})
                target_vn_s3_vnm_val = selected_target_def_s3_vnm['virtual_key']
                rules_in_target_rg_s3_vnm_val = parse_vos_rewrite_rules(target_rg_info_s3_vnm_val.get("rewriteRulesInCaller", ""))
                
                auto_backup_found_key_s3_vnm_val = None
                auto_backup_found_reals_s3_vnm_val = []
                for suffix_bk_s3_vnm_val in ["bk", "BK", "_bk", "-bk", "backup", "_backup", "-backup"]:
                    potential_key_bk_s3_vnm_val = f"{target_vn_s3_vnm_val}{suffix_bk_s3_vnm_val}"
                    if potential_key_bk_s3_vnm_val in rules_in_target_rg_s3_vnm_val:
                        auto_backup_found_key_s3_vnm_val = potential_key_bk_s3_vnm_val
                        auto_backup_found_reals_s3_vnm_val = rules_in_target_rg_s3_vnm_val[auto_backup_found_key_s3_vnm_val]
                        break
                st.session_state.qvn_auto_backup_key_in_target = auto_backup_found_key_s3_vnm_val
                st.session_state.qvn_auto_backup_reals_in_target = auto_backup_found_reals_s3_vnm_val if auto_backup_found_reals_s3_vnm_val != ["hetso"] else []
                
                st.session_state.qvn_source_type = None 
                st.session_state.qvn_step = "4b_select_source_type_option"
                st.rerun()
            elif chosen_main_action_key_s3_vnm == "instruct_edit_reals":
                display_status_message("Please choose 'Replace/Get Real Numbers from another Source' to continue on this page, or go to 'Configure Server' for direct editing.", "INFO")


        if st.button("Back (Re-select Target VN or Re-search)", key="qvn_back_from_main_action_select_button_s3_vnm", type="secondary"):
            if len(st.session_state.get('qvn_target_vn_definitions_found', [])) > 1:
                st.session_state.qvn_step = "2_select_target_definition"
            else:
                st.session_state.qvn_step = "1_input_target_vn"
            st.session_state.qvn_main_action_choice = None; st.rerun()

    elif st.session_state.qvn_step == "4b_select_source_type_option":
        st.subheader("Step 4b: Select Source for Real Numbers")
        selected_def_target_s4b_final_vnm = st.session_state.qvn_selected_target_definition_obj
        st.markdown(f"Target VN: `{selected_def_target_s4b_final_vnm['virtual_key']}` (RG: `{selected_def_target_s4b_final_vnm['rg_name']}`, Server: `{selected_def_target_s4b_final_vnm['server_name']}`)")

        auto_backup_key_s4b_final_vnm = st.session_state.get('qvn_auto_backup_key_in_target')
        auto_backup_reals_s4b_final_vnm = st.session_state.get('qvn_auto_backup_reals_in_target', [])
        
        source_options_s4b_final_vnm = []
        default_source_radio_idx_s4b_final_vnm = 0

        if auto_backup_key_s4b_final_vnm and auto_backup_reals_s4b_final_vnm:
            source_options_s4b_final_vnm.append(f"Use auto-backup: '{auto_backup_key_s4b_final_vnm}' ({len(auto_backup_reals_s4b_final_vnm)} numbers) from the same Target RG")
        
        source_options_s4b_final_vnm.append("Enter a different Rewrite Rule Key as Source")
        source_options_s4b_final_vnm.append("CANCEL and return to main action selection")

        if not (auto_backup_key_s4b_final_vnm and auto_backup_reals_s4b_final_vnm) and len(source_options_s4b_final_vnm) > 1 and "Enter a different" in source_options_s4b_final_vnm[0] :
             default_source_radio_idx_s4b_final_vnm = 0
        elif not (auto_backup_key_s4b_final_vnm and auto_backup_reals_s4b_final_vnm) and len(source_options_s4b_final_vnm) > 1:
            try: default_source_radio_idx_s4b_final_vnm = source_options_s4b_final_vnm.index("Enter a different Rewrite Rule Key as Source")
            except ValueError: default_source_radio_idx_s4b_final_vnm = 0

        selected_source_option_s4b_vnm = st.radio(
            "Choose source of real numbers:", options=source_options_s4b_final_vnm, index=default_source_radio_idx_s4b_final_vnm,
            key="qvn_source_type_radio_widget_s4b_vnm"
        )

        if st.button("Proceed with this Source Type", key="qvn_confirm_source_type_button_s4b_vnm"):
            if selected_source_option_s4b_vnm.startswith("Use auto-backup"):
                st.session_state.qvn_source_type = "auto_backup"
                st.session_state.qvn_source_reals_to_use_original = list(auto_backup_reals_s4b_final_vnm)
                st.session_state.qvn_selected_manual_source_obj = None
                st.session_state.qvn_step = "5a_confirm_source_numbers_to_take"
            elif selected_source_option_s4b_vnm.startswith("Enter a different"):
                st.session_state.qvn_source_type = "manual_source_key"
                st.session_state.qvn_manual_source_search_input = ""
                st.session_state.qvn_manual_source_keys_found = []
                st.session_state.qvn_selected_manual_source_obj = None
                st.session_state.qvn_step = "4c_input_manual_source_key_form"
            elif selected_source_option_s4b_vnm.startswith("CANCEL"):
                st.session_state.qvn_step = "3_select_main_action"
                st.session_state.qvn_source_type = None; st.session_state.qvn_auto_backup_key_in_target = None 
                st.session_state.qvn_auto_backup_reals_in_target = []
            st.rerun()
        
        if st.button("Back to Select Main Action (Step 3)", key="qvn_back_to_step3_from_s4b_button_vnm", type="secondary"):
            st.session_state.qvn_step = "3_select_main_action"; st.rerun()

    elif st.session_state.qvn_step == "4c_input_manual_source_key_form":
        st.subheader("Step 4c: Input Manual Source Rewrite Rule Key")
        st.session_state.qvn_manual_source_search_input = st.text_input(
            "Enter Source Rewrite Rule Key to search (can be partial name):",
            value=st.session_state.qvn_manual_source_search_input,
            key="qvn_manual_source_key_input_widget_s4c_vnm"
        )
        if st.button("🔍 Search Source Key", key="qvn_find_manual_source_key_button_s4c_vnm"):
            if not st.session_state.qvn_manual_source_search_input.strip():
                display_status_message("Please enter a Source Key to search.", "WARNING")
            else:
                search_str_s4c_vnm = st.session_state.qvn_manual_source_search_input.strip()
                with st.spinner(f"Searching for Rewrite Rule Keys matching '{search_str_s4c_vnm}'..."):
                    found_keys_defs_s4c_vnm, err_find_keys_s4c_vnm = find_rewrite_rule_keys_globally_backend(search_str_s4c_vnm)
                
                if err_find_keys_s4c_vnm: display_status_message(f"Error searching source keys: {err_find_keys_s4c_vnm}", "ERROR")
                st.session_state.qvn_manual_source_keys_found = found_keys_defs_s4c_vnm if found_keys_defs_s4c_vnm else []
                
                if not found_keys_defs_s4c_vnm:
                    display_status_message(f"No Rewrite Rule Keys found matching '{search_str_s4c_vnm}'.", "ERROR")
                elif len(found_keys_defs_s4c_vnm) == 1:
                    source_def_manual_single_s4c_vnm = found_keys_defs_s4c_vnm[0]
                    source_reals_manual_single_s4c_vnm = source_def_manual_single_s4c_vnm.get("reals", [])
                    if not source_reals_manual_single_s4c_vnm or source_reals_manual_single_s4c_vnm == ["hetso"]:
                        display_status_message(f"Selected Source Key '{source_def_manual_single_s4c_vnm['found_key']}' (RG: {source_def_manual_single_s4c_vnm['rg_name']}) is empty or 'hetso'. Please choose/find another.", "WARNING")
                    else:
                        st.session_state.qvn_selected_manual_source_obj = source_def_manual_single_s4c_vnm
                        st.session_state.qvn_selected_manual_source_idx = 0
                        st.session_state.qvn_source_reals_to_use_original = list(source_reals_manual_single_s4c_vnm)
                        display_status_message(f"Found 1 Source Key: '{source_def_manual_single_s4c_vnm['found_key']}' (RG: {source_def_manual_single_s4c_vnm['rg_name']}).", "SUCCESS")
                        st.session_state.qvn_step = "5a_confirm_source_numbers_to_take"
                        st.rerun()
                else: 
                    display_status_message(f"Found {len(found_keys_defs_s4c_vnm)} matching Rewrite Rule Keys. Please select one.", "INFO")
                    st.session_state.qvn_step = "4d_select_manual_source_key_definition"
                    st.rerun()
        
        if st.button("Back to Select Source Type (Step 4b)", key="qvn_back_to_step4b_from_s4c_button_vnm", type="secondary"):
            st.session_state.qvn_step = "4b_select_source_type_option"
            st.session_state.qvn_manual_source_search_input = ""; st.session_state.qvn_manual_source_keys_found = []
            st.rerun()

    elif st.session_state.qvn_step == "4d_select_manual_source_key_definition":
        st.subheader("Step 4d: Select Specific Manual Source Key Definition")
        found_keys_list_s4d_vnm = st.session_state.get('qvn_manual_source_keys_found', [])
        if not found_keys_list_s4d_vnm:
            display_status_message("Error: No Source Keys to select. Returning to search.", "ERROR")
            st.session_state.qvn_step = "4c_input_manual_source_key_form"; st.rerun()
        else:
            searched_key_disp_s4d_vnm = st.session_state.get('qvn_manual_source_search_input', 'N/A')
            options_map_manual_source_s4d_vnm = {
                i_s4d_vnm: (f"Key: '{d_s4d_vnm['found_key']}', Server: {d_s4d_vnm['server_name']}, RG: {d_s4d_vnm['rg_name']} "
                        f"(Reals: {'hetso' if d_s4d_vnm['is_hetso'] else d_s4d_vnm.get('real_numbers_count',0)} num(s))")
                for i_s4d_vnm, d_s4d_vnm in enumerate(found_keys_list_s4d_vnm)
            }
            default_idx_manual_src_s4d_vnm = st.session_state.get('qvn_selected_manual_source_idx', 0)
            if not (isinstance(default_idx_manual_src_s4d_vnm, int) and 0 <= default_idx_manual_src_s4d_vnm < len(options_map_manual_source_s4d_vnm)):
                default_idx_manual_src_s4d_vnm = 0
            
            selected_idx_val_manual_src_s4d_vnm = st.radio(
                f"Multiple results for '{searched_key_disp_s4d_vnm}'. Please select one Source Key:",
                options=list(options_map_manual_source_s4d_vnm.keys()),
                format_func=lambda x_idx_s4d_vnm: options_map_manual_source_s4d_vnm[x_idx_s4d_vnm],
                index=default_idx_manual_src_s4d_vnm,
                key="qvn_select_manual_source_def_radio_widget_s4d_vnm"
            )
            st.session_state.qvn_selected_manual_source_idx = selected_idx_val_manual_src_s4d_vnm

            if st.button("Confirm This Source Key", key="qvn_confirm_manual_source_def_button_s4d_vnm"):
                selected_manual_def_obj_s4d_vnm = found_keys_list_s4d_vnm[selected_idx_val_manual_src_s4d_vnm]
                source_reals_check_s4d_vnm = selected_manual_def_obj_s4d_vnm.get("reals", [])
                if not source_reals_check_s4d_vnm or source_reals_check_s4d_vnm == ["hetso"]:
                    display_status_message(f"Selected Source Key '{selected_manual_def_obj_s4d_vnm['found_key']}' (RG: {selected_manual_def_obj_s4d_vnm['rg_name']}) is empty or 'hetso'. Please select a different source or search again.", "WARNING")
                else:
                    st.session_state.qvn_selected_manual_source_obj = selected_manual_def_obj_s4d_vnm
                    st.session_state.qvn_source_reals_to_use_original = list(source_reals_check_s4d_vnm)
                    display_status_message(f"Selected Source Key: '{selected_manual_def_obj_s4d_vnm['found_key']}' (RG: {selected_manual_def_obj_s4d_vnm['rg_name']}).", "INFO")
                    st.session_state.qvn_step = "5a_confirm_source_numbers_to_take"
                    st.rerun()
            
            if st.button("Back to Search Manual Source Key (Step 4c)", key="qvn_back_to_step4c_button_s4d_vnm", type="secondary"):
                st.session_state.qvn_step = "4c_input_manual_source_key_form"
                st.session_state.qvn_manual_source_keys_found = []; st.session_state.qvn_selected_manual_source_idx = None
                st.session_state.qvn_selected_manual_source_obj = None; st.rerun()

    elif st.session_state.qvn_step == "5a_confirm_source_numbers_to_take":
        st.subheader("Step 5a: Confirm Number of Reals to Take from Source")
        source_reals_list_s5a_vnm = st.session_state.get('qvn_source_reals_to_use_original', [])
        source_display_name_s5a_vnm = "Undefined Source"
        source_type_s5a_vnm = st.session_state.get('qvn_source_type')

        if source_type_s5a_vnm == "auto_backup":
            source_display_name_s5a_vnm = f"Auto-backup '{st.session_state.qvn_auto_backup_key_in_target}' (in Target RG)"
        elif source_type_s5a_vnm == "manual_source_key" and st.session_state.qvn_selected_manual_source_obj:
            manual_src_obj_s5a_vnm = st.session_state.qvn_selected_manual_source_obj
            source_display_name_s5a_vnm = f"Manual Source Key '{manual_src_obj_s5a_vnm['found_key']}' (RG: {manual_src_obj_s5a_vnm['rg_name']}, Server: {manual_src_obj_s5a_vnm['server_name']})"
        
        if not source_reals_list_s5a_vnm:
            display_status_message(f"Source '{source_display_name_s5a_vnm}' has no real numbers available.", "WARNING")
            if st.button("Back to Select Source Type (Step 4b)", key="qvn_csn_back_no_reals_button_s5a_vnm"):
                st.session_state.qvn_step = "4b_select_source_type_option"; reset_source_states_qvn_helper_vnm(); st.rerun()
        else:
            st.markdown(f"Selected Source: **{source_display_name_s5a_vnm}**")
            st.markdown(f"Available Real Numbers in Source: **{len(source_reals_list_s5a_vnm)}**")
            with st.expander("View Real Numbers from Selected Source"): st.json(source_reals_list_s5a_vnm)

            max_take_s5a_vnm = len(source_reals_list_s5a_vnm)
            default_take_s5a_vnm = st.session_state.get('qvn_num_to_take_from_source', max_take_s5a_vnm)
            current_val_s5a_vnm = max(1, min(default_take_s5a_vnm, max_take_s5a_vnm)) if max_take_s5a_vnm > 0 else 1

            st.session_state.qvn_num_to_take_from_source = st.number_input(
                f"Number of real numbers to TAKE from source '{source_display_name_s5a_vnm}' (max {max_take_s5a_vnm}):",
                min_value=1, max_value=max_take_s5a_vnm if max_take_s5a_vnm > 0 else 1,
                value=current_val_s5a_vnm, key="qvn_num_to_take_input_widget_s5a_vnm", disabled=(max_take_s5a_vnm == 0)
            )

            if st.button("Proceed with This Quantity", key="qvn_confirm_num_to_take_button_s5a_vnm"):
                num_taken_val_s5a_vnm = st.session_state.qvn_num_to_take_from_source
                if 1 <= num_taken_val_s5a_vnm <= max_take_s5a_vnm:
                    st.session_state.qvn_final_numbers_for_target_vn = source_reals_list_s5a_vnm[:num_taken_val_s5a_vnm]
                    st.session_state.qvn_remaining_reals_in_source_key = source_reals_list_s5a_vnm[num_taken_val_s5a_vnm:]
                    st.session_state.qvn_step = "5b_define_target_vn_action_with_source"
                    st.rerun()
                else: display_status_message(f"Invalid quantity: {num_taken_val_s5a_vnm}. Must be between 1 and {max_take_s5a_vnm}.", "ERROR")
            
            if st.button("Back to Select Source Type (Step 4b)", key="qvn_csn_back_to_source_type_button_s5a_alt_vnm", type="secondary"):
                st.session_state.qvn_step = "4b_select_source_type_option"; reset_source_states_qvn_helper_vnm(); st.rerun()

    elif st.session_state.qvn_step == "5b_define_target_vn_action_with_source":
        st.subheader("Step 5b: Define Action for Target VN & Handle Empty Source")
        target_def_obj_s5b_vnm = st.session_state.qvn_selected_target_definition_obj
        target_original_reals_s5b_vnm = list(target_def_obj_s5b_vnm.get('reals', [])) if not target_def_obj_s5b_vnm['is_hetso'] else []
        numbers_from_source_s5b_vnm = st.session_state.get('qvn_final_numbers_for_target_vn', [])

        st.markdown(f"Target VN: **{target_def_obj_s5b_vnm['virtual_key']}** (RG: `{target_def_obj_s5b_vnm['rg_name']}`, Server: `{target_def_obj_s5b_vnm['server_name']}`)")
        current_reals_disp_s5b_vnm = "hetso" if target_def_obj_s5b_vnm['is_hetso'] else (f"{len(target_original_reals_s5b_vnm)} numbers" if target_original_reals_s5b_vnm else "(Empty)")
        st.markdown(f"Current Reals in Target: `{current_reals_disp_s5b_vnm}`")
        st.markdown(f"Numbers from Source ({len(numbers_from_source_s5b_vnm)} numbers): `{'; '.join(numbers_from_source_s5b_vnm[:5])}{'...' if len(numbers_from_source_s5b_vnm)>5 else ''}`")

        action_options_target_s5b_vnm = [
            f"ADD these {len(numbers_from_source_s5b_vnm)} numbers to Target VN",
            f"REPLACE existing reals of Target VN with these {len(numbers_from_source_s5b_vnm)} numbers"
        ]
        default_action_idx_target_s5b_vnm = 0
        is_target_empty_s5b_vnm = target_def_obj_s5b_vnm['is_hetso'] or not target_original_reals_s5b_vnm

        if is_target_empty_s5b_vnm:
            st.session_state.qvn_target_vn_action_on_reals_display = action_options_target_s5b_vnm[0]
            st.info("Target VN is currently empty or 'hetso'. Numbers from source will be assigned (equivalent to ADD).")
            st.session_state.qvn_target_vn_action_on_reals = "add_or_assign"
        else:
            current_target_action_disp_s5b_vnm = st.session_state.get('qvn_target_vn_action_on_reals_display')
            if current_target_action_disp_s5b_vnm in action_options_target_s5b_vnm: default_action_idx_target_s5b_vnm = action_options_target_s5b_vnm.index(current_target_action_disp_s5b_vnm)
            
            st.session_state.qvn_target_vn_action_on_reals_display = st.radio(
                "Select action for Target VN:", options=action_options_target_s5b_vnm, index=default_action_idx_target_s5b_vnm,
                key="qvn_target_vn_action_radio_widget_s5b_vnm"
            )
            st.session_state.qvn_target_vn_action_on_reals = "add" if st.session_state.qvn_target_vn_action_on_reals_display == action_options_target_s5b_vnm[0] else "replace"
        
        remaining_in_source_s5b_vnm = st.session_state.get('qvn_remaining_reals_in_source_key', [])
        source_disp_name_s5b_vnm = get_qvn_source_details_helper_vnm()

        if not remaining_in_source_s5b_vnm:
            st.markdown("---"); st.warning(f"Source '{source_disp_name_s5b_vnm}' will have no real numbers left.")
            empty_source_options_map_s5b_vnm = {"Set to 'hetso'": "hetso", "Leave empty (key:)": "empty", "Delete Source Key from its RG": "delete_key"}
            current_empty_src_action_disp_s5b_vnm = st.session_state.get('qvn_empty_source_key_action_display', "Set to 'hetso'")
            st.session_state.qvn_empty_source_key_action_display = st.radio(
                f"Handle empty Source '{source_disp_name_s5b_vnm}':", options=list(empty_source_options_map_s5b_vnm.keys()),
                index=list(empty_source_options_map_s5b_vnm.keys()).index(current_empty_src_action_disp_s5b_vnm) if current_empty_src_action_disp_s5b_vnm in empty_source_options_map_s5b_vnm else 0,
                key="qvn_empty_source_key_radio_widget_s5b_vnm"
            )
            st.session_state.qvn_empty_source_key_action = empty_source_options_map_s5b_vnm[st.session_state.qvn_empty_source_key_action_display]
        else: st.session_state.qvn_empty_source_key_action = None

        if st.button("Review and Confirm Changes", key="qvn_goto_confirm_changes_button_s5b_vnm"):
            new_list_for_target_s5b_vnm = []
            action_vn_s5b_vnm = st.session_state.qvn_target_vn_action_on_reals
            if action_vn_s5b_vnm == "add_or_assign" or action_vn_s5b_vnm == "add":
                new_list_for_target_s5b_vnm = list(target_original_reals_s5b_vnm)
                for num_s5b_vnm in numbers_from_source_s5b_vnm:
                    if num_s5b_vnm not in new_list_for_target_s5b_vnm: new_list_for_target_s5b_vnm.append(num_s5b_vnm)
            elif action_vn_s5b_vnm == "replace": new_list_for_target_s5b_vnm = list(numbers_from_source_s5b_vnm)
            st.session_state.qvn_final_numbers_for_target_vn = new_list_for_target_s5b_vnm
            st.session_state.qvn_step = "5c_confirm_all_changes"; st.rerun()

        if st.button("Back to Confirm Source Numbers (Step 5a)", key="qvn_back_to_step5a_from_5b_button_vnm", type="secondary"):
            st.session_state.qvn_step = "5a_confirm_source_numbers_to_take"; st.rerun()

    elif st.session_state.qvn_step == "5c_confirm_all_changes":
        st.subheader("Step 5c: Review and Confirm All Changes")
        target_def_s5c_vnm = st.session_state.qvn_selected_target_definition_obj
        new_target_reals_s5c_vnm = st.session_state.get('qvn_final_numbers_for_target_vn', [])
        source_key_name_s5c_vnm, source_rg_name_s5c_vnm, source_server_name_s5c_vnm = get_qvn_source_details_helper_vnm()
        remaining_source_reals_s5c_vnm = st.session_state.get('qvn_remaining_reals_in_source_key', [])
        empty_src_action_s5c_vnm = st.session_state.get('qvn_empty_source_key_action')

        st.markdown(f"**1. Changes for Target Virtual Number:**")
        st.markdown(f"   - Target VN: **{target_def_s5c_vnm['virtual_key']}**")
        st.markdown(f"   - RG: `{target_def_s5c_vnm['rg_name']}` (Server: `{target_def_s5c_vnm['server_name']}`)")
        target_reals_disp_s5c_vnm = '; '.join(new_target_reals_s5c_vnm[:5]) + ('...' if len(new_target_reals_s5c_vnm) > 5 else '') if new_target_reals_s5c_vnm and new_target_reals_s5c_vnm != ["hetso"] else ("(Empty)" if not new_target_reals_s5c_vnm else "hetso")
        st.markdown(f"   - NEW Real Numbers ({len(new_target_reals_s5c_vnm) if new_target_reals_s5c_vnm != ['hetso'] else 1} item(s)): `{target_reals_disp_s5c_vnm}`")
        st.markdown("---")
        st.markdown(f"**2. Changes for Source Key ('{source_key_name_s5c_vnm}'):**")
        st.markdown(f"   - Source RG: `{source_rg_name_s5c_vnm}` (Server: `{source_server_name_s5c_vnm}`)")
        
        source_action_summary_s5c_vnm = ""
        if empty_src_action_s5c_vnm == "delete_key": source_action_summary_s5c_vnm = f"**Source Key '{source_key_name_s5c_vnm}' will be DELETED from its RG.**"
        elif empty_src_action_s5c_vnm == "hetso": source_action_summary_s5c_vnm = f"NEW Real Numbers for Source Key: **['hetso']**"
        elif empty_src_action_s5c_vnm == "empty": source_action_summary_s5c_vnm = f"NEW Real Numbers for Source Key: **(Empty - key:)**"
        else: 
            source_reals_rem_disp_s5c_vnm = '; '.join(remaining_source_reals_s5c_vnm[:5]) + ('...' if len(remaining_source_reals_s5c_vnm) > 5 else '') if remaining_source_reals_s5c_vnm else "(Empty)"
            source_action_summary_s5c_vnm = f"NEW Real Numbers ({len(remaining_source_reals_s5c_vnm)} number(s)): `{source_reals_rem_disp_s5c_vnm}`"
        st.markdown(f"   - {source_action_summary_s5c_vnm}")

        st.warning("CAUTION: This action will directly modify configurations on VOS servers. Please review carefully before confirming.")
        col_confirm1_s5c_vnm, col_confirm2_s5c_vnm = st.columns(2)
        with col_confirm1_s5c_vnm:
            if st.button(" CONFIRM AND SAVE ALL CHANGES", type="primary", key="qvn_execute_all_changes_button_s5c_vnm"):
                st.session_state.qvn_step = "5d_executing_changes"; st.rerun()
        with col_confirm2_s5c_vnm:
            if st.button("Back to Define Target Action (Step 5b)", key="qvn_back_to_define_target_action_button_s5c_vnm", type="secondary"):
                st.session_state.qvn_step = "5b_define_target_vn_action_with_source"; st.rerun()
        
        if st.button("Cancel and Reset Flow", key="qvn_reset_from_confirm_all_button_s5c_vnm", type="secondary"):
            reset_qvn_states_full_flow_function_final_vnm()

    elif st.session_state.qvn_step == "5d_executing_changes":
        st.subheader("Step 5d: Executing Changes on Server...")
        log_exec_qvn_s5d_vnm = st.session_state.qvn_execution_log.append
        target_def_exec_s5d_vnm = st.session_state.qvn_selected_target_definition_obj
        new_target_reals_s5d_vnm = st.session_state.qvn_final_numbers_for_target_vn
        source_type_s5d_vnm = st.session_state.qvn_source_type
        source_key_name_s5d_vnm, _, _, source_server_url_s5d_vnm, source_raw_rg_info_s5d_vnm, source_rg_name_s5d_vnm, source_server_name_s5d_vnm = get_qvn_source_details_for_execution_helper_vnm()
        
        final_source_reals_payload_s5d_vnm = st.session_state.qvn_remaining_reals_in_source_key
        if st.session_state.qvn_empty_source_key_action == "hetso": final_source_reals_payload_s5d_vnm = ["hetso"]
        elif st.session_state.qvn_empty_source_key_action == "empty": final_source_reals_payload_s5d_vnm = []
        delete_source_key_flag_s5d_vnm = (st.session_state.qvn_empty_source_key_action == "delete_key")

        st.session_state.qvn_execution_log = []
        log_exec_qvn_s5d_vnm(f"Starting update for Target VN '{target_def_exec_s5d_vnm['virtual_key']}' and Source '{source_key_name_s5d_vnm}'.")
        st.session_state.qvn_exec_status_target = False; st.session_state.qvn_exec_status_source = True 

        with st.spinner("Applying changes to VOS servers..."):
            target_rg_latest_info_s5d_vnm, err_get_target_s5d_vnm = get_routing_gateway_details(
                {"url": target_def_exec_s5d_vnm['server_url'], "name": target_def_exec_s5d_vnm['server_name']}, target_def_exec_s5d_vnm['rg_name']
            )
            if err_get_target_s5d_vnm or not target_rg_latest_info_s5d_vnm:
                log_exec_qvn_s5d_vnm(f"CRITICAL ERROR: Could not get Target RG info '{target_def_exec_s5d_vnm['rg_name']}'. Update aborted for Target. Error: {err_get_target_s5d_vnm}")
            else:
                rules_in_target_exec_s5d_vnm = parse_vos_rewrite_rules(target_rg_latest_info_s5d_vnm.get("rewriteRulesInCaller", ""))
                rules_in_target_exec_s5d_vnm[target_def_exec_s5d_vnm['virtual_key']] = new_target_reals_s5d_vnm if new_target_reals_s5d_vnm else []
                
                is_source_in_same_target_rg_vnm = (source_type_s5d_vnm == "auto_backup") or \
                                              (source_type_s5d_vnm == "manual_source_key" and \
                                               source_server_url_s5d_vnm == target_def_exec_s5d_vnm['server_url'] and \
                                               source_rg_name_s5d_vnm == target_def_exec_s5d_vnm['rg_name'])

                if is_source_in_same_target_rg_vnm and source_key_name_s5d_vnm != "N/A": # Make sure source_key_name_s5d_vnm is valid
                    log_exec_qvn_s5d_vnm(f"Source '{source_key_name_s5d_vnm}' is in the same Target RG. Updating in one API call.")
                    if delete_source_key_flag_s5d_vnm:
                        if source_key_name_s5d_vnm in rules_in_target_exec_s5d_vnm: del rules_in_target_exec_s5d_vnm[source_key_name_s5d_vnm]
                    else: rules_in_target_exec_s5d_vnm[source_key_name_s5d_vnm] = final_source_reals_payload_s5d_vnm
                
                payload_target_exec_s5d_vnm = target_rg_latest_info_s5d_vnm.copy()
                payload_target_exec_s5d_vnm["rewriteRulesInCaller"] = format_rewrite_rules_for_vos(rules_in_target_exec_s5d_vnm)
                apply_locktype_logic_qvn_helper(payload_target_exec_s5d_vnm, rules_in_target_exec_s5d_vnm)

                success_target_s5d_vnm, msg_target_s5d_vnm = update_routing_gateway(
                    {"url": target_def_exec_s5d_vnm['server_url'], "name": target_def_exec_s5d_vnm['server_name']},
                    target_def_exec_s5d_vnm['rg_name'], payload_target_exec_s5d_vnm
                )
                log_exec_qvn_s5d_vnm(f"{'SUCCESS' if success_target_s5d_vnm else 'ERROR'}: Target RG '{target_def_exec_s5d_vnm['rg_name']}' update. {msg_target_s5d_vnm}")
                st.session_state.qvn_exec_status_target = success_target_s5d_vnm

                if not is_source_in_same_target_rg_vnm and source_type_s5d_vnm == "manual_source_key" and source_raw_rg_info_s5d_vnm:
                    log_exec_qvn_s5d_vnm(f"Source '{source_key_name_s5d_vnm}' in different RG. Updating Source RG '{source_rg_name_s5d_vnm}' on Server '{source_server_name_s5d_vnm}'.")
                    source_rg_latest_info_s5d_vnm_val, err_get_source_s5d_vnm = get_routing_gateway_details(
                        {"url": source_server_url_s5d_vnm, "name": source_server_name_s5d_vnm}, source_rg_name_s5d_vnm
                    )
                    if err_get_source_s5d_vnm or not source_rg_latest_info_s5d_vnm_val:
                        log_exec_qvn_s5d_vnm(f"CRITICAL ERROR: Could not get Source RG info '{source_rg_name_s5d_vnm}'. Update aborted for Source. Error: {err_get_source_s5d_vnm}")
                        st.session_state.qvn_exec_status_source = False
                    else:
                        rules_in_source_exec_s5d_vnm = parse_vos_rewrite_rules(source_rg_latest_info_s5d_vnm_val.get("rewriteRulesInCaller", ""))
                        if delete_source_key_flag_s5d_vnm:
                            if source_key_name_s5d_vnm in rules_in_source_exec_s5d_vnm: del rules_in_source_exec_s5d_vnm[source_key_name_s5d_vnm]
                        else: rules_in_source_exec_s5d_vnm[source_key_name_s5d_vnm] = final_source_reals_payload_s5d_vnm
                        
                        payload_source_exec_s5d_vnm = source_rg_latest_info_s5d_vnm_val.copy()
                        payload_source_exec_s5d_vnm["rewriteRulesInCaller"] = format_rewrite_rules_for_vos(rules_in_source_exec_s5d_vnm)
                        apply_locktype_logic_qvn_helper(payload_source_exec_s5d_vnm, rules_in_source_exec_s5d_vnm)

                        success_source_s5d_vnm, msg_source_s5d_vnm = update_routing_gateway(
                            {"url": source_server_url_s5d_vnm, "name": source_server_name_s5d_vnm},
                            source_rg_name_s5d_vnm, payload_source_exec_s5d_vnm
                        )
                        log_exec_qvn_s5d_vnm(f"{'SUCCESS' if success_source_s5d_vnm else 'ERROR'}: Source RG '{source_rg_name_s5d_vnm}' update. {msg_source_s5d_vnm}")
                        st.session_state.qvn_exec_status_source = success_source_s5d_vnm
            
            log_exec_qvn_s5d_vnm("--- Update process finished ---")
            st.session_state.qvn_step = "6_done"; st.rerun()

    elif st.session_state.qvn_step == "6_done":
        st.subheader(" Step 6: Operation Completed")
        final_log_qvn_s6_vnm = st.session_state.get("qvn_execution_log", ["No execution log."])
        st.text_area("Execution Log:", value="\n".join(final_log_qvn_s6_vnm), height=300, disabled=True, key="qvn_final_log_display_widget_main_s6_vnm")

        target_exec_ok_s6_vnm = st.session_state.get('qvn_exec_status_target', False)
        source_exec_ok_s6_vnm = st.session_state.get('qvn_exec_status_source', True) 

        if target_exec_ok_s6_vnm and source_exec_ok_s6_vnm:
            st.success("All changes applied successfully!"); st.balloons()
        else:
            err_summary_list_s6_vnm = []
            if not target_exec_ok_s6_vnm: err_summary_list_s6_vnm.append("Updating Target VN/Key failed.")
            if not source_exec_ok_s6_vnm: err_summary_list_s6_vnm.append("Updating Source VN/Key failed.")
            display_status_message(f"Errors occurred: {' '.join(err_summary_list_s6_vnm)} Please review the log.", "ERROR")
        
        if st.button("Perform Another Virtual Number Operation", key="qvn_start_another_op_button_final_s6_vnm"):
            reset_qvn_states_full_flow_function_final_vnm()
    
    else:
        display_status_message(f"Undefined QVN step: {st.session_state.qvn_step}. Resetting flow.", "WARNING")
        reset_qvn_states_full_flow_function_final_vnm()

elif current_page_key is None:
    st.error("Lỗi: Lựa chọn menu không hợp lệ hoặc không tìm thấy khóa trang. Vui lòng kiểm tra cấu hình menu.")
else:
    st.header(selected_page_label) 
    st.write(f"Nội dung cho khóa trang '{current_page_key}' đang được phát triển.")
    st.warning("Phần này hiện đang được refactor. Vui lòng kiểm tra lại sau.")

# --- Helper functions for QVN flow (can be defined at the end of the QVN elif block or globally if preferred) ---



