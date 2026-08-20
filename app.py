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
        
        # 1. Dạng nhiều cặp xiên chung tiền trên 1 dòng (VD: Xiên 62-65,26-56 55k)
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

        # 2. Dạng Lô cặp gạch ngang có chung số điểm (VD: 62-65 10đ)
        m_pair_lo = re.match(r'^(\d{2})\s*-\s*(\d{2})\s+(\d+)\s*(đ|diem)?$', line)
        if m_pair_lo:
            n1, n2, pts = m_pair_lo.group(1), m_pair_lo.group(2), int(m_pair_lo.group(3))
            for n in [n1, n2]:
                st.session_state.bets.append({"customer": customer_name, "type": "Lô", "number": n, "amount": pts, "total": pts * LO_REV})
                added_count += 1
            continue

        # 3. Dạng chuỗi 3 chữ số liên tiếp kèm tiền cuối (VD: 050 636 959 525 616 20k đề)
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

        # 4. 3 Càng đơn lẻ
        m3c = re.search(r'3c\s*(\d{3})\s*(\d+)(k)?', line)
        if m3c:
            num, amt = m3c.group(1), int(m3c.group(2))
            if m3c.group(3) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "3 càng", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        # 5. Xiên 2 đơn lẻ
        mx2 = re.search(r'(?:xiên|x2)\s*2?\s+(\d{2})\D+(\d{2})\D*(\d+)(k)?', line)
        if mx2:
            num = f"{mx2.group(1)}-{mx2.group(2)}"
            amt = int(mx2.group(3))
            if mx2.group(4) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Xiên 2", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        # 6. Xiên 3
        mx3 = re.search(r'(?:xiên\s*3|x3)\s+(\d{2})\s+(\d{2})\s+(\d{2})\s*(\d+)(k)?', line)
        if mx3:
            num = f"{mx3.group(1)}-{mx3.group(2)}-{mx3.group(3)}"
            amt = int(mx3.group(4))
            if mx3.group(5) or amt < 1000: amt *= 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Xiên 3", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        # 7. Đề đơn lẻ
        m_de = re.search(r'(?:đề|de)?\s*(\d{2})\s*(\d+)(k)', line)
        if m_de:
            num, amt = m_de.group(1), int(m_de.group(2)) * 1000
            st.session_state.bets.append({"customer": customer_name, "type": "Đề", "number": num, "amount": amt, "total": amt})
            added_count += 1
            continue

        # 8. Lô đơn lẻ hoặc Lô + Đề gộp (VD: 05 10đ)
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

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Hệ Thống Quản Trị Rủi Ro Tài Chính")

col1, col2 = st.columns([1, 1])

with col1:
    name = st.text_input("Tên Khách Hàng", value="đạt")
    msg = st.text_area("Danh mục cược", height=120, placeholder="VD:\nXiên 29 99 100k\n05 10đ\n62-65 10đ\n050 636 959 20k đề")
    if st.button("Cập Nhật Vào Bảng", type="primary"):
        with st.spinner("Đang xử lý dữ liệu..."):
            if msg.strip():
                count = parse_and_add_bets(name, msg)
                if count > 0: st.success(f"Ghi nhận thành công {count} mục!")
                else: st.warning("Cú pháp không hợp lệ!")
            else:
                st.warning("Vui lòng nhập nội dung danh mục cược!")
            
    if st.button("Làm mới/Xóa tất cả dữ liệu"): 
        st.session_state.bets = []
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.success("Đã xóa toàn bộ dữ liệu!")
        st.rerun()

with col2:
    st.header("📈 Bảng Tổng Hợp")
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
st.header("📜 Lịch Sử Cược Chi Tiết & Quản Lý")

if st.session_state.bets:
    total_lo_pts = sum(b['amount'] for b in st.session_state.bets if b['type'] == 'Lô')
    total_lo_money = sum(b['total'] for b in st.session_state.bets if b['type'] == 'Lô')
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Tổng điểm Lô khách đánh", f"{total_lo_pts} điểm")
    with col_m2:
        st.metric("Tổng thành tiền Lô", format_vnd(total_lo_money))
    
    st.markdown("---")
    st.markdown("Bấm vào nút **🗑️** ở dòng tương ứng để xóa mục cược đó.")
    
    # Nhóm dữ liệu theo từng khách hàng
    customers_dict = {}
    for i, b in enumerate(st.session_state.bets):
        cust = b['customer']
        if cust not in customers_dict:
            customers_dict[cust] = []
        customers_dict[cust].append((i, b))
        
    for cust, items in customers_dict.items():
        st.markdown(f"### 👤 Khách hàng: {cust}")
        
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
                st.success("Đã xóa mục cược!")
                st.rerun()
                
        # Dòng tổng tô đậm tách riêng tiền Lô và tiền khác ngoài Lô
        summary_html = f'<div style="background-color: #e6f4ea; padding: 10px; border-radius: 5px; margin-bottom: 25px; font-weight: bold; color: #137333; border: 1px solid #ceead6;">📊 Tổng kết của {cust}: {cust_lo_pts} điểm Lô ({format_vnd(cust_lo_money)}) | Tiền ngoài Lô (Đề/Xiên/...): {format_vnd(cust_other_money)} | Tổng cộng: {format_vnd(cust_lo_money + cust_other_money)}</div>'
        st.markdown(summary_html, unsafe_allow_html=True)

# --- ĐỐI CHIẾU KẾT QUẢ ---
st.markdown("---")
st.header("🏁 Đối chiếu kết quả")

api_url = "https://api-xsmb-today.onrender.com/api/v1"
use_api = st.checkbox("Sử dụng dữ liệu tự động từ API trực tuyến", value=True)
manual_res = st.text_input("Hoặc dán kết quả thủ công (phòng hờ API lỗi)", value="")

if st.button("Chạy Đối Chiếu & Tính Toán"):
    with st.spinner("Đang xử lý đối chiếu kết quả..."):
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
            st.subheader("🏢 Thông Tin Chuyển Nhà Cung Cấp (NCC)")
            c_n1, c_n2, c_n3 = st.columns(3)
            with c_n1: st.metric("Tổng tiền chuyển NCC", format_vnd(total_ncc_revenue))
            with c_n2: st.metric("Tiền trúng NCC hoàn trả", format_vnd(total_ncc_payout))
            with c_n3: st.metric("Lợi nhuận mảng NCC", format_vnd(ncc_profit))

            st.subheader("📋 Bảng Công Nợ Chi Tiết Khách Cuối Ngày")
            
            html_parts = [
                '<style>',
                '.debt-table { width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 10px; margin-bottom: 20px; }',
                '.debt-table th { background-color: #f0f2f6; color: #31333F; padding: 10px; border: 1px solid #d6d6d6; text-align: left; }',
                '.debt-table td { padding: 8px 10px; border: 1px solid #d6d6d6; color: #31333F; }',
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
                    row_bg = "#e6f4ea"
                elif net < 0:
                    status_str = f"🔴 Chủ phải TRẢ KHÁCH: {format_vnd(abs(net))}"
                    row_bg = "#fce8e6"
                else:
                    status_str = "⚪ Hòa vốn (0 đ)"
                    row_bg = "#f1f3f4"
                
                summary_text = f"Tổng cược: {format_vnd(data['total_bet'])} | Tổng trúng: {format_vnd(data['total_win'])} | {status_str}"
                html_parts.append(f'<tr style="background-color: {row_bg}; font-weight: bold;"><td colspan="6" style="text-align: right; padding: 12px; color: #111;">👤 {cust} — {summary_text}</td></tr>')
            
            html_parts.append('</tbody></table>')
            
            final_html_table = "".join(html_parts)
            st.markdown(final_html_table, unsafe_allow_html=True)
            
            st.divider()
            st.subheader("📈 Tổng Kết Lợi Nhuận Thực Tế")
            total_master_profit = total_lo_profit + ncc_profit
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Lãi/Lỗ mảng Lô", format_vnd(total_lo_profit))
            with c2: st.metric("Lãi/Lỗ mảng NCC", format_vnd(ncc_profit))
            with c3: st.metric("Tổng lãi/lỗ thực tế", format_vnd(total_master_profit), delta=format_vnd(total_master_profit))
