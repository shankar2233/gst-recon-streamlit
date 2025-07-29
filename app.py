import pandas as pd
import streamlit as st
from fuzzywuzzy import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
import io
from datetime import datetime
import base64

# Set page config
st.set_page_config(
    page_title="GST Reconciliation Tool",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'final_matches' not in st.session_state:
    st.session_state.final_matches = []
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'processed_file' not in st.session_state:
    st.session_state.processed_file = None

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
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def create_multi_sheet_download(dfs_dict, filename):
    """Create download link for multi-sheet Excel file"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

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
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a function:", [
        "📤 Upload File & Fuzzy Matching",
        "🔄 Name Replacement",
        "📊 GST Reconciliation",
        "🧾 Invoice-wise Reconciliation"
    ])
    
    if page == "📤 Upload File & Fuzzy Matching":
        st.header("📤 Upload Excel File & Run Fuzzy Matching")
        
        uploaded_file = st.file_uploader(
            "Choose Excel file with 'Tally' and 'GSTR-2A' sheets",
            type=['xlsx', 'xls']
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
            # Threshold setting
            threshold = st.slider("Match Threshold", min_value=50, max_value=100, value=80, step=5)
            
            if st.button("🚀 Start Fuzzy Matching", type="primary"):
                try:
                    # Read Excel sheets
                    df_tally = pd.read_excel(uploaded_file, sheet_name='Tally', header=1)
                    df_gstr = pd.read_excel(uploaded_file, sheet_name='GSTR-2A', header=1)
                    
                    col_supplier_tally = get_column(df_tally, 'Supplier')
                    col_supplier_gstr = get_column(df_gstr, 'Supplier')
                    
                    tally_parties = get_raw_unique_names(df_tally[col_supplier_tally])
                    gstr_parties = get_raw_unique_names(df_gstr[col_supplier_gstr])
                    
                    st.info(f"Found {len(tally_parties)} unique suppliers in Tally and {len(gstr_parties)} unique suppliers in GSTR-2A")
                    
                    # Run matching
                    with st.spinner("Running fuzzy matching..."):
                        final_matches = two_way_match(tally_parties, gstr_parties, threshold)
                        st.session_state.final_matches = final_matches
                    
                    # Display results
                    df_result = pd.DataFrame(final_matches, columns=['GSTR-2A Party', 'Tally Party', 'Score', 'Manual Confirmation'])
                    df_result = df_result.sort_values(by=['Manual Confirmation', 'GSTR-2A Party', 'Tally Party'], ascending=[False, False, False])
                    
                    st.success("✅ Matching completed!")
                    st.subheader("Match Results")
                    st.dataframe(df_result, use_container_width=True)
                    
                    # Download link
                    st.markdown(create_download_link(df_result, "GSTR_Tally_Match.xlsx", "GSTR_Tally_Match"), unsafe_allow_html=True)
                    
                    # Summary statistics
                    matched_count = len(df_result[df_result['Manual Confirmation'] == 'Yes'])
                    st.metric("Successful Matches", matched_count, f"out of {len(df_result)} total")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    elif page == "🔄 Name Replacement":
        st.header("🔄 Replace Matched Names")
        
        if not st.session_state.final_matches:
            st.warning("⚠️ Please run fuzzy matching first!")
            return
        
        if not st.session_state.uploaded_file:
            st.warning("⚠️ Please upload a file first!")
            return
        
        if st.button("🔁 Replace Names in Tally Sheet", type="primary"):
            try:
                df_tally = pd.read_excel(st.session_state.uploaded_file, sheet_name='Tally', header=1)
                col_supplier = get_column(df_tally, 'Supplier')
                
                # Create name mapping
                name_map = {tally: gstr for gstr, tally, score, confirm in st.session_state.final_matches 
                           if gstr and tally and confirm == "Yes"}
                
                df_new = df_tally.copy()
                df_new[col_supplier] = df_new[col_supplier].apply(lambda x: name_map.get(x, x))
                
                st.success("✅ Names replaced successfully!")
                st.subheader("Updated Tally Data (Preview)")
                st.dataframe(df_new.head(10), use_container_width=True)
                
                # Download link
                st.markdown(create_download_link(df_new, "Tally_Replaced.xlsx", "Tally_Replaced"), unsafe_allow_html=True)
                
                st.info(f"Replaced {len(name_map)} supplier names in the Tally sheet.")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    elif page == "📊 GST Reconciliation":
        st.header("📊 GST Reconciliation")
        
        if not st.session_state.uploaded_file:
            st.warning("⚠️ Please upload a file first!")
            return
        
        if st.button("📊 Run GST Reconciliation", type="primary"):
            try:
                with st.spinner("Processing reconciliation..."):
                    df_tally = pd.read_excel(st.session_state.uploaded_file, sheet_name='Tally', header=1)
                    df_gstr = pd.read_excel(st.session_state.uploaded_file, sheet_name='GSTR-2A', header=1)
                    
                    # Add Cess column if missing
                    for df in [df_tally, df_gstr]:
                        if 'Cess' not in df.columns:
                            df['Cess'] = 0
                    
                    col_name = get_column(df_tally, 'Supplier')
                    col_itax = get_column(df_tally, 'Integrated Tax')
                    col_ctax = get_column(df_tally, 'Central Tax')
                    col_stax = get_column(df_tally, 'State/UT tax')
                    
                    # Try GSTIN grouping, fallback to name
                    try:
                        col_gstin_tally = get_column(df_tally, 'GSTIN of supplier')
                        col_gstin_gstr = get_column(df_gstr, 'GSTIN of supplier')
                        group_cols = [col_gstin_tally]
                    except KeyError:
                        group_cols = [col_name]
                    
                    # Fill NaN values
                    for df in [df_tally, df_gstr]:
                        for col in group_cols:
                            df[col] = df[col].fillna('UNKNOWN')
                    
                    # Group and aggregate
                    df_tally_grp = df_tally.groupby(group_cols).sum(numeric_only=True).reset_index()
                    df_gstr_grp = df_gstr.groupby(group_cols).sum(numeric_only=True).reset_index()
                    
                    # Inner join for variance calculation
                    df_combined = pd.merge(df_gstr_grp, df_tally_grp, on=group_cols, how='inner', suffixes=('_GSTR', '_Tally'))
                    df_combined['Integrated Tax Variance'] = df_combined[col_itax + '_GSTR'] - df_combined[col_itax + '_Tally']
                    df_combined['Central Tax Variance'] = df_combined[col_ctax + '_GSTR'] - df_combined[col_ctax + '_Tally']
                    df_combined['State/UT Tax Variance'] = df_combined[col_stax + '_GSTR'] - df_combined[col_stax + '_Tally']
                    
                    # Outer join for missing records
                    df_combined_outer = pd.merge(df_gstr_grp, df_tally_grp, on=group_cols, how='outer', suffixes=('_GSTR', '_Tally'))
                    not_in_tally = df_combined_outer[df_combined_outer[col_itax + '_Tally'].isna()]
                    not_in_gstr = df_combined_outer[df_combined_outer[col_itax + '_GSTR'].isna()]
                    
                    # Summary
                    df_summary = pd.DataFrame({
                        'Particulars': ['GST Input as per GSTR-2A Sheet', 'GST Input as per Tally', 'Variance (1-2)'],
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
                        ]
                    })
                    
                    # Reconciliation details
                    df_recon = pd.DataFrame({
                        'Particulars': [
                            'Not in Tally but found in GSTR-2A',
                            'Not in GSTR-2A but found in Tally',
                            'Difference in Input between Tally and GSTR-2A'
                        ],
                        'Integrated Tax': [
                            not_in_tally[col_itax + '_GSTR'].sum(),
                            not_in_gstr[col_itax + '_Tally'].sum(),
                            df_combined['Integrated Tax Variance'].sum()
                        ],
                        'Central Tax': [
                            not_in_tally[col_ctax + '_GSTR'].sum(),
                            not_in_gstr[col_ctax + '_Tally'].sum(),
                            df_combined['Central Tax Variance'].sum()
                        ],
                        'State/UT Tax': [
                            not_in_tally[col_stax + '_GSTR'].sum(),
                            not_in_gstr[col_stax + '_Tally'].sum(),
                            df_combined['State/UT Tax Variance'].sum()
                        ]
                    })
                
                st.success("✅ Reconciliation completed!")
                
                # Display results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("GST Input Summary")
                    st.dataframe(df_summary, use_container_width=True)
                
                with col2:
                    st.subheader("Reconciliation Details")
                    st.dataframe(df_recon, use_container_width=True)
                
                st.subheader("Detailed Comparison")
                st.dataframe(df_combined, use_container_width=True)
                
                # Create download with multiple sheets
                sheets_dict = {
                    'GST_Input_Summary': df_summary,
                    'Reconciliation': df_recon,
                    'T_vs_G-2A': df_combined,
                    'N_I_T_B_I_G': not_in_tally,
                    'N_I_G_B_I_T': not_in_gstr
                }
                
                st.markdown(create_multi_sheet_download(sheets_dict, "GST_Reconciliation_Report.xlsx"), unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    elif page == "🧾 Invoice-wise Reconciliation":
        st.header("🧾 Invoice-wise Reconciliation")
        
        if not st.session_state.uploaded_file:
            st.warning("⚠️ Please upload a file first!")
            return
        
        if st.button("🧾 Run Invoice-wise Reconciliation", type="primary"):
            try:
                with st.spinner("Processing invoice-wise reconciliation..."):
                    df_tally = pd.read_excel(st.session_state.uploaded_file, sheet_name='Tally', header=1)
                    df_gstr = pd.read_excel(st.session_state.uploaded_file, sheet_name='GSTR-2A', header=1)
                    
                    # Clean and prepare data
                    for df in [df_tally, df_gstr]:
                        df.columns = df.columns.str.strip()
                        if 'Cess' not in df.columns:
                            df['Cess'] = 0
                        df['GSTIN of supplier'] = df['GSTIN of supplier'].fillna('No GSTIN')
                    
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
                    
                    df_combined = pd.merge(
                        gstr_grouped, tally_grouped, 
                        on=group_columns, how='outer', 
                        suffixes=('_GSTR', '_Tally')
                    ).fillna(0)
                    
                    # Calculate variances
                    df_combined['Taxable Value Variance'] = df_combined['Taxable Value_GSTR'] - df_combined['Taxable Value_Tally']
                    df_combined['Integrated Tax Variance'] = df_combined['Integrated Tax_GSTR'] - df_combined['Integrated Tax_Tally']
                    df_combined['Central Tax Variance'] = df_combined['Central Tax_GSTR'] - df_combined['Central Tax_Tally']
                    df_combined['State/UT Tax Variance'] = df_combined['State/UT tax_GSTR'] - df_combined['State/UT tax_Tally']
                    df_combined['Cess Variance'] = df_combined['Cess_GSTR'] - df_combined['Cess_Tally']
                
                st.success("✅ Invoice-wise reconciliation completed!")
                
                # Display summary by supplier
                suppliers = df_combined['Supplier'].unique()
                selected_supplier = st.selectbox("Select Supplier to view details:", suppliers)
                
                if selected_supplier:
                    supplier_data = df_combined[df_combined['Supplier'] == selected_supplier]
                    st.subheader(f"Invoice Details for: {selected_supplier}")
                    st.dataframe(supplier_data, use_container_width=True)
                
                # Full download
                st.markdown(create_download_link(df_combined, "Invoice_Reconciliation.xlsx", "Invoice_Recon"), unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
