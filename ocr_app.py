import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Kratingdaeng AI Scanner", page_icon="⚡", layout="wide") 
# ปรับ layout="wide" เพื่อให้มีพื้นที่แสดงรูปแนวนอนมากขึ้น

# --- เตรียมหน่วยความจำ (Session State) ---
if 'scan_results' not in st.session_state:
    st.session_state['scan_results'] = {}

# --- ส่วนจัดการ API Key (แบบปลอดภัย) ---
with st.sidebar:
    st.header("🔑 ตั้งค่าระบบ")
    st.success("Model: gemini-3-flash-preview")
    
    api_key = None
    
    # 1. เช็คใน App Settings
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.info("✅ เชื่อมต่อ API Key แล้ว")
    else:
        # 2. กรอกเอง
        api_key_input = st.text_input("ใส่ Google API Key", type="password")
        api_key = api_key_input
        
        if not api_key:
            st.warning("⚠️ กรุณากรอก API Key")
    
    if st.button("ล้างค่าทั้งหมด (Reset)"):
        st.session_state['scan_results'] = {}
        st.rerun()

# --- ฟังก์ชันอ่านภาพด้วย Gemini ---
def gemini_vision_scan(image_pil, key):
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-pro-latest')

        prompt = """
        You are an advanced AI reading a serial code on a bottle cap.
        The text is in a DOT-MATRIX font.
        
        YOUR TASK: Extract the exactly 12-character alphanumeric code.

        CORRECTION RULES:
        1. '7' vs 'Z': In this font, '7' has a curved top like 'Z'. Unless clearly 'Z', interpret as '7'.
        2. '6' vs 'G': '6' often looks like 'G'. Check closely.
        3. 'W' vs 'I': 'W' is wide, do not mistake for 'I'.
        
        OUTPUT FORMAT:
        - Exact 12 characters (A-Z, 0-9).
        - Ignore "P Bev", "21", "HDPE".
        - Output ONLY the code.
        """
        
        response = model.generate_content([prompt, image_pil])
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# --- ส่วนแสดงผล UI ---
try:
    st.image("banner.png", width=150)
except:
    pass 

st.title("⚡ Kratingdaeng AI Scanner")
st.caption("Mode: Batch Processing (แสดงผลแบบชัดเจน)") 
st.write("---")

if not api_key:
    st.info("👈 กรุณาตั้งค่า API Key เพื่อเริ่มใช้งาน")
else:
    tab1, tab2 = st.tabs(["📂 อัปโหลดหลายรูป (Batch)", "📷 ถ่ายรูป"])

    # --- TAB 1: Upload แบบ Batch ---
    with tab1:
        uploaded_files = st.file_uploader(
            "เลือกรูปภาพ (กด Ctrl ค้างเพื่อเลือกหลายรูป)...", 
            type=["jpg", "png", "jpeg"], 
            accept_multiple_files=True
        )

        if uploaded_files:
            st.info(f"คุณเลือกไว้ทั้งหมด {len(uploaded_files)} รูป")
            
            if st.button("🚀 เริ่มสแกนรูปทั้งหมด", type="primary"):
                progress_bar = st.progress(0)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                    
                    if file_id not in st.session_state['scan_results']:
                        image = Image.open(uploaded_file)
                        code = gemini_vision_scan(image, api_key)
                        st.session_state['scan_results'][file_id] = code
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success("✅ สแกนครบแล้ว!")

            st.markdown("---")
            st.subheader("📝 ตรวจสอบผลลัพธ์:")

            # วนลูปแสดงผล (ปรับปรุงใหม่ให้รูปใหญ่ขึ้น)
            for i, uploaded_file in enumerate(uploaded_files):
                file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                image = Image.open(uploaded_file)
                
                # ใช้ Container เพื่อสร้างกรอบให้แต่ละรายการดูเป็นสัดส่วน
                with st.container():
                    # ปรับสัดส่วนเป็น 1:1 (รูปครึ่งนึง ผลลัพธ์ครึ่งนึง) เพื่อให้รูปใหญ่สะใจ
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # แสดงรูปใหญ่ เต็มความกว้างคอลัมน์
                        st.image(image, use_column_width=True, caption=f"รูปที่ {i+1}: {uploaded_file.name}")
                        # เพิ่มปุ่มขยายรูปดูต้นฉบับ
                        with st.expander(f"🔎 ซูมดูรูปต้นฉบับ ({uploaded_file.name})"):
                            st.image(image, use_column_width=True)
                    
                    with col2:
                        st.markdown(f"**ผลลัพธ์รูปที่ {i+1}:**")
                        if file_id in st.session_state['scan_results']:
                            code = st.session_state['scan_results'][file_id]
                            
                            if "Error" in code:
                                st.error(code)
                            else:
                                clean_code = code.replace(" ", "").replace("\n", "")
                                
                                # แสดง Code ตัวใหญ่ๆ
                                st.code(clean_code, language=None)
                                
                                # ตรวจสอบความยาว
                                if len(clean_code) == 12:
                                    st.success("✅ ครบ 12 หลัก")
                                else:
                                    st.warning(f"⚠️ อ่านได้ {len(clean_code)} หลัก")
                        else:
                            st.info("⏳ รอการสแกน...")
                
                # เส้นคั่นระหว่างรายการ
                st.divider()

    # --- TAB 2: Camera ---
    with tab2:
        camera_image = st.camera_input("ถ่ายรูป")
        if camera_image is not None:
            image = Image.open(camera_image)
            
            # แบ่งคอลัมน์เหมือนกันเพื่อความชัดเจน
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(image, use_column_width=True, caption="รูปที่ถ่าย")
            
            with col2:
                with st.spinner('AI กำลังอ่าน...'):
                    code = gemini_vision_scan(image, api_key)
                    if "Error" in code:
                        st.error(code)
                    else:
                        clean_code = code.replace(" ", "").replace("\n", "")
                        st.markdown("**ผลลัพธ์:**")
                        st.code(clean_code, language=None)
                        if len(clean_code) == 12:
                            st.success("✅ ครบ 12 หลัก")
                        else:
                            st.warning(f"⚠️ อ่านได้ {len(clean_code)} หลัก")

