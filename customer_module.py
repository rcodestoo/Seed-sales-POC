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
""", unsafe_allow_html=True)

# Add new order status constants for clarity
ORDER_STATUS = {
    'PENDING_PRODUCTION': 'pending_production',
    'PENDING_PAYMENT_TERM': 'pending_payment_term',
    'PENDING_MARKETING': 'pending_marketing_approval',
    'PAYMENT_TERM_REJECTED': 'payment_term_rejected',
    'PENDING_PAYMENT': 'pending_payment',
    'PROCESSING_PAYMENT': 'processing_payment',
    'PAYMENT_VERIFIED': 'payment_verified',
    'DO_GENERATED': 'do_generated',
    'DO_APPROVED': 'do_approved',
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
    """Enhanced payment processing section with hide after submit functionality"""
    
    st.markdown("### 💳 Payment Processing")
    
    # Get payment details
    details = order.get('payment_details', {})
    payment_term = order.get('payment_term')
    
    # Calculate amount to pay upfront to avoid errors
    if payment_term == 'Prepayment':
        amount_to_pay = details.get('discounted_amount', order['total'] * 0.95)
    else:
        if details.get('payment_schedule'):
            current_date = datetime.now().date()
            amount_to_pay = sum(
                installment['amount'] 
                for installment in details['payment_schedule']
                if current_date >= installment['due_date']
            )
        else:
            amount_to_pay = details.get('total_with_interest', order['total'])
    
    # Only show payment form if payment terms are approved
    if order.get('status') != 'payment_terms_approved':
        st.warning("Please wait for payment terms approval before proceeding with payment.")
        return
    
    # Display payment summary only once
    if not st.session_state.get('payment_summary_shown'):
        st.markdown('<div class="payment-details">', unsafe_allow_html=True)
        st.write("**Payment Summary**")
        
        if payment_term == 'Prepayment':
            st.write(f"Original Amount: ${order['total']:.2f}")
            st.write("Discount Applied: 5%")
            st.write(f"Final Amount to Pay: ${amount_to_pay:.2f}")
        else:
            if details.get('payment_schedule'):
                st.write("**Payment Schedule:**")
                current_date = datetime.now().date()
                
                for installment in details['payment_schedule']:
                    is_due = current_date >= installment['due_date']
                    status = "Due Now" if is_due else "Upcoming"
                    
                    st.write(f"Installment {installment['installment']}:")
                    st.write(f"- Amount: ${installment['amount']:.2f}")
                    st.write(f"- Due Date: {installment['due_date']} ({status})")
            else:
                st.write(f"Total Amount (with interest): ${amount_to_pay:.2f}")
                st.write(f"Due Date: {details.get('due_date', 'Not specified')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.payment_summary_shown = True
    
    # Payment method selection
    payment_methods = {
        'credit_card': 'Credit Card',
        'bank_transfer': 'Bank Transfer',
        'cheque': 'Company Cheque'
    }
    
    payment_method = st.selectbox(
        "Select Payment Method",
        options=list(payment_methods.keys()),
        format_func=lambda x: payment_methods[x],
        key="payment_method_select"
    )
    
    # Display payment fields based on method
    if payment_method == 'credit_card':
        st.text_input("Card Number", placeholder="XXXX-XXXX-XXXX-XXXX")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Expiry Date", placeholder="MM/YY")
        with col2:
            st.text_input("CVV", placeholder="123", type="password")
            
    elif payment_method == 'bank_transfer':
        st.info(f"""
        Bank Transfer Details:
        - Bank: Example Bank
        - Account Name: Palm Oil Seeds Co.
        - Account Number: 1234-5678-9012
        - Reference: Order #{order['order_id'][:8]}
        - Amount to Transfer: ${amount_to_pay:.2f}
        """)
        st.file_uploader("Upload Payment Receipt", type=['pdf', 'jpg', 'png'])
        
    elif payment_method == 'cheque':
        st.write(f"Amount to Pay: ${amount_to_pay:.2f}")
        st.text_input("Cheque Number")
        st.file_uploader("Upload Cheque Image", type=['jpg', 'png'])
    
    # Submit payment button
    if st.button("Submit Payment", key="submit_payment_button"):
        # Update order status and payment details
        for idx, o in enumerate(st.session_state.orders):
            if o['order_id'] == order['order_id']:
                st.session_state.orders[idx]['status'] = 'payment_submitted'
                st.session_state.orders[idx]['payment_status'] = 'pending_verification'
                st.session_state.orders[idx]['payment_method'] = payment_method
                st.session_state.orders[idx]['payment_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.orders[idx]['payment_amount'] = amount_to_pay
                
                # Add tracking update
                st.session_state.orders[idx]['tracking_updates'].append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'status': 'Payment Submitted',
                    'message': f'Payment of ${amount_to_pay:.2f} submitted via {payment_methods[payment_method]}'
                })
        
        # Create notifications
        create_notification(
            order_id=order['order_id'],
            notification_type='payment',
            title='Payment Submitted',
            message=f'Payment of ${amount_to_pay:.2f} for order #{order["order_id"][:8]} has been submitted and is being processed.',
            priority='high',
            recipient='customer'
        )
        
        create_notification(
            order_id=order['order_id'],
            notification_type='payment_verification',
            title='Payment Verification Required',
            message=f'Payment of ${amount_to_pay:.2f} for order #{order["order_id"][:8]} requires verification.',
            priority='high',
            recipient='marketing'
        )
        
        # Set the payment_submitted flag in session state
        st.session_state.payment_submitted = True
        
        # Show success message
        st.success("Payment submitted successfully! We will process your payment and update you shortly.")
        
        # Rerun the app to hide the payment section
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
    
    if st.button("Submit Order Request"):
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
            order = {
                'order_id': order_id,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'items': st.session_state.cart.copy(),
                'total': calculate_cart_total(),
                'company_name': company_name,
                'contact_name': contact_name,
                'email': email,
                'phone': phone,
                'courier_company': courier_company,
                'special_instructions': special_instructions,
                'status': 'pending_production',  # Initial status
                'tracking_updates': [{
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'status': 'Order Submitted',
                    'message': 'Order submitted for production approval'
                }],
                'production_approved': False,
                'marketing_approved': False,
                'payment_status': 'pending',
                'payment_term': None,
                'delivery_order': None,
                'pickup_date': None,
                'pickup_time': None,  
            }
            
            # Create notification for customer
            create_notification(
                order_id=order_id,
                notification_type='order_status',
                title='Order Submitted Successfully',
                message=f'Your order #{order_id[:8]} has been submitted and is pending approval.',
                priority='high',
                recipient='customer'
            )
            
            # Create notification for production team
            create_notification(
                order_id=order_id,
                notification_type='order_status',
                title='New Order Submitted',
                message=f'Order #{order_id[:8]} has been submitted and is awaiting production approval.',
                priority='high',
                recipient='production'
            )
            

             # Add order and notification to session state
            st.session_state.orders.append(order)
            
            # Clear cart
            st.session_state.cart = []
            
            st.success("Order submitted successfully!")
            st.balloons()
            
            # Delay for 2 seconds before redirecting
            with st.spinner("Redirecting to tracking page..."):
                time.sleep(2)
            
            # Redirect to tracking
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
    # Initialize session state keys
    payment_key = f'payment_submitted_{order["order_id"]}'
    term_key = f'selected_term_{order["order_id"]}'
    transition_key = f'transition_{order["order_id"]}'
    
    if payment_key not in st.session_state:
        st.session_state[payment_key] = False
    if term_key not in st.session_state:
        st.session_state[term_key] = None
    if transition_key not in st.session_state:
        st.session_state[transition_key] = False

    # Show selection interface for pending payment term
    if order['status'] == 'pending_payment_term' and not order.get('payment_term') and not st.session_state[payment_key]:
        st.subheader("💳 Select Your Payment Term")
        st.write("Choose the payment option that best suits your business needs. Each option comes with different benefits and terms.")
        
        payment_terms = [
            {
                'name': 'Prepayment',
                'description': 'Pay upfront and enjoy an immediate 5% discount on your total order.',
                'recommended': True,
                'features': [
                    'Immediate 5% discount',
                    'No additional fees',
                    'Priority order processing',
                    'Flexible payment methods'
                ]
            },
            {
                'name': 'Net 30',
                'description': 'Pay the full amount within 30 days with a small 2% interest charge.',
                'features': [
                    '30-day payment window',
                    'Single payment',
                    'Standard order processing',
                    '2% interest rate'
                ]
            },
            {
                'name': 'Net 60',
                'description': 'Split your payment into two installments over 60 days with a 4% interest charge.',
                'features': [
                    '60-day payment window',
                    'Two equal installments',
                    'Flexible payment scheduling',
                    '4% interest rate'
                ]
            }
        ]

        for term in payment_terms:
            details = calculate_payment_details(order['total'], term['name'])
            
            with st.container():
                col1, col2 = st.columns([2, 1])
                
                # Term title and badges
                with col1:
                    st.write(f"### {term['name']}")
                    if term.get('recommended'):
                        st.write("**Recommended**")
                
                with col2:
                    if term['name'] == 'Prepayment':
                        st.write("5% Discount")
                    else:
                        st.write(f"{details['interest']*100}% Interest")

                # Term description and features
                st.write(term['description'])
                for feature in term['features']:
                    st.write(f"✓ {feature}")

                # Payment summary
                st.write("#### Amount Summary")
                if term['name'] == 'Prepayment':
                    st.write(f"Original Amount: ${order['total']:.2f}")
                    st.write(f"Discount Amount: ${order['total'] * 0.05:.2f}")
                    st.write(f"Final Amount: ${details['discounted_amount']:.2f}")
                else:
                    if details.get('payment_schedule'):
                        for i, installment in enumerate(details['payment_schedule'], 1):
                            st.write(f"Installment {i}: ${installment['amount']:.2f}")
                            st.write(f"Due Date: {installment['due_date']}")
                    else:
                        st.write(f"Total Amount: ${details['total_with_interest']:.2f}")
                        st.write(f"Due Date: {details['due_date']}")

                # Selection button
                if st.button(f"Select {term['name']}", key=f"select_{term['name']}_{order['order_id']}"):
                    st.session_state[term_key] = term['name']
                    order['payment_term'] = term['name']
                    order['payment_details'] = details
                    order['status'] = 'pending_payment_approval'
                    
                    order['tracking_updates'].append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "Payment Term Selected",
                        "message": f'Payment term "{term["name"]}" has been submitted for review.'
                    })
                    
                    create_notification(
                        order_id=order['order_id'],
                        notification_type='payment_term',
                        title='Payment Term Submitted',
                        message=f'Payment term "{term["name"]}" submitted for review.',
                        priority='high',
                        recipient='marketing'
                    )
                    
                    st.session_state[payment_key] = True
                    st.session_state[transition_key] = True
                    
                    # Show brief success message
                    success_placeholder = st.empty()
                    success_placeholder.success("✅ Payment term submitted successfully!")
                    time.sleep(0.5)  # Brief delay
                    success_placeholder.empty()  # Remove the success message
                    st.rerun()  # Force a rerun to update the UI immediately

    # Show selected term and status
    elif (order.get('payment_term') or st.session_state[transition_key]):
        status_display = {
            'pending_payment_approval': '(Pending Approval)',
            'payment_terms_approved': '(Approved)',
            'payment_terms_rejected': '(Rejected)',
        }.get(order.get('status'), '')
        
        st.subheader(f"💳 Payment Term Status {status_display}")
        
        # Show payment details
        if order.get('payment_details'):
            details = order['payment_details']
            
            st.write("#### Payment Summary")
            if order['payment_term'] == 'Prepayment':
                st.write(f"Original Amount: ${order['total']:.2f}")
                st.write(f"Discount Applied: 5%")
                st.write(f"Final Amount: ${details['discounted_amount']:.2f}")
            else:
                if details.get('payment_schedule'):
                    st.write("Payment Schedule:")
                    for installment in details['payment_schedule']:
                        st.write(f"- Installment {installment['installment']}: ${installment['amount']:.2f}")
                        st.write(f"  Due Date: {installment['due_date']}")
                else:
                    st.write(f"Total Amount (with interest): ${details['total_with_interest']:.2f}")
                    st.write(f"Due Date: {details['due_date']}")
        
        # Show appropriate interface based on status
        if order.get('status') == 'payment_terms_approved':
            show_payment_section(order)
        elif order.get('status') == 'payment_terms_rejected':
            if order.get('rejection_reason'):
                st.error(f"Rejection Reason: {order['rejection_reason']}")
            show_customer_support_chat(order)
        elif order.get('status') == 'pending_payment_approval':
            st.info("Your payment term request is being reviewed. Please wait for approval.")
            
def show_customer_tracking():
    initialize_session_state()
    
    st.title("📦 Order Tracking")
    
    st.markdown("""
    <style>
    .tracking-status { padding: 10px; border-radius: 5px; margin: 5px 0; font-weight: bold; }
    .status-pending { background-color: #FEF3C7; color: #92400E; }
    .status-confirmed { background-color: #DBEAFE; color: #1E40AF; }
    .status-ready { background-color: #D1FAE5; color: #065F46; }
    .status-completed { background-color: #E0E7FF; color: #3730A3; }
    
    /* Timeline styles */
    .timeline {position: relative; padding-left: 32px; margin: 24px 0;}
    .timeline-item {position: relative; padding-bottom: 24px;}
    .timeline-item::before { content: ''; position: absolute; left: -24px; top: 0; width: 2px; height: 100%; background-color: #e5e7eb; }
    .timeline-item::after { content: ''; position: absolute; left: -28px; top: 0; width: 10px; height: 10px; border-radius: 50%; background-color: #6366F1; border: 2px solid white; }
    </style>
    """, unsafe_allow_html=True)
    
    # Add filters
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search orders", placeholder="Order ID or Company name")
        with col2:
            status_filter = st.multiselect(
                "Status",
                ["Pending", "Confirmed", "Ready for Pickup", "Completed"]
            )
        with col3:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
            date_range = st.date_input(
                "Date range",
                [start_date.date(), end_date.date()],
                key="tracking_filter_date_range"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.orders:
        st.info("No orders found")
        return
    
    # Filter orders based on search and filters
    filtered_orders = st.session_state.orders
    
    if search_term:
        filtered_orders = [
            order for order in filtered_orders
            if (search_term.lower() in order['order_id'].lower() or 
                search_term.lower() in order['company_name'].lower())
        ]
    
    if status_filter:
        filtered_orders = [
            order for order in filtered_orders
            if order['status'] in status_filter
        ]
    
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_orders = [
            order for order in filtered_orders
            if start_date <= datetime.strptime(order['date'], "%Y-%m-%d %H:%M:%S").date() <= end_date
        ]
    
    for order in filtered_orders:
        st.markdown(f'<div class="catalog-container">', unsafe_allow_html=True)
        # Order Header
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"Order #{format_order_id(order['order_id'])}")
            st.markdown(f"<div class='tracking-status {get_status_class(order['status'])}'>{order['status']}</div>", 
                      unsafe_allow_html=True)
        with col2:
            st.write(f"**Ordered:** {order['date']}")
            st.write(f"**Total:** ${order['total']:.2f}")

        # Show different sections based on order status
        if order['status'] in ['pending_payment_term', 'pending_payment_approval', 'payment_terms_approved', 'payment_terms_rejected']:
            show_payment_term_selection(order)
            
        elif order['status'] == ORDER_STATUS['PAYMENT_TERM_REJECTED']:
            show_customer_support_chat(order)
            
        elif order['status'] == ORDER_STATUS['PENDING_PAYMENT']:
            show_payment_section(order)
            
        elif order['status'] == ORDER_STATUS['PAYMENT_VERIFIED']:
            st.info("Payment verified. Your order is being processed.")
            
        elif order['status'] == ORDER_STATUS['DO_GENERATED']:
            st.info("Your order is being processed by our team.")
            
        elif order['status'] == ORDER_STATUS['DO_APPROVED']:
            st.info("Your order has been approved. Please wait for pickup notification.")
            
        elif order['status'] == ORDER_STATUS['READY_FOR_PICKUP']:
            st.success("Your order is ready for pickup! 🎉")
            show_pickup_scheduling(order)
                
        # Always show order timeline and details
        with st.expander("Order Timeline"):
            show_order_timeline(order)
            
        with st.expander("Order Details"):
            show_order_details(order)
        
        st.markdown('</div>', unsafe_allow_html=True)

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
        'Production Approved': '✅',
        'Payment Term Submitted': '💰',
        'Payment Term Approved': '✔️',
        'Payment Term Rejected': '❌',
        'Payment Verified': '💳',
        'DO Generated': '📋',
        'DO Approved': '✅',
        'Ready for Pickup': '🚚',
        'Pickup Scheduled': '📅',
        'Completed': '🎉',
        'Pending Production': '⏳',
        'Pending Payment': '💸',
        'Processing Payment': '🔄',
        'Payment Submitted': '💵',
        'Payment Term Selected': '🗓️',
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

        
def show_delivery_order(order):
    """Display delivery order details after marketing approval"""
    st.markdown("### 📋 Delivery Order")
    
    if order['status'] not in [ORDER_STATUS['DO_APPROVED'], ORDER_STATUS['READY_FOR_PICKUP']]:
        st.info("Delivery order is being processed...")
        return
        
    # Display delivery order details
    st.write(f"**DO Number:** {order['delivery_order']['do_number']}")
    st.write(f"**Generated Date:** {order['delivery_order']['generated_date']}")
    st.write(f"**Valid Until:** {order['delivery_order']['validity']}")
    
    # Download button for DO
    if st.button("Download Delivery Order"):
        st.info("Delivery Order download functionality will be implemented here")

def format_order_id(order_id):
    """Format the order ID to display only the first 8 characters."""
    return order_id[:8]





