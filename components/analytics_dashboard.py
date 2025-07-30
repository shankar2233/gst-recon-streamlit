import streamlit as st
from utils.analytics import analytics_manager
from datetime import datetime

def show_analytics_widget():
    """Display clean, minimal analytics widget in top-right corner"""
    
    try:
        stats = analytics_manager.get_real_time_stats()
        current_time = datetime.now().strftime("%H:%M")
        
        # Initialize collapse state
        if 'widget_collapsed' not in st.session_state:
            st.session_state.widget_collapsed = False
        
        st.markdown("""
        <style>
        .analytics-widget-clean {
            position: fixed;
            top: 70px;
            right: 20px;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .widget-header {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px 15px;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .widget-title {
            color: white;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .live-dot {
            width: 6px;
            height: 6px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse-dot 2s infinite;
        }
        
        @keyframes pulse-dot {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .minimize-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            width: 20px;
            height: 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s ease;
        }
        
        .minimize-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .widget-content {
            padding: 12px;
            color: white;
        }
        
        .stats-compact {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: space-between;
        }
        
        .stat-compact {
            background: rgba(255, 255, 255, 0.1);
            padding: 6px 8px;
            border-radius: 6px;
            text-align: center;
            flex: 1;
            min-width: 70px;
        }
        
        .stat-number {
            display: block;
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
        }
        
        .stat-text {
            display: block;
            font-size: 8px;
            opacity: 0.8;
            margin-top: 2px;
        }
        
        .widget-footer {
            padding: 6px 12px;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 0 0 12px 12px;
            text-align: center;
            font-size: 9px;
            opacity: 0.7;
            color: white;
        }
        
        .widget-collapsed {
            width: 50px;
            height: 50px;
            border-radius: 25px;
            cursor: pointer;
        }
        
        .widget-expanded {
            width: 240px;
        }
        
        .collapsed-content {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            font-size: 16px;
            color: white;
        }
        
        @media (max-width: 768px) {
            .analytics-widget-clean {
                top: 60px;
                right: 10px;
            }
            .widget-expanded {
                width: 200px;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create the widget HTML
        if st.session_state.widget_collapsed:
            # Collapsed state - just a small circle with active users
            widget_html = f"""
            <div class="analytics-widget-clean widget-collapsed" onclick="window.parent.postMessage({{'type': 'toggle_widget'}}, '*')">
                <div class="collapsed-content">
                    <div style="text-align: center;">
                        <div style="font-size: 14px; font-weight: bold;">{stats['active_users']}</div>
                        <div style="font-size: 8px; opacity: 0.8;">LIVE</div>
                    </div>
                </div>
            </div>
            """
        else:
            # Expanded state - full widget
            widget_html = f"""
            <div class="analytics-widget-clean widget-expanded">
                <div class="widget-header">
                    <div class="widget-title">
                        <span class="live-dot"></span>
                        Live Analytics
                    </div>
                    <button class="minimize-btn" onclick="window.parent.postMessage({{'type': 'toggle_widget'}}, '*')">−</button>
                </div>
                
                <div class="widget-content">
                    <div class="stats-compact">
                        <div class="stat-compact">
                            <span class="stat-number">{stats['total_visits']}</span>
                            <span class="stat-text">VISITS</span>
                        </div>
                        <div class="stat-compact">
                            <span class="stat-number">{stats['unique_visitors']}</span>
                            <span class="stat-text">USERS</span>
                        </div>
                        <div class="stat-compact">
                            <span class="stat-number">{stats['active_users']}</span>
                            <span class="stat-text">ONLINE</span>
                        </div>
                    </div>
                    
                    <div class="stats-compact" style="margin-top: 8px;">
                        <div class="stat-compact">
                            <span class="stat-number">{stats['total_reconciliations']}</span>
                            <span class="stat-text">JOBS</span>
                        </div>
                        <div class="stat-compact">
                            <span class="stat-number">{stats['total_files_uploaded']}</span>
                            <span class="stat-text">FILES</span>
                        </div>
                    </div>
                </div>
                
                <div class="widget-footer">
                    🕐 {current_time} • GST Analytics
                </div>
            </div>
            """
        
        st.markdown(widget_html, unsafe_allow_html=True)
        
        # Handle toggle functionality
        # Using a hidden button approach since we can't easily handle JavaScript events
        
    except Exception as e:
        # Minimal error widget
        st.markdown(f"""
        <div style="
            position: fixed;
            top: 70px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 11px;
            z-index: 1000;
        ">
            📊 Analytics Error
        </div>
        """, unsafe_allow_html=True)

def show_simple_analytics_badge():
    """Ultra-minimal analytics badge - cleanest option"""
    
    try:
        stats = analytics_manager.get_real_time_stats()
        
        st.markdown(f"""
        <div style="
            position: fixed;
            top: 70px;
            right: 20px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.2);
        ">
            👥 {stats['active_users']} online • 📊 {stats['total_visits']} visits
        </div>
        """, unsafe_allow_html=True)
        
    except:
        pass

# Keep your existing functions unchanged
def show_detailed_analytics():
    """Keep your existing detailed analytics dashboard exactly as is"""
    # Your existing detailed dashboard code stays the same
    pass

def track_page_visit(page_name):
    """Helper function to track page visits"""
    try:
        analytics_manager.track_page_view(page_name)
    except:
        pass

def track_feature_usage(feature_name, additional_data=None):
    """Helper function to track feature usage"""
    try:
        analytics_manager.track_feature_usage(feature_name, additional_data)
    except:
        pass
