import streamlit as st

def show_contact_page():
    st.markdown(
        """
        <style>
        /* Animated Headers */
        .contact-header {
            text-align: center;
            font-size: 2.5em;
            font-weight: 900;
            color: #154360;
            margin-bottom: 0.4em;
            animation: fadeInDown 1s ease-in-out;
        }

        .subtext {
            text-align: center;
            font-size: 1.15em;
            color: #444;
            margin-bottom: 2em;
            animation: fadeInUp 1.2s ease-in-out;
        }

        /* Boxes */
        .contact-box {
            background: linear-gradient(to top left, #e6f0ff, #ffffff);
            border: 1px solid #a8cbee;
            border-radius: 14px;
            padding: 1.6em;
            box-shadow: 0 8px 16px rgba(0,0,0,0.07);
            transition: 0.3s ease-in-out;
            animation: fadeIn 1.2s ease;
        }

        .contact-box:hover {
            transform: scale(1.015);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }

        .pulse-email {
            display: inline-block;
            animation: pulse 2s infinite;
        }

        /* Animations */
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(15px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInDown {
            0% { opacity: 0; transform: translateY(-20px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Header Section
    st.markdown('<div class="contact-header">📞 Get in Touch</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtext">We’re here to help! Reach out with questions, feedback, or support needs.</div>', unsafe_allow_html=True)

    # Two Columns
    col1, col2 = st.columns(2)

    # Column 1: Email Support
    with col1:
        st.markdown("""
        <div class="contact-box">
            <h4>📧 <u>Email Support</u></h4>
            <p><span class="pulse-email">📬</span> <strong>General Inquiries:</strong><br>
            <a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a></p>

            <p><span class="pulse-email">🛠️</span> <strong>Technical Issues:</strong><br>
            <a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a></p>

            <p>⏱️ <strong>Response Time:</strong> Within 24 hours</p>
        </div>
        """, unsafe_allow_html=True)

    # Column 2: Support Hours
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
