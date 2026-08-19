import streamlit as st
import re
import pandas as pd
import requests

st.set_page_config(page_title="Hệ Thống Quản Lý Lô Đề Master", layout="wide")

if 'bets' not in st.session_state: 
    st.session_state.bets = []

# Cấu hình tỷ lệ tài chính
LO_REV = 22500  # Doanh thu thu khách 1 điểm lô
LO_PAY = 80000  # Trả thưởng 1 nháy lô
DE_PAY = 70     # Đề ăn 70
BC_PAY = 400    # 3 càng ăn 400
X2_PAY = 10     # Xiên 2 ăn 10
X3_PAY = 40     # Xiên 3 ăn 40

def format_vnd(val): 
    return f"{val:,.0f}".replace(',', '.') + ' đ'

def parse_and_add_bets(customer_name, message_text):
    raw_parts = []
    for line in message_text.strip().split('\n'):
        parts = line.split(',')
        for p in parts:
            if p.strip():
                raw_parts.append(p.strip().lower())
                
    added_count = 0
    for part in raw_parts:
        # 1. 3 Càng
        m3c = re.search(r'3c\s*(\d{3})\s*(\d+)(k)?', part)
        if m3c:
            num, amt = m3c.group(1), int(m3c.group(2))
            if m3c.group(3) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "3 càng", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        # 2. Xiên 2
        mx2 = re.search(r'x2\s+(\d{2})\s+(\d{2})\s*(\d+)(k)?', part)
        if mx2:
            num = f"{mx2.group(1)}-{mx2.group(2)}"
            amt = int(mx2.group(3))
            if mx2.group(4) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Xiên 2", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        # 3. Xiên 3
        mx3 = re.search(r'x3\s+(\d{2})\s+(\d{2})\s+(\d{2})\s*(\d+)(k)?', part)
        if mx3:
            num = f"{mx3.group(1)}-{mx3.group(2)}-{mx3.group(3)}"
            amt = int(mx3.group(4))
            if mx3.group(5) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Xiên 3", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        # 4. Đề đơn lẻ
        m_de = re.search(r'(?:đề|de)?\s*(\d{2})\s*(\d+)(k)', part)
        if m_de:
            num, amt = m_de.group(1), int(m_de.group(2)) * 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Đề", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        # 5. Lô đơn lẻ hoặc Lô + Đề gộp
        tokens = part.split()
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
    return added_count

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Hệ Thống Quản Lý Lô Đề Master (API Chuẩn JSON)")

col1, col2 = st.columns([1, 1])

with col1:
    name = st.text_input("Tên Khách Hàng", value="đạt")
    msg = st.text_area("Tin nhắn cược (VD: 83 20k, 3c 183 50k\n90 30đ)", height=120)
    if st.button("Cập Nhật Vào Bảng", type="primary"):
        if msg.strip():
            count = parse_and_add_bets(name, msg)
            if count > 0:
                st.success(f"Đã ghi nhận thành công {count} mục cược!")
            else:
                st.warning("Không nhận diện được cú pháp!")
    if st.button("Làm mới dữ liệu"): 
        st.session_state.bets = []

with col2:
    st.header("📈 Bảng Tổng Hợp Exposure & Hedge")
    if st.session_state.bets:
        exp_dict = {}
        for b in st.session_state.bets:
            key = (b['type'], b['number'])
            if key not in exp_dict:
                exp_dict[key] = {"Loại": b['type'], "Số": b['number'], "Tổng khối lượng": 0}
            exp_dict[key]["Tổng khối lượng"] += b['amount']
            
        exp_list = []
        for k, v in exp_dict.items():
            vol = v["Tổng khối lượng"]
            if v["Loại"] == "Lô":
                warn = "⚠️ Ôm Lô lớn (>50đ)" if vol > 50 else "✅ An toàn"
                disp = f"{vol} điểm"
            else:
                warn = "⚠️ Ôm số lớn (>500k)" if vol > 500000 else "✅ An toàn"
                disp = format_vnd(vol)
            exp_list.append({"Loại": v["Loại"], "Số": v["Số"], "Tổng nhận": disp, "Cảnh báo Exposure": warn})
            
        st.dataframe(pd.DataFrame(exp_list), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu tổng hợp.")

# --- BẢNG CHI TIẾT LỊCH SỬ CƯỢC ---
st.markdown("---")
st.header("📜 Lịch Sử Cược & Chi Tiết Từng Khách")
if st.session_state.bets:
    df_bets = []
    for b in st.session_state.bets:
        unit_str = f"{b['amount']} điểm" if b['type'] == "Lô" else format_vnd(b['amount'])
        df_bets.append({
            "Khách hàng": b['customer'],
            "Loại": b['type'],
            "Số đánh": b['number'],
            "Mức cược gốc": unit_str,
            "Thành tiền": format_vnd(b['total'])
        })
    st.dataframe(pd.DataFrame(df_bets), use_container_width=True)
else:
    st.info("Chưa có dữ liệu cược.")

# --- ĐỐI CHIẾU KẾT QUẢ TỪ API CHUẨN JSON ---
st.markdown("---")
st.header("🏁 Đối Chiếu Kết Quả Xổ Số Tự Động (API JSON)")

api_url = "https://api-xsmb-today.onrender.com/api/v1"
use_api = st.checkbox("Sử dụng dữ liệu tự động từ API kết quả trực tuyến", value=True)
manual_res = st.text_input("Hoặc dán kết quả thủ công dạng text (nếu API lỗi)", value="")

if st.button("Chạy Đối Chiếu & Tính Toán Tài Chính"):
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
                
                # 1. Lấy chuẩn Giải Đặc Biệt cho Đề và 3 Càng
                db_list = results_dict.get("ĐB", [])
                if db_list:
                    giai_db = db_list[0]
                    so_de = giai_db[-2:]
                    so_3c = giai_db[-3:]
                
                # 2. Gom tất cả số từ các giải để làm mảng đối chiếu Lô và Xiên
                for prize_name, prize_values in results_dict.items():
                    for val in prize_values:
                        res_2d.append(val[-2:])
                
                success_load = True
                st.success(f"Đã lấy dữ liệu chuẩn từ API! Giải ĐB là: {db_list[0] if db_list else 'Không rõ'}")
            else:
                st.warning("API phản hồi lỗi, hệ thống chuyển sang dữ liệu thủ công.")
        except Exception as e:
            st.error(f"Lỗi kết nối API: {e}")

    # Nếu không dùng API hoặc API lỗi, fallback về nhập thủ công
    if not success_load and manual_res.strip():
        all_nums = re.findall(r'\d{2,}', manual_res)
        res_2d = [n[-2:] for n in all_nums]
        if res_2d:
            so_de = res_2d[0]
            so_3c = manual_res[-3:] # Lấy tạm 3 số cuối nếu nhập tay
            success_load = True

    if not success_load or not res_2d:
        st.warning("Chưa có dữ liệu kết quả hợp lệ để đối chiếu. Vui lòng kiểm tra lại kết nối API hoặc nhập thủ công.")
    else:
        fin = {}
        total_lo_profit = 0
        total_ncc_revenue = 0
        total_ncc_payout = 0
        
        for b in st.session_state.bets:
            cust = b['customer']
            if cust not in fin: 
                fin[cust] = {"bet": 0, "win": 0}
            fin[cust]["bet"] += b['total']
            
            win = 0
            if b['type'] == "Lô":
                hits = res_2d.count(b['number'])
                win = hits * b['amount'] * LO_PAY
            elif b['type'] == "Đề":
                if b['number'] == so_de:
                    win = b['amount'] * DE_PAY
            elif b['type'] == "3 càng":
                if b['number'] == so_3c:
                    win = b['amount'] * BC_PAY
            elif b['type'] == "Xiên 2":
                parts = b['number'].split('-')
                if len(parts) == 2 and parts[0] in res_2d and parts[1] in res_2d:
                    win = b['amount'] * X2_PAY
            elif b['type'] == "Xiên 3":
                parts = b['number'].split('-')
                if len(parts) == 3 and parts[0] in res_2d and parts[1] in res_2d and parts[2] in res_2d:
                    win = b['amount'] * X3_PAY
                    
            fin[cust]["win"] += win
            
            # Phân định tài chính Chủ & NCC
            if b['type'] == "Lô":
                total_lo_profit += ((b['amount'] * LO_REV) - win)
            else: 
                total_ncc_revenue += b['total']
                total_ncc_payout += win

        # Hiển thị thông tin NCC
        ncc_profit = total_ncc_revenue - total_ncc_payout
        st.subheader("🏢 Thông Tin Chuyển Nhà Cung Cấp (NCC)")
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            st.metric("Tổng tiền chuyển NCC (Đề/3c/Xiên)", format_vnd(total_ncc_revenue))
        with col_n2:
            st.metric("Tiền trúng NCC hoàn trả", format_vnd(total_ncc_payout))
        with col_n3:
            st.metric("Lợi nhuận mảng chuyển NCC", format_vnd(ncc_profit))

        # Hiển thị công nợ khách
        st.subheader("📋 Bảng Công Nợ Chi Tiết Khách Cuối Ngày")
        debt_list = []
        for c, v in fin.items():
            net = v['bet'] - v['win']
            status = f"🟢 Khách phải TRẢ: {format_vnd(net)}" if net > 0 else f"🔴 Chủ phải TRẢ KHÁCH: {format_vnd(abs(net))}"
            if net == 0: status = "⚪ Hòa vốn (0 đ)"
            debt_list.append({
                "Khách hàng": c,
                "Tổng cược": format_vnd(v['bet']),
                "Tổng trúng": format_vnd(v['win']),
                "Trạng thái": status
            })
        st.dataframe(pd.DataFrame(debt_list), use_container_width=True)
        
        # Tổng kết lãi lỗ chủ lô
        st.divider()
        st.subheader("📈 Tổng Kết Lợi Nhuận Thực Tế Chủ Lô")
        total_master_profit = total_lo_profit + ncc_profit
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Lãi/Lỗ mảng Lô (Ôm)", format_vnd(total_lo_profit))
        with c2:
            st.metric("Lãi/Lỗ mảng NCC (Đề/3c/Xiên)", format_vnd(ncc_profit))
        with c3:
            st.metric("Tổng lãi/lỗ thực tế", format_vnd(total_master_profit), delta=format_vnd(total_master_profit))
