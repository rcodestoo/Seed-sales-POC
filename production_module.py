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
    """Show the production dashboard with improved UI."""
    initialize_production_state()
    
    st.title("🏭 Production Dashboard")
    
    # Show quick statistics at the top
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pending_approvals = len([o for o in st.session_state.orders if o.get('status') == 'pending_production_approval'])
        st.metric("Pending Approvals", pending_approvals, delta=None)
    
    with col2:
        pending_packing = len([o for o in st.session_state.orders if o.get('status') == 'payment_verified'])
        st.metric("Orders to Pack", pending_packing, delta=None)
    
    with col3:
        completed_today = len([o for o in st.session_state.orders 
                             if o.get('status') == 'completed' and 
                             o.get('completion_date', '').startswith(datetime.now().strftime("%Y-%m-%d"))])
        st.metric("Completed Today", completed_today, delta=None)
    
    with col4:
        total_active = len([o for o in st.session_state.orders 
                          if o.get('status') not in ['completed', 'rejected']])
        st.metric("Active Orders", total_active, delta=None)
    
    # Main content tabs with icons
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Pending Orders",
        "📦 Packing Queue",
        "📊 Inventory",
        "📜 Order History"
    ])
    
    with tab1:
        show_pending_orders()
    
    with tab2:
        show_packing_orders()
    
    with tab3:
        show_inventory_management()
    
    with tab4:
        show_order_history()

def show_pending_orders():
    st.subheader("📦 Pending Orders")
    
    # Filter orders that need production approval (after marketing approval)
    pending_orders = [order for order in st.session_state.orders 
                     if order['status'] == 'pending_production_approval' and 
                     order.get('marketing_approved', False)]
    
    if not pending_orders:
        st.info("No pending orders to review")
        return
    
    for order in pending_orders:
        with st.expander(f"Order #{format_order_id(order['order_id'])} - Pending Production Approval"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Company:** {order['company_name']}")
                st.write(f"**Contact name:** {order['contact_name']}")
                st.write(f"**Total Amount:** ${order['total']:.2f}")
                
                # Show order items
                st.write("**Order Items:**")
                for item in order['items']:
                    st.write(f"- {item['seed']}: {item['quantity']}kg at ${item['price_per_kg']}/kg")
                if order.get('special_instructions'):
                    st.write("**Special Instructions:**")
                    st.write(order['special_instructions'])
            
            with col2:
                if st.button("✅ Approve", key=f"approve_{order['order_id']}"):
                    # Single update to pending_payment_term status
                    update_order_status(
                        order=order,
                        status='pending_payment_term',
                        production_approved=True,
                        marketing_approved=True
                    )
                    
                    # Notify customer
                    create_notification(
                        order_id=order['order_id'],
                        notification_type='order_status',
                        title='Order Approved - Select Payment Terms',
                        message=f'Your order #{format_order_id(order["order_id"])} has been approved by production. Please select your payment terms.',
                        priority='high',
                        recipient='customer'
                    )
                    st.success("Order approved!")
                    st.rerun()
                
                if st.button("❌ Reject", key=f"reject_{order['order_id']}"):
                    rejection_reason = st.text_area(
                        "Rejection Reason",
                        key=f"reject_reason_{order['order_id']}"
                    )
                    if rejection_reason and st.button("Confirm Rejection", key=f"confirm_reject_{order['order_id']}"):
                        update_order_status(
                            order=order,
                            status='production_rejected',
                            production_approved=False,
                            marketing_approved=True
                        )
                        # Add rejection reason to order
                        for idx, o in enumerate(st.session_state.orders):
                            if o['order_id'] == order['order_id']:
                                st.session_state.orders[idx]['rejection_reason'] = rejection_reason
                                st.session_state.orders[idx]['rejection_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Notify customer
                        create_notification(
                            order_id=order['order_id'],
                            notification_type='order_status',
                            title='Order Rejected by Production',
                            message=f'Your order #{format_order_id(order["order_id"])} has been rejected by production. Reason: {rejection_reason}',
                            priority='high',
                            recipient='customer'
                        )
                        st.error("Order rejected!")
                        st.rerun()

def update_order_status(order, status, production_approved=False, marketing_approved=True):
    """Update order status and maintain history."""
    # Ensure order_history exists
    if 'order_history' not in st.session_state:
        st.session_state.order_history = []
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update the order status
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            previous_status = o.get('status', '')
            st.session_state.orders[idx]['status'] = status
            st.session_state.orders[idx]['production_approved'] = production_approved
            st.session_state.orders[idx]['marketing_approved'] = marketing_approved
            
            # Get appropriate message for the status change
            message = get_status_message(status, previous_status)
            
            # Add tracking update to the order
            if 'tracking_updates' not in st.session_state.orders[idx]:
                st.session_state.orders[idx]['tracking_updates'] = []
            
            # Map internal status to display status
            display_status = {
                'pending_marketing_approval': 'Pending Marketing Approval',
                'marketing_approved': 'Marketing Approved',
                'pending_production_approval': 'Pending Production Approval',
                'production_approved': 'Production Approved',
                'pending_payment_term': 'Pending Payment Term',
                'payment_verified': 'Payment Verified',
                'ready_for_pickup': 'Ready for Pickup',
                'completed': 'Completed'
            }.get(status, status.replace('_', ' ').title())
            
            # Add the tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': timestamp,
                'status': display_status,  # Use display status for tracking
                'message': message
            })
            
            # Add to order history
            history_entry = {
                'order_id': order['order_id'],
                'timestamp': timestamp,
                'previous_status': previous_status,
                'new_status': status,
                'message': message,
                'updated_by': 'Production Team'
            }
            st.session_state.order_history.append(history_entry)

def get_status_message(new_status, previous_status):
    """Generate appropriate message based on status change."""
    status_messages = {
        'pending_marketing_approval': 'Order submitted for marketing review',
        'marketing_approved': 'Order approved by marketing team',
        'pending_production_approval': 'Order sent to production for review',
        'production_approved': 'Order approved by production team',
        'pending_payment_term': 'Order approved by production team. Please select payment terms.',
        'production_rejected': 'Order rejected by production team',
        'payment_term_selected': 'Payment term selected',
        'pending_payment': 'Awaiting payment',
        'payment_verified': 'Payment has been verified',
        'packing': 'Order is being packed',
        'ready_for_pickup': 'Order has been packed and is ready for pickup',
        'completed': 'Order has been completed',
        'do_generated': 'Delivery Order has been generated'
    }
    return status_messages.get(new_status, f'Status changed from {previous_status} to {new_status}')

def show_order_history():
    """Display order history with filtering and sorting options."""
    st.title("📜 Order History")
    
    if 'order_history' not in st.session_state:
        st.session_state.order_history = []
        
    if not st.session_state.order_history:
        st.info("No order history available")
        return
    
    # Filtering options
    col1, col2, col3 = st.columns(3)
    with col1:
        order_id_filter = st.text_input("Filter by Order ID")
    with col2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=list(set(entry['new_status'] for entry in st.session_state.order_history))
        )
    with col3:
        date_filter = st.date_input("Filter by Date", None)
    
    # Apply filters
    filtered_history = st.session_state.order_history
    
    if order_id_filter:
        filtered_history = [
            entry for entry in filtered_history 
            if order_id_filter.lower() in format_order_id(entry['order_id']).lower()
        ]
    
    if status_filter:
        filtered_history = [
            entry for entry in filtered_history 
            if entry['new_status'] in status_filter
        ]
    
    if date_filter:
        filtered_history = [
            entry for entry in filtered_history 
            if entry['timestamp'].startswith(date_filter.strftime("%Y-%m-%d"))
        ]
    
    # Sort by timestamp (newest first)
    filtered_history.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Display history entries
    for entry in filtered_history:
        with st.expander(f"Order #{format_order_id(entry['order_id'])} - {entry['timestamp']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Status Change:**")
                st.write(f"From: {entry['previous_status']}")
                st.write(f"To: {entry['new_status']}")
                st.write(f"**Updated By:** {entry['updated_by']}")
            
            with col2:
                st.write("**Timestamp:**")
                st.write(entry['timestamp'])
                st.write("**Message:**")
                st.write(entry['message'])

def show_inventory_management():
    st.subheader("📊 Inventory Management")
    
    # Initialize inventory if not exists
    if 'inventory' not in st.session_state:
        st.session_state.inventory = [
            {
                'seed_type': 'Dura Palm',
                'quantity': 1000,
                'price': 15.00,
                'min_stock': 100,
                'location': 'Category A',
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                'seed_type': 'Pisifera Palm',
                'quantity': 750,
                'price': 18.00,
                'min_stock': 150,
                'location': 'Category B',
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                'seed_type': 'Tenera Palm',
                'quantity': 500,
                'price': 20.00,
                'min_stock': 75,
                'location': 'Category A',
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                'seed_type': 'Compact Palm',
                'quantity': 300,
                'price': 16.50,
                'min_stock': 50,
                'location': 'Category C',
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                'seed_type': 'Elite Palm',
                'quantity': 400,
                'price': 25.00,
                'min_stock': 80,
                'location': 'Category B',
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
    
    # Quick stats cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = len(st.session_state.inventory)
        st.metric("Total Products", total_items)
    
    with col2:
        total_value = sum(item['quantity'] * item['price'] for item in st.session_state.inventory)
        st.metric("Total Inventory Value", f"${total_value:,.2f}")
    
    with col3:
        total_quantity = sum(item['quantity'] for item in st.session_state.inventory)
        st.metric("Total Stock (kg)", f"{total_quantity:,}")
    
    with col4:
        low_stock = len([item for item in st.session_state.inventory if item['quantity'] <= item['min_stock']])
        st.metric("Low Stock Items", low_stock, delta_color="inverse")
    
    # Add new inventory
    with st.expander("➕ Add New Inventory"):
        col1, col2, col3 = st.columns(3)
        with col1:
            seed_type = st.selectbox(
                "Seed Type",
                options=['Dura Palm', 'Pisifera Palm', 'Tenera Palm', 'Compact Palm', 'Elite Palm']
            )
            location = st.selectbox("Location", ["Category A", "Category B", "Category C"])
        with col2:
            quantity = st.number_input("Quantity (kg)", min_value=0)
            min_stock = st.number_input("Minimum Stock Level (kg)", min_value=0)
        with col3:
            price = st.number_input("Price per kg ($)", min_value=0.0, step=0.01)
        
        if st.button("Add Inventory"):
            st.session_state.inventory.append({
                'seed_type': seed_type,
                'quantity': quantity,
                'price': price,
                'min_stock': min_stock,
                'location': location,
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success("✅ Inventory added successfully!")
            st.rerun()
    
    # Update existing inventory
    with st.expander("📝 Update Existing Inventory"):
        for idx, item in enumerate(st.session_state.inventory):
            st.markdown(f"### {item['seed_type']}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_quantity = st.number_input(
                    "Quantity (kg)", 
                    value=item['quantity'],
                    key=f"qty_{idx}"
                )
            with col2:
                new_price = st.number_input(
                    "Price per kg ($)", 
                    value=item['price'],
                    step=0.01,
                    key=f"price_{idx}"
                )
            with col3:
                if st.button("Update", key=f"update_{idx}"):
                    st.session_state.inventory[idx]['quantity'] = new_quantity
                    st.session_state.inventory[idx]['price'] = new_price
                    st.session_state.inventory[idx]['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success("✅ Updated successfully!")
                    st.rerun()
    
    # Display current inventory
    st.markdown("### 📊 Current Inventory")
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(st.session_state.inventory)
    
    # Add total value column
    df['total_value'] = df['quantity'] * df['price']
    
    # Add stock status
    df['stock_status'] = df.apply(
        lambda x: '🔴 Low' if x['quantity'] <= x['min_stock'] 
        else '🟢 Good' if x['quantity'] > x['min_stock'] * 2 
        else '🟡 Medium',
        axis=1
    )
    
    # Reorder columns
    columns = ['seed_type', 'quantity', 'price', 'total_value', 'min_stock', 'stock_status', 'location', 'last_updated']
    df = df[columns]
    
    # Format the DataFrame
    formatted_df = df.style.format({
        'price': '${:.2f}',
        'total_value': '${:,.2f}',
        'quantity': '{:,.0f}',
        'min_stock': '{:,.0f}'
    })
    
    st.dataframe(formatted_df, use_container_width=True)

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

def show_packing_orders():
    st.subheader("📦 Orders for Packing")
    
    packing_orders = [
        order for order in st.session_state.orders 
        if order.get('status') == 'payment_verified'
    ]
    
    if not packing_orders:
        st.info("No orders pending packing")
        return
    
    for order in packing_orders:
        with st.expander(f"Order #{format_order_id(order['order_id'])} - Pack Order"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Customer:** {order['contact_name']}")
                st.write(f"**Company:** {order['company_name']}")
                
                # Show order items
                st.write("**Order Items:**")
                for item in order['items']:
                    st.write(f"- {item['seed']}: {item['quantity']}kg")
                
                if order.get('special_instructions'):
                    st.write("**Special Instructions:**")
                    st.write(order['special_instructions'])
            
            with col2:
                if st.button("✅ Packing Complete", key=f"pack_{order['order_id']}"):
                    # Use update_order_status instead of direct update
                    update_order_status(
                        order=order,
                        status='ready_for_pickup',
                        production_approved=True,
                        marketing_approved=True
                    )
                    
                    # Add packing date
                    for idx, o in enumerate(st.session_state.orders):
                        if o['order_id'] == order['order_id']:
                            st.session_state.orders[idx]['packing_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Notify marketing team
                    create_notification(
                        order_id=order['order_id'],
                        notification_type='order_packed',
                        title='Order Ready for Pickup',
                        message=f'Order #{format_order_id(order["order_id"])} has been packed and is ready for pickup.',
                        priority='high',
                        recipient='marketing'
                    )
                    
                    st.success("Order marked as ready for pickup!")
                    st.rerun()