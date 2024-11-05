# production_module.py
import streamlit as st
from datetime import datetime
import pandas as pd
import uuid
from notification import create_notification

def initialize_production_state():
    """Initialize all production-related session state variables."""
    if 'orders' not in st.session_state:
        st.session_state.orders = []
    if 'production_notifications' not in st.session_state:
        st.session_state.production_notifications = []
    if 'notification_customer' not in st.session_state:
        st.session_state.notification_customer = []
    if 'order_history' not in st.session_state:
        st.session_state.order_history = []

def format_order_id(order_id):
    """Format the order ID to display only the first 8 characters."""
    return order_id[:8]

def show_production_dashboard():
    """Show the production dashboard."""
    # Initialize session state
    initialize_production_state()
    
    st.title("🏭 Production Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Pending Orders", "Inventory", "Production Schedule", "DO Management"])
    
    with tab1:
        show_pending_orders()
    
    with tab2:
        show_inventory_management()
    
    with tab3:
        show_production_schedule()
    
    with tab4:
        show_do_management()

def show_pending_orders():
    st.subheader("📦 Pending Orders")
    
    # Filter orders that need production approval
    pending_orders = [order for order in st.session_state.orders if order['status'] == 'pending_production']
    
    if not pending_orders:
        st.info("No pending orders to review")
        return
    
    for order in pending_orders:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### Order #{format_order_id(order['order_id'])}")
                st.write(f"**Company:** {order['company_name']}")
                st.write(f"**Contact name:** {order['contact_name']}")
                st.write(f"**Total Amount:** ${order['total']:.2f}")
                
                # Show order items
                with st.expander("View Order Items"):
                    for item in order['items']:
                        st.write(f"- {item['seed']}: {item['quantity']}kg at ${item['price_per_kg']}/kg")
                    if order['special_instructions']:
                        st.write("**Special Instructions:**")
                        st.write(order['special_instructions'])
            
            with col2:
                if st.button("✅ Approve", key=f"approve_{order['order_id']}"):
                    update_order_status(order, 'pending_payment_term', True, False)
                    create_notification(
                        title='Order Approved by Production',
                        notification_type='approval',
                        message=f'Your order #{format_order_id(order["order_id"])} has been approved. Please select payment terms.',
                        order_id=order['order_id'],
                        priority='high',
                        recipient='customer'
                    )
                    st.success("Order approved!")
                    st.rerun()
                
                if st.button("❌ Reject", key=f"reject_{order['order_id']}"):
                    update_order_status(order, 'rejected', False, False)
                    create_notification(
                        title='Order Rejected by Production',
                        notification_type='rejection',
                        message=f'Your order #{format_order_id(order["order_id"])} has been rejected.',
                        order_id=order['order_id'],
                        priority='high',
                        recipient='customer'
                    )
                    st.error("Order rejected!")
                    st.rerun()

def update_order_status(order, status, production_approved, marketing_approved):
    """Update order status and maintain history."""
    # Ensure order_history exists
    if 'order_history' not in st.session_state:
        st.session_state.order_history = []
    
    order['status'] = status
    order['production_approved'] = production_approved
    order['marketing_approved'] = marketing_approved
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = 'Order approved by production team' if production_approved else 'Order rejected by production team'
    
    # Add the status update to order's tracking updates
    if 'tracking_updates' not in order:
        order['tracking_updates'] = []
        
    order['tracking_updates'].append({
        'timestamp': timestamp,
        'status': 'Production Approved' if production_approved else 'Production Rejected',
        'message': message
    })
    
    # Save to order history using formatted order ID
    history_entry = {
        'order_id': format_order_id(order['order_id']),
        'timestamp': timestamp,
        'status': status,
        'message': message
    }
    
    st.session_state.order_history.append(history_entry)

def show_order_history():
    st.title("📜 Order History")
    
    # Order history filtering options
    order_id_filter = st.text_input("Filter by Order ID", "")
    date_filter = st.date_input("Filter by Date", None)
    
    # Filter order history based on the inputs, using formatted order IDs for comparison
    filtered_history = [
        history for history in st.session_state.order_history
        if (order_id_filter in format_order_id(history['order_id'])) and
           (not date_filter or history['timestamp'].startswith(date_filter.strftime("%Y-%m-%d")))
    ]
    
    if not filtered_history:
        st.info("No order history to display.")
        return
    
    # Display order history entries with formatted order IDs
    for entry in filtered_history:
        with st.container():
            st.write(f"**Order ID:** #{format_order_id(entry['order_id'])}")  # Added # for better readability
            st.write(f"**Timestamp:** {entry['timestamp']}")
            st.write(f"**Status:** {entry['status']}")
            st.write(f"**Message:** {entry['message']}")
            st.divider()

def show_inventory_management():
    st.subheader("📊Inventory Management")
    st.write("Current inventory levels and management tools will be displayed here.")
    # Add your inventory management implementation here

def show_production_schedule():
    st.subheader("Production Schedule")
    st.write("Production schedule and planning tools will be displayed here.")
    # Add your production schedule implementation here

def show_do_management():
    st.subheader("📋Delivery Order Management")
    
    # Filter orders that are payment verified and need DO
    verified_orders = [
        order for order in st.session_state.orders 
        if order.get('status') == 'payment_verified' and not order.get('do_number')
    ]
    
    if not verified_orders:
        st.info("No orders pending DO generation")
        return
    
    for order in verified_orders:
        with st.expander(f"Order #{format_order_id(order['order_id'])} - Generate DO"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Customer:** {order['contact_name']}")
                st.write(f"**Company:** {order['company_name']}")
                st.write(f"**Total Amount:** ${order.get('total', 0):,.2f}")
                
                # Show order items
                st.write("**Order Items:**")
                for item in order['items']:
                    st.write(f"- {item['seed']}: {item['quantity']}kg")
            
            with col2:
                if st.button("Generate DO", key=f"do_{order['order_id']}"):
                    generate_delivery_order(order)
                    st.success("DO generated successfully!")
                    st.rerun()

def generate_delivery_order(order):
    # Create DO number
    do_number = f"DO{datetime.now().strftime('%Y%m%d')}-{format_order_id(order['order_id'])}"
    
    # Update order status
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['status'] = 'do_generated'
            st.session_state.orders[idx]['do_number'] = do_number
            st.session_state.orders[idx]['do_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'DO Generated',
                'message': f'Delivery Order generated. DO Number: {do_number}'
            })
    
    # Notify marketing team about DO generation
    create_notification(
        order_id=format_order_id(order['order_id']),
        notification_type='do_generated',
        title='DO Generated - Ready for Customer Notification',
        message=f"DO has been generated for order #{format_order_id(order['order_id'])}. DO Number: {do_number}",
        priority='high',
        recipient='marketing'
    )