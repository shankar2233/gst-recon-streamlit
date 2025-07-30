import streamlit as st

def show_contact_page():
    st.markdown(
        """
        <style>
        /* Page Header */
        .contact-header {
            text-align: center;
            font-size: 2.7em;
            font-weight: 800;
            color: #1F618D;
            margin-bottom: 0.2em;
            animation: fadeInDown 1s ease-in-out;
        }

        .subtext {
            text-align: center;
            font-size: 1.2em;
            color: #555;
            margin-bottom: 2em;
            animation: fadeInUp 1.2s ease-in-out;
        }

        /* Boxes */
        .contact-box {
            background: linear-gradient(135deg, #f0faff, #ffffff);
            border: 1px solid #cce0ff;
            border-radius: 16px;
            padding: 1.8em;
            box-shadow: 0 8px 20px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            animation: fadeIn 1s ease-in;
        }

        .contact-box:hover {
            transform: translateY(-6px);
            box-shadow: 0 12px 30px rgba(0,0,0,0.15);
        }

        .contact-box h4 {
            margin-bottom: 1em;
        }

        /* Email pulse effect */
        .pulse-email {
            display: inline-block;
            animation: pulse 2s infinite;
        }

        /* Animations */
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInDown {
            0% { opacity: 0; transform: translateY(-30px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
            0% { opacity: 0; transform: translateY(30px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
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
            <p><span class="pulse-email">📬</span> <strong>General Inquiries:</strong><br>
            <a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a></p>
            
            <p><span class="pulse-email">🛠️</span> <strong>Technical Issues:</strong><br>
            <a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a></p>

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
