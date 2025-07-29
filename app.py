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

# --- Utility Functions ---

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
    expected_cols = ['GSTIN of supplier', 'Supplier', 'Invoice number', 'Invoice Date',
                     'Invoice Value', 'Rate', 'Taxable Value', 'Integrated Tax',
                     'Central Tax', 'State/UT tax', 'Cess']
    
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

# --- Fuzzy Matching Logic ---

def two_way_match(tally_list, gstr_list, threshold):
    match_map, used_tally, used_gstr = {}, set(), set()
    
    tally_upper = {name.upper(): name for name in tally_list}
    gstr_upper = {name.upper(): name for name in gstr_list}
    tally_keys, gstr_keys = list(tally_upper.keys()), list(gstr_upper.keys())
    
    total_steps = len(gstr_keys) + len(tally_keys)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
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
        
        progress = (len(gstr_keys) + i + 1) / total_steps
        progress_bar.progress(progress)
        status_text.text(f"Tally → GSTR: {i+1}/{len(tally_keys)}")
    
    results = []
    for gstr_name, tally_name, score in match_map.values():
        confirm = "Yes" if gstr_name and tally_name else "No"
        results.append([gstr_name, tally_name, score, confirm])
    
    return results

# --- Streamlit App ---

def main():
    st.set_page_config(
        page_title="GSTR vs Tally Reconciliation", 
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🔄 GSTR vs Tally Match + GST Reconciliation")
    st.markdown("**Fuzzy Match GSTR-2A/2B vs Books and Perform GST Reconciliation**")
    
    # Initialize session state
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'match_results' not in st.session_state:
        st.session_state.match_results = None
    if 'temp_file_path' not in st.session_state:
        st.session_state.temp_file_path = None
    
    # File upload
    st.header("📂 Upload Excel File")
    uploaded_file = st.file_uploader(
        "Choose an Excel file with 'Tally' and 'GSTR-2A' sheets",
        type=['xlsx', 'xls']
    )
    
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            st.session_state.temp_file_path = tmp_file.name
        
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Validate sheets
        try:
            excel_file = pd.ExcelFile(st.session_state.temp_file_path)
            sheets = excel_file.sheet_names
            
            if 'Tally' in sheets and 'GSTR-2A' in sheets:
                st.success("✅ Required sheets 'Tally' and 'GSTR-2A' found!")
            else:
                st.error(f"❌ Required sheets not found. Available sheets: {sheets}")
                return
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            return
    
    if st.session_state.uploaded_file is None:
        st.info("👆 Please upload an Excel file to continue")
        return
    
    # Main functionality tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Fuzzy Matching", 
        "🔁 Name Replacement", 
        "📊 GST Reconciliation", 
        "🧾 Invoice Reconciliation"
    ])
    
    with tab1:
        st.header("🚀 Start Fuzzy Matching")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            threshold = st.number_input(
                "Match Threshold (%)", 
                min_value=0, 
                max_value=100, 
                value=80,
                help="Minimum similarity score for matching names"
            )
        
        if st.button("🚀 Start Matching", use_container_width=True):
            try:
                with st.spinner("Processing fuzzy matching..."):
                    # Read data
                    df_tally = pd.read_excel(st.session_state.temp_file_path, sheet_name='Tally', header=1)
                    df_gstr = pd.read_excel(st.session_state.temp_file_path, sheet_name='GSTR-2A', header=1)
                    
                    # Get supplier columns
                    col_supplier_tally = get_column(df_tally, 'Supplier')
                    col_supplier_gstr = get_column(df_gstr, 'Supplier')
                    
                    # Get unique names
                    tally_parties = get_raw_unique_names(df_tally[col_supplier_tally])
                    gstr_parties = get_raw_unique_names(df_gstr[col_supplier_gstr])
                    
                    # Perform matching
                    matches = two_way_match(tally_parties, gstr_parties, threshold)
                    st.session_state.match_results = matches
                    
                    # Create results dataframe
                    df_result = pd.DataFrame(matches, columns=['GSTR-2A Party', 'Tally Party', 'Score', 'Manual Confirmation'])
                    df_result.sort_values(by=['Manual Confirmation', 'GSTR-2A Party', 'Tally Party'], 
                                        ascending=[False, False, False], inplace=True)
                    
                    # Save to Excel
                    with pd.ExcelWriter(st.session_state.temp_file_path, engine='openpyxl', mode='a') as writer:
                        df_result.to_excel(writer, sheet_name='GSTR_Tally_Match', index=False)
                    
                    st.success("✅ Matching completed successfully!")
                    
                    # Display results
                    st.subheader("📋 Matching Results")
                    st.dataframe(df_result, use_container_width=True)
                    
                    # Download button
                    with open(st.session_state.temp_file_path, 'rb') as file:
                        st.download_button(
                            label="📥 Download Excel with Matches",
                            data=file.read(),
                            file_name=f"matched_{uploaded_file.name}",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
            except Exception as e:
                st.error(f"❌ Error during matching: {e}")
    
    with tab2:
        st.header("🔁 Name Replacement")
        st.info("💡 First complete fuzzy matching, then use this to replace Tally names with GSTR names")
        
        if st.button("🔁 Replace Matched Names", use_container_width=True):
            try:
                with st.spinner("Processing name replacements..."):
                    # Read match results
                    df_matches = pd.read_excel(st.session_state.temp_file_path, sheet_name='GSTR_Tally_Match')
                    df_tally = pd.read_excel(st.session_state.temp_file_path, sheet_name='Tally', header=1)
                    
                    col_supplier = get_column(df_tally, 'Supplier')
                    
                    # Create name mapping
                    name_map = {}
                    replacement_count = 0
                    
                    for _, row in df_matches.iterrows():
                        gstr_name = row['GSTR-2A Party']
                        tally_name = row['Tally Party']
                        confirmation = str(row['Manual Confirmation']).strip().upper()
                        
                        if confirmation == "YES" and pd.notna(gstr_name) and pd.notna(tally_name):
                            if gstr_name != '' and tally_name != '':
                                name_map[tally_name] = gstr_name
                                replacement_count += 1
                    
                    # Apply replacements
                    df_new = df_tally.copy()
                    
                    def replace_name(name):
                        if pd.isna(name):
                            return name
                        return name_map.get(name, name)
                    
                    df_new[col_supplier] = df_new[col_supplier].apply(replace_name)
                    
                    # Format Invoice Date
                    if 'Invoice Date' in df_new.columns:
                        df_new['Invoice Date'] = pd.to_datetime(df_new['Invoice Date'], errors='coerce').dt.strftime('%d-%m-%Y')
                    
                    # Save updated data
                    with pd.ExcelWriter(st.session_state.temp_file_path, engine='openpyxl', mode='a') as writer:
                        df_new.to_excel(writer, sheet_name='Tally_Replaced', index=False, header=True)
                    
                    st.success(f"✅ Replaced {replacement_count} supplier names successfully!")
                    
                    # Show preview
                    st.subheader("📋 Preview of Replaced Data")
                    st.dataframe(df_new.head(), use_container_width=True)
                    
                    # Download button
                    with open(st.session_state.temp_file_path, 'rb') as file:
                        st.download_button(
                            label="📥 Download Excel with Replacements",
                            data=file.read(),
                            file_name=f"replaced_{uploaded_file.name}",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
            except Exception as e:
                st.error(f"❌ Error during replacement: {e}")
    
    with tab3:
        st.header("📊 GST Reconciliation")
        
        if st.button("📊 Run GST Reconciliation", use_container_width=True):
            try:
                with st.spinner("Processing GST reconciliation..."):
                    # Check which Tally sheet to use
                    try:
                        df_tally = pd.read_excel(st.session_state.temp_file_path, sheet_name='Tally_Replaced', header=0)
                        tally_sheet_used = "Tally_Replaced"
                        st.info("✅ Using Tally_Replaced sheet for reconciliation")
                    except:
                        df_tally = pd.read_excel(st.session_state.temp_file_path, sheet_name='Tally', header=1)
                        tally_sheet_used = "Tally"
                        st.info("✅ Using original Tally sheet for reconciliation")
                    
                    df_gstr = pd.read_excel(st.session_state.temp_file_path, sheet_name='GSTR-2A', header=1)
                    
                    # Fix columns
                    df_tally = fix_tally_columns(df_tally)
                    
                    # Add Cess column if missing
                    for df in [df_tally, df_gstr]:
                        if 'Cess' not in df.columns:
                            df['Cess'] = 0
                    
                    # Get column mappings
                    col_name = get_column(df_tally, 'Supplier')
                    col_itax = get_column(df_tally, 'Integrated Tax')
                    col_ctax = get_column(df_tally, 'Central Tax')
                    col_stax = get_column(df_tally, 'State/UT tax')
                    
                    # Check for GSTIN columns
                    try:
                        col_gstin_tally = get_column(df_tally, 'GSTIN of supplier')
                        col_gstin_gstr = get_column(df_gstr, 'GSTIN of supplier')
                        has_gstin = True
                    except KeyError:
                        has_gstin = False
                    
                    # Process data
                    df_tally_processed = df_tally.copy()
                    df_gstr_processed = df_gstr.copy()
                    
                    if has_gstin:
                        # GSTIN-based grouping
                        df_tally_processed[col_gstin_tally] = df_tally_processed[col_gstin_tally].fillna('NO_GSTIN').astype(str)
                        df_gstr_processed[col_gstin_gstr] = df_gstr_processed[col_gstin_gstr].fillna('NO_GSTIN').astype(str)
                        
                        def create_group_key(row, gstin_col, supplier_col):
                            gstin_val = str(row[gstin_col]).strip() if pd.notna(row[gstin_col]) else ''
                            supplier_val = str(row[supplier_col]).strip() if pd.notna(row[supplier_col]) else ''
                            
                            if not gstin_val or gstin_val == 'NO_GSTIN' or gstin_val == 'nan':
                                return f"SUPPLIER_{supplier_val}"
                            else:
                                return f"GSTIN_{gstin_val}"
                        
                        df_tally_processed['Group_Key'] = df_tally_processed.apply(
                            lambda row: create_group_key(row, col_gstin_tally, col_name), axis=1
                        )
                        df_gstr_processed['Group_Key'] = df_gstr_processed.apply(
                            lambda row: create_group_key(row, col_gstin_gstr, col_name), axis=1
                        )
                    else:
                        # Supplier-based grouping only
                        df_tally_processed['Group_Key'] = df_tally_processed[col_name].fillna('UNKNOWN')
                        df_gstr_processed['Group_Key'] = df_gstr_processed[col_name].fillna('UNKNOWN')
                    
                    # Group and aggregate
                    group_cols = ['Group_Key']
                    
                    df_tally_grp = df_tally_processed.groupby(group_cols).agg({
                        col_name: 'first',
                        col_itax: 'sum',
                        col_ctax: 'sum',
                        col_stax: 'sum',
                        'Cess': 'sum'
                    }).reset_index()
                    
                    df_gstr_grp = df_gstr_processed.groupby(group_cols).agg({
                        col_name: 'first',
                        col_itax: 'sum',
                        col_ctax: 'sum',
                        col_stax: 'sum',
                        'Cess': 'sum'
                    }).reset_index()
                    
                    # Create comparisons
                    df_combined = pd.merge(df_gstr_grp, df_tally_grp, on=group_cols, how='inner', suffixes=('_GSTR', '_Tally'))
                    df_combined['Integrated Tax Variance'] = df_combined[col_itax + '_GSTR'] - df_combined[col_itax + '_Tally']
                    df_combined['Central Tax Variance'] = df_combined[col_ctax + '_GSTR'] - df_combined[col_ctax + '_Tally']
                    df_combined['State/UT Tax Variance'] = df_combined[col_stax + '_GSTR'] - df_combined[col_stax + '_Tally']
                    df_combined['Cess Variance'] = df_combined['Cess_GSTR'] - df_combined['Cess_Tally']
                    
                    # Find missing entries
                    df_combined_outer = pd.merge(df_gstr_grp, df_tally_grp, on=group_cols, how='outer', suffixes=('_GSTR', '_Tally'))
                    not_in_tally = df_combined_outer[df_combined_outer[col_itax + '_Tally'].isna()]
                    not_in_gstr = df_combined_outer[df_combined_outer[col_itax + '_GSTR'].isna()]
                    
                    # Create summary
                    df_summary = pd.DataFrame({
                        'Particulars': [
                            'GST Input as per GSTR-2A Sheet',
                            f'GST Input as per {tally_sheet_used}',
                            'Variance (1-2)'
                        ],
                        'Integrated Tax': [
                            df_gstr_grp[col_itax].sum(),
                            df_tally_grp[col_itax].sum(),
                            df_gstr_grp[col_itax].sum() - df_tally_grp[col_itax].sum()
                        ],
                        'Central Tax': [
                            df_gstr_grp[col_ctax].sum(),
                            df_tally_grp[col_ctax].sum(),
                            df_gstr_grp[col_ctax].sum() - df_tally_grp[col_ctax].sum()
                        ],
                        'State/UT Tax': [
                            df_gstr_grp[col_stax].sum(),
                            df_tally_grp[col_stax].sum(),
                            df_gstr_grp[col_stax].sum() - df_tally_grp[col_stax].sum()
                        ],
                        'Cess': [
                            df_gstr_grp['Cess'].sum(),
                            df_tally_grp['Cess'].sum(),
                            df_gstr_grp['Cess'].sum() - df_tally_grp['Cess'].sum()
                        ]
                    })
                    
                    # Save results
                    with pd.ExcelWriter(st.session_state.temp_file_path, engine='openpyxl', mode='a') as writer:
                        df_summary.to_excel(writer, sheet_name='GST_Input_Summary', index=False)
                        df_combined.to_excel(writer, sheet_name='T_vs_G-2A', index=False)
                        not_in_tally.to_excel(writer, sheet_name='N_I_T_B_I_G', index=False)
                        not_in_gstr.to_excel(writer, sheet_name='N_I_G_B_I_T', index=False)
                    
                    st.success(f"✅ GST Reconciliation completed using {tally_sheet_used}!")
                    
                    # Display summary
                    st.subheader("📊 GST Input Summary")
                    st.dataframe(df_summary, use_container_width=True)
                    
                    # Display detailed comparison
                    st.subheader("📋 Detailed Comparison")
                    st.dataframe(df_combined, use_container_width=True)
                    
                    # Download button
                    with open(st.session_state.temp_file_path, 'rb') as file:
                        st.download_button(
                            label="📥 Download Reconciliation Report",
                            data=file.read(),
                            file_name=f"reconciled_{uploaded_file.name}",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
            except Exception as e:
                st.error(f"❌ Error during reconciliation: {e}")
    
    with tab4:
        st.header("🧾 Invoice-wise Reconciliation")
        
        if st.button("🧾 Run Invoice Reconciliation", use_container_width=True):
            try:
                with st.spinner("Processing invoice-wise reconciliation..."):
                    # Check which Tally sheet to use
                    try:
                        df_tally = pd.read_excel(st.session_state.temp_file_path, sheet_name='Tally_Replaced', header=0)
                        tally_sheet_used = "Tally_Replaced"
                        df_tally = fix_tally_columns(df_tally)
                    except:
                        df_tally = pd.read_excel(st.session_state.temp_file_path, sheet_name='Tally', header=1)
                        tally_sheet_used = "Tally"
                    
                    df_gstr = pd.read_excel(st.session_state.temp_file_path, sheet_name='GSTR-2A', header=1)
                    
                    # Clean columns
                    for df in [df_tally, df_gstr]:
                        df.columns = df.columns.str.strip()
                        if 'Cess' not in df.columns:
                            df['Cess'] = 0
                        df['GSTIN of supplier'] = df['GSTIN of supplier'].fillna('No GSTIN')
                    
                    # Group by invoice
                    group_columns = ['GSTIN of supplier', 'Supplier', 'Invoice number']
                    
                    def consolidate(df):
                        return df.groupby(group_columns).agg({
                            'Taxable Value': 'sum',
                            'Integrated Tax': 'sum',
                            'Central Tax': 'sum',
                            'State/UT tax': 'sum',
                            'Cess': 'sum'
                        }).reset_index()
                    
                    tally_grouped = consolidate(df_tally)
                    gstr_grouped = consolidate(df_gstr)
                    
                    # Combine and calculate variances
                    df_combined = pd.merge(gstr_grouped, tally_grouped, on=group_columns, how='outer', suffixes=('_GSTR', '_Tally')).fillna(0)
                    
                    df_combined['Taxable Value Variance'] = df_combined['Taxable Value_GSTR'] - df_combined['Taxable Value_Tally']
                    df_combined['Integrated Tax Variance'] = df_combined['Integrated Tax_GSTR'] - df_combined['Integrated Tax_Tally']
                    df_combined['Central Tax Variance'] = df_combined['Central Tax_GSTR'] - df_combined['Central Tax_Tally']
                    df_combined['State/UT Tax Variance'] = df_combined['State/UT tax_GSTR'] - df_combined['State/UT tax_Tally']
                    df_combined['Cess Variance'] = df_combined['Cess_GSTR'] - df_combined['Cess_Tally']
                    
                    # Save to Excel
                    with pd.ExcelWriter(st.session_state.temp_file_path, engine='openpyxl', mode='a') as writer:
                        df_combined.to_excel(writer, sheet_name='Invoice_Recon', index=False)
                    
                    st.success(f"✅ Invoice-wise reconciliation completed using {tally_sheet_used}!")
                    
                    # Display results
                    st.subheader("📋 Invoice-wise Reconciliation Results")
                    st.dataframe(df_combined, use_container_width=True)
                    
                    # Download button
                    with open(st.session_state.temp_file_path, 'rb') as file:
                        st.download_button(
                            label="📥 Download Invoice Reconciliation",
                            data=file.read(),
                            file_name=f"invoice_recon_{uploaded_file.name}",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
            except Exception as e:
                st.error(f"❌ Error during invoice reconciliation: {e}")

if __name__ == "__main__":
    main()
