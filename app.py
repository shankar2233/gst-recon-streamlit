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
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets["Match_Results"]
        
        # Add data validation for Manual Confirmation column (assuming it's column D)
        dv = DataValidation(type="list", formula1='"Yes,No"', allow_blank=False)
        dv.error = 'Invalid Entry'
        dv.errorTitle = 'Invalid Entry'
        dv.prompt = 'Please select Yes or No'
        dv.promptTitle = 'Manual Confirmation'
        
        # Apply validation to the Manual Confirmation column (column D, starting from row 2)
        worksheet.add_data_validation(dv)
        dv.add(f'D2:D{len(df)+1}')
        
        # Format headers
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
    
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 Download Editable {filename}</a>'
    return href

def load_edited_matches(uploaded_file):
    """Load edited matches from uploaded Excel file"""
    try:
        df_edited = pd.read_excel(uploaded_file, sheet_name='Match_Results')
        
        # Validate required columns
        required_cols = ['GSTR-2A Party', 'Tally Party', 'Score', 'Manual Confirmation']
        if not all(col in df_edited.columns for col in required_cols):
            st.error("❌ Invalid file format. Required columns missing.")
            return None
            
        # Validate Manual Confirmation values
        valid_confirmations = ['Yes', 'No']
        invalid_rows = df_edited[~df_edited['Manual Confirmation'].isin(valid_confirmations)]
        
        if not invalid_rows.empty:
            st.error(f"❌ Invalid Manual Confirmation values found in {len(invalid_rows)} rows. Only 'Yes' or 'No' allowed.")
            return None
            
        return df_edited.values.tolist()
        
    except Exception as e:
        st.error(f"❌ Error reading edited file: {str(e)}")
        return None

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
        
        # Store in session state
        st.session_state.df_tally = df_tally
        st.session_state.df_gstr = df_gstr
        st.session_state.uploaded_file_content = uploaded_file.getvalue()
        st.session_state.uploaded_file_name = uploaded_file.name
        
        return df_tally, df_gstr
    except Exception as e:
        st.error(f"❌ Error reading Excel file: {str(e)}")
        return None, None

def prepare_data_for_reconciliation(df_tally, df_gstr):
    """
    Prepare data for reconciliation with priority-based matching:
    1. First priority: GSTIN of supplier
    2. Second priority: Supplier name (when GSTIN is blank)
    """
    # Clean and prepare both dataframes
    for df in [df_tally, df_gstr]:
        df.columns = df.columns.str.strip()
        if 'Cess' not in df.columns:
            df['Cess'] = 0
    
    # Get required columns
    try:
        col_gstin_tally = get_column(df_tally, 'GSTIN of supplier')
        col_gstin_gstr = get_column(df_gstr, 'GSTIN of supplier')
        gstin_available = True
    except KeyError:
        gstin_available = False
        st.warning("⚠️ GSTIN columns not found. Will use supplier names only.")
    
    col_supplier_tally = get_column(df_tally, 'Supplier')
    col_supplier_gstr = get_column(df_gstr, 'Supplier')
    
    # Create composite keys for matching
    def create_composite_key(df, gstin_col, supplier_col):
        """Create a composite key with priority: GSTIN first, then Supplier name"""
        df_copy = df.copy()
        
        if gstin_available:
            # Fill NaN GSTIN values
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
        else:
            # Only supplier names available
            df_copy[supplier_col] = df_copy[supplier_col].fillna('').astype(str).str.strip()
            df_copy['Match_Key'] = df_copy[supplier_col].apply(lambda x: f"NAME_{x}")
            df_copy['Match_Type'] = 'NAME'
        
        return df_copy
    
    if gstin_available:
        df_tally_prep = create_composite_key(df_tally, col_gstin_tally, col_supplier_tally)
        df_gstr_prep = create_composite_key(df_gstr, col_gstin_gstr, col_supplier_gstr)
    else:
        df_tally_prep = create_composite_key(df_tally, None, col_supplier_tally)
        df_gstr_prep = create_composite_key(df_gstr, None, col_supplier_gstr)
    
    return df_tally_prep, df_gstr_prep

def perform_priority_reconciliation(df_tally_prep, df_gstr_prep):
    """
    Perform reconciliation with priority matching
    """
    # Group and aggregate by Match_Key
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
        'Supplier': 'first',  # Take first supplier name for display
        'Match_Type': 'first'  # Take first match type
    })
    
    # Add GSTIN columns if available
    try:
        col_gstin_tally = get_column(df_tally_prep, 'GSTIN of supplier')
        col_gstin_gstr = get_column(df_gstr_prep, 'GSTIN of supplier')
        agg_dict['GSTIN of supplier'] = 'first'
    except KeyError:
        pass
    
    df_tally_grouped = df_tally_prep.groupby('Match_Key').agg(agg_dict).reset_index()
    df_gstr_grouped = df_gstr_prep.groupby('Match_Key').agg(agg_dict).reset_index()
    
    # Merge the grouped data
    df_combined = pd.merge(
        df_gstr_grouped, df_tally_grouped,
        on='Match_Key', how='outer',
        suffixes=('_GSTR', '_Tally')
    ).fillna(0)
    
    # Calculate variances
    for col in numeric_cols:
        df_combined[f'{col} Variance'] = df_combined[f'{col}_GSTR'] - df_combined[f'{col}_Tally']
    
    # Add match information
    df_combined['Supplier'] = df_combined.apply(
        lambda row: row['Supplier_GSTR'] if row['Supplier_GSTR'] != 0 else row['Supplier_Tally'], axis=1
    )
    
    df_combined['Match_Type'] = df_combined.apply(
        lambda row: row['Match_Type_GSTR'] if row['Match_Type_GSTR'] != 0 else row['Match_Type_Tally'], axis=1
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
    
    # File Upload Section (Always visible)
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
            "🔍 Fuzzy Matching",
            "🔄 Name Replacement",
            "📊 GST Reconciliation",
            "🧾 Invoice-wise Reconciliation"
        ], key="navigation_radio")
        
        # Show workflow status
        st.sidebar.markdown("---")
        st.sidebar.subheader("📋 Workflow Status")
        st.sidebar.success("✅ File Loaded")
        if st.session_state.matching_completed:
            st.sidebar.success("✅ Matching Complete")
            match_count = len([m for m in st.session_state.final_matches if m[1] != '' and m[3] == 'Yes'])
            st.sidebar.info(f"🎯 {match_count} matches found")
        else:
            st.sidebar.warning("⏳ Matching Pending")
        st.sidebar.markdown("---")
        
        # Main content based on selection
        if page == "🔍 Fuzzy Matching":
            st.header("🔍 Fuzzy Matching")
            
            # Threshold setting
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
                        
                        # Run matching
                        with st.spinner("Running fuzzy matching..."):
                            final_matches = two_way_match(tally_parties, gstr_parties, threshold)
                        
                        st.session_state.final_matches = final_matches
                        st.session_state.matching_completed = True
                        st.success("✅ Matching completed!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            with col2:
                st.write("**Alternative Options:**")
                
                # Upload edited matches
                uploaded_matches = st.file_uploader(
                    "Upload edited matches Excel file",
                    type=['xlsx'],
                    key="edited_matches_uploader",
                    help="Upload previously downloaded and edited match results"
                )
                
                if uploaded_matches is not None:
                    if st.button("📤 Load Edited Matches"):
                        edited_matches = load_edited_matches(uploaded_matches)
                        if edited_matches is not None:
                            st.session_state.final_matches = edited_matches
                            st.session_state.matching_completed = True
                            st.success("✅ Edited matches loaded successfully!")
                            st.rerun()
            
            # Display and edit results
            if st.session_state.matching_completed and st.session_state.final_matches:
                st.subheader("📋 Match Results - Editable")
                
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
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.button("💾 Save Changes", type="primary"):
                        st.session_state.final_matches = edited_df.values.tolist()
                        st.success("✅ Changes saved successfully!")
                        st.rerun()
                
                with col2:
                    # Download editable Excel file
                    st.markdown(
                        create_editable_download_link(df_result, "Editable_Match_Results.xlsx"), 
                        unsafe_allow_html=True
                    )
                
                with col3:
                    # Download regular Excel file
                    st.markdown(
                        create_download_link(edited_df, "Final_Match_Results.xlsx", "Match_Results"), 
                        unsafe_allow_html=True
                    )
                
                # Summary statistics
                matched_count = len(edited_df[edited_df['Manual Confirmation'] == 'Yes'])
                unmatched_count = len(edited_df[edited_df['Manual Confirmation'] == 'No'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Confirmed Matches", matched_count)
                with col2:
                    st.metric("❌ Rejected Matches", unmatched_count)
                with col3:
                    st.metric("📊 Total Records", len(edited_df))
        
        elif page == "🔄 Name Replacement":
            st.header("🔄 Name Replacement")
            
            if not st.session_state.matching_completed or not st.session_state.final_matches:
                st.warning("⚠️ Please run fuzzy matching first!")
                st.info("👈 Use the navigation on the left to go to 'Fuzzy Matching' first")
            else:
                st.info("✅ Match data found! Ready to replace names.")
                
                # Show match summary
                matched_count = len([m for m in st.session_state.final_matches if m[1] != '' and m[3] == 'Yes'])
                st.metric("Names to be replaced", matched_count)
                
                # Show preview of matches that will be replaced
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
                                
                                # Create name mapping
                                name_map = {tally: gstr for gstr, tally, score, confirm in st.session_state.final_matches
                                           if gstr and tally and confirm == "Yes"}
                                
                                df_new = df_tally.copy()
                                df_new[col_supplier] = df_new[col_supplier].apply(lambda x: name_map.get(x, x))
                                
                                # Format Invoice Date to DD-MM-YYYY
                                if 'Invoice Date' in df_new.columns:
                                    df_new['Invoice Date'] = pd.to_datetime(df_new['Invoice Date'], errors='coerce').dt.strftime('%d-%m-%Y')

                                
                                st.success("✅ Names replaced successfully!")
                                st.subheader("📊 Updated Tally Data (Preview)")
                                st.dataframe(df_new.head(10), use_container_width=True)
                                
                                # Download link
                                st.markdown(create_download_link(df_new, "Tally_Replaced.xlsx", "Tally_Replaced"), unsafe_allow_html=True)
                                st.info(f"🔄 Replaced {len(name_map)} supplier names in the Tally sheet.")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
        
        elif page == "📊 GST Reconciliation":
            st.header("📊 GST Reconciliation")
            st.info("💡 Priority matching: GSTIN first, then Supplier name when GSTIN is blank")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("Click the button below to generate a comprehensive GST reconciliation report with priority-based matching.")
            with col2:
                use_replaced_names = st.checkbox("Use replaced names",
                                               value=st.session_state.matching_completed,
                                               disabled=not st.session_state.matching_completed)
            
            if st.button("📊 Run GST Reconciliation", type="primary"):
                try:
                    with st.spinner("Processing reconciliation with priority matching..."):
                        df_tally = st.session_state.df_tally.copy()
                        df_gstr = st.session_state.df_gstr.copy()
                        
                        # Apply name replacements if requested
                        if use_replaced_names and st.session_state.matching_completed:
                            col_supplier = get_column(df_tally, 'Supplier')
                            name_map = {tally: gstr for gstr, tally, score, confirm in st.session_state.final_matches
                                       if gstr and tally and confirm == "Yes"}
                            df_tally[col_supplier] = df_tally[col_supplier].apply(lambda x: name_map.get(x, x))
                            st.info(f"🔄 Applied {len(name_map)} name replacements to Tally data")
                        
                        # Prepare data with priority matching
                        df_tally_prep, df_gstr_prep = prepare_data_for_reconciliation(df_tally, df_gstr)
                        
                        # Perform priority-based reconciliation
                        df_combined, df_tally_grouped, df_gstr_grouped = perform_priority_reconciliation(df_tally_prep, df_gstr_prep)
                        
                        # Calculate summary statistics
                        numeric_cols = ['Integrated Tax', 'Central Tax', 'State/UT tax']
                        
                        # Summary by match type
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
                            'State/UT Tax': [
                                df_gstr_grouped['State/UT tax'].sum(),
                                df_tally_grouped['State/UT tax'].sum(),
                                df_gstr_grouped['State/UT tax'].sum() - df_tally_grouped['State/UT tax'].sum()
                            ]
                        })
                        
                        # Separate records by presence
                        not_in_tally = df_combined[(df_combined['Integrated Tax_Tally'] == 0) & (df_combined['Integrated Tax_GSTR'] != 0)]
                        not_in_gstr = df_combined[(df_combined['Integrated Tax_GSTR'] == 0) & (df_combined['Integrated Tax_Tally'] != 0)]
                        both_present = df_combined[(df_combined['Integrated Tax_GSTR'] != 0) & (df_combined['Integrated Tax_Tally'] != 0)]
                        
                        # Reconciliation details
                        df_recon = pd.DataFrame({
                            'Particulars': [
                                'Not in Tally but found in GSTR-2A',
                                'Not in GSTR-2A but found in Tally',
                                'Present in both (Variance)',
                                'Total Variance'
                            ],
                            'Integrated Tax': [
                                not_in_tally['Integrated Tax_GSTR'].sum(),
                                not_in_gstr['Integrated Tax_Tally'].sum(),
                                both_present['Integrated Tax Variance'].sum(),
                                df_combined['Integrated Tax Variance'].sum()
                            ],
                            'Central Tax': [
                                not_in_tally['Central Tax_GSTR'].sum(),
                                not_in_gstr['Central Tax_Tally'].sum(),
                                both_present['Central Tax Variance'].sum(),
                                df_combined['Central Tax Variance'].sum()
                            ],
                            'State/UT Tax': [
                                not_in_tally['State/UT tax_GSTR'].sum(),
                                not_in_gstr['State/UT tax_Tally'].sum(),
                                both_present['State/UT Tax Variance'].sum(),
                                df_combined['State/UT Tax Variance'].sum()
                            ]
                        })
                        
                        st.success("✅ Priority-based reconciliation completed!")
                        
                        # Display results in tabs
                        tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "🎯 Match Types", "🔍 Details", "📥 Downloads"])
                        
                        with tab1:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader("GST Input Summary")
                                st.dataframe(df_summary, use_container_width=True)
                            with col2:
                                st.subheader("Reconciliation Analysis")
                                st.dataframe(df_recon, use_container_width=True)
                        
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
                                st.metric("📊 Total Unique Suppliers", len(df_combined))
                            
                            if len(match_type_summary) > 0:
                                st.subheader("Tax Summary by Match Type")
                                st.dataframe(match_type_summary, use_container_width=True)
                        
                        with tab3:
                            st.subheader("Detailed Comparison")
                            # Show match type in the detailed view
                            display_cols = ['Match_Key', 'Supplier', 'Match_Type'] + \
                                         [col for col in df_combined.columns if '_GSTR' in col or '_Tally' in col or 'Variance' in col]
                            st.dataframe(df_combined[display_cols], use_container_width=True)
                            
                            if len(not_in_tally) > 0:
                                st.subheader("Records Not in Tally but in GSTR-2A")
                                st.dataframe(not_in_tally[display_cols], use_container_width=True)
                            
                            if len(not_in_gstr) > 0:
                                st.subheader("Records Not in GSTR-2A but in Tally")
                                st.dataframe(not_in_gstr[display_cols], use_container_width=True)
                        
                        with tab4:
                            # Create download with multiple sheets
                            sheets_dict = {
                                'Summary': df_summary,
                                'Reconciliation': df_recon,
                                'Match_Type_Summary': match_type_summary,
                                'Detailed_Comparison': df_combined,
                                'Not_in_Tally': not_in_tally,
                                'Not_in_GSTR': not_in_gstr,
                                'Both_Present': both_present
                            }
                            st.markdown(create_multi_sheet_download(sheets_dict, "Priority_GST_Reconciliation.xlsx"), unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.write("Error details:", str(e))
        
        elif page == "🧾 Invoice-wise Reconciliation":
            st.header("🧾 Invoice-wise Reconciliation")
            st.info("💡 Priority matching: GSTIN first, then Supplier name when GSTIN is blank")
            
            if st.button("🧾 Run Invoice-wise Reconciliation", type="primary"):
                try:
                    with st.spinner("Processing invoice-wise reconciliation with priority matching..."):
                        df_tally = st.session_state.df_tally.copy()
                        df_gstr = st.session_state.df_gstr.copy()
                        
                        # Prepare data for reconciliation
                        df_tally_prep, df_gstr_prep = prepare_data_for_reconciliation(df_tally, df_gstr)
                        
                        # Group by Match_Key and Invoice number for invoice-wise analysis
                        group_columns = ['Match_Key', 'Invoice number']
                        
                        def consolidate_invoice_wise(df):
                            # Ensure Invoice number column exists
                            if 'Invoice number' not in df.columns:
                                df['Invoice number'] = 'N/A'
                            
                            numeric_cols = ['Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT tax', 'Cess']
                            agg_dict = {col: 'sum' for col in numeric_cols if col in df.columns}
                            agg_dict.update({
                                'Supplier': 'first',
                                'Match_Type': 'first'
                            })
                            
                            # Add GSTIN if available
                            try:
                                gstin_col = get_column(df, 'GSTIN of supplier')
                                agg_dict[gstin_col] = 'first'
                            except KeyError:
                                pass
                            
                            return df.groupby(group_columns).agg(agg_dict).reset_index()
                        
                        tally_grouped = consolidate_invoice_wise(df_tally_prep)
                        gstr_grouped = consolidate_invoice_wise(df_gstr_prep)
                        
                        df_combined = pd.merge(
                            gstr_grouped, tally_grouped,
                            on=group_columns, how='outer',
                            suffixes=('_GSTR', '_Tally')
                        ).fillna(0)
                        
                        # Calculate variances
                        numeric_cols = ['Taxable Value', 'Integrated Tax', 'Central Tax', 'State/UT tax', 'Cess']
                        for col in numeric_cols:
                            if f'{col}_GSTR' in df_combined.columns and f'{col}_Tally' in df_combined.columns:
                                df_combined[f'{col} Variance'] = df_combined[f'{col}_GSTR'] - df_combined[f'{col}_Tally']
                        
                        # Add supplier information
                        df_combined['Supplier'] = df_combined.apply(
                            lambda row: row['Supplier_GSTR'] if row['Supplier_GSTR'] != 0 else row['Supplier_Tally'], axis=1
                        )
                        
                        df_combined['Match_Type'] = df_combined.apply(
                            lambda row: row['Match_Type_GSTR'] if row['Match_Type_GSTR'] != 0 else row['Match_Type_Tally'], axis=1
                        )
                        
                        st.success("✅ Invoice-wise reconciliation with priority matching completed!")
                        
                        # Display summary by match type
                        col1, col2 = st.columns(2)
                        with col1:
                            gstin_invoices = len(df_combined[df_combined['Match_Type'] == 'GSTIN'])
                            st.metric("🏢 Invoices Matched by GSTIN", gstin_invoices)
                        with col2:
                            name_invoices = len(df_combined[df_combined['Match_Type'] == 'NAME'])
                            st.metric("📝 Invoices Matched by Name", name_invoices)
                        
                        # Display summary by supplier
                        suppliers = df_combined['Supplier'].unique()
                        suppliers = [s for s in suppliers if s != 0 and s != '']
                        
                        if len(suppliers) > 0:
                            selected_supplier = st.selectbox("Select Supplier to view details:", suppliers)
                            if selected_supplier:
                                supplier_data = df_combined[df_combined['Supplier'] == selected_supplier]
                                st.subheader(f"Invoice Details for: {selected_supplier}")
                                
                                # Show match type for this supplier
                                supplier_match_type = supplier_data['Match_Type'].iloc[0] if len(supplier_data) > 0 else 'Unknown'
                                st.info(f"🎯 Matching Method: {supplier_match_type}")
                                
                                st.dataframe(supplier_data, use_container_width=True)
                        
                        # Show all data in expander
                        with st.expander("📊 View All Invoice Reconciliation Data"):
                            st.dataframe(df_combined, use_container_width=True)
                        
                        # Full download
                        st.markdown(create_download_link(df_combined, "Priority_Invoice_Reconciliation.xlsx", "Invoice_Recon"), unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.write("Error details:", str(e))
    
    else:
        st.info("👆 Please upload an Excel file to get started!")
        st.markdown("""
        ### 📋 Requirements:
        - Excel file with two sheets: **'Tally'** and **'GSTR-2A'**
        - Both sheets should have headers in row 2
        - Required columns: Supplier, Integrated Tax, Central Tax, State/UT tax
        - Optional: GSTIN of supplier (for priority matching)
        
        ### 🎯 Priority Matching Logic:
        1. **First Priority**: Match by GSTIN of supplier (exact match)
        2. **Second Priority**: Match by Supplier name (when GSTIN is blank/missing)
        """)

if __name__ == "__main__":
    main()
