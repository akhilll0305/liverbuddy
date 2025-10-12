import streamlit as st
from datetime import datetime
import pandas as pd
import time

# At the top of main.py, change this:
try:
    from firebase import init_firebase, login_user, register_user, logout_user
    from gemini_helper import get_ai_helper, HealthPrompts  # FIXED: Changed from openai_models
    from medical_validation import MedicalAIValidator
    HELPERS_AVAILABLE = True
except ImportError:
    HELPERS_AVAILABLE = False
    st.warning("Helper modules not found. Some features may be limited.")

# Page config
st.set_page_config(
    page_title="Liver Buddy - Fatty Liver Disease Management",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # Premium Custom CSS
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
#     * { font-family: 'Poppins', sans-serif; }
#     #MainMenu {visibility: hidden;}
#     footer {visibility: hidden;}
#     header {visibility: hidden;}
    
#     .main {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 0;
#     }
    
#     .block-container {
#         padding: 2rem 3rem;
#         max-width: 1400px;
#     }
    
#     .login-container {
#         background: white;
#         padding: 3rem;
#         border-radius: 20px;
#         box-shadow: 0 20px 60px rgba(0,0,0,0.3);
#     }
    
#     .main-header {
#         font-size: 3rem;
#         font-weight: 700;
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         text-align: center;
#         margin-bottom: 0.5rem;
#     }
    
#     .tagline {
#         text-align: center;
#         color: #666;
#         font-size: 1.2rem;
#         margin-bottom: 2rem;
#     }
    
#     [data-testid="stSidebar"] {
#         background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
#         padding: 2rem 1rem;
#     }
    
#     [data-testid="stSidebar"] * {
#         color: white !important;
#     }
    
#     .feature-card {
#         background: white;
#         padding: 2rem;
#         border-radius: 15px;
#         box-shadow: 0 4px 20px rgba(0,0,0,0.1);
#         margin: 1rem 0;
#         transition: transform 0.3s ease;
#         border-left: 4px solid #667eea;
#     }
    
#     .feature-card:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 8px 30px rgba(102, 126, 234, 0.3);
#     }
    
#     .stButton>button {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         border: none;
#         border-radius: 10px;
#         padding: 0.75rem 2rem;
#         font-weight: 600;
#         transition: all 0.3s ease;
#     }
    
#     .stButton>button:hover {
#         transform: translateY(-2px);
#         box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
#     }
    
#     .stat-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 1.5rem;
#         border-radius: 15px;
#         text-align: center;
#         box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
#     }
    
#     .stat-number {
#         font-size: 2.5rem;
#         font-weight: 700;
#         margin: 0.5rem 0;
#     }
    
#     .risk-badge {
#         display: inline-block;
#         padding: 0.5rem 1rem;
#         border-radius: 20px;
#         font-weight: 600;
#         margin: 0.5rem;
#     }
    
#     .risk-low { background: #4ade80; color: white; }
#     .risk-moderate { background: #fbbf24; color: white; }
#     .risk-high { background: #f87171; color: white; }
# </style>
# """, unsafe_allow_html=True)
# ENHANCED MODERN CSS - COMPLETE VERSION
ENHANCED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; }
    #MainMenu, footer, header {visibility: hidden;}
    
    .main {
        background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .block-container { padding: 2rem 3rem; max-width: 1400px; }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 16px 48px rgba(102, 126, 234, 0.25);
    }
    
    .login-container {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        padding: 3.5rem;
        border-radius: 32px;
        box-shadow: 0 20px 80px rgba(0, 0, 0, 0.15);
        border: 2px solid rgba(255, 255, 255, 0.5);
        animation: fadeInUp 0.8s ease;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .tagline {
        text-align: center;
        color: #555;
        font-size: 1.3rem;
        margin-bottom: 2.5rem;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.1);
    }
    
    [data-testid="stSidebar"] * { color: white !important; }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.875rem 2.5rem;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select, .stNumberInput>div>div>input {
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        padding: 0.875rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>select:focus, .stNumberInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stat-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 16px 40px rgba(102, 126, 234, 0.4);
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 800;
        margin: 1rem 0;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    
    .risk-badge {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        font-weight: 700;
        margin: 0.5rem;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    
    .risk-low { 
        background: linear-gradient(135deg, #4ade80, #22c55e);
        box-shadow: 0 4px 20px rgba(74, 222, 128, 0.4);
    }
    .risk-moderate { 
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        box-shadow: 0 4px 20px rgba(251, 191, 36, 0.4);
    }
    .risk-high { 
        background: linear-gradient(135deg, #f87171, #ef4444);
        box-shadow: 0 4px 20px rgba(248, 113, 113, 0.4);
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 2px solid rgba(102, 126, 234, 0.2);
        border-radius: 16px;
        padding: 1rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        transform: translateX(5px);
    }
    
    .icon-box {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        margin: 0 auto 1.5rem;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .feature-card {
        background: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin: 1rem 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
    }
    
    .greeting-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        margin-bottom: 2.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        border-radius: 10px;
    }
    
    @media (max-width: 768px) {
        .main-header { font-size: 2.5rem; }
        .block-container { padding: 1rem 1.5rem; }
    }
</style>
"""

st.markdown(ENHANCED_CSS, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    defaults = {
        'logged_in': False,
        'user_email': None,
        'user_id': None,
        'user_profile': {},
        'chat_history': [],
        'meal_plans': [],
        'nutrition_logs': [],
        'medications': [],
        'workout_plans': [],
        'risk_assessments': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Initialize AI helper
if HELPERS_AVAILABLE:
    ai = get_ai_helper()
else:
    ai = None

def login_page():
    """Login and Registration page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <div style="text-align: center; font-size: 4rem; margin-bottom: 1rem;">🫀</div>
            <h1 class="main-header">Liver Buddy</h1>
            <p class="tagline">Your Companion for Fatty Liver Disease Management</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])
        
        with tab1:
            with st.form("login_form"):
                st.markdown("#### Welcome Back!")
                email = st.text_input("📧 Email", placeholder="your.email@example.com")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                col_login, col_forgot = st.columns([2, 1])
                with col_login:
                    submit = st.form_submit_button("Login", use_container_width=True, type="primary")
                with col_forgot:
                    forgot_clicked = st.form_submit_button("Forgot Password?", use_container_width=True)

                
                
                if submit:
                    if HELPERS_AVAILABLE:
                        success, message = login_user(email, password)
                        if success:
                            st.success("✅ " + message)
                            st.balloons()
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ " + message)
                    else:
                        if email and password:
                            st.session_state.logged_in = True
                            st.session_state.user_email = email
                            st.session_state.user_id = "demo_user"
                            st.session_state.user_profile = {
                                'email': email,
                                'fullName': 'Demo User',
                                'age': 35,
                                'phone': '+1234567890',
                                'bloodGroup': 'O+',
                                'address': {
                                    'street': 'Demo Street',
                                    'houseNo': '123',
                                    'pinCode': '123456',
                                    'city': 'Demo City',
                                    'state': 'Demo State'
                                }
                            }
                            st.success("✅ Logged in (Demo Mode)")
                            st.balloons()
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Please enter credentials")
        
        with tab2:
            with st.form("register_form"):
                st.markdown("#### Join Liver Buddy Today")
                
                # Personal Information
                st.markdown("##### 👤 Personal Information")
                col_name, col_age = st.columns(2)
                with col_name:
                    full_name = st.text_input("Full Name*", placeholder="John Doe")
                with col_age:
                    age = st.number_input("Age*", min_value=18, max_value=100, value=30)
                
                # Contact Information
                st.markdown("##### 📞 Contact Information")
                email = st.text_input("📧 Email*", placeholder="your.email@example.com", key="reg_email")
                phone = st.text_input("📱 Phone Number*", placeholder="+1234567890")
                
                # Address Information
                st.markdown("##### 🏠 Address")
                col_street, col_house = st.columns(2)
                with col_street:
                    street = st.text_input("Street*", placeholder="Main Street")
                with col_house:
                    house_no = st.text_input("House No.*", placeholder="123")
                
                col_pin, col_city, col_state = st.columns(3)
                with col_pin:
                    pin_code = st.text_input("PIN Code*", placeholder="123456")
                with col_city:
                    city = st.text_input("City*", placeholder="Your City")
                with col_state:
                    state = st.text_input("State*", placeholder="Your State")
                
                # Medical Information
                st.markdown("##### 🩺 Medical Information")
                blood_group = st.selectbox("Blood Group*", 
                    ["Select Blood Group", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
                
                # Account Security
                st.markdown("##### 🔒 Account Security")
                new_password = st.text_input("Password*", type="password", placeholder="Min 6 characters", key="reg_pass")
                confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Re-enter password")
                
                agree = st.checkbox("I agree to Terms & Conditions and understand this app is for fatty liver disease management")
                
                submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if submit:
                    if not agree:
                        st.warning("⚠️ Please agree to Terms & Conditions")
                    elif not all([full_name, email, phone, street, house_no, pin_code, city, state, new_password]):
                        st.error("❌ Please fill all required fields (*)")
                    elif blood_group == "Select Blood Group":
                        st.error("❌ Please select a blood group")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords don't match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        user_data = {
                            'fullName': full_name,
                            'age': age,
                            'email': email,
                            'phone': phone,
                            'bloodGroup': blood_group,
                            'address': {
                                'street': street,
                                'houseNo': house_no,
                                'pinCode': pin_code,
                                'city': city,
                                'state': state
                            },
                            'createdAt': datetime.now().isoformat()
                        }
                        
                        if HELPERS_AVAILABLE:
                            with st.spinner("Creating account..."):
                                success, message = register_user(email, new_password, user_data)
                                if success:
                                    st.success("✅ " + message)
                                    st.balloons()
                                else:
                                    st.error("❌ " + message)
                        else:
                            st.success("✅ Registration successful (Demo Mode)! Please login.")
        
        # Features showcase
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### ✨ Why Choose Liver Buddy?")
        
        feat_col1, feat_col2, feat_col3 = st.columns(3)
        
        features = [
            ("🫀", "Specialized Care", "Designed specifically for fatty liver disease patients"),
            ("🍽️", "Smart Nutrition", "AI-powered meal analysis and planning"),
            ("📊", "Track Progress", "Monitor your liver health journey with detailed analytics")
        ]
        
        for col, (icon, title, desc) in zip([feat_col1, feat_col2, feat_col3], features):
            with col:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 3rem;">{icon}</div>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)

def patient_profile_page():
    """Patient Profile Management"""
    st.markdown("## 👤 Patient Profile")
    st.markdown("*View and manage your personal information*")
    
    profile = st.session_state.user_profile
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("update_profile_form"):
            st.markdown("### 📋 Personal Information")
            
            col_a, col_b = st.columns(2)
            with col_a:
                full_name = st.text_input("Full Name", value=profile.get('fullName', ''))
                age = st.number_input("Age", min_value=18, max_value=100, value=profile.get('age', 30))
            with col_b:
                blood_group = st.selectbox("Blood Group", 
                    ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"],
                    index=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"].index(profile.get('bloodGroup', 'O+')))
                phone = st.text_input("Phone", value=profile.get('phone', ''))
            
            st.markdown("### 🏠 Address Information")
            address = profile.get('address', {})
            
            col_c, col_d = st.columns(2)
            with col_c:
                street = st.text_input("Street", value=address.get('street', ''))
                pin_code = st.text_input("PIN Code", value=address.get('pinCode', ''))
            with col_d:
                house_no = st.text_input("House No.", value=address.get('houseNo', ''))
                city = st.text_input("City", value=address.get('city', ''))
            
            state = st.text_input("State", value=address.get('state', ''))
            
            if st.form_submit_button("💾 Update Profile", use_container_width=True, type="primary"):
                updated_profile = {
                    **profile,
                    "fullName": full_name,
                    "age": age,
                    "phone": phone,
                    "bloodGroup": blood_group,
                    "address": {
                        "street": street,
                        "houseNo": house_no,
                        "pinCode": pin_code,
                        "city": city,
                        "state": state
                    },
                    "updatedAt": datetime.now().isoformat()
                }
                
                if HELPERS_AVAILABLE:
                    db = init_firebase()
                    success = db.update_user_profile(st.session_state.user_id, updated_profile)
                    if success:
                        st.session_state.user_profile = updated_profile
                        st.success("✅ Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update profile")
                else:
                    st.session_state.user_profile = updated_profile
                    st.success("✅ Profile updated successfully!")
                    st.rerun()
    
    with col2:
        st.markdown("### 📊 Health Summary")
        
        st.markdown("#### 🩺 Medical Information")
        st.info(f"""
        **Name:** {profile.get('fullName', 'Not specified')}
        **Age:** {profile.get('age', 'Not specified')} years
        **Blood Group:** {profile.get('bloodGroup', 'Not specified')}
        **Phone:** {profile.get('phone', 'Not specified')}
        """)
        
        address = profile.get('address', {})
        st.markdown("#### 🏠 Address")
        st.info(f"""
        {address.get('houseNo', '')} {address.get('street', '')}
        {address.get('city', '')}, {address.get('state', '')}
        PIN: {address.get('pinCode', '')}
        """)
        
        st.markdown("#### 📈 Activity Summary")
        st.metric("Meals Logged", len(st.session_state.nutrition_logs))
        st.metric("Meal Plans", len(st.session_state.meal_plans))
        st.metric("Risk Assessments", len(st.session_state.risk_assessments))

# def smart_meal_planner_page():
#     """Smart Meal Planner with Image Upload"""
#     st.markdown("## 🍽️ Smart Meal Planner")
#     st.markdown("*AI-powered meal analysis for fatty liver disease management*")
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         with st.form("meal_analysis_form"):
#             st.markdown("### 📋 Meal Input")
            
#             input_method = st.radio("Choose input method:", ["📝 Text Description", "📷 Upload Photo", "📝+📷 Both"])
            
#             meal_description = ""
#             uploaded_image = None
            
#             if input_method in ["📝 Text Description", "📝+📷 Both"]:
#                 meal_description = st.text_area(
#                     "🍽️ Describe your meal",
#                     placeholder="E.g., Grilled chicken breast (150g), steamed broccoli (1 cup), brown rice (1/2 cup), olive oil (1 tsp)",
#                     height=100
#                 )
            
#             if input_method in ["📷 Upload Photo", "📝+📷 Both"]:
#                 uploaded_image = st.file_uploader("📷 Upload meal photo", type=["jpg", "jpeg", "png"])
            
#             col_a, col_b = st.columns(2)
#             with col_a:
#                 meal_type = st.selectbox("🕐 Meal Type", 
#                     ["Breakfast", "Morning Snack", "Lunch", "Afternoon Snack", "Dinner", "Evening Snack"])
#             with col_b:
#                 portion_size = st.select_slider("🍽️ Portion Size",
#                     options=["Small", "Medium", "Large", "Extra Large"])
            
#             preferences = st.text_input("🎯 Dietary Preferences/Restrictions", 
#                 placeholder="E.g., vegetarian, low-sodium, no dairy")
            
#             submitted = st.form_submit_button("🔬 Analyze Meal", use_container_width=True, type="primary")
            
#             if submitted and (meal_description or uploaded_image):
#                 with st.spinner("🧬 Analyzing meal for fatty liver suitability..."):
#                     progress = st.progress(0)
#                     for i in range(100):
#                         time.sleep(0.01)
#                         progress.progress(i + 1)
                    
#                     analysis_context = f"""
# Analyze this meal for a patient with fatty liver disease. Focus on:
# 1. Identify all food items and portion sizes
# 2. Calculate nutritional composition (calories, macros, key nutrients)
# 3. Assess suitability for fatty liver disease (rate as Excellent/Good/Fair/Poor)
# 4. Identify foods to avoid or limit for liver health
# 5. Provide specific recommendations for improvement
# 6. Suggest healthier alternatives if needed

# Meal Type: {meal_type}
# Portion: {portion_size}
# Preferences: {preferences if preferences else 'None specified'}
# """
                    
#                     if ai and ai.enabled:
#                         # Analyze image if uploaded
#                         image_analysis = ""
#                         if uploaded_image:
#                             image_bytes = uploaded_image.getvalue()
#                             image_prompt = f"{analysis_context}\n\nAnalyze the food items visible in this image."
#                             image_analysis = ai.analyze_image(image_bytes, image_prompt)
                        
#                         # Combine text and image analysis
#                         full_prompt = analysis_context
#                         if meal_description:
#                             full_prompt += f"\n\nText Description: {meal_description}"
#                         if image_analysis:
#                             full_prompt += f"\n\nImage Analysis: {image_analysis}"
                        
#                         messages = [
#                             {"role": "system", "content": "You are a specialized nutritionist for fatty liver disease patients. Provide detailed, actionable advice focused on liver health."},
#                             {"role": "user", "content": full_prompt}
#                         ]
#                         analysis = ai.chat_completion(messages, temperature=0.3, max_tokens=1200)
#                     else:
#                         analysis = f"""### 🔬 Nutritional Analysis for Fatty Liver Disease

# **Food Items Identified:**
# - Grilled chicken breast (lean protein)
# - Steamed broccoli (cruciferous vegetable)
# - Brown rice (whole grain)
# - Olive oil (healthy fat)

# **Nutritional Composition:**
# - **Calories:** ~420 kcal
# - **Protein:** 35g (33%)
# - **Carbs:** 45g (43%)
# - **Fat:** 11g (24%)
# - **Fiber:** 6g

# **Liver Health Suitability:** ✅ **Excellent**

# This meal is well-suited for fatty liver disease management:
# - ✅ High in lean protein (supports liver repair)
# - ✅ Rich in fiber (aids fat metabolism)
# - ✅ Contains antioxidants from broccoli
# - ✅ Low in saturated fats
# - ✅ No added sugars or processed ingredients

# **Recommendations:**
# 1. Perfect portion size for liver health
# 2. Consider adding more colorful vegetables for phytonutrients
# 3. Ensure olive oil is used raw (don't overheat)
# 4. Stay hydrated with water or green tea

# **Foods to Continue:**
# - Lean proteins (chicken, fish, legumes)
# - Cruciferous vegetables (broccoli, cauliflower)
# - Whole grains in moderation
# - Healthy fats (olive oil, avocado, nuts)

# *💡 Add OpenAI API key for detailed AI-powered analysis with image recognition!*"""
                    
#                     meal_data = {
#                         "date": datetime.now().isoformat(),
#                         "meal_type": meal_type,
#                         "portion": portion_size,
#                         "description": meal_description,
#                         "preferences": preferences,
#                         "has_image": uploaded_image is not None,
#                         "analysis": analysis,
#                         "timestamp": datetime.now().isoformat()
#                     }
                    
#                     st.session_state.meal_plans.insert(0, meal_data)
#                     st.session_state.nutrition_logs.insert(0, meal_data)
                    
#                     if HELPERS_AVAILABLE:
#                         db = init_firebase()
#                         db.save_meal_analysis(st.session_state.user_id, meal_data)
                    
#                     st.success("✅ Meal analyzed successfully!")
#                     st.markdown(analysis)
#                     st.balloons()
    
#     with col2:
#         st.markdown("### 📚 Recent Analyses")
        
#         if st.session_state.meal_plans:
#             for i, meal in enumerate(st.session_state.meal_plans[:5]):
#                 date_str = datetime.fromisoformat(meal['date']).strftime('%b %d, %Y')
#                 with st.expander(f"🍽️ {meal['meal_type']} - {date_str}", expanded=(i==0)):
#                     if meal.get('description'):
#                         st.markdown(f"**Description:** {meal['description']}")
#                     st.markdown(f"**Portion:** {meal['portion']}")
#                     st.markdown("---")
#                     st.markdown(meal['analysis'][:300] + "..." if len(meal['analysis']) > 300 else meal['analysis'])
#         else:
#             st.info("🍽️ No meal analyses yet. Start by analyzing your first meal!")
        
#         st.markdown("### 💡 Liver-Friendly Tips")
#         st.info("""
#         **Foods to Favor:**
#         ✅ Leafy greens
#         ✅ Fatty fish (salmon, sardines)
#         ✅ Nuts (walnuts, almonds)
#         ✅ Olive oil
#         ✅ Green tea
#         ✅ Whole grains
        
#         **Foods to Limit:**
#         ❌ Fried foods
#         ❌ Processed meats
#         ❌ Added sugars
#         ❌ White bread/pasta
#         ❌ Alcohol
#         ❌ High-sodium foods
#         """)
def smart_meal_planner_page():
    """Smart Meal Planner with Image Upload - FIXED"""
    st.markdown("## 🍽️ Smart Meal Planner")
    st.markdown("*AI-powered meal analysis for fatty liver disease management*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("meal_analysis_form"):
            st.markdown("### 📋 Meal Input")
            
            input_method = st.radio("Choose input method:", ["📝 Text Description", "📷 Upload Photo", "📝+📷 Both"])
            
            meal_description = ""
            uploaded_image = None
            
            if input_method in ["📝 Text Description", "📝+📷 Both"]:
                meal_description = st.text_area(
                    "🍽️ Describe your meal",
                    placeholder="E.g., Grilled chicken breast (150g), steamed broccoli (1 cup), brown rice (1/2 cup), olive oil (1 tsp)",
                    height=100
                )
            
            if input_method in ["📷 Upload Photo", "📝+📷 Both"]:
                uploaded_image = st.file_uploader("📷 Upload meal photo", type=["jpg", "jpeg", "png"])
            
            col_a, col_b = st.columns(2)
            with col_a:
                meal_type = st.selectbox("🍴 Meal Type", 
                    ["Breakfast", "Morning Snack", "Lunch", "Afternoon Snack", "Dinner", "Evening Snack"])
            with col_b:
                portion_size = st.select_slider("🍽️ Portion Size",
                    options=["Small", "Medium", "Large", "Extra Large"])
            
            preferences = st.text_input("🎯 Dietary Preferences/Restrictions", 
                placeholder="E.g., vegetarian, low-sodium, no dairy")
            
            submitted = st.form_submit_button("📬 Analyze Meal", use_container_width=True, type="primary")
            
            if submitted:
                # VALIDATION: Check if user provided input
                if not meal_description and not uploaded_image:
                    st.error("❌ Please provide either a meal description or upload a photo")
                    return
                
                with st.spinner("🧬 Analyzing meal for fatty liver suitability..."):
                    progress = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress.progress(i + 1)
                    
                    # BUILD PROMPT FROM ACTUAL USER INPUTS (NOT DEFAULTS)
                    analysis_context = f"""
Analyze this meal for a patient with fatty liver disease. Focus on:
1. Identify all food items and portion sizes
2. Calculate nutritional composition (calories, macros, key nutrients)
3. Assess suitability for fatty liver disease (rate as Excellent/Good/Fair/Poor)
4. Identify foods to avoid or limit for liver health
5. Provide specific recommendations for improvement
6. Suggest healthier alternatives if needed

**ACTUAL USER INPUT:**
Meal Type: {meal_type}
Portion: {portion_size}
Preferences: {preferences if preferences else 'None specified'}
Description: {meal_description if meal_description else 'Image analysis only'}
"""
                    
                    if ai and ai.enabled:
                        # Analyze image if uploaded
                        image_analysis = ""
                        if uploaded_image:
                            image_bytes = uploaded_image.getvalue()
                            image_prompt = f"{analysis_context}\n\nAnalyze the food items visible in this image."
                            image_analysis = ai.analyze_image(image_bytes, image_prompt)
                        
                        # Combine text and image analysis
                        full_prompt = analysis_context
                        if meal_description:
                            full_prompt += f"\n\n**Text Description:** {meal_description}"
                        if image_analysis:
                            full_prompt += f"\n\n**Image Analysis Results:** {image_analysis}"
                        
                        messages = [
                            {"role": "system", "content": "You are a specialized nutritionist for fatty liver disease patients. Provide detailed, actionable advice focused on liver health. Base recommendations on AASLD (American Association for Study of Liver Diseases) guidelines for NAFLD/NASH management."},
                            {"role": "user", "content": full_prompt}
                        ]
                        analysis = ai.chat_completion(messages, temperature=0.3, max_tokens=1200)
                    else:
                        # Demo mode with user inputs reflected
                        analysis = f"""### 📬 Nutritional Analysis for Fatty Liver Disease

**YOUR INPUT:**
- Meal Type: {meal_type}
- Portion Size: {portion_size}
- Preferences: {preferences if preferences else 'None specified'}
- Description: {meal_description if meal_description else 'Photo uploaded for analysis'}

---

**Food Items Identified:**
Based on your description: {meal_description if meal_description else '[Image analysis would be performed with OpenAI API key]'}

**Nutritional Composition:**
[Detailed breakdown would appear here with real API]

**Liver Health Suitability:** Assessment based on your input

**Recommendations:**
1. Continue with healthy choices
2. Monitor portion sizes
3. Stay hydrated

*📝 Add OpenAI API key for detailed AI-powered analysis with image recognition!*"""
                    

                    
                    meal_data = {
                        "date": datetime.now().isoformat(),
                        "meal_type": meal_type,
                        "portion": portion_size,
                        "description": meal_description,
                        "preferences": preferences,
                        "has_image": uploaded_image is not None,
                        "analysis": analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    st.session_state.meal_plans.insert(0, meal_data)
                    st.session_state.nutrition_logs.insert(0, meal_data)
                    
                    if HELPERS_AVAILABLE:
                        db = init_firebase()
                        db.save_meal_analysis(st.session_state.user_id, meal_data)
                    
                    st.success("✅ Meal analyzed successfully!")
                    st.markdown(analysis)
                    st.balloons()
    
    with col2:
        st.markdown("### 📚 Recent Analyses")
        
        if st.session_state.meal_plans:
            for i, meal in enumerate(st.session_state.meal_plans[:5]):
                date_str = datetime.fromisoformat(meal['date']).strftime('%b %d, %Y')
                with st.expander(f"🍽️ {meal['meal_type']} - {date_str}", expanded=(i==0)):
                    if meal.get('description'):
                        st.markdown(f"**Your Description:** {meal['description']}")
                    st.markdown(f"**Portion:** {meal['portion']}")
                    if meal.get('preferences'):
                        st.markdown(f"**Preferences:** {meal['preferences']}")
                    st.markdown("---")
                    st.markdown(meal['analysis'][:300] + "..." if len(meal['analysis']) > 300 else meal['analysis'])
        else:
            st.info("🍽️ No meal analyses yet. Start by analyzing your first meal!")
        
        st.markdown("### 💡 Liver-Friendly Tips")
        st.info("""
        **Foods to Favor:**
        ✅ Leafy greens
        ✅ Fatty fish (salmon, sardines)
        ✅ Nuts (walnuts, almonds)
        ✅ Olive oil
        ✅ Green tea
        ✅ Whole grains
        
        **Foods to Limit:**
        ❌ Fried foods
        ❌ Processed meats
        ❌ Added sugars
        ❌ White bread/pasta
        ❌ Alcohol
        ❌ High-sodium foods
        """)

def nutrition_tracker_dashboard():
    """Unified Nutrition Tracking Dashboard"""
    st.markdown("## 📊 Nutrition Tracker & Dashboard")
    st.markdown("*Monitor your daily nutrition and progress*")
    
    tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "📝 History", "📊 Trends"])
    
    with tab1:
        if len(st.session_state.nutrition_logs) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class="stat-card">
                    <div style="font-size: 2rem;">🍽️</div>
                    <div class="stat-number">{}</div>
                    <div>Total Meals</div>
                </div>
                """.format(len(st.session_state.nutrition_logs)), unsafe_allow_html=True)
            
            with col2:
                unique_dates = len(set(log['date'][:10] for log in st.session_state.nutrition_logs))
                st.markdown("""
                <div class="stat-card">
                    <div style="font-size: 2rem;">📅</div>
                    <div class="stat-number">{}</div>
                    <div>Days Tracked</div>
                </div>
                """.format(unique_dates), unsafe_allow_html=True)
            
            with col3:
                avg_meals = len(st.session_state.nutrition_logs) / max(unique_dates, 1)
                st.markdown("""
                <div class="stat-card">
                    <div style="font-size: 2rem;">📊</div>
                    <div class="stat-number">{:.1f}</div>
                    <div>Avg Meals/Day</div>
                </div>
                """.format(avg_meals), unsafe_allow_html=True)
            
            with col4:
                st.markdown("""
                <div class="stat-card">
                    <div style="font-size: 2rem;">✅</div>
                    <div class="stat-number">85%</div>
                    <div>Liver-Friendly</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("### 📊 Meal Distribution")
            meal_counts = {}
            for log in st.session_state.nutrition_logs:
                meal_type = log.get('meal_type', 'Unknown')
                meal_counts[meal_type] = meal_counts.get(meal_type, 0) + 1
            
            if meal_counts:
                df = pd.DataFrame(list(meal_counts.items()), columns=['Meal Type', 'Count'])
                st.bar_chart(df.set_index('Meal Type'))
            
            st.markdown("### 🎯 This Week's Goals")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Liver-Friendly Meals", "12/15", delta="+2 from last week")
            with col_b:
                st.metric("Consistency Streak", "5 days", delta="+2 days")
        else:
            st.info("📊 Start logging meals to see your nutrition dashboard!")
    
    with tab2:
        st.markdown("### 📝 Nutrition History")
        
        if st.session_state.nutrition_logs:
            for i, log in enumerate(st.session_state.nutrition_logs[:15]):
                date_obj = datetime.fromisoformat(log['date'])
                date_str = date_obj.strftime('%b %d, %Y %I:%M %p')
                
                with st.expander(f"🍽️ {log.get('meal_type', 'Meal')} - {date_str}", expanded=False):
                    if log.get('description'):
                        st.markdown(f"**Description:** {log['description']}")
                    st.markdown(f"**Portion:** {log.get('portion', 'Not specified')}")
                    st.markdown("---")
                    st.markdown(log.get('analysis', 'No analysis available'))
                    
                    if st.button(f"🗑️ Delete", key=f"del_log_{i}", use_container_width=True):
                        st.session_state.nutrition_logs.pop(i)
                        st.rerun()
        else:
            st.info("📝 No nutrition logs yet. Start tracking in the Meal Planner!")
    
    with tab3:
        st.markdown("### 📊 Weekly & Monthly Trends")
        
        if len(st.session_state.nutrition_logs) >= 7:
            st.markdown("#### 📅 Daily Meal Frequency")
            
            dates = [datetime.fromisoformat(log['date']).date() for log in st.session_state.nutrition_logs]
            date_counts = pd.Series(dates).value_counts().sort_index()
            
            st.line_chart(date_counts)
            
            st.markdown("#### 🍽️ Meal Type Distribution")
            meal_types = [log.get('meal_type', 'Unknown') for log in st.session_state.nutrition_logs]
            meal_type_counts = pd.Series(meal_types).value_counts()
            
            st.bar_chart(meal_type_counts)
            
            st.markdown("#### 💡 Insights")
            st.success("""
            **Your Progress:**
            - You're consistently logging meals ✅
            - 85% of your meals are liver-friendly 🎉
            - Keep focusing on lean proteins and vegetables 💪
            """)
        else:
            st.info("📈 Log at least 7 meals to see trend analysis!")

def risk_assessment_page():
    """Fatty Liver Risk Assessment"""
    st.markdown("## ⚖️ Fatty Liver Risk Assessment")
    st.markdown("*Comprehensive AI-powered risk analysis for fatty liver disease*")
    
    with st.form("risk_assessment_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 👤 Physical Measurements")
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                age = st.number_input("Age", 18, 100, 30)
            with col_b:
                height = st.number_input("Height (cm)", 100, 250, 170)
            with col_c:
                weight = st.number_input("Weight (kg)", 30, 200, 70)
            
            bmi = weight / ((height/100) ** 2)
            
            if bmi < 18.5:
                bmi_status, bmi_color = "Underweight", "🟡"
            elif 18.5 <= bmi < 25:
                bmi_status, bmi_color = "Normal", "🟢"
            elif 25 <= bmi < 30:
                bmi_status, bmi_color = "Overweight", "🟠"
            else:
                bmi_status, bmi_color = "Obese", "🔴"
            
            st.info(f"{bmi_color} **Your BMI: {bmi:.1f}** ({bmi_status}) - {'High risk factor for fatty liver' if bmi >= 25 else 'Normal range'}")
            
            st.markdown("### 🫀 Liver-Specific Information")
            
            col_d, col_e = st.columns(2)
            with col_d:
                liver_diagnosis = st.selectbox("Current Liver Status", 
                    ["Suspected fatty liver", "Diagnosed NAFLD (Non-alcoholic Fatty Liver Disease)", 
                     "Diagnosed NASH (Non-alcoholic Steatohepatitis)", "Elevated liver enzymes", 
                     "Not diagnosed but concerned", "Other"])
                
                liver_symptoms = st.multiselect("Symptoms (if any)",
                    ["None", "Fatigue", "Upper right abdominal pain", "Weight loss", 
                     "Weakness", "Enlarged liver (hepatomegaly)", "Jaundice"])
            
            with col_e:
                family_liver_history = st.selectbox("Family History of Liver Disease",
                    ["No", "Yes - immediate family", "Yes - extended family", "Unknown"])
                
                lab_results = st.text_area("Recent Lab Results (optional)",
                    placeholder="E.g., ALT: 45 U/L, AST: 38 U/L, GGT: 55 U/L",
                    height=80)
            
            st.markdown("### 🏃 Lifestyle Factors")
            
            col_f, col_g = st.columns(2)
            with col_f:
                alcohol = st.selectbox("🍺 Alcohol Consumption", 
                    ["None", "Rare (1-2 drinks/month)", "Occasional (1-2 drinks/week)", 
                     "Moderate (3-7 drinks/week)", "Heavy (>7 drinks/week)"])
                
                exercise = st.slider("💪 Exercise (hours/week)", 0, 20, 3)
                
                diet_quality = st.select_slider("🥗 Diet Quality",
                    options=["Poor (mostly processed)", "Fair", "Good", "Very Good", "Excellent (whole foods)"])
            
            with col_g:
                sleep = st.slider("😴 Sleep (hours/night)", 3, 12, 7)
                
                smoking = st.selectbox("🚬 Smoking Status", 
                    ["Never", "Former (quit >1 year)", "Current"])
                
                stress = st.select_slider("😰 Stress Level",
                    options=["Low", "Moderate", "High", "Very High"])
        
        with col2:
            st.markdown("### 🩺 Medical Conditions")
            
            risk_factors = st.multiselect("Related Conditions",
                ["None", "Type 2 Diabetes", "Pre-diabetes", "Obesity", 
                 "Metabolic Syndrome", "High Blood Pressure", "High Cholesterol", 
                 "High Triglycerides", "Sleep Apnea", "PCOS", "Hypothyroidism"])
            
            medications = st.text_area("Current Medications",
                placeholder="List any medications you're taking",
                height=100)
            
            st.markdown("### 📝 Additional Information")
            
            recent_weight_change = st.selectbox("Recent Weight Change",
                ["Stable", "Lost weight (5-10 lbs)", "Lost weight (>10 lbs)", 
                 "Gained weight (5-10 lbs)", "Gained weight (>10 lbs)"])
            
            concerns = st.text_area("Specific Concerns",
                placeholder="Any specific symptoms or concerns?",
                height=80)
        
        submitted = st.form_submit_button("🔬 Analyze Fatty Liver Risk", use_container_width=True, type="primary")
        
        if submitted:
            with st.spinner("🧬 Analyzing your fatty liver disease risk profile..."):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress.progress(i + 1)
                
                
                
                health_data = {
                    'age': age, 'bmi': round(bmi, 1), 'height': height, 'weight': weight,
                    'liver_diagnosis': liver_diagnosis, 'liver_symptoms': liver_symptoms,
                    'family_liver_history': family_liver_history, 'lab_results': lab_results,
                    'alcohol': alcohol, 'exercise': exercise, 'sleep': sleep,
                    'diet_quality': diet_quality, 'smoking': smoking, 'stress': stress,
                    'risk_factors': risk_factors, 'medications': medications,
                    'recent_weight_change': recent_weight_change, 'concerns': concerns,
                    'assessment_date': datetime.now().isoformat()
                }
                
                if ai and ai.enabled:
                    prompt = f"""
Perform a comprehensive fatty liver disease risk assessment for this patient:

PHYSICAL DATA:
- Age: {age}, BMI: {bmi:.1f} ({bmi_status})
- Height: {height}cm, Weight: {weight}kg

LIVER STATUS:
- Current Status: {liver_diagnosis}
- Symptoms: {', '.join(liver_symptoms) if liver_symptoms else 'None'}
- Family History: {family_liver_history}
- Lab Results: {lab_results if lab_results else 'Not provided'}

LIFESTYLE:
- Alcohol: {alcohol}
- Exercise: {exercise}h/week
- Sleep: {sleep}h/night
- Diet Quality: {diet_quality}
- Smoking: {smoking}
- Stress: {stress}

MEDICAL:
- Conditions: {', '.join(risk_factors) if risk_factors else 'None'}
- Medications: {medications if medications else 'None'}
- Recent Weight Change: {recent_weight_change}

Please provide:
1. **Risk Score** (0-100 scale) with interpretation
2. **Risk Level** (Low/Moderate/High/Severe)
3. **Stage Assessment** (if applicable: Simple steatosis/NASH/Fibrosis/Cirrhosis risk)
4. **Key Risk Factors** identified
5. **Protective Factors** (positive aspects)
6. **Detailed Recommendations** for:
   - Diet modifications
   - Exercise program
   - Lifestyle changes
   - Medical follow-up
7. **Action Plan** (immediate, short-term, long-term)
8. **Red Flags** requiring immediate medical attention

Be specific, actionable, and evidence-based. Focus on fatty liver disease management.
"""
                    messages = [
                        {"role": "system", "content": "You are a hepatologist specializing in fatty liver disease. Provide thorough, personalized risk assessments with actionable recommendations."},
                        {"role": "user", "content": prompt}
                    ]
                    assessment = ai.chat_completion(messages, temperature=0.4, max_tokens=1800)
                else:
                    risk_level = "Moderate" if bmi >= 25 else "Low"
                    risk_color = "🟠" if bmi >= 25 else "🟢"
                    risk_score = min(int(40 + (bmi - 25) * 3 + len(risk_factors) * 5), 95) if bmi >= 25 else 25
                    
                    assessment = f"""### 🔬 Fatty Liver Risk Assessment

**Overall Risk Score:** {risk_score}/100

<div class="risk-badge risk-{risk_level.lower()}">{risk_color} {risk_level.upper()} RISK</div>

---

### 📊 Risk Analysis

**Physical Assessment:**
- BMI: {bmi:.1f} ({bmi_status}) - {'⚠️ Significant risk factor' if bmi >= 25 else '✅ Normal range'}
- Current Liver Status: {liver_diagnosis}

**Key Risk Factors Identified:**
{'1. Elevated BMI (BMI ≥25 is a major risk factor)' if bmi >= 25 else ''}
{'2. ' + ', '.join(risk_factors[:3]) if risk_factors and 'None' not in risk_factors else ''}
{'3. Low physical activity (<150 min/week recommended)' if exercise < 2.5 else ''}
{'4. ' + alcohol + ' alcohol consumption' if alcohol not in ['None', 'Rare (1-2 drinks/month)'] else ''}

**Protective Factors:**
{'✅ Normal BMI range' if bmi < 25 else ''}
✅ Exercise: {exercise}h/week {'(Good!)' if exercise >= 3 else '(needs improvement)'}
✅ Sleep: {sleep}h/night {'(Adequate)' if 7 <= sleep <= 9 else '(needs optimization)'}
{'✅ No alcohol consumption' if alcohol == 'None' else ''}

---

### 🎯 Recommendations for Fatty Liver Management

**1. Dietary Modifications:**
- Focus on Mediterranean diet pattern
- Increase: Leafy greens, fatty fish (omega-3), nuts, olive oil
- Reduce: Sugary foods, refined carbs, fried foods, processed meats
- Limit fructose (high-fructose corn syrup, excessive fruit juice)
- Target weight loss of 5-10% if overweight

**2. Exercise Program:**
- Goal: At least 150 minutes/week of moderate aerobic activity
- Include: Brisk walking, swimming, cycling
- Add resistance training 2-3 times/week
- Start gradually if currently inactive

**3. Lifestyle Changes:**
- Eliminate or minimize alcohol consumption
- Manage stress through meditation, yoga, or counseling
- Optimize sleep (7-9 hours/night)
- Avoid rapid weight loss (aim for 1-2 lbs/week)

**4. Medical Follow-up:**
- Schedule appointment with hepatologist or gastroenterologist
- Request comprehensive liver panel (ALT, AST, GGT, ALP)
- Consider FibroScan or liver ultrasound
- Monitor every 6 months initially

---

### 📋 Action Plan

**Immediate (This Week):**
- Schedule doctor's appointment
- Start food diary
- Eliminate sugary drinks
- Begin 30-min daily walks

**Short-term (1-3 Months):**
- Achieve 5% weight loss if overweight
- Establish consistent exercise routine
- Adopt liver-friendly diet pattern
- Get baseline liver function tests

**Long-term (3-12 Months):**
- Continue healthy lifestyle habits
- Regular medical monitoring
- Maintain healthy weight
- Reassess risk factors

---

### ⚠️ When to Seek Immediate Medical Attention:
- Severe abdominal pain
- Jaundice (yellowing of skin/eyes)
- Dark urine or pale stools
- Unexplained weight loss
- Persistent fatigue affecting daily life
- Swelling in legs or abdomen

---

*💡 This assessment is for informational purposes. Always consult with healthcare professionals for personalized medical advice. Add OpenAI API key for detailed AI-powered analysis!*"""
                
                assessment_data = {
                    **health_data,
                    'assessment': assessment,
                    'risk_score': risk_score if not (ai and ai.enabled) else None
                }
                # # NOW validate it
                # validator = MedicalAIValidator()
                # validated_assessment, validation = validator.validate_and_display(assessment, "risk")
                
                # # Display validation
                # st.markdown("---")
                # st.markdown("### 🔍 Medical Accuracy Check")
                # validator.display_validation_badge(validation)
                # st.markdown("---")
                
                # # Display assessment if validation passed
                # if "HIGH RISK" not in validation["status"] and "CRITICAL" not in validation["status"]:
                #     st.markdown(validated_assessment)
                # else:
                #     st.error("⚠️ This assessment requires medical review")
                
                
                st.session_state.risk_assessments.insert(0, assessment_data)
                
                if HELPERS_AVAILABLE:
                    db = init_firebase()
                    db.save_risk_assessment(st.session_state.user_id, assessment_data)
                
                st.success("✅ Risk Assessment Complete!")
                st.markdown("---")
                st.markdown(assessment)
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    st.download_button(
                        "📥 Download Report",
                        assessment,
                        f"fatty_liver_assessment_{datetime.now().strftime('%Y%m%d')}.txt",
                        use_container_width=True
                    )
                with col_btn2:
                    if st.button("📧 Email Report", use_container_width=True):
                        st.info("💡 Email feature coming soon!")
                with col_btn3:
                    if st.button("📊 View History", use_container_width=True):
                        st.info(f"You have {len(st.session_state.risk_assessments)} assessment(s) on record")

def workout_planner_page():
    """Safe Workout Plans for Fatty Liver Patients"""
    st.markdown("## 💪 Exercise & Workout Plans")
    st.markdown("*Safe, effective workouts designed for fatty liver disease management*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("workout_form"):
            st.markdown("### 🎯 Workout Preferences")
            
            col_a, col_b = st.columns(2)
            with col_a:
                workout_type = st.selectbox("🏃 Activity Type",
                    ["Walking", "Swimming", "Cycling", "Light Yoga", "Water Aerobics",
                     "Gentle Stretching", "Low-Impact Aerobics", "Tai Chi"])
                
                fitness_level = st.select_slider("📊 Current Fitness Level",
                    options=["Sedentary", "Beginner", "Intermediate", "Active"])
            
            with col_b:
                duration = st.slider("⏱️ Session Duration (minutes)", 10, 60, 30, 5)
                
                frequency = st.slider("📅 Sessions per Week", 1, 7, 3)
            
            focus_areas = st.multiselect("🎯 Primary Goals",
                ["Weight Loss", "Improve Insulin Sensitivity", "Cardiovascular Health", 
                 "Flexibility", "Stress Relief", "General Fitness"])
            
            limitations = st.text_area("⚠️ Physical Limitations or Concerns",
                placeholder="E.g., knee pain, back issues, recent surgery",
                height=80)
            
            submitted = st.form_submit_button("✨ Generate Workout Plan", use_container_width=True, type="primary")
            
            if submitted:
                with st.spinner("🏋️ Creating your personalized safe workout plan..."):
                    progress = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress.progress(i + 1)
                    

                    
                    if ai and ai.enabled:
                        prompt = f"""
Create a safe, effective workout plan for a fatty liver disease patient:

PROFILE:
- Fitness Level: {fitness_level}
- Preferred Activity: {workout_type}
- Duration: {duration} minutes per session
- Frequency: {frequency} times per week
- Goals: {', '.join(focus_areas) if focus_areas else 'General health'}
- Limitations: {limitations if limitations else 'None specified'}

REQUIREMENTS:
1. Design a structured {duration}-minute workout session
2. Include proper warm-up (5-10 min) and cool-down (5-10 min)
3. Focus on moderate-intensity aerobic exercise (beneficial for fatty liver)
4. Avoid high-impact or strenuous activities that could cause injury
5. Include progression plan for gradual improvement
6. Add specific precautions for liver health
7. Format as a clear daily schedule with exercises, sets/reps/duration

IMPORTANT: Keep intensity moderate (50-70% max heart rate). Exercise is crucial for fatty liver management through improved insulin sensitivity and weight loss.
"""
                        messages = [
                            {"role": "system", "content": "You are a certified fitness trainer specializing in exercise programs for patients with chronic liver disease. Prioritize safety and gradual progression."},
                            {"role": "user", "content": prompt}
                        ]
                        workout_plan = ai.chat_completion(messages, temperature=0.6, max_tokens=1200)
                    else:
                        workout_plan = f"""### 💪 {duration}-Minute {workout_type} Plan for Fatty Liver Health
**Level:** {fitness_level} | **Frequency:** {frequency}x per week

---

#### 🔥 Warm-Up (5 minutes)
1. **Gentle March in Place** - 2 minutes
   - Start slow, gradually increase knee lift
   - Focus on controlled breathing
   
2. **Arm Circles** - 1 minute
   - 30 seconds forward, 30 seconds backward
   - Keep movements smooth and controlled
   
3. **Gentle Torso Twists** - 1 minute
   - Stand with feet hip-width apart
   - Rotate gently side to side
   
4. **Leg Swings** - 1 minute
   - Hold wall for support
   - 30 seconds each leg, front to back

---

#### 💪 Main Workout ({duration-10} minutes)

**Exercise 1: {workout_type}** - {duration-10} minutes
- Maintain moderate intensity (able to talk but slightly breathless)
- Target heart rate: 50-70% of maximum
- Focus on steady, consistent pace
- Take breaks as needed

{'**For Walking:**' if workout_type == 'Walking' else ''}
{'- Start at comfortable pace' if workout_type == 'Walking' else ''}
{'- Gradually increase speed after 5 minutes' if workout_type == 'Walking' else ''}
{'- Maintain good posture' if workout_type == 'Walking' else ''}
{'- Swing arms naturally' if workout_type == 'Walking' else ''}

---

#### 🧘 Cool-Down (5 minutes)
1. **Slow Walking/Movement** - 2 minutes
   - Gradually reduce intensity
   - Focus on deep breathing
   
2. **Hamstring Stretch** - 1 minute
   - Hold each side for 30 seconds
   - No bouncing, gentle pressure
   
3. **Quad Stretch** - 1 minute
   - Hold wall for balance
   - 30 seconds each leg
   
4. **Shoulder & Neck Stretches** - 1 minute
   - Gentle neck rolls
   - Shoulder shrugs and releases

---

### 📈 Weekly Progression Plan

**Week 1-2:** Focus on consistency, maintain comfortable pace
**Week 3-4:** Increase duration by 5 minutes OR add 1 extra session
**Week 5-8:** Gradually increase intensity (slightly faster pace)
**Week 9-12:** Add variety (hills for walking, intervals for cycling)

---

### ⚠️ Important Precautions for Fatty Liver Patients

**DO:**
✅ Start slowly and progress gradually
✅ Stay well-hydrated (water before, during, after)
✅ Exercise at moderate intensity (can talk during exercise)
✅ Listen to your body and rest when needed
✅ Exercise regularly (consistency > intensity)
✅ Combine with healthy diet for best results

**DON'T:**
❌ Push to exhaustion or extreme fatigue
❌ Exercise immediately after large meals
❌ Skip warm-up or cool-down
❌ Exercise if feeling unwell or feverish
❌ Ignore pain or discomfort
❌ Expect immediate results (changes take 8-12 weeks)

---

### 🎯 Goals for Fatty Liver Management
- **Primary:** {', '.join(focus_areas) if focus_areas else 'Improve liver health'}
- **Target:** 150-300 minutes of moderate activity per week
- **Expected Benefits:**
  - Improved insulin sensitivity
  - Reduced liver fat content
  - Weight loss (if overweight)
  - Better cardiovascular health
  - Enhanced mood and energy

---

### 📊 Track Your Progress
- **Weekly Goal:** {frequency} sessions of {duration} minutes each
- **Monthly Target:** {frequency * 4} total sessions
- Log each workout and note how you feel
- Measure improvements in stamina and ease of exercise

---

*💡 Always consult your healthcare provider before starting a new exercise program. This plan is designed specifically for fatty liver disease management. Add OpenAI API key for more personalized AI-generated plans!*"""
                    
                    plan_data = {
                        "date": datetime.now().isoformat(),
                        "workout_type": workout_type,
                        "fitness_level": fitness_level,
                        "duration": duration,
                        "frequency": frequency,
                        "focus_areas": focus_areas,
                        "limitations": limitations,
                        "plan": workout_plan
                    }
                    # # ADD VALIDATION HERE:
                    # validator = MedicalAIValidator()
                    # validated_plan, validation = validator.validate_and_display(workout_plan, "workout")
            
                    # # Display validation
                    # st.markdown("---")
                    # st.markdown("### 🔍 Safety Check")
                    # validator.display_validation_badge(validation)
                    # st.markdown("---")
            
                    # # Display workout plan
                    # st.markdown(validated_plan)
            
                    # if "CAUTION" in validation["status"]:
                    #     st.warning("⚠️ Review the warnings above before starting this workout")
                    # st.session_state.workout_plans.insert(0, plan_data)
                    
                    if HELPERS_AVAILABLE:
                        db = init_firebase()
                        db.save_workout_plan(st.session_state.user_id, plan_data)
                    
                    st.success("✅ Workout plan created!")
                    st.markdown(workout_plan)
                    st.balloons()
    
    with col2:
        st.markdown("### 📚 Your Workout Plans")
        
        if st.session_state.workout_plans:
            for i, plan in enumerate(st.session_state.workout_plans[:3]):
                date_str = datetime.fromisoformat(plan['date']).strftime('%b %d, %Y')
                with st.expander(f"💪 {plan['workout_type']} - {date_str}", expanded=(i==0)):
                    st.markdown(f"**Duration:** {plan['duration']} min")
                    st.markdown(f"**Frequency:** {plan['frequency']}x/week")
                    st.markdown(f"**Level:** {plan['fitness_level']}")
                    if st.button(f"📋 View Full Plan", key=f"view_plan_{i}"):
                        st.markdown(plan['plan'])
        else:
            st.info("💪 No workout plans yet. Create your first one!")
        
        st.markdown("### 💡 Exercise Benefits for Liver Health")
        st.success("""
        **Regular exercise helps:**
        ✅ Reduce liver fat by 20-40%
        ✅ Improve insulin sensitivity
        ✅ Support weight loss
        ✅ Decrease inflammation
        ✅ Boost overall health
        
        **Target:** 150+ min/week
        **Intensity:** Moderate
        **Consistency is key!**
        """)

def medication_analysis_page():
    """Medication Tracking and Analysis"""
    st.markdown("## 💊 Medication Tracker & Analysis")
    st.markdown("*Track medications and get AI-powered safety analysis for fatty liver patients*")
    
    tab1, tab2 = st.tabs(["➕ Add Medication", "📋 My Medications"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("medication_form"):
                st.markdown("### 💊 Medication Details")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    med_name = st.text_input("Medication Name*", placeholder="E.g., Vitamin E")
                    dosage = st.text_input("Dosage*", placeholder="E.g., 800 IU, 500mg")
                
                with col_b:
                    med_purpose = st.selectbox("Purpose/Indication",
                        ["Liver Support", "Diabetes Management", "Cholesterol Management",
                         "Blood Pressure", "Vitamin/Supplement", "Pain Relief", "Other"])
                    
                    frequency = st.selectbox("Frequency*",
                        ["Once daily", "Twice daily", "Three times daily", 
                         "As needed", "Other"])
                
                col_c, col_d = st.columns(2)
                with col_c:
                    time_of_day = st.multiselect("Time(s) of Day*",
                        ["Morning", "Afternoon", "Evening", "Night", "With meals"])
                
                with col_d:
                    start_date = st.date_input("Start Date", datetime.now())
                    duration = st.number_input("Duration (days)", 1, 365, 30)
                
                notes = st.text_area("Additional Notes",
                    placeholder="E.g., Take with food, avoid alcohol",
                    height=80)
                
                analyze = st.form_submit_button("🔬 Add & Analyze Medication", use_container_width=True, type="primary")
                
                if analyze and med_name and dosage:
                    with st.spinner("🔬 Analyzing medication safety for fatty liver patients..."):
                        progress = st.progress(0)
                        for i in range(100):
                            time.sleep(0.01)
                            progress.progress(i + 1)
                        
                        
                        if ai and ai.enabled:
                            prompt = f"""
Analyze the following medication for a patient with fatty liver disease:

MEDICATION INFORMATION:
- Name: {med_name}
- Dosage: {dosage}
- Purpose: {med_purpose}
- Frequency: {frequency}
- Timing: {', '.join(time_of_day)}

Please provide:
1. **General Information**: What is this medication and what is it used for?
2. **Liver Safety Assessment**: Is this medication safe for fatty liver patients? (Safe/Caution/Risk)
3. **Hepatotoxicity Risk**: Does this medication have known liver toxicity?
4. **Metabolism**: How is this medication processed by the liver?
5. **Drug Interactions**: Common interactions that may affect liver health
6. **Side Effects**: Liver-related side effects to watch for
7. **Monitoring**: What tests/monitoring is recommended?
8. **Recommendations**: Specific advice for fatty liver patients taking this medication
9. **Alternatives**: If risky, suggest liver-friendly alternatives

Be evidence-based and provide specific, actionable guidance.
"""
                            messages = [
                                {"role": "system", "content": "You are a clinical pharmacist specializing in hepatology. Provide detailed medication safety assessments for fatty liver disease patients based on current medical literature."},
                                {"role": "user", "content": prompt}
                            ]
                            analysis = ai.chat_completion(messages, temperature=0.3, max_tokens=1200)
                        else:
                            analysis = f"""### 💊 Medication Analysis: {med_name}

**Dosage:** {dosage}
**Purpose:** {med_purpose}
**Frequency:** {frequency}

---

#### 🏥 General Information
{med_name} is commonly used for {med_purpose.lower()}. 

#### ✅ Liver Safety Assessment: GENERALLY SAFE
Most standard medications can be used safely with fatty liver disease when monitored appropriately.

#### 🫀 Hepatotoxicity Risk: LOW TO MODERATE
- Monitor liver enzymes periodically
- Report any unusual symptoms to your doctor

#### 🔄 Metabolism
This medication is processed through the liver. Regular monitoring is recommended for patients with liver conditions.

#### ⚠️ Important Considerations
1. Take as prescribed by your healthcare provider
2. Avoid alcohol consumption
3. Do not exceed recommended dosage
4. Report side effects: jaundice, dark urine, severe fatigue
5. Regular liver function tests recommended

#### 💡 Recommendations for Fatty Liver Patients
- Continue healthy lifestyle modifications
- Maintain regular medical follow-ups
- Monitor for any adverse effects
- Discuss all medications with your hepatologist

---

**⚠️ IMPORTANT:** This is an AI-generated analysis for informational purposes only. Always consult your healthcare provider or pharmacist for personalized medical advice about medications.

*💡 Add OpenAI API key for detailed AI-powered medication analysis with evidence-based recommendations!*"""
                        
                        med_data = {
                            "date_added": datetime.now().isoformat(),
                            "medication_name": med_name,
                            "dosage": dosage,
                            "purpose": med_purpose,
                            "frequency": frequency,
                            "time_of_day": time_of_day,
                            "start_date": start_date.isoformat(),
                            "duration_days": duration,
                            "end_date": (start_date + pd.Timedelta(days=duration)).isoformat(),
                            "notes": notes,
                            "analysis": analysis,
                            "active": True
                        }
                        # # ADD VALIDATION HERE (HIGHEST PRIORITY):
                        # validator = MedicalAIValidator()
                        # validated_analysis, validation = validator.validate_and_display(analysis, "medication")
            
                        # # Display validation
                        # st.markdown("---")
                        # st.markdown("### 🔍 Safety Check")
                        # validator.display_validation_badge(validation)
                        # st.markdown("---")
            
                        # # Only show medication analysis if it passes critical checks
                        # if validation.get("recommendation") != "DO NOT SHOW TO PATIENT":
                        #     st.markdown(validated_analysis)
                        # else:
                        #     st.error("❌ CRITICAL: This medication analysis has safety issues and cannot be displayed")
                        #     st.error("Detected issues:")
                        # for issue in validation.get("issues", []):
                        #     st.error(f"  • {issue}")
                        st.session_state.medications.insert(0, med_data)
                        
                        if HELPERS_AVAILABLE:
                            db = init_firebase()
                            db.save_medication(st.session_state.user_id, med_data)
                        
                        st.success(f"✅ {med_name} added successfully!")
                        st.markdown("---")
                        st.markdown("### 🔬 Medication Analysis")
                        st.markdown(analysis)
                        st.balloons()
        
        with col2:
            st.markdown("### 💡 Medication Tips")
            st.info("""
            **For Liver Health:**
            ⚠️ Avoid unnecessary meds
            ⚠️ Never exceed dosages
            ⚠️ Avoid mixing with alcohol
            ⚠️ Report all meds to doctors
            ⚠️ Regular liver monitoring
            
            **Common Liver-Safe:**
            ✅ Most vitamins
            ✅ Omega-3 supplements
            ✅ Vitamin E (prescribed)
            ✅ Metformin (diabetes)
            """)
            
            st.markdown("### 🔔 Reminder System")
            st.success("Set reminders for medications to ensure consistent dosing!")
    
    with tab2:
        st.markdown("### 📋 Your Medications")
        
        if st.session_state.medications:
            for i, med in enumerate(st.session_state.medications):
                date_added = datetime.fromisoformat(med['date_added']).strftime('%b %d, %Y')
                end_date = datetime.fromisoformat(med['end_date'])
                days_remaining = (end_date - datetime.now()).days
                
                with st.expander(f"💊 {med['medication_name']} ({med['dosage']}) - Added {date_added}", expanded=(i==0)):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.markdown(f"**Purpose:** {med['purpose']}")
                        st.markdown(f"**Frequency:** {med['frequency']}")
                        st.markdown(f"**Timing:** {', '.join(med['time_of_day'])}")
                    
                    with col_b:
                        st.markdown(f"**Start Date:** {med['start_date']}")
                        st.markdown(f"**Duration:** {med['duration_days']} days")
                        if days_remaining > 0:
                            st.markdown(f"**Days Remaining:** {days_remaining}")
                            st.progress(1 - (days_remaining / med['duration_days']))
                        else:
                            st.markdown("**Status:** ✅ Completed")
                    
                    if med.get('notes'):
                        st.markdown(f"**Notes:** {med['notes']}")
                    
                    st.markdown("---")
                    
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        if st.button("📖 View Analysis", key=f"view_analysis_{i}", use_container_width=True):
                            st.markdown(med['analysis'])
                    with col_btn2:
                        if st.button("✅ Mark Taken", key=f"taken_{i}", use_container_width=True):
                            st.success("Logged!")
                    with col_btn3:
                        if st.button("🗑️ Delete", key=f"del_med_{i}", use_container_width=True):
                            st.session_state.medications.pop(i)
                            st.rerun()
        else:
            st.info("💊 No medications tracked yet. Add your first medication in the 'Add Medication' tab!")
        
        if st.session_state.medications:
            st.markdown("---")
            st.markdown("### 📊 Medication Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Active Medications", len([m for m in st.session_state.medications if (datetime.fromisoformat(m['end_date']) - datetime.now()).days > 0]))
            with col2:
                st.metric("Total Tracked", len(st.session_state.medications))
            with col3:
                st.metric("Completed", len([m for m in st.session_state.medications if (datetime.fromisoformat(m['end_date']) - datetime.now()).days <= 0]))

def health_report_dashboard():
    """Comprehensive Health Report and Dashboard"""
    st.markdown("## 📊 Health Reports & Analytics")
    st.markdown("*Comprehensive view of your fatty liver disease management journey*")
    
    tab1, tab2, tab3 = st.tabs(["📈 Dashboard Overview", "📄 Generate Report", "📊 Visualizations"])
    
    with tab1:
        st.markdown("### 🎯 Your Health at a Glance")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="stat-card">
                <div style="font-size: 2rem;">🍽️</div>
                <div class="stat-number">{}</div>
                <div>Meals Logged</div>
            </div>
            """.format(len(st.session_state.nutrition_logs)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="stat-card">
                <div style="font-size: 2rem;">💪</div>
                <div class="stat-number">{}</div>
                <div>Workout Plans</div>
            </div>
            """.format(len(st.session_state.workout_plans)), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="stat-card">
                <div style="font-size: 2rem;">💊</div>
                <div class="stat-number">{}</div>
                <div>Medications</div>
            </div>
            """.format(len(st.session_state.medications)), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="stat-card">
                <div style="font-size: 2rem;">⚖️</div>
                <div class="stat-number">{}</div>
                <div>Assessments</div>
            </div>
            """.format(len(st.session_state.risk_assessments)), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("### 📅 Recent Activity")
            
            all_activities = []
            
            for log in st.session_state.nutrition_logs[:5]:
                date_obj = datetime.fromisoformat(log['date'])
                all_activities.append({
                    'date': date_obj,
                    'type': '🍽️ Meal',
                    'description': log.get('meal_type', 'Meal logged')
                })
            
            for plan in st.session_state.workout_plans[:3]:
                date_obj = datetime.fromisoformat(plan['date'])
                all_activities.append({
                    'date': date_obj,
                    'type': '💪 Workout',
                    'description': f"{plan['workout_type']} plan created"
                })
            
            for assessment in st.session_state.risk_assessments[:2]:
                date_obj = datetime.fromisoformat(assessment['assessment_date'])
                all_activities.append({
                    'date': date_obj,
                    'type': '⚖️ Assessment',
                    'description': 'Risk assessment completed'
                })
            
            all_activities.sort(key=lambda x: x['date'], reverse=True)
            
            if all_activities:
                for activity in all_activities[:10]:
                    st.markdown(f"**{activity['type']}** - {activity['date'].strftime('%b %d, %I:%M %p')}")
                    st.markdown(f"_{activity['description']}_")
                    st.markdown("---")
            else:
                st.info("Start using Liver Buddy to see your activity timeline!")
        
        with col_b:
            st.markdown("### 🎯 Health Goals Progress")
            
            if len(st.session_state.nutrition_logs) > 0:
                st.markdown("#### 🍽️ Nutrition Goals")
                liver_friendly_count = len([log for log in st.session_state.nutrition_logs if 'excellent' in log.get('analysis', '').lower() or 'good' in log.get('analysis', '').lower()])
                total_meals = len(st.session_state.nutrition_logs)
                percentage = (liver_friendly_count / total_meals * 100) if total_meals > 0 else 0
                
                st.progress(percentage / 100)
                st.markdown(f"**{percentage:.0f}%** of meals are liver-friendly ({liver_friendly_count}/{total_meals})")
                
                st.markdown("#### 💪 Exercise Goals")
                workout_count = len(st.session_state.workout_plans)
                st.progress(min(workout_count / 12, 1.0))
                st.markdown(f"**{workout_count}/12** workout plans created")
                
                st.markdown("#### 📊 Overall Health Score")
                health_score = min(50 + (percentage * 0.3) + (workout_count * 3), 100)
                st.progress(health_score / 100)
                st.markdown(f"**{health_score:.0f}/100** - {'Excellent' if health_score >= 80 else 'Good' if health_score >= 60 else 'Fair'}")
            else:
                st.info("Start tracking your nutrition and exercise to see progress!")
    
    with tab2:
        st.markdown("### 📄 Generate Comprehensive Health Report")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            report_type = st.selectbox("Report Type",
                ["Weekly Summary", "Monthly Summary", "Custom Date Range", "Complete History"])
            
            if report_type == "Custom Date Range":
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input("Start Date", datetime.now() - pd.Timedelta(days=30))
                with col_date2:
                    end_date = st.date_input("End Date", datetime.now())
            
            include_sections = st.multiselect("Include Sections",
                ["Executive Summary", "Nutrition Analysis", "Exercise Summary", 
                 "Medication List", "Risk Assessments", "Recommendations", "Visualizations"],
                default=["Executive Summary", "Nutrition Analysis", "Exercise Summary", "Recommendations"])
            
            if st.button("📊 Generate Report", type="primary", use_container_width=True):
                with st.spinner("📝 Generating your comprehensive health report..."):
                    progress = st.progress(0)
                    for i in range(100):
                        time.sleep(0.02)
                        progress.progress(i + 1)
                    
                    report_date = datetime.now().strftime('%B %d, %Y')
                    
                    report = f"""# 🫀 LIVER BUDDY - HEALTH REPORT
**Patient:** {st.session_state.user_profile.get('fullName', 'User')}
**Report Date:** {report_date}
**Report Type:** {report_type}

---

"""
                    
                    if "Executive Summary" in include_sections:
                        liver_friendly = len([log for log in st.session_state.nutrition_logs if 'excellent' in log.get('analysis', '').lower() or 'good' in log.get('analysis', '').lower()])
                        total_meals = len(st.session_state.nutrition_logs)
                        compliance_rate = (liver_friendly / total_meals * 100) if total_meals > 0 else 0
                        
                        report += f"""## 📊 EXECUTIVE SUMMARY

**Overall Health Status:** {"Excellent Progress" if compliance_rate >= 80 else "Good Progress" if compliance_rate >= 60 else "Fair Progress"}
**Liver-Friendly Diet Compliance:** {compliance_rate:.0f}%

### Key Metrics:
- **Total Meals Logged:** {len(st.session_state.nutrition_logs)}
- **Workout Plans Created:** {len(st.session_state.workout_plans)}
- **Medications Tracked:** {len(st.session_state.medications)}
- **Risk Assessments:** {len(st.session_state.risk_assessments)}

### Quick Stats:
- **Active Days:** {len(set(log['date'][:10] for log in st.session_state.nutrition_logs))} days
- **Average Meals/Day:** {len(st.session_state.nutrition_logs) / max(len(set(log['date'][:10] for log in st.session_state.nutrition_logs)), 1):.1f}
- **Liver-Friendly Meals:** {liver_friendly}/{total_meals}

---

"""
                    
                    if "Nutrition Analysis" in include_sections and st.session_state.nutrition_logs:
                        report += f"""## 🍽️ NUTRITION ANALYSIS

### Overview:
You have logged **{len(st.session_state.nutrition_logs)} meals** during this period.

### Meal Distribution:
"""
                        meal_counts = {}
                        for log in st.session_state.nutrition_logs:
                            meal_type = log.get('meal_type', 'Unknown')
                            meal_counts[meal_type] = meal_counts.get(meal_type, 0) + 1
                        
                        for meal_type, count in sorted(meal_counts.items(), key=lambda x: x[1], reverse=True):
                            report += f"- **{meal_type}:** {count} meals\n"
                        
                        report += f"""
### Nutrition Quality:
- **Liver-Friendly Meals:** {liver_friendly} ({compliance_rate:.0f}%)
- **Meals Needing Improvement:** {total_meals - liver_friendly}

### Top Recommendations:
1. Continue focusing on whole, unprocessed foods
2. Maintain high vegetable intake
3. Choose lean proteins (fish, chicken, legumes)
4. Limit added sugars and refined carbohydrates
5. Stay hydrated with water and green tea

---

"""
                    
                    if "Exercise Summary" in include_sections and st.session_state.workout_plans:
                        report += f"""## 💪 EXERCISE SUMMARY

You have created **{len(st.session_state.workout_plans)} workout plans** during this period.

### Workout Types:
"""
                        workout_types = {}
                        for plan in st.session_state.workout_plans:
                            wtype = plan['workout_type']
                            workout_types[wtype] = workout_types.get(wtype, 0) + 1
                        
                        for wtype, count in sorted(workout_types.items(), key=lambda x: x[1], reverse=True):
                            report += f"- **{wtype}:** {count} plan(s)\n"
                        
                        report += f"""
### Exercise Benefits for Fatty Liver:
- Regular exercise reduces liver fat by 20-40%
- Improves insulin sensitivity
- Supports healthy weight management
- Reduces systemic inflammation

### Recommendations:
- Target: 150-300 minutes of moderate activity per week
- Include both aerobic and resistance training
- Maintain consistency over intensity
- Monitor progress and adjust as needed

---

"""
                    
                    if "Medication List" in include_sections and st.session_state.medications:
                        report += f"""## 💊 MEDICATION SUMMARY

**Active Medications:** {len([m for m in st.session_state.medications if (datetime.fromisoformat(m['end_date']) - datetime.now()).days > 0])}

### Current Medications:
"""
                        for med in st.session_state.medications:
                            days_remaining = (datetime.fromisoformat(med['end_date']) - datetime.now()).days
                            status = "Active" if days_remaining > 0 else "Completed"
                            report += f"""
**{med['medication_name']}** ({med['dosage']})
- Purpose: {med['purpose']}
- Frequency: {med['frequency']}
- Status: {status}
"""
                        
                        report += """
### Important Reminders:
- Take all medications as prescribed
- Avoid alcohol while on medication
- Report any side effects to your healthcare provider
- Regular liver function monitoring recommended

---

"""
                    
                    if "Risk Assessments" in include_sections and st.session_state.risk_assessments:
                        latest_assessment = st.session_state.risk_assessments[0]
                        report += f"""## ⚖️ RISK ASSESSMENT SUMMARY

**Latest Assessment Date:** {datetime.fromisoformat(latest_assessment['assessment_date']).strftime('%B %d, %Y')}
**BMI:** {latest_assessment['bmi']}
**Total Assessments:** {len(st.session_state.risk_assessments)}

### Key Risk Factors Identified:
"""
                        if latest_assessment.get('risk_factors'):
                            for factor in latest_assessment['risk_factors']:
                                if factor != 'None':
                                    report += f"- {factor}\n"
                        
                        report += """
### Monitoring Recommendations:
- Regular liver function tests (ALT, AST, GGT)
- Periodic FibroScan or ultrasound
- Monitor weight and BMI
- Track symptoms and overall wellbeing

---

"""
                    
                    if "Recommendations" in include_sections:
                        report += f"""## 🎯 PERSONALIZED RECOMMENDATIONS

### Dietary Recommendations:
1. **Increase:** Leafy greens, fatty fish (salmon), nuts, olive oil, whole grains
2. **Moderate:** Lean meats, low-fat dairy, fruits (watch portions)
3. **Limit:** Processed foods, added sugars, refined carbs, saturated fats
4. **Avoid:** Alcohol, fried foods, high-fructose corn syrup

### Lifestyle Modifications:
1. **Weight Management:** Aim for 5-10% weight loss if overweight
2. **Physical Activity:** 150-300 minutes/week of moderate exercise
3. **Sleep Hygiene:** 7-9 hours of quality sleep nightly
4. **Stress Management:** Practice relaxation techniques daily

### Medical Follow-up:
1. Schedule regular check-ups with your hepatologist
2. Monitor liver enzymes every 3-6 months
3. Consider FibroScan annually
4. Discuss all medications and supplements with your doctor

### Action Items for Next Month:
- [ ] Log at least 60 meals (2/day average)
- [ ] Complete 12+ exercise sessions
- [ ] Achieve 90% liver-friendly meal compliance
- [ ] Schedule follow-up medical appointment
- [ ] Maintain medication adherence

---

"""
                    
                    report += f"""## 📈 PROGRESS TRACKING

### Achievements:
✅ Logged {len(st.session_state.nutrition_logs)} meals
✅ Created {len(st.session_state.workout_plans)} workout plans
✅ Tracked {len(st.session_state.medications)} medications
✅ Completed {len(st.session_state.risk_assessments)} risk assessment(s)

### Areas for Improvement:
- Continue consistent meal logging
- Increase exercise frequency if below target
- Maintain liver-friendly food choices
- Regular medical monitoring

---

## ⚠️ IMPORTANT DISCLAIMER

This report is generated by Liver Buddy for informational and tracking purposes only. It does not constitute medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for personalized medical guidance regarding fatty liver disease management.

**Generated by:** Liver Buddy AI System
**Report ID:** LB-{datetime.now().strftime('%Y%m%d%H%M%S')}

---

*Continue your journey with Liver Buddy. Consistency is key to managing fatty liver disease!* 🫀
"""
                    
                    st.success("✅ Report generated successfully!")
                    st.markdown("---")
                    
                    with st.expander("📄 View Full Report", expanded=True):
                        st.markdown(report)
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            "📥 Download as Text",
                            report,
                            f"liver_buddy_report_{datetime.now().strftime('%Y%m%d')}.txt",
                            use_container_width=True
                        )
                    with col_dl2:
                        if st.button("📧 Email Report", use_container_width=True):
                            st.info("💡 Email feature coming soon!")
        
        with col2:
            st.markdown("### 💡 Report Tips")
            st.info("""
            **Report includes:**
            ✅ Nutrition summary
            ✅ Exercise tracking
            ✅ Medication list
            ✅ Risk assessment
            ✅ Personalized advice
            ✅ Progress metrics
            
            **Best for:**
            📋 Doctor appointments
            📊 Progress tracking
            📈 Goal setting
            🎯 Self-monitoring
            """)
    
    with tab3:
        st.markdown("### 📊 Data Visualizations")
        
        if len(st.session_state.nutrition_logs) >= 3:
            st.markdown("#### 📅 Meal Logging Frequency (Last 30 Days)")
            
            dates = [datetime.fromisoformat(log['date']).date() for log in st.session_state.nutrition_logs]
            date_counts = pd.Series(dates).value_counts().sort_index()
            
            st.line_chart(date_counts)
            
            st.markdown("#### 🍽️ Meal Type Distribution")
            meal_types = [log.get('meal_type', 'Unknown') for log in st.session_state.nutrition_logs]
            meal_type_df = pd.DataFrame({'Meal Type': meal_types})
            meal_type_counts = meal_type_df['Meal Type'].value_counts()
            
            st.bar_chart(meal_type_counts)
            
            st.markdown("#### 💪 Activity Overview")
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                activity_data = {
                    'Activity': ['Meals', 'Workouts', 'Medications', 'Assessments'],
                    'Count': [
                        len(st.session_state.nutrition_logs),
                        len(st.session_state.workout_plans),
                        len(st.session_state.medications),
                        len(st.session_state.risk_assessments)
                    ]
                }
                activity_df = pd.DataFrame(activity_data)
                st.bar_chart(activity_df.set_index('Activity'))
            
            with col_v2:
                st.markdown("##### 📈 Trend Analysis")
                unique_days = len(set(log['date'][:10] for log in st.session_state.nutrition_logs))
                avg_meals_per_day = len(st.session_state.nutrition_logs) / max(unique_days, 1)
                
                st.metric("Days Active", unique_days)
                st.metric("Avg Meals/Day", f"{avg_meals_per_day:.1f}")
                st.metric("Consistency Score", f"{min(unique_days * 3, 100)}%")
        else:
            st.info("📊 Log more meals and activities to see visual analytics!")

def main_app():
    """Main application with sidebar navigation"""
    
    with st.sidebar:
        # User Profile Section
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 15px; margin-bottom: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">👤</div>
            <h3 style="margin: 0; color: white;">{st.session_state.user_profile.get('fullName', 'User')}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">{st.session_state.user_email}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🧭 Navigation")
        page = st.radio(
            "Navigate",
            [
                "👤 Patient Profile",
                "🍽️ Smart Meal Planner",
                "📊 Nutrition Dashboard",
                "⚖️ Risk Assessment",
                "💪 Workout Plans",
                "💊 Medications",
                "📊 Health Reports"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick Stats
        st.markdown("### 📈 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Meals", len(st.session_state.nutrition_logs))
        with col2:
            st.metric("Workouts", len(st.session_state.workout_plans))
        
        st.metric("Medications", len(st.session_state.medications))
        
        st.markdown("---")
        
        # Health Tip of the Day
        st.markdown("### 💡 Daily Tip")
        tips = [
            "Drink green tea - it's great for liver health!",
            "Aim for 10,000 steps today!",
            "Add colorful vegetables to every meal",
            "Stay hydrated - water helps flush toxins",
            "Get 7-9 hours of quality sleep tonight",
            "Practice stress-relief: try 5 minutes of deep breathing"
        ]
        import random
        st.info(tips[datetime.now().day % len(tips)])
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            if HELPERS_AVAILABLE:
                logout_user()
            else:
                for key in ['logged_in', 'user_email', 'user_id', 'user_profile']:
                    if key in st.session_state:
                        st.session_state[key] = None if key != 'logged_in' else False
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; opacity: 0.7; font-size: 0.8rem;">
            <p>🫀 <b>Liver Buddy</b></p>
            <p>v1.0 | Powered by AI</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main Content
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting, emoji = "Good Morning", "🌅"
    elif current_hour < 18:
        greeting, emoji = "Good Afternoon", "☀️"
    else:
        greeting, emoji = "Good Evening", "🌙"
    
    st.markdown(f"""
    <div style="background: white; padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <h2 style="margin: 0; color: #667eea;">{emoji} {greeting}, {st.session_state.user_profile.get('fullName', 'User')}!</h2>
        <p style="margin: 0.5rem 0 0 0; color: #666;">Managing your fatty liver disease, one healthy choice at a time</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to pages
    if page == "👤 Patient Profile":
        patient_profile_page()
    elif page == "🍽️ Smart Meal Planner":
        smart_meal_planner_page()
    elif page == "📊 Nutrition Dashboard":
        nutrition_tracker_dashboard()
    elif page == "⚖️ Risk Assessment":
        risk_assessment_page()
    elif page == "💪 Workout Plans":
        workout_planner_page()
    elif page == "💊 Medications":
        medication_analysis_page()
    elif page == "📊 Health Reports":
        health_report_dashboard()

# Main app logic
if not st.session_state.logged_in:
    login_page()
else:
    main_app()