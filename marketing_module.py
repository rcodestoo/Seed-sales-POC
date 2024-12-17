import streamlit as st
from datetime import datetime
import pandas as pd
from notification import create_notification,show_do_notifications

status_mapping = {
    'pending_marketing_approval': 'Pending Marketing Approval',
    'pending_marketing': 'Pending Marketing Approval',
    'marketing_approved': 'Marketing Approved',
    'marketing_rejected': 'Marketing Rejected',
    'pending_production_approval': 'Pending Production Approval',
    'production_approved': 'Production Approved',
    'production_rejected': 'Production Rejected',
    'pending_payment_term': 'Pending Payment Term',
    'pending_payment': 'Pending Payment',
    'payment_verified': 'Payment Verified',
    'in_production': 'In Production',
    'production_completed': 'Production Completed',
    'ready_for_pickup': 'Ready for Pickup',
    'do_generated': 'DO Generated',
    'completed': 'Completed'
}

def format_order_id(order_id):
    """Format the order ID to display only the first 8 characters."""
    return order_id[:8]

def show_marketing_dashboard():
    """Show marketing dashboard with improved UI."""
    st.title("📊 Marketing Dashboard")
    
    # Dashboard Overview Cards in two rows
    st.markdown("### 📈 Overview")
    
    # First row of metrics
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    
    with row1_col1:
        new_orders = len([o for o in st.session_state.orders 
                         if o.get('status') == 'pending_marketing_approval'])
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center;'>
                <h3 style='color: #0d6efd; margin: 0;'>New Orders</h3>
                <h2 style='margin: 10px 0;'>{}</h2>
                <p style='color: #6c757d; margin: 0;'>Pending Marketing Approval</p>
            </div>
        """.format(new_orders), unsafe_allow_html=True)
    
    with row1_col2:
        completed_orders = len([o for o in st.session_state.orders 
                              if o.get('status') == 'completed'])
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center;'>
                <h3 style='color: #198754; margin: 0;'>Completed Orders</h3>
                <h2 style='margin: 10px 0;'>{}</h2>
                <p style='color: #6c757d; margin: 0;'>Successfully Processed</p>
            </div>
        """.format(completed_orders), unsafe_allow_html=True)
    
    with row1_col3:
        total_revenue = sum([o.get('total', 0) for o in st.session_state.orders 
                           if o.get('status') == 'completed'])
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center;'>
                <h3 style='color: #198754; margin: 0;'>Total Revenue</h3>
                <h2 style='margin: 10px 0;'>${:,.2f}</h2>
                <p style='color: #6c757d; margin: 0;'>From Completed Orders</p>
            </div>
        """.format(total_revenue), unsafe_allow_html=True)

    # Second row of metrics
    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    
    with row2_col1:
        ready_pickup = len([o for o in st.session_state.orders 
                          if o.get('status') == 'ready_for_pickup'])
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center;'>
                <h3 style='color: #fd7e14; margin: 0;'>Ready for Pickup</h3>
                <h2 style='margin: 10px 0;'>{}</h2>
                <p style='color: #6c757d; margin: 0;'>Awaiting Customer Pickup</p>
            </div>
        """.format(ready_pickup), unsafe_allow_html=True)
    
    with row2_col2:
        pending_support = len([o for o in st.session_state.orders 
                             if o.get('status') == 'payment_terms_rejected'])
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center;'>
                <h3 style='color: #dc3545; margin: 0;'>Need Support</h3>
                <h2 style='margin: 10px 0;'>{}</h2>
                <p style='color: #6c757d; margin: 0;'>Require Attention</p>
            </div>
        """.format(pending_support), unsafe_allow_html=True)
    
    with row2_col3:
        active_orders = len([o for o in st.session_state.orders 
                           if o.get('status') not in ['completed', 'marketing_rejected', 'production_rejected']])
        st.markdown("""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6; text-align: center;'>
                <h3 style='color: #0dcaf0; margin: 0;'>Active Orders</h3>
                <h2 style='margin: 10px 0;'>{}</h2>
                <p style='color: #6c757d; margin: 0;'>In Progress</p>
            </div>
        """.format(active_orders), unsafe_allow_html=True)
    
    # Main content tabs with icons
    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
    tab1, tab2, tab3 = st.tabs([
        "📋 Order Management",
        "📊 Inventory",
        "👥 Customer Support"
    ])
    
    with tab1:
        show_order_management()
    
    with tab2:
        show_inventory_management()
    
    with tab3:
        show_customer_support()


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



def show_order_management():
    st.subheader("📋 Order Management")
    
    if 'orders' not in st.session_state or not st.session_state.orders:
        st.info("No orders to review")
        return
    
    # Add filter options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=list(status_mapping.values()),
            default=[]
        )
    with col2:
        date_filter = st.date_input("Filter by Date", None)
    with col3:
        search_query = st.text_input("Search Order ID")
    
    # Filter orders based on selected statuses
    filtered_orders = st.session_state.orders
    if status_filter:
        filtered_orders = [
            order for order in filtered_orders 
            if status_mapping.get(order.get('status', '')) in status_filter
        ]
    
    # Apply date filter
    if date_filter:
        filtered_orders = [
            order for order in filtered_orders
            if order.get('date', '').startswith(date_filter.strftime("%Y-%m-%d"))
        ]
    
    # Apply search filter
    if search_query:
        filtered_orders = [
            order for order in filtered_orders
            if search_query.lower() in format_order_id(order['order_id']).lower()
        ]
    
    # Sort orders by date (newest first)
    filtered_orders.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Show order statistics
    st.write("### 📈 Order Statistics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_orders = len(filtered_orders)
        st.metric("Total Orders", total_orders)
    
    with col2:
        pending_approval = len([o for o in filtered_orders if o.get('status') == 'pending_marketing_approval'])
        st.metric("Pending Approval", pending_approval)
    
    with col3:
        pending_pickup = len([o for o in filtered_orders if o.get('status') == 'ready_for_pickup'])
        st.metric("Ready for Pickup", pending_pickup)
    
    with col4:
        completed_orders = len([o for o in filtered_orders if o.get('status') == 'completed'])
        st.metric("Completed Orders", completed_orders)
    
    with col5:
        rejected_orders = len([o for o in filtered_orders if o.get('status') in ['marketing_rejected', 'production_rejected']])
        st.metric("Rejected Orders", rejected_orders)
    
    # Update status colors to match new flow
    status_color = {
        'pending_marketing_approval': '🟡',
        'marketing_approved': '🟢',
        'marketing_rejected': '🔴',
        'pending_production_approval': '🟡',
        'production_approved': '🟢',
        'production_rejected': '🔴',
        'pending_payment_term': '🟡',
        'pending_payment': '🟡',
        'payment_verified': '🟢',
        'packing': '🟡',
        'ready_for_pickup': '🟢',
        'completed': '🟢'
    }
    
    # Display orders
    st.write("### 📦 Orders List")
    for order in filtered_orders:
        current_status = order.get('status', 'unknown')
        status_display = status_mapping.get(current_status, current_status.replace('_', ' ').title())
        
        with st.expander(f"{status_color.get(current_status, '⚪')} Order #{format_order_id(order['order_id'])} - {status_display}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                show_order_details(order)
                
                # Show tracking updates
                if order.get('tracking_updates'):
                    st.write("**Order Timeline:**")
                    for update in reversed(order['tracking_updates']):
                        st.write(f"- {update['timestamp']}: {update['status']} - {update['message']}")
            
            with col2:
                st.write("**Actions Available:**")
                current_status = order.get('status', '')
                
                # Show action buttons based on status
                if current_status == 'pending_marketing_approval':
                    if st.button("✅ Approve", key=f"approve_{order['order_id']}"):
                        approve_marketing_order(order)
                        st.success("Order approved!")
                        st.rerun()
                    
                    if st.button("❌ Reject", key=f"reject_{order['order_id']}"):
                        rejection_reason = st.text_area(
                            "Rejection Reason", 
                            key=f"reason_{order['order_id']}"
                        )
                        if rejection_reason and st.button("Confirm Rejection", key=f"confirm_reject_{order['order_id']}"):
                            reject_marketing_order(order, rejection_reason)
                            st.error("Order rejected!")
                            st.rerun()
                
                # Show notify customer button for ready for pickup orders
                elif current_status == 'ready_for_pickup':
                    if st.button("📞 Notify Customer", key=f"notify_{order['order_id']}"):
                        notify_customer_pickup(order)
                        st.success("Customer notified successfully!")
                        st.rerun()

def show_order_details(order):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"**Customer:** {order['contact_name']}")
        st.write(f"**Company:** {order['company_name']}")
        st.write(f"**Order Date:** {order['date']}")
        st.write(f"**Total Amount:** ${order.get('total', 0):,.2f}")
        
        if order.get('payment_approval_date'):
            st.write(f"**Payment Approval Date:** {order['payment_approval_date']}")
        if order.get('rejection_date'):
            st.write(f"**Rejection Date:** {order['rejection_date']}")
            st.write(f"**Rejection Reason:** {order.get('rejection_reason', 'Not specified')}")
    


def show_customer_support():
    st.subheader("👥Customer Support")
    
    # Filter for orders with rejected payment terms
    rejected_orders = [
        order for order in st.session_state.orders
        if order.get('status') == 'payment_terms_rejected'
    ]
    
    if not rejected_orders:
        st.info("No rejected payment terms to review")
        return
    
    for order in rejected_orders:
        with st.expander(f"Order #{order['order_id']} - Customer Support Required"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Customer:** {order['contact_name']}")
                st.write(f"**Company:** {order['company_name']}")
                st.write(f"**Rejection Reason:** {order.get('rejection_reason', 'Not specified')}")
                st.write(f"**Rejection Date:** {order.get('rejection_date', 'Not specified')}")
                
                # Support notes
                support_notes = st.text_area(
                    "Support Notes",
                    value=order.get('support_notes', ''),
                    key=f"support_notes_{order['order_id']}"
                )
            
            with col2:
                if st.button("Update Support Notes", key=f"update_notes_{order['order_id']}"):
                    update_support_notes(order['order_id'], support_notes)
                    st.success("Support notes updated successfully!")
                
                if st.button("Resubmit for Review", key=f"resubmit_{order['order_id']}"):
                    resubmit_payment_terms(order['order_id'])
                    st.success("Order resubmitted for payment terms review!")

def update_support_notes(order_id, notes):
    for idx, order in enumerate(st.session_state.orders):
        if order['order_id'] == order_id:
            st.session_state.orders[idx]['support_notes'] = notes
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Support Notes Updated',
                'message': 'Customer support notes have been updated.'
            })

def resubmit_payment_terms(order_id):
    for idx, order in enumerate(st.session_state.orders):
        if order['order_id'] == order_id:
            st.session_state.orders[idx]['status'] = 'pending_payment_approval'
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Payment Terms Resubmitted',
                'message': 'Payment terms have been resubmitted for review.'
            })
            
            # Create notification for marketing team
            create_notification(
                order_id=order_id,
                notification_type='payment_terms',
                title='Payment Terms Resubmission',
                message=f"Order #{order_id} has been resubmitted for payment terms review after customer support intervention.",
                priority='high',
                recipient='marketing'
            )

def approve_marketing_order(order):
    """Approve order and send to production"""
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['status'] = 'pending_production_approval'
            st.session_state.orders[idx]['marketing_approved'] = True
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Marketing Approved',
                'message': 'Order approved by marketing team and sent to production for review'
            })
    
    # Notify production team
    create_notification(
        order_id=order['order_id'],
        notification_type='new_order',
        title='New Order for Review',
        message=f'Order #{format_order_id(order["order_id"])} has been approved by marketing and requires production review.',
        priority='high',
        recipient='production'
    )

def reject_marketing_order(order, reason):
    """Reject order and notify customer"""
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['status'] = 'marketing_rejected'
            st.session_state.orders[idx]['rejection_reason'] = reason
            st.session_state.orders[idx]['rejection_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Marketing Rejected',
                'message': f'Order rejected by marketing team. Reason: {reason}'
            })
            
            # Create notification for customer
            create_notification(
                order_id=order['order_id'],
                notification_type='order_status',
                title='Order Rejected',
                message=f'Your order #{format_order_id(order["order_id"])} has been rejected. Reason: {reason}',
                priority='high',
                recipient='customer'
            )

def notify_customer_pickup(order):
    """Notify customer that order is ready for pickup"""
    create_notification(
        order_id=order['order_id'],
        notification_type='pickup_ready',
        title='Order Ready for Pickup',
        message=f'Your order #{format_order_id(order["order_id"])} has been packed and is ready for pickup.',
        priority='high',
        recipient='customer'
    )
    
    # Add tracking update
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Customer Notified',
                'message': 'Customer has been notified that order is ready for pickup.'
            })

