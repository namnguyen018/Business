import streamlit as st
import re
import pandas as pd
import requests
import json
import os

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống Quản Trị Rủi Ro Tài Chính", layout="wide")

# CSS cho nút bấm
st.markdown("""
    <style>
    div.stButton > button:first-child { transition: all 0.2s; border-radius: 5px; }
    div.stButton > button:hover { transform: scale(1.02); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
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

LO_REV, LO_PAY, DE_PAY, BC_PAY, X2_PAY, X3_PAY = 22500, 80000, 70, 400, 10, 40

def format_vnd(val): return f"{val:,.0f}".replace(',', '.') + ' đ'

# ... (Giữ nguyên hàm parse_and_add_bets như cũ) ...

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Hệ Thống Quản Trị Rủi Ro Tài Chính")

col1, col2 = st.columns([1, 1])

with col1:
    name = st.text_input("Tên Khách Hàng", value="đạt")
    msg = st.text_area("Danh mục cược", height=120, placeholder="VD:\nXiên 29 99 100k\n05 10đ")
    if st.button("Cập Nhật Vào Bảng", type="primary"):
        count = parse_and_add_bets(name, msg) # Cần đảm bảo hàm này đã được nạp
        if count > 0: st.success(f"Ghi nhận {count} mục!")
        st.rerun()

with col2:
    st.header("📈 Bảng Tổng Hợp")
    if st.session_state.bets:
        # TÍNH TỔNG TIỀN LÔ
        total_lo_amount = sum(b['amount'] for b in st.session_state.bets if b['type'] == 'Lô')
        st.metric("Tổng tiền Lô khách đánh", f"{total_lo_amount} điểm")
        
        # ... (Giữ nguyên logic bảng exp_list cũ) ...

st.markdown("---")
st.header("📜 Lịch Sử Cược Chi Tiết")

# NÚT XÓA CƯỢC
if st.session_state.bets:
    # Hiển thị dataframe kèm nút xóa
    for i, b in enumerate(st.session_state.bets):
        cols = st.columns([1, 1, 1, 1, 0.5])
        cols[0].write(b['customer'])
        cols[1].write(b['type'])
        cols[2].write(f"{b['number']} ({b['amount']})")
        if cols[4].button("🗑️", key=f"del_{i}"):
            st.session_state.bets.pop(i)
            save_data_to_file()
            st.rerun()

# --- (Phần Đối chiếu kết quả giữ nguyên như cũ) ---
