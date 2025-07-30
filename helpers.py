import streamlit as st

def show_success_message(message):
    """Display a success message"""
    st.success(message)

def show_error_message(message):
    """Display an error message"""
    st.error(message)

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
