# main.py
import streamlit as st
import uuid  # Add this import at the top of the file
import pandas as pd

# Page config
st.set_page_config(
    page_title="Palm Oil Seed Management System",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)
from datetime import datetime
import hashlib
import re
import time
from customer_module import (
    show_customer_catalog, 
    show_customer_cart, 
    show_customer_tracking,
    initialize_session_state
)
from notification import (
    show_production_notifications,
    show_notifications_customer,
    show_marketing_notifications,
    initialize_notifications
)
from production_module import (
    show_production_dashboard,
    show_pending_orders,
    show_inventory_management,
    show_order_history
)
from marketing_module import (
    show_marketing_dashboard,
    show_customer_support,
    show_inventory_management
)


# User roles and their corresponding pages
ROLE_PAGES = {
    'customer': {
        'catalog': {'title': '📗 Catalog', 'function': show_customer_catalog},
        'cart': {'title': '🛒 My Cart', 'function': show_customer_cart},
        'tracking': {'title': '📦 Order Tracking', 'function': show_customer_tracking},
        'notification_customer': {'title': '🔔 Notifications', 'function': show_notifications_customer}
    },
    'production': {
        'dashboard': {'title': '📋 Dashboard', 'function': show_production_dashboard},
        'pending_orders': {'title': '📦 Pending Orders', 'function': show_pending_orders},
        'order_history': {'title': '📚 Order History', 'function': show_order_history},
        'inventory': {'title': '📊 Inventory', 'function': show_inventory_management},\
        'production_notifications': {'title': '🔔 Notifications', 'function': show_production_notifications}
    },
    'marketing': {
        'dashboard': {'title': '📊 Dashboard', 'function': show_marketing_dashboard},
        'inventory': {'title': '📊 Inventory', 'function': show_inventory_management},
        'customer_support': {'title': '👥 Customer Support', 'function': show_customer_support},
        'marketing_notifications': {'title': '🔔 Notifications', 'function': show_marketing_notifications}
    }
}

def init_session_state():
    """Initialize all session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'landing'
    
    # Initialize module-specific session states
    initialize_session_state()
    
    # Initialize existing session state variables
    if 'customers' not in st.session_state:
        st.session_state.customers = {}
        
        # Add sample customer account
        sample_password = "customer123"
        password_hash = hashlib.sha256(sample_password.encode()).hexdigest()
        
        sample_customer = {
            'customer_id': 'sample123',
            'email': 'customer@example.com',
            'password_hash': password_hash,
            'company_name': 'Sample Company',
            'contact_name': 'John Doe',
            'status': 'verified',  # Important: set to verified to allow login
            'role': 'customer'
        }
        
        # Add to customers and auth_db
        st.session_state.customers['customer@example.com'] = sample_customer
        
        if 'auth_db' not in st.session_state:
            st.session_state.auth_db = {}
            
        st.session_state.auth_db['customer@example.com'] = {
            'password_hash': password_hash,
            'role': 'customer',
            'name': 'John Doe'
        }
         # Add production staff account
        st.session_state.auth_db['production1'] = {
            'password_hash': hashlib.sha256('production123'.encode()).hexdigest(),
            'role': 'production',
            'name': 'Production Staff'
        }
        
        # Add marketing staff account
        st.session_state.auth_db['marketing1'] = {
            'password_hash': hashlib.sha256('marketing123'.encode()).hexdigest(),
            'role': 'marketing',
            'name': 'Marketing Staff'
        }
        

def authenticate(username, password):
    """Authenticate user credentials."""
    if username in st.session_state.auth_db:
        stored_user = st.session_state.auth_db[username]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return stored_user['password_hash'] == password_hash
    return False

def get_user_role(username):
    """Get user role from auth database."""
    if username in st.session_state.auth_db:
        return st.session_state.auth_db[username]['role']
    return None

def show_sidebar():
    """Display sidebar navigation based on user role"""
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.user_name}")
        st.divider()
        
        # Get pages for current user role
        role_pages = ROLE_PAGES.get(st.session_state.user_role, {})
        
        # Show navigation options
        for page_id, page_info in role_pages.items():
            # Add notification count for notification pages
            if 'notification' in page_id:
                count = get_notification_count(st.session_state.user_role)
                title = f"{page_info['title']} ({count})" if count > 0 else page_info['title']
            else:
                title = page_info['title']
            
            if st.button(title, key=f"nav_{page_id}", use_container_width=True):
                st.session_state.current_page = page_id
                st.rerun()
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.current_page = 'landing'
            st.rerun()

def get_notification_count(role):
    """Get number of unread notifications for the specified role"""
    if role == 'customer':
        return len([n for n in st.session_state.get('notification_customer', []) 
                   if not n.get('read', False)])
    elif role == 'production':
        return len([n for n in st.session_state.get('production_notifications', []) 
                   if not n.get('read', False)])
    elif role == 'marketing':
        marketing_count = len([n for n in st.session_state.get('marketing_notifications', []) 
                             if not n.get('read', False)])
        do_count = len([order for order in st.session_state.get('orders', [])
                       if order.get('status') == 'do_generated' 
                       and not order.get('notification_read', False)])
        return marketing_count + do_count
    return 0

def main():
    # Initialize session state
    init_session_state()
    initialize_notifications()
    
    # Show different pages based on authentication state
    if not st.session_state.authenticated:
        if st.session_state.current_page == 'landing':
            show_landing_page()
        elif st.session_state.current_page == 'login':
            show_login()
        elif st.session_state.current_page == 'signup':
            show_signup()
        else:
            show_landing_page()  # Default to landing page if page not specified
    else:
        # Show sidebar and content for authenticated users
        show_sidebar()
        
        # Get current page function
        role_pages = ROLE_PAGES.get(st.session_state.user_role, {})
        current_page = role_pages.get(st.session_state.current_page)
        
        if current_page:
            show_navigation_bar() 
            current_page['function']()
        else:
            # Show default page for role
            show_navigation_bar()  
            if st.session_state.user_role == 'customer':
                show_customer_catalog()
            elif st.session_state.user_role == 'marketing':
                show_marketing_dashboard()
            elif st.session_state.user_role == 'production':
                show_production_dashboard()

def show_navigation_bar():
    """Show a persistent navigation bar at the top"""
    # Add custom CSS for navigation bar
    st.markdown("""
        <style>
        div[data-testid="stToolbar"] {
            z-index: 998;
        }
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            padding: 1rem 3rem;
            background-color: #ffffff;
            border-bottom: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        /* Adjust main content padding */
        .main .block-container {
            padding-top: 5rem;
            margin-top: 30px;
        }
        /* Ensure navbar stays above other elements */
        div.stButton > button {
            z-index: 1001;
            position: relative;
        }
        .nav-title {
            color: #2E7D32;
            font-size: 1.5rem;
            font-weight: bold;
            text-decoration: none;
            white-space: nowrap;
        }
        .nav-button {
            background-color: #2E7D32;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            border: none;
            transition: background-color 0.3s;
            position: relative;
        }
        .nav-button:hover {
            background-color: #1B5E20;
        }
        </style>
    """, unsafe_allow_html=True)

    # Navigation bar container
    st.markdown('<div class="navbar">', unsafe_allow_html=True)
    
    # Create columns for navigation elements
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    
    with col1:
        # Logo and title
        st.markdown(
            '<div style="display: flex; align-items: center;">'
            '<span style="font-size: 1.8rem; margin-right: 10px;">🌴</span>'
            '<span class="nav-title">Palm Oil Seed Management</span>'
            '</div>',
            unsafe_allow_html=True
        )
    
    # Different navigation options based on authentication state
    if not st.session_state.authenticated:
        with col4:
            if st.button("Login", key="nav_login", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
        with col5:
            if st.button("Sign Up", key="nav_signup", use_container_width=True):
                st.session_state.current_page = 'signup'
                st.rerun()
    else:
        # Show user info and navigation for authenticated users
        with col3:
            # Home button
            if st.button("🏠 Home", key="nav_home", use_container_width=True):
                if st.session_state.user_role == 'customer':
                    st.session_state.current_page = 'catalog'
                else:
                    st.session_state.current_page = 'dashboard'
                st.rerun()
        
        with col4:
            # Notifications with count
            notification_count = get_notification_count(st.session_state.user_role)
            notification_text = f"🔔 Notifications {f'({notification_count})' if notification_count > 0 else ''}"
            
            if st.button(notification_text, key="nav_notifications", use_container_width=True):
                if st.session_state.user_role == 'customer':
                    st.session_state.current_page = 'notification_customer'
                elif st.session_state.user_role == 'marketing':
                    st.session_state.current_page = 'marketing_notifications'
                elif st.session_state.user_role == 'production':
                    st.session_state.current_page = 'production_notifications'
                st.rerun()
        
        with col5:
            # Logout button
            if st.button("Logout", key="nav_logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_landing_page():
    """Show the landing page with send order inquiry"""
    # Show navigation bar
    show_navigation_bar()
    
    # Main content
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 2.5em; color: #2E7D32;'>Premium Palm Oil Seeds</h1>
            <p style='font-size: 1.2em; color: #666;'>
                Discover our high-quality palm oil seeds for your plantation needs
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Features section
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <h3>🌱 Premium Quality</h3>
                <p>High germination rate guaranteed</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <h3>🚚 Fast Delivery</h3>
                <p>Nationwide delivery service</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <h3>💯 Expert Support</h3>
                <p>Professional guidance available</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Inquiry button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Send Order Inquiry", use_container_width=True):
            handle_inquiry_click()

def show_login():
    
       # Add return button at the top left
    if st.button("← Return to Home", key="return_login"):
        st.session_state.current_page = 'landing'
        st.rerun()
    
    # Center the form with some padding
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>Login 🔐</h1>", unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            # Add some spacing
            st.write("")
            
            # Center the login button
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                # Hash the entered password
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                if username in st.session_state.auth_db:
                    stored_user = st.session_state.auth_db[username]
                    
                    if stored_user['password_hash'] == password_hash:
                        st.session_state.authenticated = True
                        st.session_state.user_role = stored_user['role']
                        st.session_state.user_name = stored_user['name']
                        st.session_state.user_email = username
                        
                        # Role-specific redirections
                        if stored_user['role'] == 'customer':
                            st.session_state.current_page = 'catalog'
                        elif stored_user['role'] in ['marketing', 'production']:
                            st.session_state.current_page = 'dashboard'
                        
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid password")
                else:
                    st.error("Username not found")
        
        # Add signup link with button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<p style='text-align: center; margin-top: 1rem;'>Don't have an account?</p>", unsafe_allow_html=True)
            if st.button("Sign up here", key="signup_button", use_container_width=True):
                st.session_state.current_page = 'signup'
                st.rerun()
        
def handle_inquiry_click():
    """Handle click on inquiry button"""
    if not st.session_state.authenticated:
        st.session_state.current_page = 'login'
        st.rerun()
    else:
        if st.session_state.user_role == 'customer':
            st.session_state.current_page = 'catalog'
            st.rerun()

def show_landing_page():
    
    """Show the landing page with navigation buttons and send order inquiry"""
    
    # Navigation buttons in header
    with st.container():
        # Right-aligned buttons
        col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
        with col4:
            if st.button("Sign Up"):
                st.session_state.current_page = 'signup'
                st.rerun()
        with col3:
            if st.button("Login"):
                st.session_state.current_page = 'login'
                st.rerun()

    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 2.5em; color: #2E7D32;'>Premium Palm Oil Seeds</h1>
            <p style='font-size: 1.2em; color: #666;'>
                Discover our high-quality palm oil seeds for your plantation needs
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Features section
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <h3>🌱 Premium Quality</h3>
                <p>High germination rate guaranteed</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <h3>🚚 Fast Delivery</h3>
                <p>Nationwide delivery service</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div style='text-align: center; padding: 1rem;'>
                <h3>💯 Expert Support</h3>
                <p>Professional guidance available</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Show catalog
    show_public_catalog()
    
def show_public_catalog():
    """Display the public catalog page with similar functionality to customer catalog."""
    st.markdown("""
        <style>
        .main-title { font-size: 2.5em; font-weight: bold; margin-bottom: 1em; }
        .sub-title { font-size: 1.5em; color: #666; margin-bottom: 1em; }
        .catalog-container {
            padding: 20px;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            margin-bottom: 20px;
            background-color: #f8f9fa;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-title">🌴 Premium Palm Oil Seeds</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Available Premium Seeds</div>', unsafe_allow_html=True)
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        price_range = st.slider("Price Range ($)", 0, 30, (0, 30))
    with col2:
        sort_by = st.selectbox("Sort by", ["Price: Low to High", "Price: High to Low", "Germination Rate"])
    
    # Sample catalog data - replace with your actual catalog data
    catalog = pd.DataFrame({
        'Seed': ['Premium Palm Seeds', 'Standard Palm Seeds', 'Elite Palm Seeds'],
        'Description': [
            'High-yield palm seeds with excellent germination rate',
            'Quality palm seeds for commercial plantations',
            'Premium grade seeds with superior genetics'
        ],
        'Price': [15.00, 12.00, 18.00],
        'Germination_Rate': [95, 85, 98],
        'Maturity_Period': ['4-5 months', '5-6 months', '4-5 months'],
        'Min_Order': [10, 20, 10],
        'Image': ['path/to/image1.jpg', 'path/to/image2.jpg', 'path/to/image3.jpg']
    })
    
    # Sort catalog
    if sort_by == "Price: Low to High":
        catalog_sorted = catalog.sort_values(by="Price")
    elif sort_by == "Price: High to Low":
        catalog_sorted = catalog.sort_values(by="Price", ascending=False)
    else:
        catalog_sorted = catalog.sort_values(by="Germination_Rate", ascending=False)
    
    # Display catalog
    for _, row in catalog_sorted.iterrows():
        if price_range[0] <= row['Price'] <= price_range[1]:
            st.markdown(f'<div class="catalog-container">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                # You can replace this with actual image display
                st.markdown("🌱")  # Placeholder for image
            with col2:
                st.markdown(f'<div class="sub-title">{row["Seed"]}</div>', unsafe_allow_html=True)
                st.write(row['Description'])
                st.write(f"🌱 Germination Rate: {row['Germination_Rate']}%")
                st.write(f"⏳ Maturity Period: {row['Maturity_Period']}")
                st.write(f"💰 Price: ${row['Price']} per kg")
                st.write(f"📦 Minimum Order: {row['Min_Order']} kg")
            
            with col3:
                if st.button("Send Order Inquiry", key=f"inquiry_{row['Seed']}"):
                    handle_inquiry_click()
            
            st.markdown('</div>', unsafe_allow_html=True)

def handle_inquiry_click():
    """Handle click on inquiry button."""
    if not st.session_state.authenticated:
        st.session_state.current_page = 'login'
        st.rerun()
    else:
        if st.session_state.user_role == 'customer':
            st.session_state.current_page = 'catalog'
            st.rerun()

def redirect_to_chatbot():
    """Redirect to WhatsApp Business chatbot."""
    # Replace with your actual WhatsApp Business link
    whatsapp_link = "https://wa.me/your_number"
    st.markdown(f'<meta http-equiv="refresh" content="0;url={whatsapp_link}">', unsafe_allow_html=True)
    st.info("Redirecting to WhatsApp Business...")
    


def show_signup():
    # Add return button at the top left
    if st.button("← Return to Home", key="return_login"):
        st.session_state.current_page = 'landing'
        st.rerun()
        
    st.subheader("Create an Account")
    
    with st.form("signup_form", clear_on_submit=True):
        # Company Information
        st.markdown("### Company Details")
        company_name = st.text_input("Company Name*")
        company_registration = st.text_input("Company Registration Number*")
        
        # Personal Information
        st.markdown("### Personal Information")
        contact_name = st.text_input("Contact Person Name (as per IC)*")
        ic_number = st.text_input("IC Number*", 
                                placeholder="e.g., 900101-12-3456",
                                help="Format: YYMMDD-PB-XXXX")
        
        # Contact Information
        st.markdown("### Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Business Email*", 
                                placeholder="company@example.com",
                                help="This will be your username for login")
            phone = st.text_input("Mobile Number*", 
                                placeholder="+60xx-xxxxxxx",
                                help="Format: +60xx-xxxxxxx")
        with col2:
            office_phone = st.text_input("Office Phone", 
                                       placeholder="+603-xxxxxxxx",
                                       help="Format: +603-xxxxxxxx")
            address = st.text_area("Business Address*", 
                                 placeholder="Enter your complete business address")
        
        # Document Upload
        st.markdown("### Document Verification")
        ic_front = st.file_uploader("Upload IC (Front)*", 
                                  type=['jpg', 'jpeg', 'png'],
                                  help="Maximum file size: 2MB")
        ic_back = st.file_uploader("Upload IC (Back)*", 
                                 type=['jpg', 'jpeg', 'png'],
                                 help="Maximum file size: 2MB")
        
        # Account Security
        st.markdown("### Account Security")
        password = st.text_input("Password*", 
                               type="password",
                               help="Minimum 8 characters, include numbers and special characters")
        confirm_password = st.text_input("Confirm Password*", 
                                       type="password")
        
        # Terms and Conditions
        agree_terms = st.checkbox("I agree to the Terms and Conditions*")
        agree_privacy = st.checkbox("I agree to the Privacy Policy*")
        
        submitted = st.form_submit_button("Create Account")
        
        if submitted:
            """
            # Validate all required fields
            required_fields = {
                'Company Name': company_name,
                'Company Registration': company_registration,
                'Contact Name': contact_name,
                'IC Number': ic_number,
                'Email': email,
                'Phone': phone,
                'Address': address,
                'IC Front': ic_front,
                'IC Back': ic_back,
                'Password': password,
                'Confirm Password': confirm_password
            }
            
            # Check required fields
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
                return
            
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Please enter a valid email address")
                return
            
            # Validate phone format
            if not re.match(r"^\+60\d{2}-\d{7,8}$", phone):
                st.error("Please enter a valid phone number format: +60xx-xxxxxxx")
                return
            
            # Validate IC number format
            if not re.match(r"^\d{6}-\d{2}-\d{4}$", ic_number):
                st.error("Please enter a valid IC number format: YYMMDD-PB-XXXX")
                return
            
            # Validate password
            if len(password) < 8:
                st.error("Password must be at least 8 characters long")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            """
            # Check terms agreement
            if not (agree_terms and agree_privacy):
                st.error("Please agree to both Terms and Conditions and Privacy Policy")
                return
            
            try:
                # Create customer account with all information
                create_customer_account(
                    email=email,  # Use email as username
                    password=password,
                    company_name=company_name,
                    company_registration=company_registration,
                    contact_name=contact_name,
                    ic_number=ic_number,
                    phone=phone,
                    office_phone=office_phone,
                    address=address,
                    ic_front=ic_front,
                    ic_back=ic_back,
                )
                
                # Set session state for immediate login
                st.session_state.authenticated = True
                st.session_state.user_role = 'customer'
                st.session_state.user_name = contact_name
                st.session_state.user_email = email
                st.session_state.current_page = 'catalog'  # Redirect to catalog
                
                st.success("Account created successfully!")
                time.sleep(1)  # Brief pause to show success message
                st.rerun()  # Refresh to show catalog
                
            except Exception as e:
                st.error(f"Error creating account: {str(e)}")

def create_customer_account(email, password, company_name, company_registration, 
                          contact_name, ic_number, phone, office_phone, address,
                          ic_front, ic_back):
    """Create a new customer account with verification documents."""
    try:
        # Initialize customers in session state if it doesn't exist
        if 'customers' not in st.session_state:
            st.session_state.customers = {}
        
        # Check if email already exists
        if email in st.session_state.customers:
            raise ValueError("An account with this email already exists")
        
        # Generate a unique customer ID
        customer_id = str(uuid.uuid4())
        
        # Save uploaded documents
        doc_paths = {}
        if ic_front:
            doc_paths['ic_front'] = f"uploads/{customer_id}_ic_front.{ic_front.type.split('/')[-1]}"
        if ic_back:
            doc_paths['ic_back'] = f"uploads/{customer_id}_ic_back.{ic_back.type.split('/')[-1]}"
        
        # Hash password for security
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create customer record - Set status to verified directly
        customer_data = {
            'customer_id': customer_id,
            'email': email,
            'password_hash': password_hash,
            'company_name': company_name,
            'company_registration': company_registration,
            'contact_name': contact_name,
            'ic_number': ic_number,
            'phone': phone,
            'office_phone': office_phone,
            'address': address,
            'document_paths': doc_paths,
            'status': 'verified',  # Changed from 'pending_verification' to 'verified'
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'verified_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Set verification time
            'role': 'customer'
        }
        
        # Save customer data to session state
        st.session_state.customers[email] = customer_data
        
        # Update authentication database for login
        if 'auth_db' not in st.session_state:
            st.session_state.auth_db = {}
        
        st.session_state.auth_db[email] = {
            'password_hash': password_hash,
            'role': 'customer',
            'name': contact_name
        }
        
        return customer_data
        
    except Exception as e:
        raise Exception(f"Failed to create account: {str(e)}")

if __name__ == "__main__":
    main()
