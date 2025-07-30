import streamlit as st

def show_contact_page():
    st.title("📞 Get in Touch")
    st.markdown("We're here to help! Reach out with questions, feedback, or support needs.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📧 Email Support
        
        **General Inquiries:**  
        support@gstreconciliation.com
        
        **Technical Issues:**  
        tech@gstreconciliation.com
        
        ⏱️ **Response Time:** Within 24 hours
        """)
    
    with col2:
        st.markdown("""
        ### 🕐 Support Hours
        
        **Monday - Friday:**  
        9:00 AM - 6:00 PM (IST)
        
        **Saturday:**  
        10:00 AM - 4:00 PM (IST)
        
        **Sunday:** Closed
        """)
