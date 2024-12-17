# customer_module.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
import re
import time
from notification import create_notification, show_notifications_customer


st.markdown("""
    <style>
    .main-container { padding: 2rem; display: flex; flex-direction: column; align-items: center; }
    .catalog-container { padding: 20px; border: 1px solid #e2e8f0; border-radius: 15px; margin-bottom: 20px; background-color: #f8f9fa; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    .order-card{background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid #e5e7eb; transition: transform 0.2s ease;}
    .order-card:hover {transform: translateY(-2px);}
    .order-header {display: flex;justify-content: space-between;align-items: center; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb;}
    
    /* Responsive styles */
    @media (max-width: 640px) {
    .order-header {
        flex-direction: column;
        align-items: flex-start;
    }
    .filter-container {
        flex-direction: column;
    }
    
    .tracking-status {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 500;
        margin-top: 8px;
    }
    
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
    }
    
    .status-rejected {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .status-verified {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-processing {
        background-color: #cce5ff;
        color: #004085;
        border: 1px solid #b8daff;
    }
    
    .status-completed {
        background-color: #d1e7dd;
        color: #0f5132;
        border: 1px solid #badbcc;
    }
    
    .status-ready {
        background-color: #d1e7dd;
        color: #0f5132;
        border: 1px solid #badbcc;
    }
    
    .status-default {
        background-color: #e2e3e5;
        color: #383d41;
        border: 1px solid #d6d8db;
    }
    </style>
""", unsafe_allow_html=True)

# Update ORDER_STATUS dictionary
ORDER_STATUS = {
    'PENDING_MARKETING': 'pending_marketing_approval',
    'PENDING_PAYMENT_TERM': 'pending_payment_term',
    'PENDING_PAYMENT_APPROVAL': 'pending_payment_approval',
    'PAYMENT_TERM_REJECTED': 'payment_term_rejected',
    'PENDING_PAYMENT': 'pending_payment',
    'PAYMENT_VERIFIED': 'payment_verified',
    'PENDING_PRODUCTION': 'pending_production',
    'IN_PRODUCTION': 'in_production',
    'PRODUCTION_COMPLETED': 'production_completed',
    'READY_FOR_PICKUP': 'ready_for_pickup',
    'COMPLETED': 'completed'
}

def initialize_session_state():
    """Initialize all required session state variables"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'notification_customer' not in st.session_state:
        st.session_state.notification_customer = []
    if 'production_notifications' not in st.session_state:
        st.session_state.production_notifications = []
    if 'orders' not in st.session_state:
        st.session_state.orders = []
    if 'order_updated' not in st.session_state:
        st.session_state.order_updated = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = {}

def show_payment_section(order):
    """Enhanced payment processing section"""
    st.markdown("### 💳 Payment Processing")
    
    # Get payment details
    details = order.get('payment_details', {})
    payment_term = order.get('payment_term')
    
    # Calculate amount to pay
    if payment_term == 'Prepayment':
        amount_to_pay = details.get('discounted_amount', order['total'] * 0.95)
    else:
        amount_to_pay = details.get('total_with_interest', order['total'])
    
    st.write(f"**Amount to Pay:** ${amount_to_pay:.2f}")
    
    # Simulated payment gateway
    payment_method = st.selectbox(
        "Select Payment Method",
        ["Credit Card", "Bank Transfer", "E-Wallet"]
    )
    
    if payment_method == "Credit Card":
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Card Number", placeholder="**** **** **** ****")
            st.text_input("Card Holder Name", placeholder="JOHN DOE")
        with col2:
            st.text_input("Expiry Date", placeholder="MM/YY")
            st.text_input("CVV", placeholder="***", type="password")
    
    if st.button("Process Payment"):
        # Simulate payment processing
        with st.spinner("Processing payment..."):
            time.sleep(2)  # Simulate payment gateway delay
            
            # Update order status
            for idx, o in enumerate(st.session_state.orders):
                if o['order_id'] == order['order_id']:
                    st.session_state.orders[idx]['status'] = 'payment_verified'
                    st.session_state.orders[idx]['payment_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.orders[idx]['tracking_updates'].append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'status': 'Payment Verified',
                        'message': f'Payment of ${amount_to_pay:.2f} has been verified.'
                    })
            
            # Notify marketing team
            create_notification(
                order_id=order['order_id'],
                notification_type='payment_verified',
                title='Payment Verified - Ready for Processing',
                message=f'Payment for order #{format_order_id(order["order_id"])} has been verified.',
                priority='high',
                recipient='marketing'
            )
            
            # Notify production team to start packing
            create_notification(
                order_id=order['order_id'],
                notification_type='start_packing',
                title='Start Order Packing',
                message=f'Payment verified for order #{format_order_id(order["order_id"])}. Please begin packing.',
                priority='high',
                recipient='production'
            )
            
            st.success("✅ Payment processed successfully!")
            st.rerun()


def show_customer_support_chat(order):
    """Display customer support chat interface for rejected payment terms"""
    st.markdown("### 🤝 Customer Support")
    
    if order['order_id'] not in st.session_state.chat_history:
        st.session_state.chat_history[order['order_id']] = []
    
    # Display chat history
    for message in st.session_state.chat_history[order['order_id']]:
        with st.chat_message(message['role']):
            st.write(message['content'])
    
    # Message input
    message = st.chat_input("Type your message here...")
    if message:
        # Add user message to chat history
        st.session_state.chat_history[order['order_id']].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Create notification for marketing team
        create_notification(
            order_id=order['order_id'],
            notification_type='support',
            title='New Customer Support Message',
            message=f'New message from customer regarding order #{order["order_id"][:8]}',
            priority='high',
            recipient='marketing'
        )
        
        st.rerun()


        
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r"^\+60\d{2}-\d{7,8}$"
    return bool(re.match(pattern, phone))

# Utility functions
def add_to_cart(seed_data, quantity):
    cart_item = {
        'id': str(uuid.uuid4()),
        'seed': seed_data['Seed'],
        'quantity': quantity,
        'price_per_kg': seed_data['Price'],
        'total_price': quantity * seed_data['Price']
    }
    st.session_state.cart.append(cart_item)

def remove_from_cart(item_id):
    st.session_state.cart = [item for item in st.session_state.cart if item['id'] != item_id]

def calculate_cart_total():
    return sum(item['total_price'] for item in st.session_state.cart)

def get_status_class(status):
    status_classes = {
        'Pending': 'status-pending',
        'Confirmed': 'status-confirmed',
        'Ready for Pickup': 'status-ready',
        'Completed': 'status-completed'
    }
    return status_classes.get(status.lower(), 'status-pending')

def get_order_progress(status):
    """Returns the progress percentage based on order status"""
    status_progress = {
        'Pending': 25,
        'Confirmed': 50,
        'Ready for Pickup': 75,
        'Completed': 100
    }
    return status_progress.get(status, 0)


# Sample catalog data
catalog = pd.DataFrame({
    'SeedId':["SEED001","SEED002","SEED003","SEED004","SEED005"],
    'Seed': ['Dura Palm', 'Pisifera Palm', 'Tenera Palm', 'Compact Palm', 'Elite Palm'],
    'Description': [
        'High oil content palm seeds, ideal for commercial plantations.',
        'Shell-less palm variety with excellent breeding potential.',
        'Hybrid palm seeds known for exceptional yield and disease resistance.',
        'Compact growing palm variety suitable for smaller plantations.',
        'Premium quality seeds with certified genetic superiority.'
    ],
    'Price': [15.00, 18.00, 20.00, 16.50, 25.00],
    'Min_Order': [5, 5, 5, 3, 5],
    'Germination_Rate': [85, 82, 90, 87, 92],
    'Maturity_Period': ['24-28 months', '26-30 months', '24-26 months', '22-24 months', '24-28 months'],
    'Image': [
        'https://via.placeholder.com/150?text=Dura+Palm',
        'https://via.placeholder.com/150?text=Pisifera+Palm',
        'https://via.placeholder.com/150?text=Tenera+Palm',
        'https://via.placeholder.com/150?text=Compact+Palm',
        'https://via.placeholder.com/150?text=Elite+Palm'
    ]
})

def show_customer_catalog():
    st.markdown('<div class="main-title">🌴 Premium Palm Oil Seeds</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Available Premium Seeds</div>', unsafe_allow_html=True)
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        price_range = st.slider("Price Range ($)", 0, 30, (0, 30))
    with col2:
        sort_by = st.selectbox("Sort by", ["Price: Low to High", "Price: High to Low", "Germination Rate"])
    
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
                st.image(row['Image'], width=150)
            with col2:
                st.markdown(f'<div class="sub-title">{row["Seed"]}</div>', unsafe_allow_html=True)
                st.write(row['Description'])
                st.write(f"🌱 Germination Rate: {row['Germination_Rate']}%")
                st.write(f"⏳ Maturity Period: {row['Maturity_Period']}")
                st.write(f"💰 Price: ${row['Price']} per kg")
                
            with col3:
                quantity = st.number_input("Quantity (kg)", 
                                        min_value=row['Min_Order'], 
                                        max_value=100, 
                                        step=1, 
                                        key=f"qty_{row['Seed']}")
                if st.button("Add to Cart", key=f"add_{row['Seed']}"):
                    add_to_cart(row, quantity)
                    st.success(f"{row['Seed']} added to cart!")
            st.markdown('</div>', unsafe_allow_html=True)

def update_order_status(order_id, new_status, message):
    for order in st.session_state.orders:
        if order['order_id'] == order_id:
            order['status'] = new_status
            order['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': new_status,
                'message': message
            })

def show_customer_cart():
    # Initialize session state at the start
    initialize_session_state()
    
    st.title("🛒 Shopping Cart")
    
    if not st.session_state.cart:
        st.info("Your cart is currently empty")
        return

    for item in st.session_state.cart:
        st.markdown(f'<div class="cart-item">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{item['seed']}**")
            st.write(f"Quantity: {item['quantity']}kg")
        with col2:
            st.write(f"Price/kg: ${item['price_per_kg']}")
            st.write(f"Total: ${item['total_price']:.2f}")
        with col3:
            if st.button("Remove", key=f"remove_{item['id']}"):
                remove_from_cart(item['id'])
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.write(f"**Cart Total: ${calculate_cart_total():.2f}**")
    
    # Order Form
    st.markdown('<div class="order-form">', unsafe_allow_html=True)
    st.subheader("Order Information")
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name*", placeholder="Enter your company name")
        contact_name = st.text_input("Contact Person*", placeholder="Enter contact person name")
        email = st.text_input("Email*", placeholder="example@company.com")
        phone = st.text_input("Phone*", placeholder="+60xx-xxxxxxx")
    
    with col2:
        courier_company = st.text_input("Courier Company Name*", placeholder="Enter courier company name")
        special_instructions = st.text_area("Special Instructions", placeholder="Enter any special instructions")
    
    if st.button("Submit Order Inquiry"):
        # Validation
        validation_errors = []
        if not all([company_name, contact_name, email, phone, courier_company]):
            validation_errors.append("Please fill in all required fields")
        if not validate_email(email):
            validation_errors.append("Please enter a valid email address")
        if not validate_phone(phone):
            validation_errors.append("Please enter a valid phone number (Format: +60xx-xxxxxxx)")
        
        if validation_errors:
            for error in validation_errors:
                st.error(error)
        else:
            # Create order
            order_id = str(uuid.uuid4())
            
            # Make sure to use st.session_state.user_email instead of the form email
            user_email = st.session_state.get('user_email', '')
            
            order = {
                'order_id': order_id,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'items': st.session_state.cart.copy(),
                'total': calculate_cart_total(),
                'company_name': company_name,
                'contact_name': contact_name,
                'email': user_email,
                'phone': phone,
                'courier_company': courier_company,
                'special_instructions': special_instructions,
                'status': 'pending_marketing_approval',
                'tracking_updates': [{
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'status': 'Order Submitted',
                    'message': 'Order submitted for marketing review'
                }],
                'marketing_approved': False,
                'payment_status': 'pending',
                'payment_term': None
            }

            # Initialize orders if not exists
            if 'orders' not in st.session_state:
                st.session_state.orders = []
            
            # Add order to session state
            st.session_state.orders.append(order)
            
            # Create notification for marketing team
            create_notification(
                order_id=order_id,
                notification_type='new_order',
                title='New Order Submitted',
                message=f'Order #{order_id[:8]} has been submitted and is awaiting marketing review.',
                priority='high',
                recipient='marketing'
            )
            
            # Create notification for customer
            create_notification(
                order_id=order_id,
                notification_type='order_status',
                title='Order Submitted Successfully',
                message=f'Your order #{order_id[:8]} has been submitted and is pending approval.',
                priority='high',
                recipient='customer'
            )
            
            # Clear cart
            st.session_state.cart = []
            
            st.success("Order submitted successfully!")
            st.balloons()
            
            # Delay for 2 seconds before redirecting
            with st.spinner("Redirecting to tracking page..."):
                time.sleep(2)
            
            # Set the page to tracking
            st.session_state.current_page = 'tracking'
            st.rerun()

def calculate_payment_details(total_amount, payment_term):
    """Calculate payment details based on selected term"""
    today = datetime.now()
    
    payment_details = {
        'Prepayment': {
            'payment_amount': total_amount,
            'due_date': today.date(),
            'discount': 0.05,  # 5% discount for prepayment
            'discounted_amount': total_amount * 0.95,
            'payment_schedule': None
        },
        'Net 30': {
            'payment_amount': total_amount,
            'due_date': (today + timedelta(days=30)).date(),
            'interest': 0.02,  # 2% interest for Net 30
            'total_with_interest': total_amount * 1.02,
            'payment_schedule': None
        },
        'Net 60': {
            'payment_amount': total_amount,
            'due_date': (today + timedelta(days=60)).date(),
            'interest': 0.04,  # 4% interest for Net 60
            'total_with_interest': total_amount * 1.04,
            'payment_schedule': [
                {
                    'installment': 1,
                    'amount': total_amount * 0.5 * 1.04,
                    'due_date': (today + timedelta(days=30)).date()
                },
                {
                    'installment': 2,
                    'amount': total_amount * 0.5 * 1.04,
                    'due_date': (today + timedelta(days=60)).date()
                }
            ]
        }
    }
    
    return payment_details.get(payment_term)

def show_payment_term_selection(order):
    """Show payment term selection options"""
    st.subheader("💳 Select Payment Term")
    
    # Define payment terms
    payment_terms = [
        {
            'name': 'Prepayment',
            'description': 'Pay full amount upfront and get 5% discount',
            'details': {
                'discount': 0.05,
                'discounted_amount': order['total'] * 0.95
            }
        },
        {
            'name': 'Installment',
            'description': 'Pay in 3 installments over 3 months',
            'details': {
                'installments': 3,
                'payment_schedule': [
                    {
                        'installment': 1,
                        'amount': order['total'] / 3,
                        'due_date': (datetime.now() + timedelta(days=0)).date()
                    },
                    {
                        'installment': 2,
                        'amount': order['total'] / 3,
                        'due_date': (datetime.now() + timedelta(days=30)).date()
                    },
                    {
                        'installment': 3,
                        'amount': order['total'] / 3,
                        'due_date': (datetime.now() + timedelta(days=60)).date()
                    }
                ]
            }
        }
    ]
    
    # Display payment term options
    for term in payment_terms:
        st.write(f"### {term['name']}")
        st.write(term['description'])
        
        details = term['details']
        if term['name'] == 'Prepayment':
            st.write(f"Original amount: ${order['total']:.2f}")
            st.write(f"Discounted amount: ${details['discounted_amount']:.2f}")
        else:
            st.write("Payment Schedule:")
            for payment in details['payment_schedule']:
                st.write(f"- Installment {payment['installment']}: ${payment['amount']:.2f} (Due: {payment['due_date']})")
        
        if st.button(f"Select {term['name']}", key=f"select_{term['name']}_{order['order_id']}"):
            # Update order with payment term selection
            for idx, o in enumerate(st.session_state.orders):
                if o['order_id'] == order['order_id']:
                    st.session_state.orders[idx]['payment_term'] = term['name']
                    st.session_state.orders[idx]['payment_details'] = details
                    st.session_state.orders[idx]['status'] = 'pending_payment'
                    st.session_state.orders[idx]['tracking_updates'].append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'status': 'Payment Term Selected',
                        'message': f'Payment term "{term["name"]}" selected. Proceeding to payment.'
                    })
            
            st.success(f"✅ {term['name']} selected! Proceeding to payment...")
            time.sleep(0.5)
            st.rerun()

def show_customer_tracking():
    st.title("📦 Order Tracking")
    
    if 'orders' not in st.session_state:
        st.info("No orders to track")
        return
    
    # Filter orders for current customer and remove duplicates
    customer_orders = []
    seen_order_ids = set()
    for order in st.session_state.orders:
        if (order.get('email') == st.session_state.user_email and 
            order['order_id'] not in seen_order_ids):
            customer_orders.append(order)
            seen_order_ids.add(order['order_id'])
    
    if not customer_orders:
        st.info("No orders found")
        return
    
    # Sort orders by date (newest first)
    customer_orders.sort(key=lambda x: x['date'], reverse=True)
    
    # Add spacing between orders
    for i, order in enumerate(customer_orders):
        if i > 0:
            st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
            
        with st.container():
            # Order card with better styling
            st.markdown("""
                <style>
                .order-card {
                    background-color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .order-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }
                .order-id {
                    font-size: 1.2em;
                    font-weight: bold;
                    color: #1f2937;
                }
                .order-status {
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-size: 0.9em;
                    background-color: #f3f4f6;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Update status display
            status_display = {
                'pending_marketing_approval': 'Pending Marketing Approval',
                'marketing_approved': 'Marketing Approved',
                'marketing_rejected': 'Marketing Rejected',
                'pending_production_approval': 'Pending Production Approval',
                'production_approved': 'Production Approved',
                'production_rejected': 'Production Rejected',
                'pending_payment_term': 'Select Payment Term',
                'pending_payment': 'Pending Payment',
                'payment_verified': 'Payment Verified',
                'in_production': 'In Production',
                'production_completed': 'Production Completed',
                'ready_for_pickup': 'Ready for Pickup',
                'completed': 'Completed'
            }
            
            st.markdown(f"""
                <div class="order-card">
                    <div class="order-header">
                        <div class="order-id">Order #{format_order_id(order['order_id'])}</div>
                        <div class="order-status">{status_display.get(order['status'], order['status'].replace('_', ' ').title())}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if order['status'] == 'pending_payment_term':
                    st.info("✨ Production has approved your order. Please select your payment terms below.")
                    show_payment_term_selection(order)
                elif order['status'] == 'pending_payment':
                    show_payment_section(order)
                elif order['status'] == 'payment_verified':
                    st.success("✅ Payment verified! Your order is being processed.")
                elif order['status'] == 'in_production':
                    st.info("🏭 Your order is currently in production.")
                elif order['status'] == 'production_completed':
                    st.success("✅ Production completed! Your order will be ready for pickup soon.")
                elif order['status'] == 'ready_for_pickup':
                    st.success("🚚 Your order is ready for pickup!")
                    show_pickup_scheduling(order)
            
            with col2:
                st.write(f"**Ordered:** {order['date']}")
                st.write(f"**Total:** ${order['total']:.2f}")
            
            # Timeline and Details in expandable sections
            with st.expander("📅 Order Timeline"):
                show_order_timeline(order)
            
            with st.expander("📋 Order Details"):
                show_order_details(order)

def get_status_class(status):
    """Return CSS class based on order status"""
    status_classes = {
        'pending_marketing_approval': 'status-pending',
        'pending_payment_term': 'status-pending',
        'pending_payment_approval': 'status-pending',
        'payment_terms_rejected': 'status-rejected',
        'pending_payment': 'status-pending',
        'payment_verified': 'status-verified',
        'in_production': 'status-processing',
        'production_completed': 'status-completed',
        'ready_for_pickup': 'status-ready'
    }
    return status_classes.get(status, 'status-default')

def add_tracking_update(order_id, status, message):
    """Add a tracking update to an order"""
    for idx, order in enumerate(st.session_state.orders):
        if order['order_id'] == order_id:
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': status,
                'message': message
            })
            break

def show_pickup_scheduling(order):
    """Display pickup scheduling interface"""
    st.write("### 📅 Schedule Pickup")
    
    # Check if the pickup has already been scheduled
    if f"pickup_scheduled_{order['order_id']}" not in st.session_state:
        st.session_state[f"pickup_scheduled_{order['order_id']}"] = False

    if not st.session_state[f"pickup_scheduled_{order['order_id']}"]:
        col1, col2 = st.columns(2)
        with col1:
            pickup_date = st.date_input(
                "Select Pickup Date",
                min_value=datetime.now().date(),
                max_value=datetime.now().date() + timedelta(days=7),
                key=f"pickup_date_{order['order_id']}"  # Unique key using order ID
            )
        with col2:
            pickup_time = st.selectbox(
                "Select Pickup Time",
                ["9:00 AM", "10:00 AM", "11:00 AM", "2:00 PM", "3:00 PM", "4:00 PM"],
                key=f"pickup_time_{order['order_id']}"  # Unique key using order ID
            )
        
        if st.button("Schedule Pickup", key=f"schedule_pickup_{order['order_id']}"):  # Unique key for button
            # Update order with pickup details
            for idx, o in enumerate(st.session_state.orders):
                if o['order_id'] == order['order_id']:
                    st.session_state.orders[idx]['pickup_date'] = pickup_date.strftime("%Y-%m-%d")
                    st.session_state.orders[idx]['pickup_time'] = pickup_time
                    
                    # Add tracking update
                    add_tracking_update(
                        order_id=order['order_id'],
                        status="Pickup Scheduled",
                        message=f"Pickup scheduled for {pickup_date.strftime('%Y-%m-%d')} at {pickup_time}"
                    )
                    
                    # Set the flag to true to hide the inputs
                    st.session_state[f"pickup_scheduled_{order['order_id']}"] = True
                    st.success("Pickup scheduled successfully!")
                    st.rerun()
    else:
        # Find the order index again to use it safely
        for idx, o in enumerate(st.session_state.orders):
            if o['order_id'] == order['order_id']:
                st.success(f"Pickup scheduled for {o['pickup_date']} at {o['pickup_time']}")
                if st.button("Mark as Received", key=f"mark_received_{order['order_id']}"):
                    st.session_state.orders[idx]['status'] = ORDER_STATUS['COMPLETED']
                    add_tracking_update(
                        order_id=order['order_id'],
                        status="Completed",
                        message="Order has been received by the customer."
                    )
                    st.success("Order marked as received!")
                    st.rerun()
                break

def show_order_timeline(order):
    """Display order timeline with all status updates"""
    st.markdown("### 📝 Order Timeline")
    
    # Define status icons for better visualization
    STATUS_ICONS = {
        'Order Submitted': '📝',
        'Marketing Approved': '✅',
        'Marketing Rejected': '❌',
        'Production Approved': '✅',  # Add Production Approved icon
        'Production Rejected': '❌',  # Add Production Rejected icon
        'Payment Term Selected': '🗓️',
        'Payment Term Submitted': '💰',
        'Payment Submitted': '💵',
        'Payment Verified': '💳',
        'Production Started': '🏭',
        'Customer Notified': '📱',
        'Ready for Pickup': '🚚',
        'Pickup Scheduled': '📅',
        'Completed': '🎉',
        'Pending Marketing': '⏳',
        'Pending Payment': '💸',
        'Processing Payment': '🔄',
        'In Production': '🔧',
        'Pending Production Approval': '⏳',  # Add specific status icons
        'Pending Payment Term': '💳'
    }
    
    if not order.get('tracking_updates'):
        st.info("No tracking updates available")
        return
    
    # Custom CSS to style the timeline
    st.markdown("""
    <style>
        .timeline {
            padding-left: 32px;
            margin: 24px 0;
            border-left: 2px solid #e5e7eb;
        }
        .timeline-item {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }
        .timeline-icon {
            font-size: 24px;
            margin-right: 12px;
        }
        .timeline-content {
            background-color: #f9fafb;
            padding: 10px;
            border-radius: 5px;
            width: 100%;
        }
        .timeline-timestamp {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 4px;
        }
        .timeline-status {
            font-weight: bold;
            margin-bottom: 4px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Generate the timeline with icons and statuses
    st.markdown('<div class="timeline">', unsafe_allow_html=True)
    for update in reversed(order['tracking_updates']):
        icon = STATUS_ICONS.get(update['status'], '•')  # Default icon if status is not found
        st.markdown(
            f"""
            <div class="timeline-item">
                <div class="timeline-icon">{icon}</div>
                <div class="timeline-content">
                    <div class="timeline-timestamp">{update['timestamp']}</div>
                    <div class="timeline-status">{update['status']}</div>
                    <div class="timeline-message">{update['message']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)


def show_order_details(order):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Order Information:**")
        st.write(f"Company: {order['company_name']}")
        st.write(f"Contact: {order['contact_name']}")
        st.write(f"Phone: {order['phone']}")
        st.write(f"Courier: {order['courier_company']}")
    
    with col2:
        st.write("**Items:**")
        for item in order['items']:
            st.write(f"- {item['seed']}: {item['quantity']}kg (${item['total_price']:.2f})")
        
        if order.get('special_instructions'):
            st.write("**Special Instructions:**")
            st.write(order['special_instructions'])   

def format_order_id(order_id):
    """Format the order ID to display only the first 8 characters."""
    return order_id[:8]





