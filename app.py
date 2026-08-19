import streamlit as st
import re
import pandas as pd
import requests

st.set_page_config(page_title="Hệ Thống Quản Lý Lô Đề Master", layout="wide")

if 'bets' not in st.session_state: 
    st.session_state.bets = []

# Cấu hình tỷ lệ tài chính
LO_REV = 22500  
LO_PAY = 80000  
DE_PAY = 70     
BC_PAY = 400    
X2_PAY = 10     
X3_PAY = 40     

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
        # 0. Dạng chuỗi 3 chữ số liên tiếp kèm tiền cuối (VD: 050 191 40k hoặc 818 959 636 909 20k)
        m_group_3d = re.search(r'^((?:\d{3}\s*)+)(\d+)(k)$', part)
        if m_group_3d:
            nums_str = m_group_3d.group(1)
            amt = int(m_group_3d.group(2)) * 1000
            three_digit_nums = re.findall(r'\d{3}', nums_str)
            for t_num in three_digit_nums:
                d1 = t_num[:2]      # 2 chữ số đầu (VD: '05' từ '050')
                d2 = d1[::-1]       # Lật ngược lại (VD: '50')
                for n in set([d1, d2]):
                    st.session_state.bets.append({"customer": customer_name, "type": "Đề", "number": n, "amount": amt, "total": amt})
                    added_count += 1
            continue

        # 1. 3 Càng đơn lẻ
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
st.title("📊 Hệ Thống Quản Lý Lô Đề Master")

col1, col2 = st.columns([1, 1])

with col1:
    name = st.text_input("Tên Khách Hàng", value="đạt")
    msg = st.text_area("Tin nhắn cược", height=120, placeholder="VD: 050 191 40k\n818 959 636 909 20k")
    if st.button("Cập Nhật Vào Bảng", type="primary"):
        if msg.strip():
            count = parse_and_add_bets(name, msg)
            if count > 0: st.success(f"Đã ghi nhận thành công {count} mục cược!")
            else: st.warning("Không nhận diện được cú pháp!")
    if st.button("Làm mới dữ liệu"): st.session_state.bets = []

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
            disp = f"{vol} điểm" if v["Loại"] == "Lô" else format_vnd(vol)
            exp_list.append({"Loại": v["Loại"], "Số": v["Số"], "Tổng nhận": disp, "Cảnh báo": "⚠️ Lớn" if vol > 50 else "✅ An toàn"})
        st.dataframe(pd.DataFrame(exp_list), use_container_width=True)

st.markdown("---")
st.header("📜 Lịch Sử Cược Chi Tiết")
if st.session_state.bets:
    df_bets = [{"Khách hàng": b['customer'], "Loại": b['type'], "Số đánh": b['number'], "Mức cược": f"{b['amount']} điểm" if b['type']=="Lô" else format_vnd(b['amount']), "Thành tiền": format_vnd(b['total'])} for b in st.session_state.bets]
    st.dataframe(pd.DataFrame(df_bets), use_container_width=True)

# --- ĐỐI CHIẾU TỰ ĐỘNG API ---
st.markdown("---")
st.header("🏁 Đối Chiếu Kết Quả Xổ Số Tự Động (API JSON)")

api_url = "https://api-xsmb-today.onrender.com/api/v1"
use_api = st.checkbox("Sử dụng dữ liệu tự động từ API trực tuyến", value=True)
manual_res = st.text_input("Hoặc dán kết quả thủ công (phòng hờ API lỗi)", value="")

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
                
                # Quét an toàn toàn bộ các giải trả về từ API
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
                st.success(f"Đã lấy dữ liệu API thành công! Số Đề (2 số cuối giải ĐB): {so_de}")
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
        fin = {}
        total_lo_profit = 0
        total_ncc_revenue = 0
        total_ncc_payout = 0
        
        for b in st.session_state.bets:
            cust = b['customer']
            if cust not in fin: fin[cust] = {"bet": 0, "win": 0}
            fin[cust]["bet"] += b['total']
            
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
                    
            fin[cust]["win"] += win
            
            if b['type'] == "Lô":
                total_lo_profit += ((b['amount'] * LO_REV) - win)
            else: 
                total_ncc_revenue += b['total']
                total_ncc_payout += win

        ncc_profit = total_ncc_revenue - total_ncc_payout
        st.subheader("🏢 Thông Tin Chuyển Nhà Cung Cấp (NCC)")
        c_n1, c_n2, c_n3 = st.columns(3)
        with c_n1: st.metric("Tổng tiền chuyển NCC", format_vnd(total_ncc_revenue))
        with c_n2: st.metric("Tiền trúng NCC hoàn trả", format_vnd(total_ncc_payout))
        with c_n3: st.metric("Lợi nhuận mảng NCC", format_vnd(ncc_profit))

        st.subheader("📋 Bảng Công Nợ Chi Tiết Khách Cuối Ngày")
        debt_list = []
        for c, v in fin.items():
            net = v['bet'] - v['win']
            status = f"🟢 Khách phải TRẢ: {format_vnd(net)}" if net > 0 else f"🔴 Chủ phải TRẢ KHÁCH: {format_vnd(abs(net))}"
            if net == 0: status = "⚪ Hòa vốn (0 đ)"
            debt_list.append({"Khách hàng": c, "Tổng cược": format_vnd(v['bet']), "Tổng trúng": format_vnd(v['win']), "Trạng thái": status})
        st.dataframe(pd.DataFrame(debt_list), use_container_width=True)
        
        st.divider()
        st.subheader("📈 Tổng Kết Lợi Nhuận Thực Tế Chủ Lô")
        total_master_profit = total_lo_profit + ncc_profit
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Lãi/Lỗ mảng Lô", format_vnd(total_lo_profit))
        with c2: st.metric("Lãi/Lỗ mảng NCC", format_vnd(ncc_profit))
        with c3: st.metric("Tổng lãi/lỗ thực tế", format_vnd(total_master_profit), delta=format_vnd(total_master_profit))
