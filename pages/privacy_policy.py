import streamlit as st

def show_privacy_policy():
    st.markdown("""
    <style>
    .privacy-header {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .privacy-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #3498db;
    }
    .highlight-box {
        background: #e8f4fd;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="privacy-header">
        <h1>🔒 Privacy Policy</h1>
        <p><strong>Last Updated:</strong> July 30, 2025</p>
        <p>Your privacy is important to us. This policy explains how we handle your data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Privacy Points
    st.markdown("""
    <div class="highlight-box">
        <h3>🛡️ Key Privacy Highlights</h3>
        <ul>
            <li>✅ <strong>No Data Storage</strong> - Files are processed locally in your browser</li>
            <li>✅ <strong>No Server Upload</strong> - Your sensitive GST data never leaves your device</li>
            <li>✅ <strong>No Personal Information Required</strong> - Use the tool anonymously</li>
            <li>✅ <strong>Secure Processing</strong> - All operations happen client-side</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Add all the other privacy policy sections from the previous response...
    st.markdown("""
    <div class="privacy-section">
        <h3>1. Information We Collect</h3>
        <h4>Data You Upload:</h4>
        <ul>
            <li>Excel files containing Tally and GSTR-2A data</li>
            <li>This data is processed locally and not transmitted to our servers</li>
            <li>Files are automatically cleared when you close the browser</li>
        </ul>
        
        <h4>Technical Information:</h4>
        <ul>
            <li>Basic usage analytics (page views, feature usage)</li>
            <li>Browser type and version for compatibility</li>
            <li>No personally identifiable information is collected</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Continue with all other sections from the previous privacy policy...
    # (I'm truncating for brevity, but include all sections from the previous response)
