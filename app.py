import streamlit as st
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
from io import BytesIO
from snp_data import snp_data  # Make sure this file exists and is imported correctly

# Convert SNP list to DataFrame
snp_df = pd.DataFrame(snp_data)
last_match_data = []

def save_risk_chart(risk_level):
    fig, ax = plt.subplots(figsize=(4, 2))
    risk_colors = {'High': 'red', 'Medium': 'orange', 'Low': 'green'}
    color = risk_colors.get(risk_level, 'gray')

    ax.bar(['Risk Level'], [1], color=color)
    ax.set_ylim(0, 1.5)
    ax.set_ylabel('')
    ax.set_title(f'Risk Level: {risk_level}')
    ax.axis('off')

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf

def generate_pdf_report(list_of_data_dicts, chart_buffer):
    pdf = FPDF()
    pdf.add_page()

    if not list_of_data_dicts:
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "No SNP data to report.", align="L")
    else:
        for i, data_record in enumerate(list_of_data_dicts):
            pdf.set_font("Arial", 'BU', 14)
            pdf.cell(0, 10, f"SNP Data - Genotype: {data_record.get('Genotype', 'N/A')}", ln=True)
            pdf.set_font("Arial", size=12)
            for key, value in data_record.items():
                try:
                    value_str = str(value).replace('\n', ' ').replace('\r', ' ')
                    if pdf.get_string_width(f"{key.title()}: {value_str}") > 180:
                        # Wrap long values manually
                        wrapped = "\n".join([value_str[i:i+100] for i in range(0, len(value_str), 100)])
                        pdf.multi_cell(0, 7, f"{key.title()}: {wrapped}", align="L")
                    else:
                        pdf.multi_cell(0, 7, f"{key.title()}: {value_str}", align="L")
                except Exception:
                    pdf.multi_cell(0, 7, f"{key.title()}: [Value could not be displayed]", align="L")
            pdf.ln(3)

    if chart_buffer:
        chart_path = "chart_temp.png"
        with open(chart_path, "wb") as f:
            f.write(chart_buffer.getbuffer())
        pdf.image(chart_path, x=10, w=180)
        os.remove(chart_path)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# Streamlit UI
st.title("🧬 NutriGene SNP Analyzer")

snp_input = st.text_input("Enter SNP ID (e.g., rs1801133):")

if st.button("Analyze SNP"):
    snp_id_input = snp_input.strip().lower()
    match_df = snp_df[snp_df["SNP"].str.lower() == snp_id_input]

    if not match_df.empty:
        last_match_data = match_df.to_dict('records')
        st.success(f"✅ Match Found for SNP ID: {snp_id_input.upper()}")

        for i, data_record in enumerate(last_match_data):
            st.subheader(f"🧬 Genotype: {data_record.get('Genotype', 'N/A')}")
            for key, value in data_record.items():
                st.write(f"**{key.title()}**: {value}")

        first_risk = last_match_data[0].get("Risk Level", "UNKNOWN")
        chart_buffer = save_risk_chart(first_risk)
        st.image(chart_buffer, caption="Risk Level Chart")

        # Generate PDF and store as bytes
        pdf_bytes = generate_pdf_report(last_match_data, chart_buffer)

        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name="nutrigene_report.pdf",
            mime="application/pdf"
        )
    else:
        st.error(f"❌ No matching SNP found for ID: {snp_id_input.upper()}")
