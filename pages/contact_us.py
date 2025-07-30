import streamlit as st
from utils.helpers import show_success_message, show_error_message

def show_contact_page():
    st.markdown("""
    <style>
    .contact-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .contact-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem;
        border-top: 4px solid #667eea;
    }
    .contact-form {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="contact-header">
        <h1>📞 Get in Touch</h1>
        <p>We're here to help! Reach out with questions, feedback, or support needs.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Contact Information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="contact-card">
            <h3>📧 Email Support</h3>
            <p><strong>General Inquiries:</strong><br>
            <a href="mailto:support@gstreconciliation.com">support@gstreconciliation.com</a></p>
            
            <p><strong>Technical Issues:</strong><br>
            <a href="mailto:tech@gstreconciliation.com">tech@gstreconciliation.com</a></p>
            
            <p><strong>Business Inquiries:</strong><br>
            <a href="mailto:business@gstreconciliation.com">business@gstreconciliation.com</a></p>
            
            <p><small>⏱️ <strong>Response Time:</strong> Within 24 hours</small></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="contact-card">
            <h3>🕐 Support Hours</h3>
            <p><strong>Monday - Friday:</strong><br>9:00 AM - 6:00 PM (IST)</p>
            
            <p><strong>Saturday:</strong><br>10:00 AM - 4:00 PM (IST)</p>
            
            <p><strong>Sunday:</strong><br>Closed</p>
            
            <p><strong>Emergency Support:</strong><br>Available for critical issues</p>
            
            <p><small>🌍 <strong>Time Zone:</strong> Indian Standard Time (IST)</small></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Contact Form
    st.markdown("""
    <div class="contact-form">
        <h3>💬 Send us a Message</h3>
        <p>Fill out the form below and we'll get back to you shortly.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("contact_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name *", placeholder="Enter your full name")
            email = st.text_input("Email Address *", placeholder="your.email@company.com")
        
        with col2:
            company = st.text_input("Company Name", placeholder="Your company (optional)")
            subject = st.selectbox("Subject *", [
                "General Inquiry",
                "Technical Support",
                "Bug Report",
                "Feature Request",
                "Business Partnership",
                "Other"
            ])
        
        message = st.text_area("Message *", 
                              placeholder="Please describe your inquiry in detail...",
                              height=150)
        
        # Checkbox for privacy policy
        privacy_agreed = st.checkbox("I agree to the Privacy Policy and Terms of Service *")
        
        submitted = st.form_submit_button("Send Message", 
                                         use_container_width=True,
                                         type="primary")
        
        if submitted:
            if not name or not email or not message:
                show_error_message("Please fill in all required fields marked with *")
            elif not privacy_agreed:
                show_error_message("Please agree to the Privacy Policy and Terms of Service")
            elif "@" not in email:
                show_error_message("Please enter a valid email address")
            else:
                show_success_message(f"Thank you {name}! Your message has been sent successfully. We'll get back to you within 24 hours.")
                st.balloons()
    
    # Add FAQ and other sections from the previous response...
