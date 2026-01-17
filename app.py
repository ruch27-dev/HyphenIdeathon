import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import time

# --- 1. SETUP (MUST BE FIRST) ---
st.set_page_config(page_title="MediTriage Pro", page_icon="🩺", layout="wide")

# PASTE KEY HERE
GOOGLE_API_KEY = "PASTE_YOUR_KEY_HERE"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- 2. SAFE STYLING (Works in Light & Dark Mode) ---
st.markdown("""
<style>
    /* ANIMATION */
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* CARDS */
    .st-card {
        animation: slideIn 0.8s ease-out;
        background-color: #ffffff;
        color: #333333;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* DARK MODE OVERRIDE FOR CARDS */
    @media (prefers-color-scheme: dark) {
        .st-card {
            background-color: #262730;
            color: #ffffff;
            border: 1px solid #4a4a4a;
        }
    }

    /* BADGES */
    .badge-red { background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-green { background-color: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
    .badge-blue { background-color: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 6px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE MANAGEMENT ---
if "history" not in st.session_state:
    st.session_state.history = []
if "current_view" not in st.session_state:
    st.session_state.current_view = None

# --- 4. DISPLAY LOGIC ---
def display_results(symptoms_text, response_text, city_context="Local Area", user_image=None):
    try:
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        col1, col2 = st.columns([1, 1], gap="medium")

        # --- LEFT: DIAGNOSIS ---
        with col1:
            st.markdown(f"""
            <div class="st-card" style="border-left: 5px solid #ef4444;">
                <h3>🧬 Analysis Results</h3>
                <p><i>Input: {symptoms_text}</i></p>
            """, unsafe_allow_html=True)
            
            if user_image:
                st.image(user_image, caption="Analyzed Scan", use_column_width=True)
                
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            
            for condition in data.get("differential_diagnosis", []):
                st.markdown(f"""
                <div style="margin-bottom: 12px;">
                    <span class="badge-red">{condition['match_percentage']}% Match</span>
                    <strong style="font-size: 1.1em; margin-left: 8px;">{condition['name']}</strong>
                    <p style="font-size: 0.9em; margin-top: 4px;">{condition['reasoning']}</p>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- RIGHT: TREATMENT ---
        with col2:
            st.markdown(f"""
            <div class="st-card" style="border-left: 5px solid #22c55e;">
                <h3>💊 Treatment Plan</h3>
                <p><strong>Consult:</strong> <span class="badge-blue">{data.get('specialist_type', 'Doctor')}</span></p>
            """, unsafe_allow_html=True)
            
            st.markdown("**Medicines & Costs:**")
            for med in data.get("medicines", []):
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px; background: rgba(0,0,0,0.05); padding: 5px; border-radius: 5px;">
                    <span>{med['name']} ({med['dosage']})</span>
                    <span class="badge-green">{med['estimated_cost']}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>**Immediate Actions:**", unsafe_allow_html=True)
            for action in data.get("actions", []):
                st.markdown(f"✅ {action}")
            st.markdown("</div>", unsafe_allow_html=True)

        # --- BOTTOM: HOSPITALS ---
        st.markdown(f"""
        <div class="st-card" style="border-top: 5px solid #3b82f6; text-align: center;">
            <h3>🏥 Recommended Hospitals in {city_context}</h3>
        </div>
        """, unsafe_allow_html=True)

        h_cols = st.columns(3)
        hospitals = data.get("hospitals", [])
        
        for i, hospital in enumerate(hospitals[:3]):
            with h_cols[i]:
                st.markdown(f"""
                <div class="st-card" style="text-align: center; height: 100%;">
                    <div style="font-size: 2em;">🏥</div>
                    <h4>{hospital['name']}</h4>
                    <p style="font-size: 0.85em; opacity: 0.8;">{hospital['location']}</p>
                    <span class="badge-blue">{hospital['estimated_cost']}</span>
                </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error reading data: {e}")
        st.code(response_text)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🗂️ History")
    if st.button("➕ New Consultation", type="primary", use_container_width=True):
        st.session_state.current_view = None
        st.rerun()
    st.divider()
    for i, entry in enumerate(reversed(st.session_state.history)):
        if st.button(f"Case #{len(st.session_state.history)-i}", key=f"h_{i}", use_container_width=True):
            st.session_state.current_view = entry
            st.rerun()

# --- 6. MAIN PAGE ---
if st.session_state.current_view:
    st.title("📂 Archived Record")
    if st.button("← Back"):
        st.session_state.current_view = None
        st.rerun()
    entry = st.session_state.current_view
    # Handle image retrieval if saved (simplified for session state)
    display_results(entry['symptoms'], entry['result'], user_image=entry.get('image'))

else:
    st.title("🩺 Smart MediTriage")
    st.caption("AI-Powered Diagnosis (Text + Imaging) & Cost Estimator")

    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        symptoms = st.text_area("Symptoms", height=150, placeholder="Describe symptoms or leave blank if uploading a scan...")
        city = st.text_input("City", placeholder="Enter City (e.g. Mumbai)")
        
    with c2:
        st.markdown("### 📸 Upload Medical Scan")
        st.caption("Supported: X-Ray, MRI, CT, Skin Lesions")
        uploaded_file = st.file_uploader("Drop image here", type=["jpg", "png", "jpeg"])
        user_image = None
        if uploaded_file:
            user_image = Image.open(uploaded_file)
            st.image(user_image, caption="Preview", width=200)

    if st.button("Run Analysis 🚀", type="primary", use_container_width=True):
        if not symptoms and not uploaded_file:
            st.warning("⚠️ Please provide either Symptoms OR an Image.")
        elif not city:
            st.warning("⚠️ Please enter City.")
        else:
            with st.spinner("Analyzing Scan & Symptoms..."):
                try:
                    # --- REAL API CALL ---
                    prompt = f"""
                    Act as an expert Medical AI. Location: {city}.
                    Analyze the attached image (if any) and symptoms: {symptoms}.
                    Output ONLY valid JSON:
                    {{
                        "differential_diagnosis": [{{"name": "Condition", "match_percentage": "80", "reasoning": "Reason"}}],
                        "specialist_type": "Doctor Type",
                        "medicines": [{{"name": "Med", "dosage": "Dose", "estimated_cost": "$10"}}],
                        "actions": ["Action1"],
                        "hospitals": [{{"name": "Hospital", "location": "Loc", "estimated_cost": "$50"}}]
                    }}
                    """
                    
                    inputs = [prompt]
                    if user_image: inputs.append(user_image)
                    
                    response = model.generate_content(inputs)
                    result_text = response.text
                
                except Exception:
                    # --- MOCK DATA FALLBACK ---
                    time.sleep(1)
                    st.warning("⚠️ API Limit/Error - Using Demo Data")
                    result_text = """
                    {
                        "differential_diagnosis": [
                            {"name": "Fracture (Demo Scan)", "match_percentage": "95", "reasoning": "Visible hairline fracture in X-Ray analysis."},
                            {"name": "Bone Bruise", "match_percentage": "40", "reasoning": "Similar pain profile but no break visible."}
                        ],
                        "specialist_type": "Orthopedic Surgeon",
                        "medicines": [
                            {"name": "Ibuprofen", "dosage": "400mg for pain", "estimated_cost": "₹40"},
                            {"name": "Calcium Supplement", "dosage": "1 daily", "estimated_cost": "₹120"}
                        ],
                        "actions": ["Immobilize area", "Apply ice pack"],
                        "hospitals": [
                            {"name": "City Ortho Center", "location": "Downtown", "estimated_cost": "₹1500"},
                            {"name": "General Hospital", "location": "West Wing", "estimated_cost": "₹600"},
                            {"name": "Trauma Care", "location": "Highway Rd", "estimated_cost": "₹900"}
                        ]
                    }
                    """
                
                # Save & Show
                st.session_state.history.append({"symptoms": symptoms if symptoms else "Image Analysis", "result": result_text, "image": user_image})
                display_results(symptoms if symptoms else "Image Analysis", result_text, city, user_image)