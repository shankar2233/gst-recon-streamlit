from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import pandas as pd
from fuzzywuzzy import fuzz, process
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO
import threading
import time
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "replace-with-your-own-secret"

selected_file = None
final_matches = []

# --- Utility Functions ---
def get_column(df, colname):
    for col in df.columns:
        if col.strip().lower() == colname.strip().lower():
            return col
    raise KeyError(f"Column '{colname}' not found. Available columns: {df.columns.tolist()}")

def get_raw_unique_names(series):
    return pd.Series(series).dropna().drop_duplicates().tolist()

# --- Fuzzy Matching Logic ---
def two_way_match(tally_list, gstr_list, threshold):
    match_map, used_tally, used_gstr, results = {}, set(), set(), []
    tally_upper = {name.upper(): name for name in tally_list}
    gstr_upper = {name.upper(): name for name in gstr_list}
    tally_keys, gstr_keys = list(tally_upper.keys()), list(gstr_upper.keys())
    total_steps = len(gstr_keys) + len(tally_keys)
    # We won't use progress_label/progress_bar in web mode

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

    results.clear()
    for gstr_name, tally_name, score in match_map.values():
        confirm = "Yes" if gstr_name and tally_name else "No"
        results.append([gstr_name, tally_name, score, confirm])
    return results

# --- Web Handlers ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

def save_temp(f):
    """Save upload to a temp file on disk and return path."""
    now = datetime.now().strftime("%Y%m%d%H%M%S%f")
    path = f"temp_{now}.xlsx"
    f.save(path)
    return path

@app.route("/match", methods=["POST"])
def match_action():
    global selected_file, final_matches
    f = request.files.get("excel_file")
    if not f:
        flash("Please upload an Excel file.", "error")
        return redirect(url_for("index"))
    try:
        threshold = int(request.form.get("threshold", "80"))
    except ValueError:
        flash("Threshold must be an integer.", "error")
        return redirect(url_for("index"))

    selected_file = save_temp(f)
    df_tally = pd.read_excel(selected_file, sheet_name='Tally', header=1)
    df_gstr  = pd.read_excel(selected_file, sheet_name='GSTR-2A', header=1)
    col_supplier_tally = get_column(df_tally, 'Supplier')
    col_supplier_gstr  = get_column(df_gstr, 'Supplier')
    tally_parties = get_raw_unique_names(df_tally[col_supplier_tally])
    gstr_parties  = get_raw_unique_names(df_gstr[col_supplier_gstr])

    final_matches = two_way_match(tally_parties, gstr_parties, threshold)
    df_result = pd.DataFrame(final_matches, columns=['GSTR-2A Party','Tally Party','Score','Manual Confirmation'])
    df_result.sort_values(by=['Manual Confirmation','GSTR-2A Party','Tally Party'],
                          ascending=[False,False,False], inplace=True)

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df_result.to_excel(writer, sheet_name='GSTR_Tally_Match', index=False)
    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name="GSTR_Tally_Match.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/replace", methods=["POST"])
def replace_action():
    global selected_file, final_matches
    if not selected_file or not final_matches:
        flash("Please run matching first.", "error")
        return redirect(url_for("index"))

    df_tally = pd.read_excel(selected_file, sheet_name='Tally', header=1)
    col_supplier = get_column(df_tally, 'Supplier')
    name_map = {tally: gstr for gstr, tally, score, confirm in final_matches if gstr and tally and confirm=="Yes"}
    df_new = df_tally.copy()
    df_new[col_supplier] = df_new[col_supplier].apply(lambda x: name_map.get(x, x))

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl', mode='w') as writer:
        df_new.to_excel(writer, sheet_name='Tally_Replaced', index=False)
    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name="Tally_Replaced.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/reconcile", methods=["POST"])
def reconcile_action():
    global selected_file
    if not selected_file:
        flash("Please run matching first.", "error")
        return redirect(url_for("index"))

    # Run in background thread to avoid timeout
    def do_recon(path):
        df_tally = pd.read_excel(path, sheet_name='Tally', header=1)
        df_gstr  = pd.read_excel(path, sheet_name='GSTR-2A', header=1)
        for df in [df_tally, df_gstr]:
            if 'Cess' not in df.columns:
                df['Cess'] = 0
        col_name  = get_column(df_tally, 'Supplier')
        col_itax  = get_column(df_tally, 'Integrated Tax')
        col_ctax  = get_column(df_tally, 'Central Tax')
        col_stax  = get_column(df_tally, 'State/UT tax')
        try:
            col_gstin_tally = get_column(df_tally, 'GSTIN of supplier')
            col_gstin_gstr  = get_column(df_gstr,  'GSTIN of supplier')
            group_cols = [col_gstin_tally]
        except KeyError:
            group_cols = [col_name]
        for df in [df_tally, df_gstr]:
            for col in group_cols:
                df[col] = df[col].fillna('UNKNOWN')
        df_tally_grp = df_tally.groupby(group_cols).sum(numeric_only=True).reset_index()
        df_gstr_grp  = df_gstr.groupby(group_cols).sum(numeric_only=True).reset_index()
        df_combined = pd.merge(df_gstr_grp, df_tally_grp, on=group_cols, how='inner', suffixes=('_GSTR','_Tally'))
        df_combined['Integrated Tax Variance'] = df_combined[col_itax+'_GSTR'] - df_combined[col_itax+'_Tally']
        df_combined['Central Tax Variance']  = df_combined[col_ctax+'_GSTR'] - df_combined[col_ctax+'_Tally']
        df_combined['State/UT Tax Variance']= df_combined[col_stax+'_GSTR'] - df_combined[col_stax+'_Tally']
        df_combined_outer = pd.merge(df_gstr_grp, df_tally_grp, on=group_cols, how='outer', suffixes=('_GSTR','_Tally'))
        not_in_tally = df_combined_outer[df_combined_outer[col_itax+'_Tally'].isna()]
        not_in_gstr  = df_combined_outer[df_combined_outer[col_itax+'_GSTR'].isna()]
        df_summary = pd.DataFrame({
            'Particulars': ['GST Input as per GSTR-2A Sheet','GST Input as per Tally','Variance (1-2)'],
            'Integrated Tax': [df_gstr_grp[col_itax].sum(), df_tally_grp[col_itax].sum(),
                               df_gstr_grp[col_itax].sum()-df_tally_grp[col_itax].sum()],
            'Central Tax':    [df_gstr_grp[col_ctax].sum(), df_tally_grp[col_ctax].sum(),
                               df_gstr_grp[col_ctax].sum()-df_tally_grp[col_ctax].sum()],
            'State/UT Tax':   [df_gstr_grp[col_stax].sum(), df_tally_grp[col_stax].sum(),
                               df_gstr_grp[col_stax].sum()-df_tally_grp[col_stax].sum()],
        })
        df_recon = pd.DataFrame({
            'Particulars': ['Not in Tally but found in GSTR-2A','Not in GSTR-2A but found in Tally','Difference in Input between Tally and GSTR-2A'],
            'Integrated Tax': [not_in_tally[col_itax+'_GSTR'].sum(), not_in_gstr[col_itax+'_Tally'].sum(), df_combined['Integrated Tax Variance'].sum()],
            'Central Tax':    [not_in_tally[col_ctax+'_GSTR'].sum(), not_in_gstr[col_ctax+'_Tally'].sum(), df_combined['Central Tax Variance'].sum()],
            'State/UT Tax':   [not_in_tally[col_stax+'_GSTR'].sum(), not_in_gstr[col_stax+'_Tally'].sum(), df_combined['State/UT Tax Variance'].sum()],
        })
        with pd.ExcelWriter(path, engine='openpyxl', mode='a') as writer:
            df_summary.to_excel(writer, sheet_name='GST_Input_Summary', index=False)
            df_recon.to_excel(writer, sheet_name='Reconciliation', index=False)
            df_combined.to_excel(writer, sheet_name='T_vs_G-2A', index=False)
            not_in_tally.to_excel(writer, sheet_name='N_I_T_B_I_G', index=False)
            not_in_gstr.to_excel(writer, sheet_name='N_I_G_B_I_T', index=False)
        wb = load_workbook(path)
        for sheet in ['GST_Input_Summary','Reconciliation','T_vs_G-2A']:
            ws = wb[sheet]
            for col in ws.iter_cols(min_row=1, max_row=1):
                for cell in col:
                    cell.font = Font(bold=True)
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = max_len + 2
        wb.save(path)

    threading.Thread(target=do_recon, args=(selected_file,)).start()
    flash("Reconciliation started in background; check the temp file.", "info")
    return redirect(url_for("index"))

@app.route("/invoice", methods=["POST"])
def invoice_action():
    global selected_file
    if not selected_file:
        flash("Please run matching first.", "error")
        return redirect(url_for("index"))

    def do_invoice(path):
        input_file = path
        df_tally = pd.read_excel(input_file, sheet_name='Tally', header=1)
        df_gstr  = pd.read_excel(input_file, sheet_name='GSTR-2A', header=1)
        for df in [df_tally, df_gstr]:
            df.columns = df.columns.str.strip()
            if 'Cess' not in df.columns:
                df['Cess'] = 0
            df['GSTIN of supplier'] = df['GSTIN of supplier'].fillna('No GSTIN')
        group_columns = ['GSTIN of supplier','Supplier','Invoice number']
        def consolidate(df):
            return df.groupby(group_columns).agg({
                'Taxable Value':'sum','Integrated Tax':'sum',
                'Central Tax':'sum','State/UT tax':'sum','Cess':'sum'
            }).reset_index()
        tally_grouped = consolidate(df_tally)
        gstr_grouped = consolidate(df_gstr)
        df_combined = pd.merge(gstr_grouped, tally_grouped, on=group_columns, how='outer', suffixes=('_GSTR','_Tally')).fillna(0)
        df_combined['Taxable Value Variance']   = df_combined['Taxable Value_GSTR'] - df_combined['Taxable Value_Tally']
        df_combined['Integrated Tax Variance']  = df_combined['Integrated Tax_GSTR'] - df_combined['Integrated Tax_Tally']
        df_combined['Central Tax Variance']     = df_combined['Central Tax_GSTR'] - df_combined['Central Tax_Tally']
        df_combined['State/UT Tax Variance']    = df_combined['State/UT tax_GSTR'] - df_combined['State/UT tax_Tally']
        df_combined['Cess Variance']            = df_combined['Cess_GSTR'] - df_combined['Cess_Tally']
        wb = load_workbook(input_file)
        sheet_name = 'Invoice_Recon'
        if sheet_name in wb.sheetnames:
            del wb[sheet_name]
        ws = wb.create_sheet(sheet_name)
        for party, party_data in df_combined.groupby('Supplier'):
            ws.append([party])
            ws.append([])
            for row in dataframe_to_rows(party_data, index=False, header=True):
                ws.append(row)
            ws.append([]); ws.append([])
        for col in ws.iter_cols(min_row=1, max_row=1):
            for cell in col:
                cell.font = Font(bold=True)
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = max_len + 2
        wb.save(input_file)

    threading.Thread(target=do_invoice, args=(selected_file,)).start()
    flash("Invoice reconciliation started in background; check the temp file.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
