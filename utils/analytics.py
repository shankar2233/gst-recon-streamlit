import streamlit as st
import json
import os
from datetime import datetime, timedelta
import time
import uuid
import hashlib
import pandas as pd

class AnalyticsManager:
    def __init__(self):
        self.analytics_file = "data/analytics.json"
        self.sessions_file = "data/sessions.json"
        self.usage_file = "data/usage_stats.json"
        self.ensure_data_directory()
        self.init_session()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs("data", exist_ok=True)
        
        # Initialize files if they don't exist
        if not os.path.exists(self.analytics_file):
            self.save_json(self.analytics_file, {
                "total_visits": 0,
                "unique_visitors": [],
                "daily_visits": {},
                "page_views": {
                    "home": 0,
                    "about": 0,
                    "privacy": 0,
                    "contact": 0
                },
                "created_date": datetime.now().isoformat()
            })
        
        if not os.path.exists(self.sessions_file):
            self.save_json(self.sessions_file, {
                "active_sessions": [],
                "session_history": []
            })
        
        if not os.path.exists(self.usage_file):
            self.save_json(self.usage_file, {
                "reconciliations_performed": 0,
                "files_uploaded": 0,
                "reports_downloaded": 0,
                "total_records_processed": 0,
                "average_processing_time": 0,
                "feature_usage": {
                    "file_upload": 0,
                    "reconciliation": 0,
                    "export_excel": 0,
                    "export_csv": 0
                }
            })
    
    def load_json(self, filename):
        """Load JSON data from file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_json(self, filename, data):
        """Save JSON data to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving {filename}: {e}")
    
    def get_user_id(self):
        """Generate unique user ID based on session"""
        if 'user_id' not in st.session_state:
            # Create a unique ID based on session info
            session_info = f"{st.session_state.get('session_id', str(uuid.uuid4()))}"
            st.session_state.user_id = hashlib.md5(session_info.encode()).hexdigest()[:12]
        return st.session_state.user_id
    
    def init_session(self):
        """Initialize session tracking"""
        if 'session_started' not in st.session_state:
            st.session_state.session_started = datetime.now()
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.session_state.page_views = 0
            self.track_new_visit()
    
    def track_new_visit(self):
        """Track a new visitor/visit"""
        user_id = self.get_user_id()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Load analytics data
        analytics = self.load_json(self.analytics_file)
        
        # Update total visits
        analytics["total_visits"] = analytics.get("total_visits", 0) + 1
        
        # Track unique visitors
        unique_visitors = analytics.get("unique_visitors", [])
        if user_id not in unique_visitors:
            unique_visitors.append(user_id)
            analytics["unique_visitors"] = unique_visitors
        
        # Track daily visits
        daily_visits = analytics.get("daily_visits", {})
        daily_visits[today] = daily_visits.get(today, 0) + 1
        analytics["daily_visits"] = daily_visits
        
        # Save updated analytics
        self.save_json(self.analytics_file, analytics)
        
        # Track active session
        self.update_active_sessions()
    
    def update_active_sessions(self):
        """Update active sessions list"""
        sessions = self.load_json(self.sessions_file)
        current_time = datetime.now()
        
        # Clean old sessions (older than 30 minutes)
        active_sessions = sessions.get("active_sessions", [])
        active_sessions = [
            session for session in active_sessions
            if datetime.fromisoformat(session["last_activity"]) > current_time - timedelta(minutes=30)
        ]
        
        # Add/update current session
        user_id = self.get_user_id()
        session_found = False
        
        for session in active_sessions:
            if session["user_id"] == user_id:
                session["last_activity"] = current_time.isoformat()
                session_found = True
                break
        
        if not session_found:
            active_sessions.append({
                "user_id": user_id,
                "session_id": st.session_state.session_id,
                "start_time": st.session_state.session_started.isoformat(),
                "last_activity": current_time.isoformat()
            })
        
        sessions["active_sessions"] = active_sessions
        self.save_json(self.sessions_file, sessions)
    
    def track_page_view(self, page_name):
        """Track page view"""
        analytics = self.load_json(self.analytics_file)
        page_views = analytics.get("page_views", {})
        page_views[page_name] = page_views.get(page_name, 0) + 1
        analytics["page_views"] = page_views
        self.save_json(self.analytics_file, analytics)
        
        # Update session page views
        st.session_state.page_views = st.session_state.get("page_views", 0) + 1
    
    def track_feature_usage(self, feature_name, additional_data=None):
        """Track feature usage"""
        usage_stats = self.load_json(self.usage_file)
        
        # Update feature usage count
        feature_usage = usage_stats.get("feature_usage", {})
        feature_usage[feature_name] = feature_usage.get(feature_name, 0) + 1
        usage_stats["feature_usage"] = feature_usage
        
        # Track specific metrics
        if feature_name == "reconciliation":
            usage_stats["reconciliations_performed"] = usage_stats.get("reconciliations_performed", 0) + 1
            if additional_data:
                # Track processing time and records
                if "processing_time" in additional_data:
                    current_avg = usage_stats.get("average_processing_time", 0)
                    total_reconciliations = usage_stats.get("reconciliations_performed", 1)
                    new_avg = (current_avg * (total_reconciliations - 1) + additional_data["processing_time"]) / total_reconciliations
                    usage_stats["average_processing_time"] = round(new_avg, 2)
                
                if "records_processed" in additional_data:
                    usage_stats["total_records_processed"] = usage_stats.get("total_records_processed", 0) + additional_data["records_processed"]
        
        elif feature_name == "file_upload":
            usage_stats["files_uploaded"] = usage_stats.get("files_uploaded", 0) + 1
        
        elif feature_name in ["export_excel", "export_csv"]:
            usage_stats["reports_downloaded"] = usage_stats.get("reports_downloaded", 0) + 1
        
        self.save_json(self.usage_file, usage_stats)
    
    def get_analytics_summary(self):
        """Get comprehensive analytics summary"""
        analytics = self.load_json(self.analytics_file)
        sessions = self.load_json(self.sessions_file)
        usage = self.load_json(self.usage_file)
        
        # Calculate active users (last 30 minutes)
        current_time = datetime.now()
        active_sessions = sessions.get("active_sessions", [])
        active_users = len([
            s for s in active_sessions
            if datetime.fromisoformat(s["last_activity"]) > current_time - timedelta(minutes=30)
        ])
        
        # Calculate today's visits
        today = datetime.now().strftime("%Y-%m-%d")
        today_visits = analytics.get("daily_visits", {}).get(today, 0)
        
        # Calculate this week's visits
        week_visits = 0
        for i in range(7):
            date_key = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            week_visits += analytics.get("daily_visits", {}).get(date_key, 0)
        
        return {
            "total_visits": analytics.get("total_visits", 0),
            "unique_visitors": len(analytics.get("unique_visitors", [])),
            "active_users": active_users,
            "today_visits": today_visits,
            "week_visits": week_visits,
            "total_reconciliations": usage.get("reconciliations_performed", 0),
            "total_files_uploaded": usage.get("files_uploaded", 0),
            "total_reports_downloaded": usage.get("reports_downloaded", 0),
            "total_records_processed": usage.get("total_records_processed", 0),
            "average_processing_time": usage.get("average_processing_time", 0),
            "page_views": analytics.get("page_views", {}),
            "session_duration": self.get_session_duration()
        }
    
    def get_session_duration(self):
        """Calculate current session duration"""
        if 'session_started' in st.session_state:
            duration = datetime.now() - st.session_state.session_started
            return round(duration.total_seconds() / 60, 1)  # Return in minutes
        return 0
    
    def get_real_time_stats(self):
        """Get real-time statistics"""
        self.update_active_sessions()  # Update sessions first
        return self.get_analytics_summary()

# Global analytics instance
analytics_manager = AnalyticsManager()
