import streamlit as st

def show_privacy_policy():
    st.set_page_config(page_title="Privacy Policy", layout="centered")
    
    st.title("🔒 Privacy Policy")
    st.markdown("**Last Updated: July 30, 2025**")

    st.markdown("---")

    st.markdown("### 🔍 Key Privacy Highlights")
    st.markdown("""
- ✅ **No Data Storage** – Files are processed directly on your device.
- ✅ **No Server Uploads** – Your GST data stays 100% private.
- ✅ **No Account or Login Required** – You can use the tool completely anonymously.
- ✅ **Secure Processing** – Everything happens locally in your browser using secure methods.
    """)

    st.markdown("### 📬 Contact Information")
    st.markdown("""
If you have any questions or concerns about this Privacy Policy, feel free to reach out:

📧 **Email:** [riasanimeking@gmail.com](mailto:riasanimeking@gmail.com)
    """)

    st.markdown("---")
    st.caption("This privacy policy applies only to the GST Reconciliation Tool on gstreconciliation.co.in.")
