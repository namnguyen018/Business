import streamlit as st
import re
import pandas as pd
import requests
import json
import os
from datetime import datetime
import altair as alt

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống Quản Trị & Forecast Chứng Khoán", layout="wide")

# --- CSS TOÀN CỤC ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(rgba(11, 15, 25, 0.96), rgba(11, 15, 25, 0.99)), 
                    url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #ffffff !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    label, p, span, div, .stMarkdown {
        color: #f3f4f6 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(17, 24, 39, 0.8);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: rgba(30, 41, 59, 0.7) !important;
        border-radius: 6px !important;
        padding: 0 20px;
        color: #cbd5e1 !important;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #f59e0b !important;
        color: #111827 !important;
        font-weight: 700 !important;
    }
    .stTabs [aria-selected="true"] p {
        color: #111827 !important;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: #ffffff !important;
        border: 1px solid rgba(245, 158, 11, 0.4) !important;
        border-radius: 6px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #f59e0b !important;
        box-shadow: 0 0 8px rgba(245, 158, 11, 0.3) !important;
    }

    .top-nav {
        background-color: rgba(17, 24, 39, 0.95);
        padding: 15px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        border-bottom: 3px solid #f59e0b;
        margin-bottom: 30px;
        backdrop-filter: blur(8px);
        border-radius: 6px;
    }
    .brand-logo {
        font-size: 1.2rem;
        font-weight: 800;
        letter-spacing: 1px;
        color: #ffffff;
    }
    .brand-logo span {
        color: #f59e0b;
    }

    .hero-banner {
        background: rgba(17, 24, 39, 0.9);
        padding: 40px 20px;
        text-align: center;
        border-bottom: 4px solid #f59e0b;
        border-radius: 8px;
        margin-bottom: 30px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        letter-spacing: 0.5px;
        margin-bottom: 20px;
    }
    .hero-btn {
        display: inline-block;
        background-color: #f59e0b;
        color: #111827;
        padding: 8px 20px;
        font-weight: 700;
        border-radius: 4px;
        text-transform: uppercase;
        font-size: 0.85rem;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.4);
    }

    .custom-card {
        background: rgba(30, 41, 59, 0.9);
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(245, 158, 11, 0.3);
        margin-bottom: 20px;
        backdrop-filter: blur(6px);
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 8px;
    }
    .card-desc {
        font-size: 0.9rem;
        color: #cbd5e1 !important;
        line-height: 1.5;
        margin-bottom: 15px;
    }
    .card-link {
        font-size: 0.85rem;
        font-weight: 700;
        color: #f59e0b !important;
        text-transform: uppercase;
    }

    div.stButton > button, div.stFormSubmitButton > button {
        width: 100% !important;
        background-color: #f59e0b !important;
        color: #111827 !important;
        border: none !important;
        padding: 10px 20px !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #d97706 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.5) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo trạng thái đăng nhập
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

DATA_FILE = "bets_data.json"
REV_FILE = "revenue_history.json"

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

def load_revenue_history():
    if os.path.exists(REV_FILE):
        try:
            with open(REV_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_revenue_history(history_list):
    with open(REV_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=4)

if 'bets' not in st.session_state: 
    st.session_state.bets = load_saved_data()

if 'revenue_history' not in st.session_state:
    st.session_state.revenue_history = load_revenue_history()

LO_REV, LO_PAY, DE_PAY, BC_PAY, X2_PAY, X3_PAY = 22500, 80000, 70, 400, 10, 40

def format_vnd(val): return f"{val:,.0f}".replace(',', '.') + ' đ'

def parse_and_add_bets(customer_name, message_text):
    added_count = 0
    for line in message_text.strip().split('\n'):
        line = line.strip().lower()
        if not line: continue
        
        if ',' in line and '-' in line and 'xiên' in line:
            m_amt = re.search(r'(\d+)(k)?$', line)
            if m_amt:
                amt = int(m_amt.group(1))
                if m_amt.group(2) or amt < 1000: amt *= 1000
                pairs_part = line[:m_amt.start()]
                for p1, p2 in re.findall(r'(\d{2})\s*-\s*(\d{2})', pairs_part):
                    st.session_state.bets.append({"customer": customer_name, "type": "Xiên 2", "number": f"{p1}-{p2}", "amount": amt, "total": amt})
                    added_count += 1
                continue

        m_pair_lo = re.match(r'^(\d{2})\s*-\s*(\d{2})\s+(\d+)\s*(đ|diem)?$', line)
        if m_pair_lo:
            n1, n2, pts = m_pair_lo.group(1), m_pair_lo.group(2), int(m_pair_lo.group(3))
            for n in [n1, n2]:
                st.session_state.bets.append({"customer": customer_name, "type": "Lô", "number": n, "amount": pts, "total": pts * LO_REV})
                added_count += 1
            continue

        m_group_3d = re.search(r'^((?:\d{3}\s*)+)(\d+)\s*(k)?(?:\s*đề)?$', line)
        if m_group_3d:
            nums_str = m_group_3d.group(1)
            raw_amt = int(m_group_3d.group(2))
            amt = raw_amt * 1000 if (m_group_3d.group(3) or raw_amt < 1000) else raw_amt
            for t_num in re.findall(r'\d{3}', nums_str):
                for n in set([t_num[:2], t_num[:2][::-1]]):
                    st.session_state.bets.append({"customer": customer_name, "type": "Đề", "number": n, "amount": amt, "total": amt})
                    added_count += 1
            continue

        m3c = re.search(r'3c\s*(\d{3})\s*(\d+)(k)?', line)
        if m3c:
            num, amt = m3c.group(1), int(m3c.group(2))
            if m3c.group(3) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "3 càng", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        mx2 = re.search(r'(?:xiên|x2)\s*2?\s+(\d{2})\D+(\d{2})\D*(\d+)(k)?', line)
        if mx2:
            num = f"{mx2.group(1)}-{mx2.group(2)}"
            amt = int(mx2.group(3))
            if mx2.group(4) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Xiên 2", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        mx3 = re.search(r'(?:xiên\s*3|x3)\s+(\d{2})\s+(\d{2})\s+(\d{2})\s*(\d+)(k)?', line)
        if mx3:
            num = f"{mx3.group(1)}-{mx3.group(2)}-{mx3.group(3)}"
            amt = int(mx3.group(4))
            if mx3.group(5) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Xiên 3", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        m_de = re.search(r'(?:đề|de)?\s*(\d{2})\s*(\d+)(k)', line)
        if m_de:
            num, amt = m_de.group(1), int(m_de.group(2)) * 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Đề", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        tokens = line.split()
        nums = [t for t in tokens if re.match(r'^\d{2}$', t)]
        if nums:
            pts_lo = 0
            amt_de = 0
            for t in tokens:
                if 'đ' in t or 'diem' in t:
                    m = re.search(r'(\d+)', t)
                    if m: pts_lo = int(m.group(1))
                elif 'k' in t:
                    m = re.search(r'(\d+)', t)
                    if m: amt_de = int(m.group(1)) * 1000
            
            if not pts_lo and not amt_de and len(tokens) >= 2:
                last_val = int(re.sub(r'\D', '', tokens[-1]))
                if last_val < 100: pts_lo = last_val
                else: amt_de = last_val * 1000 if last_val < 1000 else last_val

            for n in nums:
                if pts_lo > 0:
                    st.session_state.bets.append({"customer": customer_name, "type": "Lô", "number": n, "amount": pts_lo, "total": pts_lo * LO_REV})
                    added_count += 1
                if amt_de > 0:
                    st.session_state.bets.append({"customer": customer_name, "type": "Đề", "number": n, "amount": amt_de, "total": amt_de})
                    added_count += 1
                    
    if added_count > 0:
        save_data_to_file()
        
    return added_count

# ==========================================
# 1. GIAO DIỆN ĐĂNG NHẬP
# ==========================================
if not st.session_state.authenticated:
    st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">HỆ THỐNG FORECAST CHỨNG KHOÁN</div>
            <div class="hero-subtitle">Bảo Mật Cao & Quản Trị Rủi Ro Chuyên Nghiệp</div>
            <div class="hero-btn">Xác Thực Truy Cập</div>
        </div>
    """, unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("login_form"):
            st.markdown("### 🔐 Đăng Nhập Hệ Thống")
            username_input = st.text_input("Tên đăng nhập", placeholder="Nhập tên đăng nhập...")
            password_input = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu...")
            submit_login = st.form_submit_button("Xác Minh Ngay")
            
            if submit_login:
                if username_input == "spass122" and password_input == "Anhnam12@":
                    st.session_state.authenticated = True
                    st.toast("Đăng nhập thành công!", icon="🚀")
                    st.rerun()
                else:
                    st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác!")
    st.stop()


# ==========================================
# 2. GIAO DIỆN TRANG CHÍNH (SAU KHI ĐĂNG NHẬP)
# ==========================================
st.markdown("""
    <div class="top-nav">
        <div class="brand-logo">📊 FORECAST <span>SYSTEM</span></div>
        <div style="font-size: 0.9rem; color: #cbd5e1;">Xin chào, <b>spass122</b></div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title" style="font-size: 1.8rem;">HỆ THỐNG QUẢN TRỊ TÀI CHÍNH & RỦI RO</h1>
        <p class="hero-subtitle">Xây dựng giải pháp phân tích dữ liệu và tối ưu hóa vận hành thông minh</p>
        <div class="hero-btn">Trung Tâm Điều Hành</div>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Bảng Điều Khiển")
    st.write(f"Tài khoản: `spass122`")
    if st.button("🚪 Đăng Xuất Hệ Thống"):
        st.session_state.authenticated = False
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📥 Nhập liệu & Phân tích", "📜 Quản lý công nợ", "🏁 Đối chiếu & Lợi nhuận", "💰 Doanh thu"])

with tab1:
    col_input, col_stats = st.columns([1, 1.3], gap="large")
    
    with col_input:
        st.subheader("✍️ Nhập Danh Mục Cược")
        name = st.text_input("Tên Khách Hàng", value="đạt")
        msg = st.text_area("Nội dung cược", height=140, placeholder="VD:\nXiên 29 99 100k\n05 10đ\n62-65 10đ")
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("🚀 Ghi Nhận Dữ Liệu", use_container_width=True):
                if msg.strip():
                    count = parse_and_add_bets(name, msg)
                    if count > 0: 
                        current_date_str = datetime.now().strftime("%d/%m/%Y")
                        st.success(f"🎉 Đã ghi nhận khách **{name}** ngày **{current_date_str}** ({count} mục cược mới)!")
                        st.balloons()
                    else: 
                        st.warning("Cú pháp không hợp lệ!")
                else:
                    st.warning("Vui lòng nhập nội dung cược!")
        with c_btn2:
            if st.button("🗑️ Xóa Danh Sách Cược", use_container_width=True): 
                st.session_state.bets = []
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.toast("Đã làm sạch danh sách cược hiện tại!", icon="🗑️")
                st.rerun()

    with col_stats:
        st.subheader("📊 Biểu Đồ Phân Tích Rủi Ro Lô (Exposure)")
        if not st.session_state.bets:
            st.info("Chưa có dữ liệu cược. Hãy nhập dữ liệu ở khung bên trái.")
        else:
            lo_bets = [b for b in st.session_state.bets if b['type'] == 'Lô']
            
            if not lo_bets:
                st.info("Chưa có dữ liệu cược Lô nào để hiển thị biểu đồ.")
            else:
                total_lo_revenue = sum(b['total'] for b in lo_bets)
                
                lo_summary = {}
                for b in lo_bets:
                    num = b['number']
                    pts = b['amount']
                    if num not in lo_summary:
                        lo_summary[num] = 0
                    lo_summary[num] += pts
                
                chart_data = []
                for num, pts in lo_summary.items():
                    payout_if_hit = pts * LO_PAY 
                    chart_data.append({
                        "so": str(num),
                        "diem": pts,
                        "payout": payout_if_hit
                    })
                
                df_chart = pd.DataFrame(chart_data)
                df_chart = df_chart.sort_values("diem", ascending=False)
                
                # Gán màu sắc: Đỏ nếu payout >= 80% tổng thu lô, ngược lại màu Xanh dương (#3b82f6)
                colors = []
                for payout in df_chart["payout"]:
                    if total_lo_revenue > 0 and (payout >= total_lo_revenue * 0.8):
                        colors.append("#ef4444") # Đỏ cảnh báo
                    else:
                        colors.append("#3b82f6") # Xanh dương
                
                df_chart["color"] = colors
                
                # Vẽ biểu đồ Altair với nền trong suốt (transparent) hòa hợp hoàn toàn với dark mode
                chart = alt.Chart(df_chart).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                    x=alt.X('so:N', sort=None, title='Con Số Lô', axis=alt.Axis(labelColor='#cbd5e1', titleColor='#f3f4f6', labelAngle=0)),
                    y=alt.Y('payout:Q', title='Số Tiền Phải Trả (1 Nháy)', axis=alt.Axis(labelColor='#cbd5e1', titleColor='#f3f4f6', gridColor='rgba(255, 255, 255, 0.08)')),
                    color=alt.Color('color:N', scale=None),
                    tooltip=['so', 'diem', 'payout']
                ).properties(
                    height=380,
                    title=alt.TitleParams(
                        text=f"Tổng thu Lô: {format_vnd(total_lo_revenue)} (Cột đỏ = Rủi ro cao)",
                        color='#ffffff',
                        fontSize=14
                    )
                ).configure(
                    background='transparent',
                    view=alt.ViewConfig(stroke=None)
                )
                
                st.altair_chart(chart, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💡 Các Tiện Ích Phân Tích Mở Rộng")
    
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.markdown("""
            <div class="custom-card">
                <div class="card-title">Quản Lý Rủi Ro Lô Đề</div>
                <div class="card-desc">Hệ thống phân tích tự động bóc tách từng danh mục cược của khách hàng, tính toán chính xác tỷ lệ hoàn trả và biên độ lợi nhuận ròng.</div>
                <div class="card-link">CHI TIẾT VẬN HÀNH →</div>
            </div>
        """, unsafe_allow_html=True)
    with cc2:
        st.markdown("""
            <div class="custom-card">
                <div class="card-title">Đối Chiếu API Trực Tuyến</div>
                <div class="card-desc">Kết nối trực tiếp với các nguồn dữ liệu kết quả xổ số nhanh chóng, tự động quy chiếu và đối soát tiền thắng thua minh bạch.</div>
                <div class="card-link">XEM TÍCH HỢP →</div>
            </div>
        """, unsafe_allow_html=True)
    with cc3:
        st.markdown("""
            <div class="custom-card">
                <div class="card-title">Báo Cáo Công Nợ Cuối Ngày</div>
                <div class="card-desc">Tổng hợp tự động bảng thanh toán dòng tiền chi tiết cho từng cá nhân, hiển thị trực quan trạng thái phải thu và phải trả.</div>
                <div class="card-link">BÁO CÁO NGAY →</div>
            </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("📜 Danh Sách Chi Tiết & Công Nợ Khách Hàng")
    if not st.session_state.bets:
        st.info("Chưa có lịch sử cược nào được ghi nhận.")
    else:
        total_lo_pts = sum(b['amount'] for b in st.session_state.bets if b['type'] == 'Lô')
        total_lo_money = sum(b['total'] for b in st.session_state.bets if b['type'] == 'Lô')
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Tổng Điểm Lô", f"{total_lo_pts} điểm")
        with m_col2:
            st.metric("Tổng Thành Tiền Lô", format_vnd(total_lo_money))
        
        st.divider()
        
        customers_dict = {}
        for i, b in enumerate(st.session_state.bets):
            cust = b['customer']
            if cust not in customers_dict:
                customers_dict[cust] = []
            customers_dict[cust].append((i, b))
            
        for cust, items in customers_dict.items():
            with st.container(border=True):
                st.markdown(f"### 👤 Khách hàng: `{cust}`")
                
                header_cols = st.columns([1, 1.5, 2, 2, 0.8])
                header_cols[0].markdown("**Loại**")
                header_cols[1].markdown("**Số đánh**")
                header_cols[2].markdown("**Mức cược**")
                header_cols[3].markdown("**Thành tiền**")
                header_cols[4].markdown("**Xóa**")
                
                cust_lo_pts = 0
                cust_lo_money = 0
                cust_other_money = 0
                
                for i, b in items:
                    row_cols = st.columns([1, 1.5, 2, 2, 0.8])
                    row_cols[0].write(b['type'])
                    row_cols[1].write(b['number'])
                    
                    m_cuoc = f"{b['amount']} điểm" if b['type']=="Lô" else format_vnd(b['amount'])
                    row_cols[2].write(m_cuoc)
                    row_cols[3].write(format_vnd(b['total']))
                    
                    if b['type'] == 'Lô':
                        cust_lo_pts += b['amount']
                        cust_lo_money += b['total']
                    else:
                        cust_other_money += b['total']
                        
                    if row_cols[4].button("🗑️", key=f"del_row_{i}"):
                        st.session_state.bets.pop(i)
                        save_data_to_file()
                        st.toast(f"Đã xóa một mục của {cust}!", icon="⚠️")
                        st.rerun()
                        
                summary_html = f'<div style="background-color: rgba(30, 41, 59, 0.9); padding: 10px; border-radius: 5px; margin-top: 15px; font-weight: bold; color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4);">📊 Tổng kết {cust}: {cust_lo_pts} điểm Lô ({format_vnd(cust_lo_money)}) | Ngoài Lô: {format_vnd(cust_other_money)} | Tổng cộng: {format_vnd(cust_lo_money + cust_other_money)}</div>'
                st.markdown(summary_html, unsafe_allow_html=True)

with tab3:
    st.subheader("🏁 Đối Chiếu Kết Quả & Chốt Lợi Nhuận")
    
    api_url = "https://api-xsmb-today.onrender.com/api/v1"
    use_api = st.checkbox("Sử dụng dữ liệu tự động từ API trực tuyến", value=True)
    manual_res = st.text_input("Hoặc dán kết quả thủ công", value="")

    if st.button("⚡ Chạy Đối Chiếu & Tính Toán"):
        with st.spinner("Đang đối chiếu dữ liệu..."):
            res_2d = []
            so_de = ""
            so_3c = ""
            success_load = False
            
            if use_api:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        api_data = response.json()
                        results_dict = api_data.get("results", {})
                        
                        for key, val_list in results_dict.items():
                            if isinstance(val_list, list):
                                for item in val_list:
                                    res_2d.append(item[-2:])
                                    if "đb" in key.lower() or "db" in key.lower() or key == "ĐB":
                                        so_de = item[-2:]
                                        so_3c = item[-3:]
                        
                        if not so_de and results_dict:
                            first_key = list(results_dict.keys())[0]
                            if results_dict[first_key]:
                                so_de = results_dict[first_key][0][-2:]
                                so_3c = results_dict[first_key][0][-3:]

                        success_load = True
                        st.toast(f"Lấy kết quả API thành công! Số Đề: {so_de}", icon="🎯")
                except Exception as e:
                    st.error(f"Lỗi kết nối API: {e}")

            if not success_load and manual_res.strip():
                all_nums = re.findall(r'\d{2,}', manual_res)
                res_2d = [n[-2:] for n in all_nums]
                if res_2d:
                    so_de = res_2d[0]
                    so_3c = manual_res[-3:]
                    success_load = True

            if not success_load or not res_2d:
                st.warning("Chưa có dữ liệu kết quả hợp lệ để đối chiếu.")
            else:
                total_lo_profit = 0
                total_ncc_revenue = 0
                total_ncc_payout = 0
                
                customer_detailed_results = {}
                
                for b in st.session_state.bets:
                    cust = b['customer']
                    if cust not in customer_detailed_results:
                        customer_detailed_results[cust] = {"bets": [], "total_bet": 0, "total_win": 0}
                    
                    win = 0
                    if b['type'] == "Lô":
                        win = res_2d.count(b['number']) * b['amount'] * LO_PAY
                    elif b['type'] == "Đề":
                        if b['number'] == so_de: win = b['amount'] * DE_PAY
                    elif b['type'] == "3 càng":
                        if b['number'] == so_3c: win = b['amount'] * BC_PAY
                    elif b['type'] == "Xiên 2":
                        parts = b['number'].split('-')
                        if len(parts) == 2 and parts[0] in res_2d and parts[1] in res_2d:
                            win = b['amount'] * X2_PAY
                    elif b['type'] == "Xiên 3":
                        parts = b['number'].split('-')
                        if len(parts) == 3 and parts[0] in res_2d and parts[1] in res_2d and parts[2] in res_2d:
                            win = b['amount'] * X3_PAY
                            
                    b_eval = b.copy()
                    b_eval['win_amount'] = win
                    customer_detailed_results[cust]["bets"].append(b_eval)
                    customer_detailed_results[cust]["total_bet"] += b['total']
                    customer_detailed_results[cust]["total_win"] += win
                    
                    if b['type'] == "Lô":
                        total_lo_profit += ((b['amount'] * LO_REV) - win)
                    else: 
                        total_ncc_revenue += b['total']
                        total_ncc_payout += win

                ncc_profit = total_ncc_revenue - total_ncc_payout
                
                today_str = datetime.now().strftime("%Y-%m-%d")
                history = st.session_state.revenue_history
                found_idx = -1
                for idx, entry in enumerate(history):
                    if entry['date'] == today_str:
                        found_idx = idx
                        break
                
                rev_entry = {"date": today_str, "lo_profit": total_lo_profit}
                if found_idx >= 0:
                    history[found_idx] = rev_entry
                else:
                    history.append(rev_entry)
                
                st.session_state.revenue_history = history
                save_revenue_history(history)
                st.toast("Đã tự động lưu tổng lãi/lỗ mảng Lô vào Tab Doanh Thu!", icon="💾")

                st.markdown("---")
                st.subheader("🏢 Thông Tin Nhà Cung Cấp (NCC)")
                c_n1, c_n2, c_n3 = st.columns(3)
                with c_n1: st.metric("Tổng tiền chuyển NCC", format_vnd(total_ncc_revenue))
                with c_n2: st.metric("Tiền trúng NCC hoàn trả", format_vnd(total_ncc_payout))
                with c_n3: st.metric("Lợi nhuận mảng NCC", format_vnd(ncc_profit))

                st.markdown("---")
                st.subheader("📋 Bảng Công Nợ Chi Tiết")
                
                html_parts = [
                    '<style>',
                    '.debt-table { width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 10px; margin-bottom: 20px; }',
                    '.debt-table th { background-color: #1e293b; color: #f3f4f6; padding: 10px; border: 1px solid #334155; text-align: left; }',
                    '.debt-table td { padding: 8px 10px; border: 1px solid #334155; color: #e2e8f0; background-color: rgba(15, 23, 42, 0.6); }',
                    '</style>',
                    '<table class="debt-table">',
                    '<thead><tr><th>Khách hàng</th><th>Loại cược</th><th>Số đánh</th><th>Mức cược</th><th>Thành tiền</th><th>Trúng thưởng</th></tr></thead>',
                    '<tbody>'
                ]
                
                for cust, data in customer_detailed_results.items():
                    for b in data["bets"]:
                        m_cuoc = f"{b['amount']} điểm" if b['type']=="Lô" else format_vnd(b['amount'])
                        html_parts.append(f'<tr><td><b>{cust}</b></td><td>{b["type"]}</td><td>{b["number"]}</td><td>{m_cuoc}</td><td>{format_vnd(b["total"])}</td><td>{format_vnd(b["win_amount"])}</td></tr>')
                    
                    net = data["total_bet"] - data["total_win"]
                    if net > 0:
                        status_str = f"🟢 Khách phải TRẢ: {format_vnd(net)}"
                        row_bg = "rgba(6, 78, 59, 0.7)"
                    elif net < 0:
                        status_str = f"🔴 Chủ phải TRẢ KHÁCH: {format_vnd(abs(net))}"
                        row_bg = "rgba(127, 29, 29, 0.7)"
                    else:
                        status_str = "⚪ Hòa vốn (0 đ)"
                        row_bg = "rgba(30, 41, 59, 0.7)"
                    
                    summary_text = f"Tổng cược: {format_vnd(data['total_bet'])} | Tổng trúng: {format_vnd(data['total_win'])} | {status_str}"
                    html_parts.append(f'<tr style="background-color: {row_bg}; font-weight: bold;"><td colspan="6" style="text-align: right; padding: 12px; color: #fff;">👤 {cust} — {summary_text}</td></tr>')
                
                html_parts.append('</tbody></table>')
                st.markdown("".join(html_parts), unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("📈 Tổng Kết Lợi Nhuận Thực Tế")
                total_master_profit = total_lo_profit + ncc_profit
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("Lãi/Lỗ mảng Lô", format_vnd(total_lo_profit))
                with c2: st.metric("Lãi/Lỗ mảng NCC", format_vnd(ncc_profit))
                with c3: st.metric("Tổng lợi nhuận thực tế", format_vnd(total_master_profit), delta=format_vnd(total_master_profit))

with tab4:
    st.subheader("💰 Quản Lý Doanh Thu & Lợi Nhuận Mảng Lô Theo Ngày")
    
    if not st.session_state.revenue_history:
        st.info("Chưa có lịch sử doanh thu lô nào được ghi nhận. Dữ liệu sẽ tự động lưu khi bạn thực hiện 'Đối Chiếu & Tính Toán' ở Tab 3.")
    else:
        sorted_history = sorted(st.session_state.revenue_history, key=lambda x: x['date'], reverse=True)
        
        col_filter, col_spacer = st.columns([1, 2])
        with col_filter:
            cycle_option = st.selectbox("Chọn chu kỳ thống kê tổng lãi/lỗ:", ["7 ngày gần nhất", "10 ngày gần nhất", "30 ngày gần nhất", "Tất cả thời gian"])
        
        df_rev = pd.DataFrame(sorted_history)
        df_rev['date_dt'] = pd.to_datetime(df_rev['date'])
        df_rev = df_rev.sort_values('date_dt', ascending=False)
        
        limit_days = None
        if "7" in cycle_option:
            limit_days = 7
        elif "10" in cycle_option:
            limit_days = 10
        elif "30" in cycle_option:
            limit_days = 30
            
        if limit_days:
            max_date = df_rev['date_dt'].max()
            min_date = max_date - pd.Timedelta(days=limit_days - 1)
            df_filtered = df_rev[(df_rev['date_dt'] >= min_date)]
        else:
            df_filtered = df_rev
            
        total_cycle_profit = df_filtered['lo_profit'].sum()
        
        st.markdown("---")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(f"Tổng Lãi/Lỗ trong ({cycle_option})", format_vnd(total_cycle_profit), delta=format_vnd(total_cycle_profit))
        with col_m2:
            st.metric("Tổng Số Ngày Ghi Nhận", f"{len(df_filtered)} ngày")
            
        st.markdown("---")
        st.subheader("📊 Bảng Chi Tiết Lãi/Lỗ Mảng Lô Theo Từng Ngày")
        
        display_df = df_filtered[['date', 'lo_profit']].copy()
        display_df.columns = ["Ngày", "Lãi/Lỗ Mảng Lô"]
        display_df["Lãi/Lỗ Mảng Lô"] = display_df["Lãi/Lỗ Mảng Lô"].apply(format_vnd)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        if st.button("🗑️ Xóa Toàn Bộ Lịch Sử Doanh Thu Tích Lũy"):
            st.session_state.revenue_history = []
            if os.path.exists(REV_FILE):
                os.remove(REV_FILE)
            st.toast("Đã xóa toàn bộ lịch sử doanh thu tích lũy!", icon="🗑️")
            st.rerun()
