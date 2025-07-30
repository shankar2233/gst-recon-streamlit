import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
import time
import os
from datetime import datetime
import io
import tempfile

# --- Custom CSS for Rainbow Animation and Smooth Transitions ---
def apply_custom_css():
    st.markdown("""
    <style>
    /* Rainbow animated background */
    .stApp {
        background: linear-gradient(45deg, 
            #ff0000, #ff7300, #fffb00, #48ff00, 
            #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
        background-size: 400% 400%;
        animation: rainbow 8s ease infinite;
    }
    
    @keyframes rainbow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    /* Smooth element transitions */
    .element-container {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Smooth button animations */
    .stButton > button {
        transition: all 0.2s ease-in-out;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: none;
        border-radius: 8px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Smooth container transitions */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        margin-top: 2rem;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Remove large rotating animations */
    .stProgress > div > div {
        transition: width 0.3s ease-in-out;
    }
    
    /* Smooth message animations */
    .success-message, .info-message, .error-message {
        animation: fadeInUp 0.4s ease-out;
        transition: all 0.3s ease;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Animated title */
    .animated-title {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin: 2rem 0;
        background: linear-gradient(45deg, #1e3c72, #2a5298, #3b82f6, #8b5cf6);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: titleShine 3s ease-in-out infinite;
    }
    
    @keyframes titleShine {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(5px);
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.9);
        transform: translateY(-1px);
    }
    
    /* Metrics styling */
    .metric-container {
        background: rgba(255, 255, 255, 0.8);
        padding: 1rem;
        border-radius: 8px;
        backdrop-filter: blur(5px);
        transition: all 0.2s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Management ---
def initialize_session_state():
    """Initialize session state variables"""
    if 'all_steps_data' not in st.session_state:
        st.session_state.all_steps_data = {}
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

def store_step_data(step_name, dataframe):
    """Store each step's data in session state"""
    if dataframe is not None and not dataframe.empty:
        st.session_state.all_steps_data[step_name] = dataframe.copy()

# --- Complete Excel Download Function ---
def create_comprehensive_excel(all_data):
    """Create Excel with all executed steps"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Include all steps that were executed
        for step_name, data in all_data.items():
            if data is not None and not data.empty:
                data.to_excel(writer, sheet_name=step_name, index=False)
        
        # If no data, create empty sheet
        if not all_data:
            pd.DataFrame().to_excel(writer, sheet_name='No_Data', index=False)
    
    output.seek(0)
    return output.getvalue()

# --- Enhanced Message Functions ---
def show_success_message(message):
    st.markdown(f'''
    <div class="success-message" style="
        background: linear-gradient(90deg, #48bb78, #38a169);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
        animation: fadeInUp 0.4s ease-out;
    ">
        ✅ {message}
    </div>
    ''', unsafe_allow_html=True)

def show_info_message(message):
    st.markdown(f'''
    <div class="info-message" style="
        background: linear-gradient(90deg, #4299e1, #3182ce);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
        animation: fadeInUp 0.4s ease-out;
    ">
        ℹ️ {message}
    </div>
    ''', unsafe_allow_html=True)

def show_error_message(message):
    st.markdown(f'''
    <div class="error-message" style="
        background: linear-gradient(90deg, #f56565, #e53e3e);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
        animation: fadeInUp 0.4s ease-out;
    ">
        ❌ {message}
    </div>
    ''', unsafe_allow_html=True)

# --- Enhanced Progress Bar ---
def create_animated_progress_bar():
    progress_bar = st.progress(0)
    status_text = st.empty()
    return progress_bar, status_text

# --- All Sheets Display Function ---
def display_all_sheets_summary():
    """Display all generated sheets with individual download options"""
    st.markdown("## 📋 Generated Sheets Summary")
    
    if st.session_state.all_steps_data:
        # Create tabs for each sheet
        sheet_names = list(st.session_state.all_steps_data.keys())
        
        if len(sheet_names) > 1:
            tabs = st.tabs(sheet_names)
            
            for i, (sheet_name, data) in enumerate(st.session_state.all_steps_data.items()):
                with tabs[i]:
                    st.markdown(f"### {sheet_name}")
                    
                    # Display data preview
                    if data is not None and not data.empty:
                        st.dataframe(data, use_container_width=True)
                        
                        # Individual sheet download
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            data.to_excel(writer, sheet_name=sheet_name, index=False)
                        excel_buffer.seek(0)
                        
                        st.download_button(
                            label=f"📥 Download {sheet_name}",
                            data=excel_buffer.getvalue(),
                            file_name=f"{sheet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            key=f"download_{sheet_name}_{i}"
                        )
                        
                        # Show basic statistics in metric containers
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows", len(data))
                        with col2:
                            st.metric("Columns", len(data.columns))
                        with col3:
                            memory_kb = data.memory_usage(deep=True).sum() / 1024
                            st.metric("Memory Usage", f"{memory_kb:.1f} KB")
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("No data available for this sheet")
        else:
            # Single sheet display
            for sheet_name, data in st.session_state.all_steps_data.items():
                st.markdown(f"### {sheet_name}")
                if data is not None and not data.empty:
                    st.dataframe(data, use_container_width=True)
                    
                    # Individual download
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        data.to_excel(writer, sheet_name=sheet_name, index=False)
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label=f"📥 Download {sheet_name}",
                        data=excel_buffer.getvalue(),
                        file_name=f"{sheet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
    else:
        st.info("No sheets have been generated yet. Please complete the reconciliation process.")

# --- Utility Functions (keeping original functionality) ---
def get_column(df, colname):
    """FIXED: Handle integer column names properly"""
    for col in df.columns:
        col_str = str(col).strip().lower()
        colname_str = str(colname).strip().lower()
        if col_str == colname_str:
            return col
    raise KeyError(f"Column '{colname}' not found. Available columns: {df.columns.tolist()}")

def get_raw_unique_names(series):
    return pd.Series(series).dropna().drop_duplicates().tolist()

def fix_tally_columns(df_tally):
    """Fix Tally sheet column structure when headers are wrong"""
    expected_cols = [
        'GSTIN of supplier', 'Supplier', 'Invoice number', 
        'Invoice Date', 'Invoice Value', 'Rate', 'Taxable Value',
        'Integrated Tax', 'Central Tax', 'State/UT tax', 'Cess'
    ]
    
    if (len(df_tally.columns) >= 2 and 
        str(df_tally.columns[0]).startswith('Unnamed') and
        not any(col.lower().strip() == 'supplier' for col in df_tally.columns)):
        
        new_columns = []
        for i, col in enumerate(df_tally.columns):
            if i < len(expected_cols):
                new_columns.append(expected_cols[i])
            else:
                new_columns.append(f"Column_{i}")
        df_tally.columns = new_columns
    
    return df_tally

def create_default_format():
    """Create default Excel format for users"""
    # Sample data for Tally sheet
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
    
    # Sample data for GSTR-2A sheet
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
    
    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_tally.to_excel(writer, sheet_name='Tally', index=False)
        df_gstr.to_excel(writer, sheet_name='GSTR-2A', index=False)
    
    output.seek(0)
    return output.getvalue()

def show_help_instructions():
    """Enhanced help instructions with animations"""
    st.markdown("""
    <div style="
        background: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        animation: slideIn 0.5s ease-out;
    ">
        <h3>📚 How to Use This Tool</h3>
        <p><strong>Step 1:</strong> Upload your Excel files with Tally and GSTR-2A data</p>
        <p><strong>Step 2:</strong> The tool will automatically match suppliers using fuzzy logic</p>
        <p><strong>Step 3:</strong> Review and confirm matches</p>
        <p><strong>Step 4:</strong> Download comprehensive reconciliation report</p>
    </div>
    """, unsafe_allow_html=True)

# --- Enhanced Fuzzy Matching Logic ---
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
        status_text.markdown(f'''
        <div style="text-align: center; color: #2c3e50; font-weight: 500;">
            🔍 Matching GSTR suppliers... {i+1}/{len(gstr_keys)}
        </div>
        ''', unsafe_allow_html=True)
        time.sleep(0.01)
    
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
        status_text.markdown(f'''
        <div style="text-align: center; color: #2c3e50; font-weight: 500;">
            🔍 Matching Tally suppliers... {i+1}/{len([t for t in tally_keys if t not in used_tally])}
        </div>
        ''', unsafe_allow_html=True)
        time.sleep(0.01)
    
    # Complete progress
    progress_bar.progress(1.0)
    status_text.markdown('''
    <div style="text-align: center; color: #27ae60; font-weight: 600;">
        ✅ Matching Complete!
    </div>
    ''', unsafe_allow_html=True)
    time.sleep(1)
    progress_bar.empty()
    status_text.empty()
    
    results = []
    for gstr_name, tally_name, score in match_map.values():
        # Set default confirmation based on match quality
        if gstr_name and tally_name and score >= 80:
            confirm = "Yes"
        else:
            confirm = "No"
        results.append([gstr_name, tally_name, score, confirm])
    
    return results

# --- Enhanced Streamlit App ---
def main():
    # Initialize session state
    initialize_session_state()
    
    # Apply custom CSS first
    apply_custom_css()
    
    st.set_page_config(
        page_title="GSTR vs Tally Reconciliation",
        page_icon="📊",
        layout="wide"
    )
    
    # Animated title
    st.markdown('''
    <div class="animated-title">
        📊 GSTR vs Tally Reconciliation Tool
    </div>
    ''', unsafe_allow_html=True)
    
    # Sidebar for navigation
    with st.sidebar:
        st.markdown("## 🎯 Navigation")
        page = st.selectbox(
            "Choose Action:",
            ["📤 Upload & Process", "📋 View All Sheets", "📚 Help", "📥 Download Template"]
        )
    
    if page == "📤 Upload & Process":
        st.markdown("## 📤 Upload Your Files")
        
        # File upload section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Tally Data")
            tally_file = st.file_uploader(
                "Upload Tally Excel file",
                type=['xlsx', 'xls'],
                key="tally_upload"
            )
        
        with col2:
            st.markdown("### 📄 GSTR-2A Data")
            gstr_file = st.file_uploader(
                "Upload GSTR-2A Excel file",
                type=['xlsx', 'xls'],
                key="gstr_upload"
            )
        
        # Processing section
        if tally_file and gstr_file:
            st.markdown("## ⚙️ Processing Configuration")
            
            col1, col2 = st.columns(2)
            with col1:
                threshold = st.slider(
                    "🎯 Matching Threshold (%)",
                    min_value=50,
                    max_value=100,
                    value=75,
                    help="Higher values require more exact matches"
                )
            
            with col2:
                auto_confirm = st.checkbox(
                    "✅ Auto-confirm high-quality matches (≥80%)",
                    value=True
                )
            
            if st.button("🚀 Start Processing", type="primary"):
                try:
                    # Load and process files
                    show_info_message("Loading Excel files...")
                    
                    # Load Tally data
                    df_tally = pd.read_excel(tally_file, sheet_name=0)
                    df_tally = fix_tally_columns(df_tally)
                    store_step_data("Tally_Data", df_tally)
                    
                    # Load GSTR data
                    df_gstr = pd.read_excel(gstr_file, sheet_name=0)
                    store_step_data("GSTR_2A_Data", df_gstr)
                    
                    show_success_message("Files loaded successfully!")
                    
                    # Extract supplier names
                    show_info_message("Extracting supplier information...")
                    
                    try:
                        tally_supplier_col = get_column(df_tally, 'supplier')
                        gstr_supplier_col = get_column(df_gstr, 'supplier')
                        
                        tally_suppliers = get_raw_unique_names(df_tally[tally_supplier_col])
                        gstr_suppliers = get_raw_unique_names(df_gstr[gstr_supplier_col])
                        
                        show_success_message(f"Found {len(tally_suppliers)} Tally suppliers and {len(gstr_suppliers)} GSTR suppliers")
                        
                        # Perform matching
                        show_info_message("Starting intelligent supplier matching...")
                        matches = two_way_match(tally_suppliers, gstr_suppliers, threshold)
                        
                        # Create matching results dataframe
                        matching_df = pd.DataFrame(
                            matches,
                            columns=['GSTR_Supplier', 'Tally_Supplier', 'Match_Score', 'Confirmed']
                        )
                        store_step_data("Matching_Results", matching_df)
                        
                        # Create reconciliation summary
                        total_matches = len([m for m in matches if m[1] and m[0]])
                        high_confidence = len([m for m in matches if m[2] >= 80])
                        
                        summary_data = {
                            'Metric': [
                                'Total GSTR Suppliers',
                                'Total Tally Suppliers',
                                'Successful Matches',
                                'High Confidence Matches (≥80%)',
                                'Match Rate (%)'
                            ],
                            'Value': [
                                len(gstr_suppliers),
                                len(tally_suppliers),
                                total_matches,
                                high_confidence,
                                f"{(total_matches/max(len(gstr_suppliers), len(tally_suppliers)))*100:.1f}%"
                            ]
                        }
                        
                        summary_df = pd.DataFrame(summary_data)
                        store_step_data("Reconciliation_Summary", summary_df)
                        
                        st.session_state.processing_complete = True
                        show_success_message("Processing completed successfully!")
                        
                        # Display results
                        st.markdown("## 📊 Matching Results")
                        st.dataframe(matching_df, use_container_width=True)
                        
                        # Display summary metrics
                        st.markdown("## 📈 Summary Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Total Matches", total_matches)
                        with col2:
                            st.metric("High Confidence", high_confidence)
                        with col3:
                            match_rate = (total_matches/max(len(gstr_suppliers), len(tally_suppliers)))*100
                            st.metric("Match Rate", f"{match_rate:.1f}%")
                        with col4:
                            st.metric("Processing Time", "< 1 min")
                        
                    except KeyError as e:
                        show_error_message(f"Column not found: {str(e)}")
                        show_info_message("Please ensure your Excel files have the correct column headers.")
                    
                except Exception as e:
                    show_error_message(f"Error processing files: {str(e)}")
        
        # Download section for complete analysis
        if st.session_state.all_steps_data:
            st.markdown("## 📥 Download Complete Analysis")
            
            complete_excel = create_comprehensive_excel(st.session_state.all_steps_data)
            st.download_button(
                label="📥 Download Complete Analysis (All Steps)",
                data=complete_excel,
                file_name=f"complete_gstr_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type="primary"
            )
            
            show_success_message("All executed steps will be included in the download!")
    
    elif page == "📋 View All Sheets":
        display_all_sheets_summary()
    
    elif page == "📚 Help":
        show_help_instructions()
        
        st.markdown("## 🔧 File Format Requirements")
        st.markdown("""
        - **Tally Sheet**: Must contain 'Supplier' column
        - **GSTR-2A Sheet**: Must contain 'Supplier' column
        - **File Types**: Excel (.xlsx, .xls)
        - **Encoding**: UTF-8 recommended
        """)
        
        st.markdown("## 🎯 Matching Algorithm")
        st.markdown("""
        Our tool uses advanced fuzzy string matching to:
        - Handle variations in supplier names
        - Account for typos and formatting differences
        - Provide confidence scores for each match
        - Allow manual confirmation of matches
        """)
    
    elif page == "📥 Download Template":
        st.markdown("## 📥 Download Template Files")
        st.markdown("Get started with our sample Excel template that shows the correct format:")
        
        template_excel = create_default_format()
        st.download_button(
            label="📥 Download Sample Template",
            data=template_excel,
            file_name=f"GSTR_Tally_Template_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        show_info_message("The template includes sample data showing the correct column structure.")

if __name__ == "__main__":
    main()
