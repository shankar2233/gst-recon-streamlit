import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from io import BytesIO
import openpyxl

st.set_page_config(page_title="GST Reconciliation Tool", layout="wide")
st.title("🧾 GST Reconciliation Software (Tally vs GSTR-2A)")

# --- File Upload ---
tally_file = st.file_uploader("Upload Tally Excel File", type=["xlsx"])
gstr2a_file = st.file_uploader("Upload GSTR-2A Excel File", type=["xlsx"])
match_threshold = st.slider("Fuzzy Match Threshold (0–100)", min_value=0, max_value=100, value=90)

if tally_file and gstr2a_file:
    with st.spinner("Reading Excel files..."):
        df_tally = pd.read_excel(tally_file, sheet_name="Tally")
        df_gstr2a = pd.read_excel(gstr2a_file, sheet_name="GSTR-2A")

    st.success("Files loaded successfully!")

    # --- Fuzzy Matching ---
    matched_rows = []
    for idx, row in df_tally.iterrows():
        party = row['Party Name']
        match = None
        score = 0
        for _, row2 in df_gstr2a.iterrows():
            score_check = fuzz.token_sort_ratio(party, row2['Party Name'])
            if score_check > score:
                score = score_check
                match = row2['Party Name']
        matched_rows.append((party, match, score))

    matched_df = pd.DataFrame(matched_rows, columns=["Tally Party", "GSTR-2A Match", "Score"])
    matched_df['Match'] = matched_df['Score'] >= match_threshold

    st.subheader("🔍 Matched Results")
    st.dataframe(matched_df, use_container_width=True)

    # --- Download Excel ---
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Matches")
        return output.getvalue()

    excel_data = to_excel(matched_df)
    st.download_button(
        label="📥 Download Matched Excel",
        data=excel_data,
        file_name="gst_reconciliation_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
