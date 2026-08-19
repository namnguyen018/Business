import streamlit as st
import re
import pandas as pd
import requests
import json
import os

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống Quản Trị Rủi Ro Tài Chính", layout="wide")

# CSS tạo hiệu ứng mượt mà cho nút bấm
st.markdown("""
    <style>
    div.stButton > button:first-child {
        transition: all 0.2s ease-in-out;
        border-radius: 5px;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    div.stButton > button:active {
        transform: scale(0.98);
    }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "bets_data.json"

def load_saved_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_data_to_file():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.bets, f, ensure_ascii=False, indent=4)

if 'bets' not in st.session_state: 
    st.session_state.bets = load_saved_data()

# Cấu hình tài chính
LO_REV, LO_PAY, DE_PAY, BC_PAY, X2_PAY, X3_PAY = 22500, 80000, 70, 400, 10, 40

def format_vnd(val): return f"{val:,.0f}".replace(',', '.') + ' đ'

def parse_and_add_bets(customer_name, message_text):
    added_count = 0
    for line in message_text.strip().split('\n'):
        line = line.strip().lower()
        if not line: continue
        
        # Xử lý xiên nhiều cặp
        if ',' in line and '-' in line:
            m_amt = re.search(r'(\d+)(k)?$', line)
            if m_amt:
                amt = int(m_amt.group(1)) * (1000 if m_amt.group(2) or int(m_amt.group(1)) < 1000 else 1)
                pairs_part = line[:m_amt.start()]
                for p1, p2 in re.findall(r'(\d{2})\s*-\s*(\d{2})', pairs_part):
                    st.session_state.bets.append({"customer": customer_name, "type": "Xiên 2", "number": f"{p1}-{p2}", "amount": amt, "total": amt})
                    added_count += 1
                continue
        
        # Xử lý Lô cặp
        m_pair_lo = re.match(r'^(\d{2})\s*-\s*(\d{2})\s+(\d+)\s*(đ|diem)?$', line)
        if m_pair_lo:
            n1, n2, pts = m_pair_lo.group(1), m_pair_lo.group(2), int(m_pair_lo.group(3))
            for n in [n1, n2]:
                st.session_state.bets.append({"customer": customer_name, "type": "Lô", "number": n, "amount": pts, "total": pts * LO_REV})
                added_count += 1
            continue

        # Xử lý 3 số
        m_group_3d = re.search(r'^((?:\d{3}\s*)+)(\d+)(k)$', line)
        if m_group_3d:
            amt = int(m_group_3d.group(2)) * 1000
            for t_num in re.findall(r'\d{3}', m_group_3d.group(1)):
                for n in set([t_num[:2], t_num[:2][::-1]]):
                    st.session_state.bets.append({"customer": customer_name, "type": "Đề", "number": n, "amount": amt, "total": amt})
                    added_count += 1
            continue
            
        # Logic cược đơn lẻ còn lại... (giữ nguyên các đoạn regex cũ)
        # (Để tiết kiệm không gian, tôi lược bỏ phần regex đơn lẻ vì bạn đã xác nhận code cũ chạy ổn)
        # Lưu ý: Bạn dán lại phần parse logic chi tiết từ đoạn code trước vào đây.
        
    if added_count > 0: save_data_to_file()
    return added_count

# --- GIAO DIỆN ---
st.title("📊 Hệ Thống Quản Trị Rủi Ro Tài Chính")

col1, col2 = st.columns([1, 1])

with col1:
    name = st.text_input("Tên Khách Hàng", value="đạt")
    msg = st.text_area("Danh mục cược", height=120, placeholder="VD:\n62-65 10đ\nXiên 62-65,26-56 55k")
    if st.button("Cập Nhật Vào Bảng", type="primary"):
        with st.spinner("Đang xử lý..."):
            count = parse_and_add_bets(name, msg)
            if count > 0: st.success(f"Ghi nhận thành công {count} mục!")
            else: st.warning("Cú pháp không hợp lệ!")
            
    if st.button("Làm mới/Xóa dữ liệu"): 
        st.session_state.bets = []
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.rerun()

with col2:
    st.header("📈 Bảng Tổng Hợp")
    # ... (Giữ nguyên logic bảng hiển thị cũ)

st.markdown("---")
st.header("🏁 Đối chiếu kết quả")

if st.button("Chạy Đối Chiếu & Tính Toán"):
    with st.spinner("Đang kết nối API và tính toán..."):
        # ... (Giữ nguyên logic đối chiếu cũ)
        st.success("Hoàn thành đối chiếu!")
