import streamlit as st

def show_contact_page():
    # CSS Styles
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;900&display=swap');

    /* Global Styles */
    * {
        font-family: 'Poppins', sans-serif;
    }

    /* Prevent long links/emails from overflowing */
    .contact-info a {
        display: inline-block;
        max-width: 100%;
        word-break: break-all;
        white-space: normal;
    }

    /* Animated Background */
    .contact-container {
        background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Main Header with Glow Effect */
    .mega-header {
        text-align: center;
        font-size: 3.5em;
        font-weight: 900;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientText 3s ease infinite, bounceIn 1s ease;
        margin-bottom: 0.5em;
        text-shadow: 0 0 30px rgba(255,255,255,0.5);
    }
    @keyframes gradientText {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    @keyframes bounceIn {
        0% { transform: scale(0.3) rotate(-10deg); opacity: 0; }
        50% { transform: scale(1.05) rotate(2deg); }
        70% { transform: scale(0.9) rotate(-1deg); }
        100% { transform: scale(1) rotate(0); opacity: 1; }
    }

    /* Subtitle with Typing Effect */
    .typewriter {
        text-align: center;
        font-size: 1.3em;
        color: #fff;
        margin-bottom: 2.5em;
        animation: fadeInUp 1.5s ease;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }

    /* Contact Card Styles */
    .contact-card {
        max-width: 400px;
        margin: 1em auto;
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 2em;
        box-shadow:
            0 8px 32px rgba(0,0,0,0.1),
            inset 0 1px 0 rgba(255,255,255,0.2);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        overflow: hidden;
        animation: slideInFromBottom 1s ease forwards;
        transform: translateY(50px);
        opacity: 0;
        position: relative;
    }
    .contact-card:nth-child(1) { animation-delay: 0.2s; }
    .contact-card:nth-child(2) { animation-delay: 0.4s; }
    
    @keyframes slideInFromBottom {
        to { transform: translateY(0); opacity: 1; }
    }
    
    .contact-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s ease;
    }
    .contact-card:hover::before { left: 100%; }
    .contact-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow:
            0 20px 40px rgba(0,0,0,0.2),
            inset 0 1px 0 rgba(255,255,255,0.3);
    }

    /* Card Headers */
    .card-header {
        font-size: 1.8em;
        font-weight: 700;
        color: #fff;
        margin-bottom: 1em;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        position: relative;
    }
    .card-header::after {
        content: '';
        position: absolute;
        bottom: -5px; left: 0;
        width: 0; height: 3px;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        border-radius: 2px;
        transition: width 0.3s ease;
    }
    .contact-card:hover .card-header::after { width: 100%; }

    /* Contact Info */
    .contact-info {
        color: #fff;
        font-size: 1.1em;
        line-height: 1.8;
        text-shadow: 0 1px 5px rgba(0,0,0,0.3);
    }
    .contact-info strong { color: #ffeb3b; font-weight: 600; }
    .contact-info a { 
        text-decoration: none; 
        transition: all 0.3s ease;
        color: #4ecdc4;
    }
    .contact-info a:hover {
        color: #fff;
        text-shadow: 0 0 10px #4ecdc4;
        transform: scale(1.05);
    }

    /* Support Hours List */
    .support-list {
        list-style: none; 
        padding: 0;
        margin: 0;
    }
    .support-list li {
        background: rgba(255,255,255,0.1);
        margin: 0.5em 0;
        padding: 0.8em 1.2em;
        border-radius: 10px;
        border-left: 4px solid #4ecdc4;
        transition: all 0.3s ease;
        animation: slideInRight 0.8s ease forwards;
        transform: translateX(50px);
        opacity: 0;
    }
    .support-list li:nth-child(1) { animation-delay: 0.6s; }
    .support-list li:nth-child(2) { animation-delay: 0.8s; }
    .support-list li:nth-child(3) { animation-delay: 1s; }
    @keyframes slideInRight {
        to { transform: translateX(0); opacity: 1; }
    }
    .support-list li:hover {
        background: rgba(255,255,255,0.2);
        transform: translateX(5px);
        border-left-color: #ff6b6b;
    }

    /* Buttons */
    .contact-button {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        color: white !important;
        font-weight: 600;
        font-size: 1.1em;
        cursor: pointer;
        text-decoration: none !important;
        display: inline-block;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        animation: glow 2s ease-in-out infinite alternate;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    @keyframes glow {
        from { box-shadow: 0 4px 15px rgba(78,205,196,0.3); }
        to   { box-shadow: 0 6px 25px rgba(78,205,196,0.6); }
    }
    .contact-button:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 25px rgba(78,205,196,0.4);
        color: white !important;
        text-decoration: none !important;
    }

    /* Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .mega-header { font-size: 2.5em; }
        .contact-card { padding: 1.5em; }
        .typewriter { font-size: 1.1em; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Top Animated Header
    st.markdown("""
    <div class="contact-container">
        <div class="mega-header">📞 Get in Touch</div>
        <div class="typewriter">We're here to help! Reach out with questions, feedback, or support needs.</div>
    </div>
    """, unsafe_allow_html=True)

    # Two columns for email/support-hours cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="contact-card">
            <div class="card-header">📧 Email Support</div>
            <div class="contact-info">
                <p>📬 <strong>General Inquiries:</strong><br>
                   <a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a>
                </p>
                <p>🛠️ <strong>Technical Issues:</strong><br>
                   <a href="mailto:riaskingofanime@gmail.com">riaskingofanime@gmail.com</a>
                </p>
                <p>⏱️ <strong>Response Time:</strong> Within 24 hours</p>
                <a href="mailto:riaskingofanime@gmail.com" class="contact-button">Send Email Now ✉️</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="contact-card">
            <div class="card-header">🕐 Support Hours</div>
            <div class="contact-info">
                <ul class="support-list">
                    <li><strong>Monday – Friday:</strong> 9:00 AM – 6:00 PM (IST)</li>
                    <li><strong>Saturday:</strong> 10:00 AM – 4:00 PM (IST)</li>
                    <li><strong>Sunday:</strong> <span style="color:#ff6b6b;"><strong>Closed</strong></span></li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Quick Actions section
    st.markdown("""
    <div class="contact-container" style="margin-top:2rem;">
        <div class="mega-header" style="font-size:2em;">✨ Quick Actions</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="text-align:center;">
            <a href="mailto:riaskingofanime@gmail.com?subject=General Inquiry" class="contact-button">💬 General Support</a>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="text-align:center;">
            <a href="mailto:riaskingofanime@gmail.com?subject=Technical Issue" class="contact-button">🔧 Technical Help</a>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="text-align:center;">
            <a href="mailto:riaskingofanime@gmail.com?subject=Feedback" class="contact-button">⭐ Send Feedback</a>
        </div>
        """, unsafe_allow_html=True)
