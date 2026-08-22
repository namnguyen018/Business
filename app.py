import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Cấu hình file lưu trữ lịch sử doanh thu
REV_FILE = "revenue_history.json"

def load_revenue_history():
    if os.path.exists(REV_FILE):
        try:
            with open(REV_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_revenue_history(history):
    with open(REV_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def format_vnd(amount):
    try:
        return f"{int(amount):,}".replace(",", ".") + " VNĐ"
    except:
        return "0 VNĐ"

# Khởi tạo session_state cho lịch sử
if "revenue_history" not in st.session_state:
    st.session_state.revenue_history = load_revenue_history()

st.set_page_config(page_title="Quản Lý Đối Chiếu Doanh Thu", layout="wide")

st.title("📊 Hệ Thống Quản Lý & Đối Chiếu Doanh Thu")

# Tạo cấu trúc các Tab
tab1, tab2, tab3, tab4 = st.tabs(["Tab 1", "Tab 2", "Tab 3 (Đối Chiếu)", "Tab 4 (Doanh Thu)"])

# ==================== TAB 1 ====================
with tab1:
    st.header("Tab 1: Tổng Quan")
    st.write("Khu vực hiển thị thông tin tổng quan hoặc cấu hình ban đầu.")

# ==================== TAB 2 ====================
with tab2:
    st.header("Tab 2: Xử Lý Dữ Liệu")
    st.write("Khu vực nhập liệu hoặc xử lý các bước trung gian.")

# ==================== TAB 3 ====================
with tab3:
    st.header("Tab 3: Chạy Đối Chiếu & Tính Toán")
    st.write("Nhấn nút bên dưới để hệ thống thực hiện đối chiếu, tính toán và tự động lưu/cập nhật kết quả vào lịch sử các ngày.")
    
    with st.form("reconciliation_form"):
        st.subheader("Tham số đối chiếu")
        calc_date = st.date_input("Ngày đối chiếu", value=datetime.now())
        input_calculated_profit = st.number_input("Số tiền Lãi/Lỗ mảng Lô tính được (VNĐ)", value=1500000, step=100000, format="%d")
        
        submit_run = st.form_submit_button("🚀 Chạy Đối Chiếu & Tính Toán")
        if submit_run:
            date_str = calc_date.strftime("%Y-%m-%d")
            history = st.session_state.revenue_history
            
            # Kiểm tra xem ngày đó đã tồn tại trong lịch sử chưa (để cập nhật hoặc thêm mới)
            found_idx = -1
            for idx, entry in enumerate(history):
                if entry['date'] == date_str:
                    found_idx = idx
                    break
                    
            new_entry = {"date": date_str, "lo_profit": float(input_calculated_profit)}
            if found_idx >= 0:
                history[found_idx] = new_entry
                st.success(f"Đã cập nhật lại dữ liệu cho ngày {date_str}!")
            else:
                history.append(new_entry)
                st.success(f"Đã thêm mới dữ liệu cho ngày {date_str} vào danh sách!")
                
            # Lưu vào session state và ghi file JSON
            st.session_state.revenue_history = history
            save_revenue_history(history)

# ==================== TAB 4 ====================
with tab4:
    st.subheader("💰 Quản Lý Doanh Thu & Lợi Nhuận Mảng Lô Theo Ngày")
    
    # --- PHẦN BỔ SUNG: CẬP NHẬT/NHẬP LIỆU DỮ LIỆU NGÀY CŨ THỦ CÔNG ---
    with st.expander("🛠️ Cập nhật hoặc thêm dữ liệu doanh thu ngày cũ thủ công"):
        with st.form("update_old_revenue_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                input_date = st.date_input("Chọn ngày cần cập nhật", value=datetime.now())
            with col_f2:
                input_profit = st.number_input("Số tiền Lãi/Lỗ mảng Lô (VNĐ)", value=0, step=100000, format="%d")
            
            submit_update = st.form_submit_button("💾 Lưu / Cập Nhật Dữ Liệu Ngày Này")
            if submit_update:
                date_str = input_date.strftime("%Y-%m-%d")
                history = st.session_state.revenue_history
                
                found_idx = -1
                for idx, entry in enumerate(history):
                    if entry['date'] == date_str:
                        found_idx = idx
                        break
                
                new_entry = {"date": date_str, "lo_profit": float(input_profit)}
                if found_idx >= 0:
                    history[found_idx] = new_entry
                    st.success(f"Đã cập nhật lại doanh thu cho ngày {date_str}!")
                else:
                    history.append(new_entry)
                    st.success(f"Đã thêm mới doanh thu cho ngày {date_str}!")
                
                st.session_state.revenue_history = history
                save_revenue_history(history)
                st.rerun()

    if not st.session_state.revenue_history:
        st.info("Chưa có lịch sử doanh thu lô nào được ghi nhận. Dữ liệu sẽ tự động lưu khi bạn thực hiện 'Đối Chiếu & Tính Toán' ở Tab 3 hoặc dùng khung cập nhật thủ công ở trên.")
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
