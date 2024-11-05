import streamlit as st
from datetime import datetime
import pandas as pd
from notification import create_notification,show_do_notifications

def format_order_id(order_id):
    """Format the order ID to display only the first 8 characters."""
    return order_id[:8]

def show_marketing_dashboard():
    st.title("📊 Marketing Dashboard")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Order Management",
        "Payment Terms Review", 
        "Payment Verification", 
        "DO Notifications",
        "Customer Support"
    ])
    
    with tab1:
        show_order_management()
        
    
    with tab2:
        show_payment_approvals()
    
    with tab3:
        show_payment_verification()
        
    with tab4:
        show_do_notifications()
    
    with tab5:
        show_customer_support()



def show_payment_approvals():
    st.subheader("💰Payment Terms Review")
    
    # Filter orders that need payment review - updated status name
    payment_review_orders = [
        order for order in st.session_state.orders 
        if (order.get('status') == 'pending_payment_approval' and order.get('payment_term') is not None) 
    ]
    
    if not payment_review_orders:
        st.info("No payment terms pending review")
        return
    
    for order in payment_review_orders:
        with st.expander(f"Order #{format_order_id(order['order_id'])} - Payment Terms Review"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Customer:** {order['contact_name']}")
                st.write(f"**Company:** {order['company_name']}")
                st.write(f"**Total Amount:** ${order.get('total', 0):,.2f}")
                st.write(f"**Requested Payment Terms:** {order.get('payment_term', 'Not specified')}")
                
                # Additional customer information
                st.write("**Customer History:**")
                st.write(f"Previous Orders: {order.get('previous_orders_count', 0)}")
                st.write(f"Payment History Rating: {order.get('payment_rating', 'N/A')}")
            
            with col2:
                review_decision = st.radio(
                    "Payment Terms Decision",
                    ["Approve", "Reject"],
                    key=f"decision_{order['order_id']}"
                )
                
                if review_decision == "Reject":
                    rejection_reason = st.text_area(
                        "Rejection Reason",
                        key=f"reject_reason_{order['order_id']}"
                    )
                
                if st.button("Submit Decision", key=f"submit_{order['order_id']}"):
                    if review_decision == "Approve":
                        approve_payment_terms(order)
                    else:
                        reject_payment_terms(order, rejection_reason)
                    st.rerun()

def approve_payment_terms(order):
    # Update order status
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['status'] = 'payment_terms_approved'
            st.session_state.orders[idx]['payment_approval_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Payment Terms Approved',
                'message': 'Your payment terms have been approved. Please proceed with payment.'
            })
    
    # Create notification for customer
    create_notification(
        order_id=order['order_id'],
        notification_type='payment_terms',
        title='Payment Terms Approved',
        message=f"Payment terms for order #{order['order_id']} have been approved. Please proceed with payment.",
        priority='high',
        recipient='customer'
    )

def reject_payment_terms(order, reason):
    # Update order status
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['status'] = 'payment_terms_rejected'
            st.session_state.orders[idx]['rejection_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.orders[idx]['rejection_reason'] = reason
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Payment Terms Rejected',
                'message': f'Payment terms rejected: {reason}'
            })
    
    # Create notification for customer
    create_notification(
        order_id=order['order_id'],
        notification_type='payment_terms',
        title='Payment Terms Review - Action Required',
        message=f"Payment terms for order #{order['order_id']} require revision. Reason: {reason}. Please contact customer support for assistance.",
        priority='high',
        recipient='customer'
    )

def show_payment_verification():
    st.subheader("💰Payment Verification")
    
    # Filter orders that need payment verification
    pending_payment_orders = [
        order for order in st.session_state.orders 
        if order.get('status') == 'payment_submitted'
    ]
    
    if not pending_payment_orders:
        st.info("No payments pending verification")
        return
        
    for order in pending_payment_orders:
        with st.expander(f"Order #{order['order_id']} - Payment Verification"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Customer:** {order['contact_name']}")
                st.write(f"**Company:** {order['company_name']}")
                st.write(f"**Total Amount:** ${order.get('payment_amount', 0):,.2f}")
                st.write(f"**Payment Method:** {order.get('payment_method', 'Not specified')}")
                st.write(f"**Payment Date:** {order.get('payment_timestamp', 'Not specified')}")
                
                if 'payment_proof' in order:
                    st.write("**Payment Proof:**")
                    st.image(order['payment_proof'], caption="Payment Proof Document")
            
            with col2:
                verification_status = st.radio(
                    "Verification Status",
                    ["Verify Payment", "Request Clarification"],
                    key=f"verify_{order['order_id']}"
                )
                
                if verification_status == "Request Clarification":
                    clarification_reason = st.text_area(
                        "Clarification Details",
                        key=f"clarify_{order['order_id']}"
                    )
                
                if st.button("Submit Verification", key=f"submit_verify_{order['order_id']}"):
                    if verification_status == "Verify Payment":
                        verify_payment(order)
                        st.success("Payment verified successfully!")
                    else:
                        request_payment_clarification(order, clarification_reason)
                        st.success("Clarification request sent to customer!")
                    st.rerun()

def verify_payment(order):
    """Verify payment and notify production to generate DO"""
    # Update order status
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['status'] = 'payment_verified'
            st.session_state.orders[idx]['payment_verification_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Payment Verified',
                'message': 'Payment has been verified. Order is being processed.'
            })
    
    # Notify customer about payment verification
    create_notification(
        order_id=order['order_id'],
        notification_type='payment_status',
        title='Payment Verified',
        message=f"Payment for order #{order['order_id']} has been verified. Your order is being processed.",
        priority='high',
        recipient='customer'
    )
    
    # Notify production to generate DO
    create_notification(
        order_id=order['order_id'],
        notification_type='do_request',
        title='Generate Delivery Order',
        message=f"Payment verified for order #{order['order_id']}. Please generate delivery order.",
        priority='high',
        recipient='production'
    )

def request_payment_clarification(order, reason):
    # Update order status and add clarification request
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['status'] = 'payment_clarification_required'
            st.session_state.orders[idx]['clarification_reason'] = reason
            st.session_state.orders[idx]['clarification_request_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Payment Clarification Required',
                'message': f'Additional payment information required: {reason}'
            })
    
    # Create notification for customer
    create_notification(
        order_id=order['order_id'],
        notification_type='payment_clarification',
        title='Payment Clarification Required',
        message=f"We need additional information about your payment for order #{order['order_id']}: {reason}",
        priority='high',
        recipient='customer'
    )


def update_order_status_for_payment_review(order, approved):
    # Update status based on marketing team's decision
    if approved:
        order['status'] = 'payment_terms_approved'
        message = 'Payment terms approved by marketing team'
    else:
        order['status'] = 'payment_terms_rejected'
        message = 'Payment terms rejected by marketing team'

    # Append to tracking updates
    order['tracking_updates'].append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': order['status'],
        'message': message
    })

    # Create a notification for the customer
    create_notification(
        order_id=order['order_id'],
        notification_type='payment_review',
        title='Payment Review Update',
        message=message,
        priority='high',
        recipient='customer'
    )

def show_order_management():
    st.subheader("📋Order Management")
    
    # Updated status filter options with clear labels
    status_mapping = {
        "All": "All",
        "pending_payment_term": "Awaiting Payment Term Selection",
        "pending_payment_approval": "Pending Payment Term Approval",
        "payment_terms_approved": "Payment Terms Approved",
        "payment_terms_rejected": "Payment Terms Rejected",
        "payment_completed": "Payment Completed",
        "ready_for_pickup": "Ready for Pickup",
        "completed": "Order Completed",
        "payment_submitted": "Payment Submitted",
        "payment_verified": "Payment Verified",
        "do_generated": "DO Generated",
        "pending_production": "Pending Production",  # Added missing status
        "in_production": "In Production",           # Added production-related status
        "production_completed": "Production Completed"  # Added production-related status
    }
    
    status_filter = st.selectbox(
        "Filter by Status",
        list(status_mapping.keys()),
        format_func=lambda x: status_mapping[x]
    )
    
    # Filter orders based on selected status
    if status_filter != "All":
        filtered_orders = [order for order in st.session_state.orders if order['status'] == status_filter]
    else:
        filtered_orders = st.session_state.orders
    
    if not filtered_orders:
        st.info("No orders found for the selected status.")
        return
    
    for order in filtered_orders:
        with st.expander(f"Order #{format_order_id(order['order_id'])} - {status_mapping[order['status']]}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Customer:** {order['contact_name']}")
                st.write(f"**Company:** {order['company_name']}")
                st.write(f"**Order Date:** {order['date']}")
                st.write(f"**Total Amount:** ${order.get('total', 0):,.2f}")
                
                # Show order items
                st.write("**Order Items:**")
                for item in order['items']:
                    st.write(f"- {item['seed']}: {item['quantity']}kg at ${item['price_per_kg']}/kg")
                
                if order.get('special_instructions'):
                    st.write("**Special Instructions:**")
                    st.write(order['special_instructions'])
            
            with col2:
                # Actions based on order status
                if order['status'] == 'pending_payment_approval':
                    if st.button("Approve Payment", key=f"approve_payment_{order['order_id']}"):
                        approve_payment_terms(order)
                        st.success("Payment approved!")
                        st.rerun()
                    if st.button("Reject Payment", key=f"reject_payment_{order['order_id']}"):
                        reject_payment_terms(order, "Reason for rejection")
                        st.error("Payment rejected!")
                        st.rerun()
                elif order['status'] == 'payment_terms_approved':
                    st.info("Payment terms approved. Awaiting payment.")
                elif order['status'] == 'ready_for_pickup':
                    st.success("Order is ready for pickup.")
                elif order['status'] == 'completed':
                    st.success("Order has been completed.")
                elif order['status'] == 'payment_submitted':
                    st.info("Payment has been submitted.")
                elif order['status'] == 'payment_verified':
                    st.success("Payment has been verified.")
                elif order['status'] == 'do_generated':
                    st.info("Delivery Order has been generated.")
                # Add more actions as needed for other statuses

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

