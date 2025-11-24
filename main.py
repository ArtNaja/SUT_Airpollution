import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ (Page Config)
st.set_page_config(
    page_title="SUT Air Pollution Monitor",
    page_icon="☁️",
    layout="wide"
)

st.title("☁️ SUT Air Pollution Monitoring System")
st.markdown("ระบบติดตามค่าฝุ่น PM2.5 ภายในมหาวิทยาลัย (Real-time)")

# ---------------------------------------------------------
# 2. เชื่อมต่อ Google Sheets
# ⚠️ สำคัญ: อย่าลืมเปลี่ยน Link ด้านล่างเป็น Link Google Sheets ของคุณเอง
url = "https://docs.google.com/spreadsheets/d/1BTeyr9lM-VgkG0VjSgyThkm90h7Bl1PLg8f2F4xLbnI/edit?gid=0#gid=0"

# สร้าง Connection
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # อ่านข้อมูลจาก Google Sheets (TTL=5 คือดึงใหม่ทุก 5 วินาทีเมื่อโหลดหน้า)
    data = conn.read(spreadsheet=url, ttl=5)
    
    # ---------------------------------------------------------
    # 3. จัดการข้อมูล (Data Cleaning)
    
    # ลบช่องว่างหัวท้ายชื่อคอลัมน์ (เผื่อมีวรรคเกิน)
    data.columns = data.columns.str.strip()
    
    # รวม 'date' และ 'real_time' เป็น datetime object เพื่อใช้พล็อตกราฟ
    # Format: 23/11/2025 และ 0:24:37
    data['datetime'] = pd.to_datetime(
        data['date'].astype(str) + ' ' + data['real_time'].astype(str), 
        dayfirst=True, 
        errors='coerce'
    )
    
    # ลบแถวที่วันที่ผิดปกติ (NaT) และเรียงตามเวลา
    df = data.dropna(subset=['datetime']).sort_values(by='datetime')

    if df.empty:
        st.warning("ไม่พบข้อมูลในตาราง กรุณาตรวจสอบ Google Sheets")
    else:
        # ---------------------------------------------------------
        # 4. ส่วนแสดงผล (Dashboard Layout)
        
        # ดึงค่าล่าสุด (แถวสุดท้าย)
        latest = df.iloc[-1]
        
        # สร้าง Container ด้านบนเพื่อแสดงค่าปัจจุบัน
        with st.container():
            col1, col2, col3, col4 = st.columns(4)
            
            # กำหนดสีตัวเลข (สีแดงถ้าเกิน 50)
            pm25_val = pd.to_numeric(latest['pm2.5'], errors='coerce')
            pm10_val = pd.to_numeric(latest['pm10'], errors='coerce')
            
            delta_color = "inverse" if pm25_val > 50 else "normal"
            
            col1.metric("📦 จุดตรวจวัด", f"{latest['device']}")
            col2.metric("🌫️ PM2.5", f"{pm25_val} µg/m³", delta_color=delta_color)
            col3.metric("🌬️ PM10", f"{pm10_val} µg/m³")
            col4.metric("🕒 อัปเดตล่าสุด", f"{latest['real_time']}")

        st.divider()

        # ---------------------------------------------------------
        # 5. กราฟแสดงผล (Charts)
        
        col_graph1, col_graph2 = st.columns([2, 1])

        with col_graph1:
            st.subheader("📈 แนวโน้มค่าฝุ่น PM2.5 (Timeline)")
            
            # ใช้ Plotly สร้างกราฟเส้น
            fig = px.line(df, x='datetime', y=['pm2.5', 'pm10'], 
                        title='PM2.5 vs PM10 Over Time',
                        labels={'value': 'Concentration (µg/m³)', 'datetime': 'Time'},
                        color_discrete_map={'pm2.5': '#FF4B4B', 'pm10': '#1F77B4'})
            
            st.plotly_chart(fig, use_container_width=True)

        with col_graph2:
            st.subheader("📊 ค่าเฉลี่ยรายอุปกรณ์")
            if 'device' in df.columns:
                # หาค่าเฉลี่ยแยกตาม Device
                avg_by_device = df.groupby('device')[['pm2.5']].mean().reset_index()
                st.bar_chart(avg_by_device, x='device', y='pm2.5', color='#FF4B4B')

        # ---------------------------------------------------------
        # 6. ส่วนแสดงข้อมูลดิบ (Raw Data)
        with st.expander("🔍 ดูข้อมูลดิบทั้งหมด (Raw Data)"):
            st.dataframe(df.sort_values(by='datetime', ascending=False), use_container_width=True)

# ---------------------------------------------------------
# ส่วนนี้คือส่วนที่แก้ไข: เพิ่ม except เพื่อดักจับ Error ให้ถูกต้อง
except Exception as e:
    st.error("⚠️ เกิดข้อผิดพลาดในการดึงข้อมูล")
    st.error(f"Error Details: {e}")
    st.info("""
    คำแนะนำในการแก้ไขเบื้องต้น:
    1. ตรวจสอบว่าใส่ URL ของ Google Sheets ในตัวแปร 'url' ถูกต้องหรือไม่
    2. ตรวจสอบว่า Google Sheets ได้เปิด Share เป็น 'Anyone with the link' -> 'Viewer' หรือไม่
    3. ตรวจสอบชื่อคอลัมน์ในไฟล์ Google Sheets ว่าต้องมี: date, real_time, device, pm2.5, pm10
    """)