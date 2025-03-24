import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.header('Executive DPD Dag Cleanup Tool', divider='rainbow')

# Define keyword mapping
keyword_mapping = {
    'C-Officer': [
        'Chief', 'CAIO', 'CAO', 'CBDO', 'CBO', 'CCO', 'CDO', 'CEO', 'CFO',
        'CGO', 'CHRO', 'CIO', 'CISO', 'CITO', 'CLO', 'CMIO', 'CMO', 'COO',
        'CPO', 'CRDO', 'CRO', 'CSO', 'CTO', 'CWO', 'Officer'
    ],
    'Senior Leadership': ['Executive Vice President', 'EVP', 'Senior Vice President', 'SVP', 'Global Head'],
    'Vice President': ['VP', 'Vice President', 'Assistant Vice President', 'AVP'],
    'Director': ['Director', 'director']
}

def map_title(title):
    """Map job titles to predefined categories."""
    for role, keywords in keyword_mapping.items():
        if any(keyword in title for keyword in keywords):
            return role
    return '-'

@st.cache_data
def process_file(file):
    """Process the uploaded file and return the cleaned DataFrame."""
    file_extension = file.name.split('.')[-1]
    
    try:
        if file_extension == 'csv':
            df = pd.read_csv(file).fillna('-')
        elif file_extension in ['xls', 'xlsx']:
            df = pd.read_excel(file).fillna('-')
        else:
            return None, "Unsupported file format. Please upload a CSV or Excel file."
    except Exception as e:
        return None, f"Error reading file: {e}"

    required_cols = {'current_start_date', 'current_end_year', 'job_title_lemmatized'}
    if not required_cols.issubset(df.columns):
        return None, f"Missing required columns: {required_cols - set(df.columns)}"

    df['current_start_date'] = pd.to_numeric(df['current_start_date'], errors='coerce')
    df = df[df['current_start_date'] >= 1999]
    df = df[df['current_end_year'].isin(['Present', '', '-'])]

    for col in ['business_function', 'functional_workload']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[\[\]"]', '', regex=True)

    df['mapping'] = df['job_title_lemmatized'].astype(str).apply(map_title)
    return df[df['mapping'] != '-'], None

uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=['csv', 'xls', 'xlsx'])

if uploaded_file:
    st.success("File uploaded successfully!")
    result_df, error_msg = process_file(uploaded_file)

    if error_msg:
        st.error(error_msg)
    elif result_df is not None:
        st.subheader("📌 Extracted Executive Preview")
        st.dataframe(result_df, use_container_width=True)

        date_str = datetime.today().strftime("%Y_%m_%d_%H_%M")
        output_filename_csv = f"executive_extracted_dpd_{date_str}.csv"
        output_filename_excel = f"executive_extracted_dpd_{date_str}.xlsx"

        csv_data = result_df.to_csv(index=False).encode('utf-8')
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Extracted Priorities')
        output_excel.seek(0)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=output_filename_csv,
                mime="text/csv"
            )
        with col2:
            st.download_button(
                label="📥 Download as Excel",
                data=output_excel,
                file_name=output_filename_excel,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.success("✅ Processed file successfully!")

st.markdown(
    """
    <style>
    .footer {position: fixed; left: 0; bottom: -17px; width: 100%; background-color: #b1b1b5; color: black; text-align: center;}
    </style>
    <div class="footer"><p>© 2025 Draup Dataflow Engine</p></div>
    """, unsafe_allow_html=True
)
