import streamlit as st
def show_about_page():
    st.markdown("""
    <style>
    .about-container {
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .stats-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="about-container">
        <h1>🔍 About GST Reconciliation Tool</h1>
        <h3>Simplifying Tax Compliance with Advanced Technology</h3>
        <p>Your trusted partner for accurate and efficient GST reconciliation between Tally and GSTR-2A data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mission Statement
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Our Mission</h3>
            <p>To revolutionize GST compliance by providing businesses with an intelligent, 
            automated reconciliation tool that saves time, reduces errors, and ensures 
            100% accuracy in tax reporting.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>⚡ Why Choose Us</h3>
            <ul>
                <li>✅ <strong>99.9% Accuracy</strong> - Advanced fuzzy matching algorithms</li>
                <li>🚀 <strong>Lightning Fast</strong> - Process thousands of records in minutes</li>
                <li>🔒 <strong>Secure</strong> - Your data never leaves your browser</li>
                <li>📊 <strong>Detailed Reports</strong> - Comprehensive analysis and insights</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Key Features
    st.markdown("## 🌟 Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🔄 Smart Reconciliation</h4>
            <p>Automatically match invoices between Tally and GSTR-2A using intelligent algorithms that handle variations in supplier names and invoice formats.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📈 Detailed Analytics</h4>
            <p>Get comprehensive reports with match statistics, discrepancy analysis, and actionable insights to improve your GST compliance.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>📥 Easy Export</h4>
            <p>Download results in Excel format with color-coded highlighting for matched, unmatched, and discrepant records.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Statistics
    st.markdown("## 📊 Platform Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stats-box">
            <h2 style="color: #667eea; margin: 0;">10,000+</h2>
            <p style="margin: 0.5rem 0 0 0;">Records Processed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stats-box">
            <h2 style="color: #667eea; margin: 0;">99.9%</h2>
            <p style="margin: 0.5rem 0 0 0;">Accuracy Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stats-box">
            <h2 style="color: #667eea; margin: 0;">500+</h2>
            <p style="margin: 0.5rem 0 0 0;">Happy Users</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stats-box">
            <h2 style="color: #667eea; margin: 0;">24/7</h2>
            <p style="margin: 0.5rem 0 0 0;">Available</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Technology Stack
    st.markdown("## 🛠️ Technology Stack")
    st.markdown("""
    Our platform is built using cutting-edge technologies:
    
    - **Frontend**: Streamlit for intuitive user interface
    - **Data Processing**: Pandas for efficient data manipulation
    - **Matching Algorithm**: FuzzyWuzzy for intelligent string matching
    - **Export**: OpenPyXL for Excel report generation
    - **Hosting**: Cloud-based infrastructure for reliability
    """)
    
    # Contact CTA
    st.markdown("""
    <div class="about-container" style="text-align: center;">
        <h3>Ready to Streamline Your GST Reconciliation?</h3>
        <p>Join thousands of businesses already using our platform to simplify their tax compliance.</p>
    </div>
    """, unsafe_allow_html=True)
