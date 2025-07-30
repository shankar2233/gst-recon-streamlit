import streamlit as st

def show_contact_page():
    st.markdown(
        """
        <style>
        .contact-header {
            text-align: center;
            font-size: 2.5em;
            font-weight: 700;
            color: #2E86C1;
            margin-bottom: 0.5em;
        }
        .subtext {
            text-align: center;
            font-size: 1.1em;
            color: #555;
            margin-bottom: 2em;
        }
        .contact-box {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 1.5em;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="contact-header">📞 Get in Touch</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtext">We’re here to help! Reach out with questions, feedback, or support needs.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="contact-box">
            <h4>📧 <u>Email Support</u></h4>
            <ul>
                <li><strong>General Inquiries:</strong><br><a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a></li>
                <li><strong>Technical Issues:</strong><br><a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a></li>
            </ul>
            <p>⏱️ <strong>Response Time:</strong> Within 24 hours</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="contact-box">
            <h4>🕐 <u>Support Hours</u></h4>
            <ul>
                <li><strong>Monday - Friday:</strong> 9:00 AM – 6:00 PM (IST)</li>
                <li><strong>Saturday:</strong> 10:00 AM – 4:00 PM (IST)</li>
                <li><strong>Sunday:</strong> <span style="color: red;"><strong>Closed</strong></span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
