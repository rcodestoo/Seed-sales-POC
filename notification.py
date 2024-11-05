# notifications.py

import uuid
from datetime import datetime
import streamlit as st

def format_order_id(order_id):
    """Format the order ID to display only the first 8 characters."""
    return order_id[:8]


def create_notification(order_id, notification_type, title, message, priority='medium', recipient='none'):
    """Creates a new notification for the specified recipient team and adds it to the session state."""
    
    # Define the session key based on the recipient
    session_key = {
        'customer': 'notification_customer',
        'production': 'production_notifications',
        'marketing': 'marketing_notifications'
    }.get(recipient)
    
    # Initialize session state if not exists
    if session_key and session_key not in st.session_state:
        st.session_state[session_key] = []
    
    # Check for existing notification
    existing_notification = any(
        n['order_id'] == order_id and 
        n['type'] == notification_type and 
        n['title'] == title 
        for n in st.session_state[session_key]
    )
    
    # Only create and add notification if it doesn't exist
    if not existing_notification:
        notification = {
            'id': str(uuid.uuid4()),
            'type': notification_type,
            'title': title,
            'message': message,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'read': False,
            'order_id': order_id,
            'priority': priority
        }
        st.session_state[session_key].append(notification)
        return notification
    return None

def mark_as_read(notification_id):
    """Marks a notification as read."""
    for notification in st.session_state.notification_customer:
        if notification['id'] == notification_id:
            notification['read'] = True
            return True
    return False

def get_priority_icon(priority):
    """Returns the appropriate icon for notification priority"""
    icons = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }
    return icons.get(priority.lower(), '')

def get_relative_time(timestamp_str):
    """Returns a human-readable relative time string."""
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    delta = now - timestamp
    
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"
    
def get_notification_badge(notification_type):
    """Returns a formatted label for the notification type."""
    type_labels = {
        'order_status': 'Order Status',
        'system_update': 'System Update',
        'reminder': 'Reminder'
    }
    return type_labels.get(notification_type, notification_type)


def filter_notifications(notifications, filter_read, filter_priority):
    if filter_read != "All":
        is_read = filter_read == "Read"
        notifications = [n for n in notifications if n.get('read', False) == is_read]
    if filter_priority != "All":
        notifications = [n for n in notifications if n.get('priority', 'normal').lower() == filter_priority.lower()]
    return notifications

def add_notification_styles():
    st.markdown("""
        <style>
         /* Notification styles */
        .notification-card { padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid; position: relative; }
        .notification-unread { background-color: #F8FAFC; }
        .notification-unread::before { content: ''; position: absolute; top: 50%; left: -4px; transform: translateY(-50%); width: 8px; height: 8px; border-radius: 50%; background-color: #3B82F6; }
        .notification-high { border-left-color: #E53E3E; }
        .notification-medium { border-left-color: #D69E2E; }
        .notification-low { border-left-color: #38A169; }
        .notification-title { font-weight: bold; margin-bottom: 5px; }
        .notification-message { color: #4A5568; margin-bottom: 10px; }
        .notification-time { color: #718096; font-size: 0.875rem; }
        .notification-badge { display: inline-flex; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 500; margin-bottom: 8px; }
        .badge-payment_term { background-color: #EFF6FF; color: #1E40AF; }
        .badge-order_status { background-color: #F0FDF4; color: #166534; }
        .badge-customer_request { background-color: #FEF2F2; color: #991B1B; }
        .badge-system_update { background-color: #FDF2F8; color: #9D174D; }
        .badge-do_generated { background-color: #E0F2FE; color: #0369A1; }
        .badge-payment_verification { background-color: #FEE2E2; color: #B91C1C; }
        .badge-payment_status { background-color: #E7F3E7; color: #065F46; }
        .badge-payment { background-color: #F3E8FF; color: #7C3AED; }
        .badge-pickup { background-color: #FEF3C7; color: #92400E; }
        .badge-approval { background-color: #E0E7FF; color: #3730A3; }
        .badge-do_request { background-color: #FFF4E5; color: #D97706; }
        </style>
    """, unsafe_allow_html=True)


def show_notifications_customer():
    """Displays the notifications interface for customers."""
    add_notification_styles()
    st.title("🔔 Customer Notifications")
    
    # Initialize if not exists
    if 'notification_customer' not in st.session_state:
        st.session_state.notification_customer = []
    
    if not st.session_state.notification_customer:
        st.info("You have no notifications.")
        return
    
    # Filtering options
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_read = st.selectbox(
            "Filter by status",
            ["All", "Unread", "Read"],
            key="customer_read_filter"
        )
    with col2:
        filter_priority = st.selectbox(
            "Filter by priority",
            ["All", "High", "Medium", "Low"],
            key="customer_priority_filter"
        )
    with col3:
        filter_category = st.selectbox(
            "Filter by category",
            ["All", "payment_status", "payment", "payment_terms", "pickup", "approval"],
            key="customer_category_filter"
        )
    
    # Apply filters
    filtered_notifications = filter_notifications(
        st.session_state.notification_customer,
        filter_read,
        filter_priority
    )
    
    # Filter by category
    if filter_category != "All":
        filtered_notifications = [n for n in filtered_notifications if n['type'] == filter_category]
    
    # Sort notifications by timestamp (newest first)
    filtered_notifications.sort(
        key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%d %H:%M:%S"),
        reverse=True
    )
    
    # Display notifications
    for idx, notification in enumerate(filtered_notifications):
        read_class = 'notification-read' if notification['read'] else 'notification-unread'
        priority_class = f"notification-{notification['priority']}"
        
        st.markdown(
            f"""
            <div class="notification-card {read_class} {priority_class}">
                <div class="notification-badge badge-{notification['type']}">
                    {get_notification_badge(notification['type'])}
                </div>
                <div class="notification-title">
                    {get_priority_icon(notification['priority'])} {notification['title']}
                </div>
                <div class="notification-message">{notification['message']}</div>
                <div class="notification-time">
                    Order ID: {notification['order_id']} | {get_relative_time(notification['timestamp'])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if not notification['read']:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Mark as Read", key=f"customer_read_{notification['id']}_{idx}"):
                    notification['read'] = True
                    st.rerun()
                    
def show_production_notifications():
    add_notification_styles() 
    st.title("🔔 Production Notifications")

    if not st.session_state.production_notifications:
        st.info("No notifications to display")
        return

    # Filtering options
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_read = st.selectbox("Filter by Status", ["All", "Unread", "Read"])
    with col2:
        filter_priority = st.selectbox("Filter by Priority", ["All", "High", "Normal", "Low"])
    with col3:
        filter_category = st.selectbox(
            "Filter by category",
            ["All", "production_update", "order_status", "system_update", "do_request"],
            key="production_category_filter"
        )

    notifications = filter_notifications(st.session_state.production_notifications, filter_read, filter_priority)

    # Filter by category
    if filter_category != "All":
        notifications = [n for n in notifications if n['type'] == filter_category]

    # Display notifications
    for idx, notification in enumerate(notifications):
        # Assign classes based on read status and priority
        read_class = 'notification-read' if notification['read'] else 'notification-unread'
        priority_class = f'notification-{notification["priority"].lower()}'

        # Use a container for each notification
        with st.container():
            st.markdown(
                f"""
                <div class="notification-card {read_class} {priority_class}">
                    <div class="notification-badge badge-{notification['type']}">
                        {get_notification_badge(notification['type'])}
                    </div>
                    <div class="notification-title">{notification['title']}</div>
                    <div class="notification-message">{notification['message']}</div>
                    <div class="notification-time">{notification['timestamp']}</div>
                    <div class="notification-actions">
                        {'<span>' + ('🔴' if notification['priority'].lower() == 'high' else '🟡' if notification['priority'].lower() == 'normal' else '🟢') + '</span>'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if not notification['read'] and st.button("Mark as Read", key=f"read_{idx}"):
                notification['read'] = True
                st.rerun()

            st.divider()  # Adds a visual divider between notifications

def show_marketing_notifications():
    """Displays the notifications interface for marketing team."""
    add_notification_styles()
    st.title("🔔 Marketing Notifications")
    
    # Initialize marketing notifications if not exists
    if 'marketing_notifications' not in st.session_state:
        st.session_state.marketing_notifications = []
    
    if not st.session_state.marketing_notifications:
        st.info("No marketing notifications to display")
        return
    
    # Add bulk actions
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Mark all as read"):
            for notification in st.session_state.marketing_notifications:
                notification['read'] = True
            st.rerun()
    
    # Filtering options
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_read = st.selectbox(
            "Filter by status",
            ["All", "Unread", "Read"],
            key="marketing_read_filter"
        )
    with col2:
        filter_priority = st.selectbox(
            "Filter by priority",
            ["All", "High", "Medium", "Low"],
            key="marketing_priority_filter"
        )
    with col3:
        filter_category = st.selectbox(
            "Filter by category",
            ["All", "payment_term", "order_status", "customer_request", "system_update", "do_generated", "payment_verification"],
            key="marketing_category_filter"
        )
    
    # Apply filters
    filtered_notifications = filter_notifications(
        st.session_state.marketing_notifications,
        filter_read,
        filter_priority
    )
    
    # Filter by category
    if filter_category != "All":
        filtered_notifications = [n for n in filtered_notifications if n['type'] == filter_category]
    
    # Sort notifications by timestamp (newest first)
    filtered_notifications.sort(
        key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%d %H:%M:%S"),
        reverse=True
    )
    
    # Display notifications
    for idx, notification in enumerate(filtered_notifications):
        read_class = 'notification-read' if notification['read'] else 'notification-unread'
        priority_class = f"notification-{notification['priority']}"
        
        st.markdown(
            f"""
            <div class="notification-card {read_class} {priority_class}">
                <div class="notification-badge badge-{notification['type']}">
                    {get_notification_badge(notification['type'])}
                </div>
                <div class="notification-title">
                    {get_priority_icon(notification['priority'])} {notification['title']}
                </div>
                <div class="notification-message">{notification['message']}</div>
                <div class="notification-time">
                    Order ID: {notification['order_id']} | {get_relative_time(notification['timestamp'])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if not notification['read']:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Mark as Read", key=f"marketing_read_{notification['id']}_{idx}"):
                    notification['read'] = True
                    st.rerun()
        
        # Add a divider between notifications
        if idx < len(filtered_notifications) - 1:
            st.divider()
    
    # Add space between categories
    st.markdown("<br>", unsafe_allow_html=True)

def notify_customer_pickup(order):
    """Notify customer about DO and pickup availability"""
    # Update order status
    for idx, o in enumerate(st.session_state.orders):
        if o['order_id'] == order['order_id']:
            st.session_state.orders[idx]['status'] = 'ready_for_pickup'
            # Add tracking update
            st.session_state.orders[idx]['tracking_updates'].append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'Ready for Pickup',
                'message': f'Order is ready for pickup. DO Number: {order["do_number"]}'
            })
    
    # Create notification for customer
    create_notification(
        order_id=order['order_id'],
        notification_type='pickup',
        title='Order Ready for Pickup',
        message=f"Your order #{order['order_id']} is ready for pickup. DO Number: {order['do_number']}. Please schedule your pickup time.",
        priority='high',
        recipient='customer'
    )


def show_do_notifications():
    """Show DO notifications for marketing team to review and notify customers"""
    add_notification_styles()
    st.subheader("📋 Delivery Order Notifications")
    
    # Filter orders with generated DOs that haven't been notified to customers
    do_orders = [
        order for order in st.session_state.orders 
        if order.get('status') == 'do_generated'
    ]
    
    if not do_orders:
        st.info("No pending DO notifications")
        return
    
    for order in do_orders:
        with st.expander(f"Order #{format_order_id(order['order_id'])} - DO #{order.get('do_number', 'N/A')}"):
            st.write(f"**Customer:** {order['contact_name']}")
            st.write(f"**Company:** {order['company_name']}")
            st.write(f"**DO Generated Date:** {order.get('do_date', 'N/A')}")
            
            # Add DO review functionality here
            st.write("**Review DO Details:**")
            st.write("- Verify customer information")
            st.write("- Check order items and quantities")
            st.write("- Confirm DO number and date")
            
            if st.button("Approve and Notify Customer", key=f"notify_{order['order_id']}"):
                notify_customer_pickup(order)
                st.success("DO approved and customer notified successfully!")
                st.rerun()

def initialize_notifications():
    """Initialize all notification-related session state variables."""
    if 'marketing_notifications' not in st.session_state:
        st.session_state.marketing_notifications = []
    
    if 'production_notifications' not in st.session_state:
        st.session_state.production_notifications = []
    
    if 'notification_customer' not in st.session_state:
        st.session_state.notification_customer = []