import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz, process
from datetime import datetime
import io
import time
from io import BytesIO

# Initialize session state for storing all processed sheets
if 'all_sheets' not in st.session_state:
    st.session_state.all_sheets = {}
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

# --- Enhanced CSS with Modern Design and Smooth Transitions ---
def apply_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-blue: #4A90E2;
        --soft-green: #7ED321;
        --warm-gray: #F5F5F7;
        --accent-purple: #BD10E0;
        --text-dark: #2C3E50;
        --success-green: #27AE60;
        --warning-orange: #F39C12;
        --light-blue: #E3F2FD;
        --soft-shadow: rgba(74, 144, 226, 0.1);
    }

    .main .block-container {
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease-in-out;
        animation: fadeIn 0.5s ease-in;
        padding-top: 2rem;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideLeft {
        from { transform: translateX(50px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    .main-header {
        background: linear-gradient(135deg, var(--primary-blue), var(--accent-purple));
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        animation: slideLeft 0.6s ease-out;
        box-shadow: 0 10px 40px var(--soft-shadow);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }

    .step-container {
        background: linear-gradient(135deg, var(--primary-blue), var(--accent-purple));
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        animation: slideLeft 0.6s ease-out;
        box-shadow: 0 8px 32px rgba(74, 144, 226, 0.2);
        color: white;
    }

    .step-progress {
        background: rgba(255,255,255,0.3);
        height: 8px;
        border-radius: 4px;
        margin-top: 10px;
        overflow: hidden;
    }

    .step-progress-fill {
        background: white;
        height: 100%;
        border-radius: 4px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 0 10px rgba(255,255,255,0.5);
    }

    .stButton > button {
        background: linear-gradient(45deg, var(--primary-blue), var(--soft-green));
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
        position: relative;
        overflow: hidden;
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(74, 144, 226, 0.4);
        animation: pulse 0.6s ease-in-out;
    }

    .stButton > button:active {
        transform: translateY(-1px);
    }

    .download-button {
        background: linear-gradient(45deg, var(--success-green), var(--soft-green)) !important;
    }

    .download-button:hover {
        background: linear-gradient(45deg, #229954, var(--soft-green)) !important;
    }

    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        transition: all 0.3s ease;
        border: 1px solid rgba(74, 144, 226, 0.1);
        box-shadow: 0 5px 20px var(--soft-shadow);
        position: relative;
        overflow: hidden;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(74, 144, 226, 0.15);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: var(--warm-gray);
        border-radius: 15px;
        padding: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, var(--primary-blue), var(--accent-purple));
        color: white;
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, var(--soft-green), var(--primary-blue));
        border-radius: 10px;
        height: 12px;
        transition: all 0.3s ease;
    }

    .success-message {
        background: linear-gradient(45deg, var(--success-green), var(--soft-green));
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        margin: 10px 0;
        animation: slideLeft 0.5s ease-out;
        box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
    }

    .info-message {
        background: linear-gradient(45deg, var(--primary-blue), var(--light-blue));
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        margin: 10px 0;
        animation: slideLeft 0.5s ease-out;
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
    }

    .error-message {
        background: linear-gradient(45deg, #E74C3C, var(--warning-orange));
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        margin: 10px 0;
        animation: slideLeft 0.5s ease-out;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
    }

    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 5px 20px var(--soft-shadow);
    }

    .stFileUploader {
        border: 2px dashed var(--primary-blue);
        border-radius: 15px;
        padding: 20px;
        transition: all 0.3s ease;
    }

    .stFileUploader:hover {
        border-color: var(--soft-green);
        background: rgba(74, 144, 226, 0.05);
    }

    .stMetric {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 3px 15px var(--soft-shadow);
        transition: transform 0.3s ease;
    }

    .stMetric:hover {
        transform: translateY(-2px);
    }

    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
    }

    .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid var(--warm-gray);
        border-top: 4px solid var(--primary-blue);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .sheet-preview-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid rgba(74, 144, 226, 0.1);
        box-shadow: 0 5px 20px var(--soft-shadow);
        transition: all 0.3s ease;
    }

    .sheet-preview-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(74, 144, 226, 0.15);
    }

    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .metric-card {
            padding: 15px;
        }
        
        .stButton > button {
            padding: 10px 20px;
            font-size: 14px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Enhanced message display functions
def show_success_message(message):
    st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)

def show_info_message(message):
    st.markdown(f'<div class="info-message">ℹ️ {message}</div>', unsafe_allow_html=True)

def show_error_message(message):
    st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)

# Progress bar and status text for animation
def create_animated_progress_bar():
    progress_bar = st.progress(0)
    status_text = st.empty()
    return progress_bar, status_text

# Utility functions for columns and data cleaning
def get_column(df, colname):
    for col in df.columns:
        col_str = str(col).strip().lower()
        colname_str = str(colname).strip().lower()
        if col_str == colname_str:
            return col
    raise KeyError(f"Column '{colname}' not found. Available columns: {df.columns.tolist()}")

def get_raw_unique_names(series):
    return pd.Series(series).dropna().drop_duplicates().tolist()

def fix_tally_columns(df_tally):
    expected_cols = ['GSTIN of supplier', 'Supplier', 'Invoice number', 'Invoice Date', 'Invoice Value', 'Rate', 'Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT tax', 'Cess']
    if (len(df_tally.columns) >= 2 and str(df_tally.columns[0]).startswith('Unnamed') and not any(col.lower().strip() == 'supplier' for col in df_tally.columns)):
        new_columns = []
        for i, col in enumerate(df_tally.columns):
            if i < len(expected_cols):
                new_columns.append(expected_cols[i])
            else:
                new_columns.append(f"Column_{i}")
        df_tally.columns = new_columns
    return df_tally

def create_default_format():
    tally_data = {
        'GSTIN of supplier': ['27AABCU9603R1ZX', '27AABCU9603R1ZY', ''],
        'Supplier': ['ABC Private Ltd', 'XYZ Industries', 'GHI Enterprises'],
        'Invoice number': ['INV-0001', 'INV-0002', 'INV-0003'],
        'Invoice Date': ['15-04-2024', '20-04-2024', '25-04-2024'],
        'Invoice Value': [118000, 177000, 112000],
        'Rate': [18, 18, 12],
        'Taxable Value': [100000, 150000, 100000],
        'Integrated Tax': [0, 27000, 0],
        'Central Tax': [9000, 0, 6000],
        'State/UT tax': [9000, 0, 6000],
        'Cess': [0, 0, 0]
    }
    gstr_data = {
        'GSTIN of supplier': ['27AABCU9603R1ZX', '27AABCU9603R1ZZ', ''],
        'Supplier': ['ABC Private Limited', 'DEF Corporation', 'GHI Enterprises'],
        'Invoice number': ['INV-0001', 'INV-0004', 'INV-0003'],
        'Invoice Date': ['15-04-2024', '25-04-2024', '25-04-2024'],
        'Invoice Value': [118000, 89600, 112000],
        'Rate': [18, 12, 12],
        'Taxable Value': [100000, 80000, 100000],
        'Integrated Tax': [0, 0, 0],
        'Central Tax': [9000, 4800, 6000],
        'State/UT tax': [9000, 4800, 6000],
        'Cess': [0, 0, 0]
    }
    df_tally = pd.DataFrame(tally_data)
    df_gstr = pd.DataFrame(gstr_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        empty_row = pd.DataFrame([[''] * len(df_tally.columns)], columns=df_tally.columns)
        empty_row.to_excel(writer, sheet_name='Tally', index=False, header=False)
        df_tally.to_excel(writer, sheet_name='Tally', index=False, startrow=1)
        empty_row_gstr = pd.DataFrame([[''] * len(df_gstr.columns)], columns=df_gstr.columns)
        empty_row_gstr.to_excel(writer, sheet_name='GSTR-2A', index=False, header=False)
        df_gstr.to_excel(writer, sheet_name='GSTR-2A', index=False, startrow=1)
    output.seek(0)
    return output.getvalue()

def show_help_instructions():
    st.markdown("""
    <div class="metric-card">
        <h3>📋 Instructions for File Upload</h3>
        <ol>
            <li><strong>File Format:</strong> Upload Excel files (.xlsx) with sheets named 'Tally' and 'GSTR-2A'.</li>
            <li><strong>Required Columns:</strong> GSTIN of supplier, Supplier, Invoice number, Invoice Date, Invoice Value, Rate, Taxable Value, Integrated Tax, Central Tax, State/UT tax, Cess</li>
            <li><strong>Data Format:</strong> Ensure dates are in DD-MM-YYYY format and amounts are numeric.</li>
            <li><strong>Note:</strong> Both sheets must exist in the same Excel file.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# Fuzzy matching logic
def two_way_match(tally_list, gstr_list, threshold):
    match_map, used_tally, used_gstr = {}, set(), set()
    tally_upper = {name.upper(): name for name in tally_list}
    gstr_upper = {name.upper(): name for name in gstr_list}
    tally_keys, gstr_keys = list(tally_upper.keys()), list(gstr_upper.keys())
    total_steps = len(gstr_keys) + len(tally_keys)
    progress_bar, status_text = create_animated_progress_bar()
    # GSTR to Tally matching
    for i, gstr_name in enumerate(gstr_keys):
        best_match, score = process.extractOne(gstr_name, tally_keys, scorer=fuzz.ratio)
        gstr_real = gstr_upper[gstr_name]
        if best_match and score >= threshold and best_match not in used_tally:
            tally_real = tally_upper[best_match]
            match_map[(gstr_real, tally_real)] = (gstr_real, tally_real, score)
            used_gstr.add(gstr_name)
            used_tally.add(best_match)
        else:
            match_map[(gstr_real, '')] = (gstr_real, '', 0)
            used_gstr.add(gstr_name)
        progress = (i + 1) / total_steps
        progress_bar.progress(progress)
        status_text.markdown(f'<div class="info-message">🔍 Matching GSTR entries... {i+1}/{len(gstr_keys)}</div>', unsafe_allow_html=True)
        time.sleep(0.005)
    # Tally to GSTR matching
    for i, tally_name in enumerate(tally_keys):
        if tally_name in used_tally:
            continue
        best_match, score = process.extractOne(tally_name, gstr_keys, scorer=fuzz.ratio)
        tally_real = tally_upper[tally_name]
        if best_match and score >= threshold and best_match not in used_gstr:
            gstr_real = gstr_upper[best_match]
            match_map[(gstr_real, tally_real)] = (gstr_real, tally_real, score)
            used_tally.add(tally_name)
            used_gstr.add(best_match)
        else:
            match_map[('', tally_real)] = ('', tally_real, 0)
            used_tally.add(tally_name)
        progress = (len(gstr_keys) + i + 1) / total_steps
        progress_bar.progress(progress)
        status_text.markdown(f'<div class="info-message">🔍 Matching Tally entries... {i+1}/{len(tally_keys)}</div>', unsafe_allow_html=True)
        time.sleep(0.005)
    progress_bar.progress(1.0)
    status_text.markdown('<div class="success-message">✅ Matching completed successfully!</div>', unsafe_allow_html=True)
    time.sleep(1)
    progress_bar.empty()
    status_text.empty()
    results = []
    for gstr_name, tally_name, score in match_map.values():
        confirm = "Yes" if gstr_name and tally_name and score >= 80 else "No"
        results.append([gstr_name, tally_name, score, confirm])
    return results

# Store dataframes in session state
def store_sheet_data(sheet_name, dataframe, step_name):
    if 'all_sheets' not in st.session_state:
        st.session_state.all_sheets = {}
    key = f"{step_name}_{sheet_name}"
    st.session_state.all_sheets[key] = {
        'dataframe': dataframe.copy(),
        'sheet_name': sheet_name,
        'step': step_name,
        'timestamp': datetime.now()
    }

def create_full_download_excel():
    if not st.session_state.all_sheets:
        return None
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for key, sheet_data in st.session_state.all_sheets.items():
            final_sheet_name = f"{sheet_data['step']}_{sheet_data['sheet_name']}"
            if len(final_sheet_name) > 31:
                final_sheet_name = final_sheet_name[:31]
            sheet_data['dataframe'].to_excel(writer, sheet_name=final_sheet_name, index=False)
    output.seek(0)
    return output.getvalue()

def create_detailed_reconciliation_report(df_tally, df_gstr, match_df):
    report_data = []
    for _, row in match_df.iterrows():
        gstr_supplier = row['GSTR Supplier']
        tally_supplier = row['Tally Supplier']
        if gstr_supplier and tally_supplier:
            gstr_invoices = df_gstr[df_gstr['Supplier'].str.contains(gstr_supplier, case=False, na=False)]
            tally_invoices = df_tally[df_tally['Supplier'].str.contains(tally_supplier, case=False, na=False)]
            gstr_total = gstr_invoices['Invoice Value'].sum() if not gstr_invoices.empty else 0
            tally_total = tally_invoices['Invoice Value'].sum() if not tally_invoices.empty else 0
            difference = gstr_total - tally_total
            report_data.append({
                'GSTR Supplier': gstr_supplier,
                'Tally Supplier': tally_supplier,
                'GSTR Invoice Count': len(gstr_invoices),
                'Tally Invoice Count': len(tally_invoices),
                'GSTR Total Value': gstr_total,
                'Tally Total Value': tally_total,
                'Difference': difference,
                'Match Quality': row['Match Score'],
                'Status': 'Matched' if row['Confirm'] == 'Yes' else 'Manual Review Required'
            })
    return pd.DataFrame(report_data)

def create_summary_statistics(df_tally, df_gstr, match_df):
    total_gstr_suppliers = len(df_gstr['Supplier'].dropna().unique())
    total_tally_suppliers = len(df_tally['Supplier'].dropna().unique())
    matched_suppliers = len(match_df[match_df['Confirm'] == 'Yes'])
    gstr_total_value = df_gstr['Invoice Value'].sum()
    tally_total_value = df_tally['Invoice Value'].sum()
    summary_data = {
        'Metric': [
            'Total GSTR Suppliers',
            'Total Tally Suppliers', 
            'Matched Suppliers',
            'Match Percentage',
            'GSTR Total Value',
            'Tally Total Value',
            'Value Difference',
            'Total GSTR Invoices',
            'Total Tally Invoices'
        ],
        'Value': [
            total_gstr_suppliers,
            total_tally_suppliers,
            matched_suppliers,
            f"{(matched_suppliers/max(total_gstr_suppliers, 1))*100:.1f}%",
            f"₹{gstr_total_value:,.0f}",
            f"₹{tally_total_value:,.0f}",
            f"₹{gstr_total_value - tally_total_value:,.0f}",
            len(df_gstr),
            len(df_tally)
        ]
    }
    return pd.DataFrame(summary_data)

def perform_reconciliation(df_tally, df_gstr, threshold):
    store_sheet_data("Tally_Original", df_tally, "Data_Upload")
    store_sheet_data("GSTR_Original", df_gstr, "Data_Upload")
    st.session_state.current_step = 3
    show_step_indicator(3, 4)
    show_info_message("Starting reconciliation process...")
    try:
        tally_supplier_col = get_column(df_tally, 'supplier')
        gstr_supplier_col = get_column(df_gstr, 'supplier')
        tally_suppliers = get_raw_unique_names(df_tally[tally_supplier_col])
        gstr_suppliers = get_raw_unique_names(df_gstr[gstr_supplier_col])
        matches = two_way_match(tally_suppliers, gstr_suppliers, threshold)
        match_df = pd.DataFrame(matches, columns=['GSTR Supplier', 'Tally Supplier', 'Match Score', 'Confirm'])
        store_sheet_data("Supplier_Matches", match_df, "Reconciliation")
        show_success_message(f"Reconciliation completed! Found {len(matches)} supplier matches.")
        detailed_report = create_detailed_reconciliation_report(df_tally, df_gstr, match_df)
        store_sheet_data("Detailed_Report", detailed_report, "Reconciliation")
        summary_stats = create_summary_statistics(df_tally, df_gstr, match_df)
        store_sheet_data("Summary_Statistics", summary_stats, "Reconciliation")
        st.session_state.current_step = 4
        show_step_indicator(4, 4)
        return match_df, detailed_report, summary_stats
    except Exception as e:
        show_error_message(f"Error during reconciliation: {str(e)}")
        return None, None, None

def show_step_indicator(current_step, total_steps):
    step_names = ["Upload Files", "Process Data", "Reconciliation", "Download Results"]
    progress_percentage = (current_step / total_steps) * 100
    st.markdown(f"""
    <div class="step-container">
        <h3 style="margin: 0; font-size: 1.5rem;">Step {current_step} of {total_steps}: {step_names[current_step-1] if current_step <= len(step_names) else "Complete"}</h3>
        <div class="step-progress">
            <div class="step-progress-fill" style="width: {progress_percentage}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_all_sheets_with_downloads():
    if not st.session_state.all_sheets:
        show_info_message("No processed sheets available yet. Complete the reconciliation process first.")
        return
    sheet_keys = list(st.session_state.all_sheets.keys())
    if len(sheet_keys) > 1:
        tab_names = [f"📊 {key.replace('_', ' ')}" for key in sheet_keys]
        tabs = st.tabs(tab_names)
    else:
        tabs = [st.container()]
    for i, (sheet_key, sheet_data) in enumerate(st.session_state.all_sheets.items()):
        with tabs[i] if len(sheet_keys) > 1 else tabs[0]:
            st.markdown(f'<div class="sheet-preview-card"><h3>📋 {sheet_data["step"]} - {sheet_data["sheet_name"]}</h3></div>', unsafe_allow_html=True)
            df = sheet_data['dataframe']
            st.dataframe(df, use_container_width=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Rows", len(df))
            with col2:
                st.metric("📈 Columns", len(df.columns))
            with col3:
                if 'Invoice Value' in df.columns:
                    total_value = df['Invoice Value'].sum()
                    st.metric("💰 Total Value", f"₹{total_value:,.0f}")
                else:
                    st.metric("💰 Total Value", "N/A")
            with col4:
                st.metric("🕒 Last Updated", sheet_data['timestamp'].strftime("%H:%M:%S"))
            col1, col2 = st.columns(2)
            with col1:
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=sheet_data['sheet_name'], index=False)
                excel_buffer.seek(0)
                st.download_button(
                    label=f"📥 Download {sheet_data['sheet_name']} as Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"{sheet_data['step']}_{sheet_data['sheet_name']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"excel_{sheet_key}"
                )
            with col2:
                csv_buffer = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📄 Download {sheet_data['sheet_name']} as CSV",
                    data=csv_buffer,
                    file_name=f"{sheet_data['step']}_{sheet_data['sheet_name']}.csv",
                    mime="text/csv",
                    key=f"csv_{sheet_key}"
                )

def show_download_section():
    st.markdown("### 📁 Download Options")
    if st.session_state.all_sheets:
        col1, col2, col3 = st.columns(3)
        with col1:
            full_excel = create_full_download_excel()
            if full_excel:
                st.download_button(
                    label="📦 Download Complete Report",
                    data=full_excel,
                    file_name=f"GSTR_Reconciliation_Full_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Downloads Excel file with all processed sheets from all steps"
                )
        with col2:
            total_sheets = len(st.session_state.all_sheets)
            st.metric("📊 Total Sheets", total_sheets)
        with col3:
            if st.button("🗑️ Clear All Data", help="Remove all processed data and start fresh"):
                st.session_state.all_sheets = {}
                st.session_state.current_step = 1
                show_success_message("All data cleared successfully!")
                st.experimental_rerun()
    st.markdown("---")
    display_all_sheets_with_downloads()

def main():
    apply_custom_css()
    st.set_page_config(
        page_title="GSTR vs Tally Reconciliation",
        page_icon="📊",
        layout="wide"
    )

    st.markdown("""
    <div class="main-header">
        <h1>📊 GSTR vs Tally Reconciliation Tool</h1>
        <p>Advanced reconciliation system with fuzzy matching and comprehensive reporting</p>
    </div>
    """, unsafe_allow_html=True)

    current_step = st.session_state.get('current_step', 1)
    show_step_indicator(current_step, 4)

    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        threshold = st.slider(
            "🎯 Matching Threshold",
            min_value=50,
            max_value=100,
            value=75,
            help="Higher values require more exact matches"
        )
        st.markdown("---")
        st.markdown("### 📄 Sample Format")
        sample_data = create_default_format()
        st.download_button(
            label="📥 Download Sample Excel",
            data=sample_data,
            file_name="GSTR_Tally_Sample_Format.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown("---")
        with st.expander("❓ Help & Instructions"):
            show_help_instructions()

    tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "🔍 Reconciliation Results", "📊 Analytics"])

    with tab1:
        st.markdown("### 📤 File Upload Section")
        # Single file uploader for both sheets
        uploaded_file = st.file_uploader("Upload Excel file with 'Tally' and 'GSTR-2A' sheets", type=['xlsx'])
        if uploaded_file is not None:
            try:
                with st.spinner("📊 Loading Tally and GSTR-2A data..."):
                    df_tally = pd.read_excel(uploaded_file, sheet_name='Tally', header=1)
                    df_tally = fix_tally_columns(df_tally)
                    df_gstr = pd.read_excel(uploaded_file, sheet_name='GSTR-2A', header=1)
                st.session_state.current_step = 2
                show_step_indicator(2, 4)
                show_success_message("Files loaded successfully!")
                st.markdown("### 👀 Data Preview")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Tally Data Preview")
                    st.dataframe(df_tally.head(), use_container_width=True)
                    st.metric("📊 Total Tally Records", len(df_tally))
                with col2:
                    st.markdown("#### GSTR-2A Data Preview")
                    st.dataframe(df_gstr.head(), use_container_width=True)
                    st.metric("📋 Total GSTR Records", len(df_gstr))
                if st.button("🚀 Start Reconciliation Process", type="primary"):
                    match_df, detailed_report, summary_stats = perform_reconciliation(df_tally, df_gstr, threshold)
                    if match_df is not None:
                        st.session_state.reconciliation_complete = True
                        st.experimental_rerun()
            except Exception as e:
                show_error_message(f"Error processing file: {str(e)}")
                st.session_state.current_step = 1

    with tab2:
        st.markdown("### 🔍 Reconciliation Results")
        if st.session_state.all_sheets:
            match_sheets = [key for key in st.session_state.all_sheets.keys() if 'Supplier_Matches' in key]
            if match_sheets:
                latest_match = st.session_state.all_sheets[match_sheets[-1]]['dataframe']
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_matches = len(latest_match)
                    st.metric("🔍 Total Comparisons", total_matches)
                with col2:
                    confirmed_matches = len(latest_match[latest_match['Confirm'] == 'Yes'])
                    st.metric("✅ Confirmed Matches", confirmed_matches)
                with col3:
                    match_rate = (confirmed_matches / total_matches) * 100 if total_matches > 0 else 0
                    st.metric("📈 Match Rate", f"{match_rate:.1f}%")
                with col4:
                    avg_score = latest_match['Match Score'].mean()
                    st.metric("⭐ Avg Match Score", f"{avg_score:.1f}")
                st.markdown("#### 📋 Supplier Matching Results")
                st.dataframe(latest_match, use_container_width=True)
            else:
                show_info_message("No reconciliation results available. Please upload file and run reconciliation.")
        else:
            show_info_message("No data available. Please upload file and run reconciliation.")

    with tab3:
        st.markdown("### 📊 Analytics Dashboard")
        if st.session_state.all_sheets:
            summary_sheets = [key for key in st.session_state.all_sheets.keys() if 'Summary_Statistics' in key]
            if summary_sheets:
                summary_data = st.session_state.all_sheets[summary_sheets[-1]]['dataframe']
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 📈 Key Metrics")
                    for _, row in summary_data.iterrows():
                        st.metric(row['Metric'], row['Value'])
                with col2:
                    st.markdown("#### 📊 Data Summary")
                    st.dataframe(summary_data, use_container_width=True)
                detail_sheets = [key for key in st.session_state.all_sheets.keys() if 'Detailed_Report' in key]
                if detail_sheets:
                    detailed_data = st.session_state.all_sheets[detail_sheets[-1]]['dataframe']
                    st.markdown("#### 📋 Detailed Reconciliation Report")
                    st.dataframe(detailed_data, use_container_width=True)
            else:
                show_info_message("No analytics data available. Complete reconciliation to see analytics.")
        else:
            show_info_message("No data available for analytics. Please upload file and run reconciliation.")

    st.markdown("---")
    show_download_section()

if __name__ == "__main__":
    main()
