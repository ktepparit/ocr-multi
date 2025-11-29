import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Kratingdaeng AI Scanner", page_icon="⚡", layout="centered")

# --- เตรียมหน่วยความจำ (Session State) ---
if 'scan_results' not in st.session_state:
    st.session_state['scan_results'] = {}

# --- ส่วนจัดการ API Key (แบบปลอดภัย) ---
with st.sidebar:
    st.header("🔑 ตั้งค่าระบบ")
    st.success("Model: gemini-pro-latest (Batch Mode)")
    
    api_key = None
    
    # 1. เช็คใน App Settings (Secrets) ก่อน
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ เชื่อมต่อ API Key จาก App Settings แล้ว")
    else:
        # 2. ถ้าไม่มีใน Settings ให้แสดงช่องกรอก
        api_key = st.text_input("ใส่ Google API Key", type="password")
        if not api_key:
            st.warning("⚠️ ไม่พบ API Key ใน Settings กรุณากรอกเอง")
    
    # ปุ่มเคลียร์ค่า
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
    try:
        st.image("banner.png", width=150)
    except:
        pass 
    
# --- ส่วนแสดงผล UI ---
st.title("⚡ Kratingdaeng AI Scanner")
st.caption("Mode: Batch Processing (อ่านหลายรูปพร้อมกัน)") 
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
            
            if st.button("🚀 เริ่มสแกนรูปทั้งหมด (Start Scan)", type="primary"):
                progress_bar = st.progress(0)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                    
                    if file_id not in st.session_state['scan_results']:
                        image = Image.open(uploaded_file)
                        code = gemini_vision_scan(image, api_key)
                        st.session_state['scan_results'][file_id] = code
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success("✅ สแกนครบทุกรูปแล้ว!")

            st.markdown("---")
            st.subheader("📝 ผลลัพธ์:")

            for i, uploaded_file in enumerate(uploaded_files):
                file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                col1, col2 = st.columns([1, 3])
                image = Image.open(uploaded_file)
                
                with col1:
                    st.image(image, width=80, caption=f"Img {i+1}")
                
                with col2:
                    if file_id in st.session_state['scan_results']:
                        code = st.session_state['scan_results'][file_id]
                        if "Error" in code:
                            st.error(code)
                        else:
                            clean_code = code.replace(" ", "").replace("\n", "")
                            st.code(clean_code, language=None)
                            if len(clean_code) == 12:
                                st.caption("✅ ครบ 12 หลัก")
                            else:
                                st.caption(f"⚠️ อ่านได้ {len(clean_code)} หลัก")
                    else:
                        st.info("รอการกดปุ่มสแกน...")
                st.markdown("---")

    # --- TAB 2: Camera ---
    with tab2:
        camera_image = st.camera_input("ถ่ายรูป")
        if camera_image is not None:
            image = Image.open(camera_image)
            with st.spinner('AI กำลังอ่าน...'):
                code = gemini_vision_scan(image, api_key)
                if "Error" in code:
                    st.error(code)
                else:
                    clean_code = code.replace(" ", "").replace("\n", "")
                    st.code(clean_code, language=None)
                    if len(clean_code) == 12:
                        st.caption("✅ ครบ 12 หลัก")
                    else:
                        st.caption(f"⚠️ อ่านได้ {len(clean_code)} หลัก")

