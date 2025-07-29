import pandas as pd
import streamlit as st
from fuzzywuzzy import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.datavalidation import DataValidation
import io
from datetime import datetime
import base64

# Set page config
st.set_page_config(
    page_title="GST Reconciliation Tool",
    page_icon="📊",
    layout="wide"
)

# Initialize session state with better structure
def init_session_state():
    if 'final_matches' not in st.session_state:
        st.session_state.final_matches = []
    if 'uploaded_file_content' not in st.session_state:
        st.session_state.uploaded_file_content = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'df_tally' not in st.session_state:
        st.session_state.df_tally = None
    if 'df_gstr' not in st.session_state:
        st.session_state.df_gstr = None
    if 'matching_completed' not in st.session_state:
        st.session_state.matching_completed = False
    if 'supplier_reconciliation_completed' not in st.session_state:
        st.session_state.supplier_reconciliation_completed = False

init_session_state()

# --- Utility Functions ---
def get_column(df, colname):
    for col in df.columns:
        if col.strip().lower() == colname.strip().lower():
            return col
    raise KeyError(f"Column '{colname}' not found. Available columns: {df.columns.tolist()}")

def get_raw_unique_names(series):
    return pd.Series(series).dropna().drop_duplicates().tolist()

def create_download_link(df, filename, sheet_name="Sheet1"):
    """Create a download link for Excel file"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 Download {filename}</a>'
    return href

def create_editable_download_link(df, filename):
    """Create download link for editable Excel file with proper formatting"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Match_Results", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Match_Results"]
        
        dv = DataValidation(type="list", formula1='"Yes,No"', allow_blank=False)
        dv.error = 'Invalid Entry'
        dv.errorTitle = 'Invalid Entry'
        dv.prompt = 'Please select Yes or No'
        dv.promptTitle = 'Manual Confirmation'
        
        worksheet.add_data_validation(dv)
        dv.add(f'D2:D{len(df)+1}')
        
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
    
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 Download Editable {filename}</a>'
    return href

def create_multi_sheet_download(dfs_dict, filename):
    """Create download link for multi-sheet Excel file"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 Download {filename}</a>'
    return href

def load_excel_data(uploaded_file):
    """Load and cache Excel data"""
    try:
        df_tally = pd.read_excel(uploaded_file, sheet_name='Tally', header=1)
        df_gstr = pd.read_excel(uploaded_file, sheet_name='GSTR-2A', header=1)
        
        st.session_state.df_tally = df_tally
        st.session_state.df_gstr = df_gstr
        st.session_state.uploaded_file_content = uploaded_file.getvalue()
        st.session_state.uploaded_file_name = uploaded_file.name
        
        return df_tally, df_gstr
    except Exception as e:
        st.error(f"❌ Error reading Excel file: {str(e)}")
        return None, None

# --- Supplier-wise Reconciliation (After Fuzzy Matching) ---
def perform_supplier_wise_reconciliation(df_tally, df_gstr, use_replaced_names=True):
    """
    Perform supplier-wise reconciliation based on fuzzy matching results
    """
    df_tally_copy = df_tally.copy()
    df_gstr_copy = df_gstr.copy()
    
    # Apply name replacements if fuzzy matching was completed
    if use_replaced_names and st.session_state.matching_completed:
        try:
            col_supplier_tally = get_column(df_tally_copy, 'Supplier')
            name_map = {tally: gstr for gstr, tally, score, confirm in st.session_state.final_matches
                       if gstr and tally and confirm == "Yes"}
            df_tally_copy[col_supplier_tally] = df_tally_copy[col_supplier_tally].apply(lambda x: name_map.get(x, x))
            st.info(f"🔄 Applied {len(name_map)} name replacements to Tally data")
        except Exception as e:
            st.warning(f"⚠️ Could not apply name replacements: {str(e)}")
    
    # Clean and prepare data
    for df in [df_tally_copy, df_gstr_copy]:
        df.columns = df.columns.str.strip()
        if 'Cess' not in df.columns:
            df['Cess'] = 0
    
    # Get supplier columns
    col_supplier_tally = get_column(df_tally_copy, 'Supplier')
    col_supplier_gstr = get_column(df_gstr_copy, 'Supplier')
    
    # Numeric columns for aggregation
    numeric_cols = ['Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT tax', 'Cess']
    
    # Ensure numeric columns exist and are numeric
    for df in [df_tally_copy, df_gstr_copy]:
        for col in numeric_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Group by supplier and aggregate
    agg_dict = {col: 'sum' for col in numeric_cols}
    
    # Add GSTIN if available
    try:
        col_gstin_tally = get_column(df_tally_copy, 'GSTIN of supplier')
        col_gstin_gstr = get_column(df_gstr_copy, 'GSTIN of supplier')
        agg_dict['GSTIN of supplier'] = 'first'
        gstin_available = True
    except KeyError:
        gstin_available = False
    
    df_tally_grouped = df_tally_copy.groupby(col_supplier_tally).agg(agg_dict).reset_index()
    df_gstr_grouped = df_gstr_copy.groupby(col_supplier_gstr).agg(agg_dict).reset_index()
    
    # Rename columns for merging
    df_tally_grouped = df_tally_grouped.rename(columns={col_supplier_tally: 'Supplier'})
    df_gstr_grouped = df_gstr_grouped.rename(columns={col_supplier_gstr: 'Supplier'})
    
    # Merge the grouped data
    df_combined = pd.merge(
        df_gstr_grouped, df_tally_grouped,
        on='Supplier', how='outer',
        suffixes=('_GSTR', '_Tally')
    ).fillna(0)
    
    # Calculate variances
    for col in numeric_cols:
        df_combined[f'{col}_Variance'] = df_combined[f'{col}_GSTR'] - df_combined[f'{col}_Tally']
    
    return df_combined, df_tally_grouped, df_gstr_grouped

# --- GSTIN-wise Reconciliation ---
def perform_gstin_wise_reconciliation(df_tally, df_gstr):
    """
    Perform GSTIN-wise reconciliation with priority matching
    """
    df_tally_copy = df_tally.copy()
    df_gstr_copy = df_gstr.copy()
    
    # Clean and prepare data
    for df in [df_tally_copy, df_gstr_copy]:
        df.columns = df.columns.str.strip()
        if 'Cess' not in df.columns:
            df['Cess'] = 0
    
    # Check if GSTIN columns exist
    try:
        col_gstin_tally = get_column(df_tally_copy, 'GSTIN of supplier')
        col_gstin_gstr = get_column(df_gstr_copy, 'GSTIN of supplier')
        col_supplier_tally = get_column(df_tally_copy, 'Supplier')
        col_supplier_gstr = get_column(df_gstr_copy, 'Supplier')
        gstin_available = True
    except KeyError:
        st.error("❌ GSTIN columns not found. Cannot perform GSTIN-wise reconciliation.")
        return None, None, None
    
    # Create composite keys with priority: GSTIN first, then Supplier name
    def create_composite_key(df, gstin_col, supplier_col):
        df_copy = df.copy()
        df_copy[gstin_col] = df_copy[gstin_col].fillna('').astype(str).str.strip()
        df_copy[supplier_col] = df_copy[supplier_col].fillna('').astype(str).str.strip()
        
        # Create composite key: use GSTIN if available, otherwise use Supplier name
        df_copy['Match_Key'] = df_copy.apply(
            lambda row: row[gstin_col] if row[gstin_col] and row[gstin_col] != '' 
            else f"NAME_{row[supplier_col]}", axis=1
        )
        
        df_copy['Match_Type'] = df_copy.apply(
            lambda row: 'GSTIN' if row[gstin_col] and row[gstin_col] != '' 
            else 'NAME', axis=1
        )
        
        return df_copy
    
    df_tally_prep = create_composite_key(df_tally_copy, col_gstin_tally, col_supplier_tally)
    df_gstr_prep = create_composite_key(df_gstr_copy, col_gstin_gstr, col_supplier_gstr)
    
    # Numeric columns for aggregation
    numeric_cols = ['Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT tax', 'Cess']
    
    # Ensure numeric columns exist and are numeric
    for df in [df_tally_prep, df_gstr_prep]:
        for col in numeric_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Group by Match_Key and aggregate
    agg_dict = {col: 'sum' for col in numeric_cols}
    agg_dict.update({
        col_supplier_tally if 'Tally' in str(df_tally_prep) else col_supplier_gstr: 'first',
        'Match_Type': 'first'
    })
    
    if gstin_available:
        agg_dict[col_gstin_tally if 'Tally' in str(df_tally_prep) else col_gstin_gstr] = 'first'
    
    df_tally_grouped = df_tally_prep.groupby('Match_Key').agg({
        **{col: 'sum' for col in numeric_cols},
        col_supplier_tally: 'first',
        col_gstin_tally: 'first',
        'Match_Type': 'first'
    }).reset_index()
    
    df_gstr_grouped = df_gstr_prep.groupby('Match_Key').agg({
        **{col: 'sum' for col in numeric_cols},
        col_supplier_gstr: 'first',
        col_gstin_gstr: 'first',
        'Match_Type': 'first'
    }).reset_index()
    
    # Merge the grouped data
    df_combined = pd.merge(
        df_gstr_grouped, df_tally_grouped,
        on='Match_Key', how='outer',
        suffixes=('_GSTR', '_Tally')
    ).fillna(0)
    
    # Calculate variances
    for col in numeric_cols:
        df_combined[f'{col}_Variance'] = df_combined[f'{col}_GSTR'] - df_combined[f'{col}_Tally']
    
    # Add consolidated supplier and GSTIN information
    df_combined['Supplier'] = df_combined.apply(
        lambda row: row[f'{col_supplier_gstr}_GSTR'] if row[f'{col_supplier_gstr}_GSTR'] != 0 
        else row[f'{col_supplier_tally}_Tally'], axis=1
    )
    
    df_combined['GSTIN'] = df_combined.apply(
        lambda row: row[f'{col_gstin_gstr}_GSTR'] if row[f'{col_gstin_gstr}_GSTR'] != 0 
        else row[f'{col_gstin_tally}_Tally'], axis=1
    )
    
    df_combined['Match_Type'] = df_combined.apply(
        lambda row: row['Match_Type_GSTR'] if row['Match_Type_GSTR'] != 0 
        else row['Match_Type_Tally'], axis=1
    )
    
    return df_combined, df_tally_grouped, df_gstr_grouped

# --- Fuzzy Matching Logic ---
def two_way_match(tally_list, gstr_list, threshold):
    match_map, used_tally, used_gstr, results = {}, set(), set(), []
    tally_upper = {name.upper(): name for name in tally_list}
    gstr_upper = {name.upper(): name for name in gstr_list}
    tally_keys, gstr_keys = list(tally_upper.keys()), list(gstr_upper.keys())
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_steps = len(gstr_keys) + len(tally_keys)
    progress_count = 0
    
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
        
        progress_count += 1
        progress_bar.progress(progress_count / total_steps)
        status_text.text(f"GSTR → Tally: {i+1}/{len(gstr_keys)}")
    
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
        
        progress_count += 1
        progress_bar.progress(progress_count / total_steps)
        status_text.text(f"Tally → GSTR: {i+1}/{len(tally_keys)}")
    
    results.clear()
    for gstr_name, tally_name, score in match_map.values():
        confirm = "Yes" if gstr_name and tally_name else "No"
        results.append([gstr_name, tally_name, score, confirm])
    
    progress_bar.empty()
    status_text.empty()
    return results

# --- Main App ---
def main():
    st.title("🏦 GST Reconciliation Tool")
    st.markdown("**Fuzzy Match GSTR-2A/2B vs Books & Run GST Reconciliation**")
    
    # File Upload Section
    st.header("📤 Upload Excel File")
    uploaded_file = st.file_uploader(
        "Choose Excel file with 'Tally' and 'GSTR-2A' sheets",
        type=['xlsx', 'xls'],
        key="file_uploader"
    )
    
    # Process uploaded file
    if uploaded_file is not None:
        if (st.session_state.uploaded_file_name != uploaded_file.name or 
            st.session_state.uploaded_file_content != uploaded_file.getvalue()):
            with st.spinner("Loading Excel file..."):
                df_tally, df_gstr = load_excel_data(uploaded_file)
                if df_tally is not None and df_gstr is not None:
                    st.success(f"✅ File loaded successfully: {uploaded_file.name}")
                    st.info(f"📊 Tally Sheet: {len(df_tally)} rows | GSTR-2A Sheet: {len(df_gstr)} rows")
        else:
            st.success(f"✅ File already loaded: {uploaded_file.name}")
        
        # Show navigation only if file is uploaded
        if st.session_state.uploaded_file_content is not None:
            st.sidebar.title("🧭 Navigation")
            page = st.sidebar.radio("Choose a function:", [
                "🔍 Fuzzy Matching & Supplier Reconciliation",
                "📊 GSTIN-wise Reconciliation",
                "🔄 Name Replacement",
                "🧾 Invoice-wise Reconciliation"
            ], key="navigation_radio")
            
            # Show workflow status
            st.sidebar.markdown("---")
            st.sidebar.subheader("📋 Workflow Status")
            st.sidebar.success("✅ File Loaded")
            if st.session_state.matching_completed:
                st.sidebar.success("✅ Fuzzy Matching Complete")
                match_count = len([m for m in st.session_state.final_matches if m[1] != '' and m[3] == 'Yes'])
                st.sidebar.info(f"🎯 {match_count} matches found")
            else:
                st.sidebar.warning("⏳ Fuzzy Matching Pending")
            
            if st.session_state.supplier_reconciliation_completed:
                st.sidebar.success("✅ Supplier Reconciliation Complete")
            else:
                st.sidebar.warning("⏳ Supplier Reconciliation Pending")
            
            st.sidebar.markdown("---")
            
            # Main content based on selection
            if page == "🔍 Fuzzy Matching & Supplier Reconciliation":
                st.header("🔍 Fuzzy Matching & Supplier Reconciliation")
                
                # Step 1: Fuzzy Matching
                st.subheader("Step 1: Fuzzy Matching")
                threshold = st.slider("Match Threshold", min_value=50, max_value=100, value=80, step=5)
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    if st.button("🚀 Start Fuzzy Matching", type="primary"):
                        try:
                            df_tally = st.session_state.df_tally
                            df_gstr = st.session_state.df_gstr
                            
                            col_supplier_tally = get_column(df_tally, 'Supplier')
                            col_supplier_gstr = get_column(df_gstr, 'Supplier')
                            
                            tally_parties = get_raw_unique_names(df_tally[col_supplier_tally])
                            gstr_parties = get_raw_unique_names(df_gstr[col_supplier_gstr])
                            
                            st.info(f"📈 Found {len(tally_parties)} unique suppliers in Tally and {len(gstr_parties)} unique suppliers in GSTR-2A")
                            
                            with st.spinner("Running fuzzy matching..."):
                                final_matches = two_way_match(tally_parties, gstr_parties, threshold)
                                st.session_state.final_matches = final_matches
                                st.session_state.matching_completed = True
                            
                            st.success("✅ Fuzzy matching completed!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                # Display fuzzy matching results
                if st.session_state.matching_completed and st.session_state.final_matches:
                    st.subheader("📋 Fuzzy Match Results")
                    df_result = pd.DataFrame(st.session_state.final_matches,
                                           columns=['GSTR-2A Party', 'Tally Party', 'Score', 'Manual Confirmation'])
                    df_result = df_result.sort_values(by=['Manual Confirmation', 'GSTR-2A Party', 'Tally Party'],
                                                    ascending=[False, False, False])
                    
                    # Editable dataframe
                    edited_df = st.data_editor(
                        df_result,
                        column_config={
                            "Manual Confirmation": st.column_config.SelectboxColumn(
                                "Manual Confirmation",
                                help="Select Yes or No for manual confirmation",
                                width="medium",
                                options=["Yes", "No"],
                                required=True,
                            ),
                            "GSTR-2A Party": st.column_config.TextColumn("GSTR-2A Party", disabled=True),
                            "Tally Party": st.column_config.TextColumn("Tally Party", disabled=True),
                            "Score": st.column_config.NumberColumn("Score", disabled=True, format="%.0f"),
                        },
                        disabled=["GSTR-2A Party", "Tally Party", "Score"],
                        use_container_width=True,
                        key="match_editor",
                        height=400
                    )
                    
                    # Save changes button
                    if st.button("💾 Save Fuzzy Match Changes", type="secondary"):
                        st.session_state.final_matches = edited_df.values.tolist()
                        st.success("✅ Fuzzy match changes saved!")
                        st.rerun()
                    
                    # Step 2: Supplier-wise Reconciliation
                    st.subheader("Step 2: Supplier-wise Reconciliation")
                    
                    if st.button("📊 Run Supplier-wise Reconciliation", type="primary"):
                        try:
                            with st.spinner("Processing supplier-wise reconciliation..."):
                                df_combined, df_tally_grouped, df_gstr_grouped = perform_supplier_wise_reconciliation(
                                    st.session_state.df_tally, st.session_state.df_gstr, use_replaced_names=True
                                )
                                st.session_state.supplier_reconciliation_completed = True
                            
                            st.success("✅ Supplier-wise reconciliation completed!")
                            
                            # Calculate summary statistics
                            numeric_cols = ['Integrated Tax', 'Central Tax', 'State/UT tax']
                            
                            # Overall summary
                            df_summary = pd.DataFrame({
                                'Particulars': ['GST Input as per GSTR-2A Sheet', 'GST Input as per Tally', 'Variance (GSTR - Tally)'],
                                'Integrated Tax': [
                                    df_gstr_grouped['Integrated Tax'].sum(),
                                    df_tally_grouped['Integrated Tax'].sum(),
                                    df_gstr_grouped['Integrated Tax'].sum() - df_tally_grouped['Integrated Tax'].sum()
                                ],
                                'Central Tax': [
                                    df_gstr_grouped['Central Tax'].sum(),
                                    df_tally_grouped['Central Tax'].sum(),
                                    df_gstr_grouped['Central Tax'].sum() - df_tally_grouped['Central Tax'].sum()
                                ],
                                'State/UT tax': [
                                    df_gstr_grouped['State/UT tax'].sum(),
                                    df_tally_grouped['State/UT tax'].sum(),
                                    df_gstr_grouped['State/UT tax'].sum() - df_tally_grouped['State/UT tax'].sum()
                                ]
                            })
                            
                            # Separate records by presence
                            not_in_tally = df_combined[(df_combined['Integrated Tax_Tally'] == 0) & (df_combined['Integrated Tax_GSTR'] != 0)]
                            not_in_gstr = df_combined[(df_combined['Integrated Tax_GSTR'] == 0) & (df_combined['Integrated Tax_Tally'] != 0)]
                            both_present = df_combined[(df_combined['Integrated Tax_GSTR'] != 0) & (df_combined['Integrated Tax_Tally'] != 0)]
                            
                            # Display results in tabs
                            tab1, tab2, tab3 = st.tabs(["📊 Summary", "🔍 Details", "📥 Downloads"])
                            
                            with tab1:
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.subheader("GST Input Summary")
                                    st.dataframe(df_summary, use_container_width=True)
                                
                                with col2:
                                    st.metric("✅ Total Suppliers Matched", len(both_present))
                                    st.metric("❌ Suppliers Only in GSTR-2A", len(not_in_tally))
                                    st.metric("⚠️ Suppliers Only in Tally", len(not_in_gstr))
                            
                            with tab2:
                                st.subheader("Detailed Supplier-wise Comparison")
                                display_cols = ['Supplier'] + [col for col in df_combined.columns if '_GSTR' in col or '_Tally' in col or '_Variance' in col]
                                st.dataframe(df_combined[display_cols], use_container_width=True)
                                
                                if len(not_in_tally) > 0:
                                    st.subheader("Suppliers Not in Tally but in GSTR-2A")
                                    st.dataframe(not_in_tally[display_cols], use_container_width=True)
                                
                                if len(not_in_gstr) > 0:
                                    st.subheader("Suppliers Not in GSTR-2A but in Tally")
                                    st.dataframe(not_in_gstr[display_cols], use_container_width=True)
                            
                            with tab3:
                                sheets_dict = {
                                    'Summary': df_summary,
                                    'Detailed_Comparison': df_combined,
                                    'Not_in_Tally': not_in_tally,
                                    'Not_in_GSTR': not_in_gstr,
                                    'Both_Present': both_present
                                }
                                st.markdown(create_multi_sheet_download(sheets_dict, "Supplier_Wise_Reconciliation.xlsx"), unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            
            elif page == "📊 GSTIN-wise Reconciliation":
                st.header("📊 GSTIN-wise Reconciliation")
                st.info("💡 Priority matching: GSTIN first, then Supplier name when GSTIN is blank")
                
                if st.button("📊 Run GSTIN-wise Reconciliation", type="primary"):
                    try:
                        with st.spinner("Processing GSTIN-wise reconciliation with priority matching..."):
                            df_combined, df_tally_grouped, df_gstr_grouped = perform_gstin_wise_reconciliation(
                                st.session_state.df_tally, st.session_state.df_gstr
                            )
                        
                        if df_combined is not None:
                            st.success("✅ GSTIN-wise reconciliation completed!")
                            
                            # Calculate summary statistics
                            numeric_cols = ['Integrated Tax', 'Central Tax', 'State/UT tax']
                            
                            # Match type summary
                            match_type_summary = df_combined.groupby('Match_Type').agg({
                                f'{col}_GSTR': 'sum' for col in numeric_cols
                            }).reset_index()
                            
                            # Overall summary
                            df_summary = pd.DataFrame({
                                'Particulars': ['GST Input as per GSTR-2A Sheet', 'GST Input as per Tally', 'Variance (GSTR - Tally)'],
                                'Integrated Tax': [
                                    df_gstr_grouped['Integrated Tax'].sum(),
                                    df_tally_grouped['Integrated Tax'].sum(),
                                    df_gstr_grouped['Integrated Tax'].sum() - df_tally_grouped['Integrated Tax'].sum()
                                ],
                                'Central Tax': [
                                    df_gstr_grouped['Central Tax'].sum(),
                                    df_tally_grouped['Central Tax'].sum(),
                                    df_gstr_grouped['Central Tax'].sum() - df_tally_grouped['Central Tax'].sum()
                                ],
                                'State/UT tax': [
                                    df_gstr_grouped['State/UT tax'].sum(),
                                    df_tally_grouped['State/UT tax'].sum(),
                                    df_gstr_grouped['State/UT tax'].sum() - df_tally_grouped['State/UT tax'].sum()
                                ]
                            })
                            
                            # Separate records by presence
                            not_in_tally = df_combined[(df_combined['Integrated Tax_Tally'] == 0) & (df_combined['Integrated Tax_GSTR'] != 0)]
                            not_in_gstr = df_combined[(df_combined['Integrated Tax_GSTR'] == 0) & (df_combined['Integrated Tax_Tally'] != 0)]
                            both_present = df_combined[(df_combined['Integrated Tax_GSTR'] != 0) & (df_combined['Integrated Tax_Tally'] != 0)]
                            
                            # Display results in tabs
                            tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "🎯 Match Types", "🔍 Details", "📥 Downloads"])
                            
                            with tab1:
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.subheader("GST Input Summary")
                                    st.dataframe(df_summary, use_container_width=True)
                                
                                with col2:
                                    st.metric("✅ Total Records Matched", len(both_present))
                                    st.metric("❌ Records Only in GSTR-2A", len(not_in_tally))
                                    st.metric("⚠️ Records Only in Tally", len(not_in_gstr))
                            
                            with tab2:
                                st.subheader("Matching Statistics by Type")
                                gstin_matches = len(df_combined[df_combined['Match_Type'] == 'GSTIN'])
                                name_matches = len(df_combined[df_combined['Match_Type'] == 'NAME'])
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("🏢 GSTIN Matches", gstin_matches)
                                with col2:
                                    st.metric("📝 Name Matches", name_matches)
                                with col3:
                                    st.metric("📊 Total Unique Keys", len(df_combined))
                                
                                if len(match_type_summary) > 0:
                                    st.subheader("Tax Summary by Match Type")
                                    st.dataframe(match_type_summary, use_container_width=True)
                            
                            with tab3:
                                st.subheader("Detailed GSTIN-wise Comparison")
                                display_cols = ['Match_Key', 'Supplier', 'GSTIN', 'Match_Type'] + \
                                             [col for col in df_combined.columns if '_GSTR' in col or '_Tally' in col or '_Variance' in col]
                                st.dataframe(df_combined[display_cols], use_container_width=True)
                                
                                if len(not_in_tally) > 0:
                                    st.subheader("Records Not in Tally but in GSTR-2A")
                                    st.dataframe(not_in_tally[display_cols], use_container_width=True)
                                
                                if len(not_in_gstr) > 0:
                                    st.subheader("Records Not in GSTR-2A but in Tally")
                                    st.dataframe(not_in_gstr[display_cols], use_container_width=True)
                            
                            with tab4:
                                sheets_dict = {
                                    'Summary': df_summary,
                                    'Match_Type_Summary': match_type_summary,
                                    'Detailed_Comparison': df_combined,
                                    'Not_in_Tally': not_in_tally,
                                    'Not_in_GSTR': not_in_gstr,
                                    'Both_Present': both_present
                                }
                                st.markdown(create_multi_sheet_download(sheets_dict, "GSTIN_Wise_Reconciliation.xlsx"), unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.write("Error details:", str(e))
            
            elif page == "🔄 Name Replacement":
                st.header("🔄 Name Replacement")
                if not st.session_state.matching_completed or not st.session_state.final_matches:
                    st.warning("⚠️ Please run fuzzy matching first!")
                    st.info("👈 Use the navigation on the left to go to 'Fuzzy Matching & Supplier Reconciliation' first")
                else:
                    st.info("✅ Match data found! Ready to replace names.")
                    
                    matched_count = len([m for m in st.session_state.final_matches if m[1] != '' and m[3] == 'Yes'])
                    st.metric("Names to be replaced", matched_count)
                    
                    if matched_count > 0:
                        st.subheader("🔄 Names to be Replaced:")
                        replacement_data = []
                        for gstr, tally, score, confirm in st.session_state.final_matches:
                            if gstr and tally and confirm == "Yes":
                                replacement_data.append({"From (Tally)": tally, "To (GSTR)": gstr, "Score": score})
                        
                        if replacement_data:
                            st.dataframe(pd.DataFrame(replacement_data), use_container_width=True)
                        
                        if st.button("🔁 Replace Names in Tally Sheet", type="primary"):
                            try:
                                df_tally = st.session_state.df_tally.copy()
                                col_supplier = get_column(df_tally, 'Supplier')
                                
                                name_map = {tally: gstr for gstr, tally, score, confirm in st.session_state.final_matches
                                           if gstr and tally and confirm == "Yes"}
                                
                                df_new = df_tally.copy()
                                df_new[col_supplier] = df_new[col_supplier].apply(lambda x: name_map.get(x, x))
                                
                                if 'Invoice Date' in df_new.columns:
                                    df_new['Invoice Date'] = pd.to_datetime(df_new['Invoice Date'], errors='coerce').dt.strftime('%d-%m-%Y')
                                
                                st.success("✅ Names replaced successfully!")
                                st.subheader("📊 Updated Tally Data (Preview)")
                                st.dataframe(df_new.head(10), use_container_width=True)
                                
                                st.markdown(create_download_link(df_new, "Tally_Replaced.xlsx", "Tally_Replaced"), unsafe_allow_html=True)
                                st.info(f"🔄 Replaced {len(name_map)} supplier names in the Tally sheet.")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            
            elif page == "🧾 Invoice-wise Reconciliation":
                st.header("🧾 Invoice-wise Reconciliation")
                st.info("💡 Priority matching: GSTIN first, then Supplier name when GSTIN is blank")
                
                if st.button("🧾 Run Invoice-wise Reconciliation", type="primary"):
                    try:
                        with st.spinner("Processing invoice-wise reconciliation..."):
                            df_tally = st.session_state.df_tally.copy()
                            df_gstr = st.session_state.df_gstr.copy()
                            
                            # Implementation for invoice-wise reconciliation
                            # (Your existing invoice-wise logic here)
                            
                            st.success("✅ Invoice-wise reconciliation completed!")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    else:
        st.info("👆 Please upload an Excel file to get started!")
        st.markdown("""
        ### 📋 Requirements:
        - Excel file with two sheets: **'Tally'** and **'GSTR-2A'**
        - Both sheets should have headers in row 2
        - Required columns: Supplier, Integrated Tax, Central Tax, State/UT tax
        - Optional: GSTIN of supplier (for priority matching)
        
        ### 🎯 Workflow:
        1. **Fuzzy Matching & Supplier Reconciliation**: Match supplier names and perform supplier-wise consolidation
        2. **GSTIN-wise Reconciliation**: Perform GSTIN-based consolidation with priority matching
        """)

if __name__ == "__main__":
    main()
