import streamlit as st
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
from io import BytesIO
from snp_data import snp_data # Make sure snp_data.py is in the same directory
from PIL import Image

# Convert SNP list to DataFrame
snp_df = pd.DataFrame(snp_data)

def save_risk_chart(risk_level):
    fig, ax = plt.subplots(figsize=(4.5, 3)) # Slightly smaller chart dimensions

    risk_mapping = {'Low': 1, 'Medium': 2, 'High': 3, 'UNKNOWN': 0}
    risk_value = risk_mapping.get(risk_level, 0)

    risk_colors = {'High': 'red', 'Medium': 'orange', 'Low': 'green', 'UNKNOWN': 'gray'}
    color = risk_colors.get(risk_level, 'gray')

    ax.bar(['Your Risk Level'], [risk_value], color=color, width=0.5, edgecolor='black', linewidth=1.5)

    ax.set_ylim(0, 3.5)
    ax.set_ylabel('Risk Severity', fontsize=10, fontweight='bold') # Smaller font
    
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(['Low', 'Medium', 'High'], fontsize=8) # Smaller font
    
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    ax.set_xticks(['Your Risk Level'])
    ax.set_xticklabels(['Your Current Risk Level'], fontsize=8) # Smaller font

    ax.set_title(f"SNP Risk Assessment: {risk_level}", fontsize=12, fontweight='bold') # Smaller font

    ax.text('Your Risk Level', risk_value + 0.1, risk_level, ha='center', va='bottom', 
            color='black', fontsize=10, fontweight='bold') # Smaller font

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=200) # Lower DPI to potentially save size/render time
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_pdf_report(list_of_data_dicts, list_of_chart_buffers):
    pdf = FPDF()
    pdf.add_page() # Start with the first page

    # --- Header Section (Made smaller) ---
    pdf.set_font("Arial", 'B', 16) # Smaller font for main title
    pdf.cell(0, 10, "NutriGene SNP Analysis Report", ln=True, align="C") # Smaller cell height
    pdf.set_font("Arial", '', 8) # Smaller font for date
    pdf.cell(0, 4, f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="R") # Smaller cell height
    pdf.ln(3) # Very small spacing after header

    content_width = pdf.w - (2 * pdf.l_margin)
    line_height_very_small_text = 6 # Adjusted line height for very small font

    print(f"\n--- PDF Generation Debug ---")
    print(f"Initial Y after header: {pdf.get_y():.2f} mm")
    print(f"Total Page Height: {pdf.h:.2f} mm, Bottom Margin: {pdf.b_margin:.2f} mm")
    # Remaining space before the physical bottom of the page, accounting for a typical footer height
    usable_page_height_remaining = pdf.h - pdf.b_margin - pdf.get_y() - 15 # Approx footer height 15mm
    print(f"Usable Y space from current Y to bottom margin (considering footer): {usable_page_height_remaining:.2f} mm")

    if not list_of_data_dicts:
        pdf.set_font("Arial", size=9)
        pdf.multi_cell(content_width, line_height_very_small_text, "No SNP data to report.", align="L")
    else:
        for i, data_record in enumerate(list_of_data_dicts):
            # For subsequent genotypes, always add a new page to prevent extreme cramming and maintain readability.
            # This means if rs1801133 is searched, it will produce 3 pages.
            if i > 0:
                print(f"\n--- Genotype {i+1} ---")
                print(f"Current Y before adding new page for next genotype: {pdf.get_y():.2f} mm")
                pdf.add_page()
                pdf.ln(5) # Minimal top margin on new page
                print(f"New page added for Genotype {i+1}. Current Y: {pdf.get_y():.2f} mm")

            # --- DEBUGGING LINE START ---
            print(f"PDF Output: Processing Genotype {data_record.get('Genotype', 'N/A')} for SNP {data_record.get('SNP', 'N/A').upper()}")
            # --- DEBUGGING LINE END ---

            pdf.set_font("Arial", 'BU', 12) # Smaller font
            pdf.cell(0, 8, f"Genotype: {data_record.get('Genotype', 'N/A')} (SNP: {data_record.get('SNP', 'N/A').upper()})", ln=True) # Smaller cell height
            pdf.ln(2) # Minimal spacing

            ordered_keys = ["Description", "Risk Level", "Dietary Recommendations", "Lifestyle Recommendations"]
            
            for key_title in ordered_keys:
                if key_title in data_record:
                    pdf.set_font("Arial", 'B', 9) # Smaller font for section titles
                    pdf.cell(content_width, line_height_very_small_text, f"{key_title.replace('_', ' ').title()}:", ln=True)
                    pdf.set_font("Arial", '', 8) # Smallest font for content text
                    
                    value = data_record[key_title]
                    value_str = str(value).replace('\n', ' ').replace('\r', ' ')
                    
                    start_y_multicell = pdf.get_y()
                    pdf.multi_cell(content_width, line_height_very_small_text, value_str, align="J") # Justify to pack tightly
                    height_taken_multicell = pdf.get_y() - start_y_multicell
                    print(f"  Item '{key_title}': Height taken {height_taken_multicell:.2f} mm. Current Y: {pdf.get_y():.2f} mm")
                    pdf.ln(0.5) # Extremely minimal spacing

            other_keys_present = [k for k in data_record if k not in ordered_keys and k.lower() != 'snp' and k.lower() != 'genotype']
            if other_keys_present:
                pdf.set_font("Arial", 'B', 9) # Smaller font
                pdf.cell(content_width, line_height_very_small_text, "Additional Details:", ln=True)
                pdf.set_font("Arial", '', 8) # Smallest font
                for key in other_keys_present:
                    value = data_record[key]
                    value_str = str(value).replace('\n', ' ').replace('\r', ' ')
                    
                    pdf.set_font("Arial", 'B', 8) # Smaller font for key
                    pdf.write(line_height_very_small_text, f"{key.replace('_', ' ').title()}: ")
                    pdf.set_font("Arial", '', 8) # Smallest font for value
                    remaining_width = content_width - pdf.get_string_width(f"{key.replace('_', ' ').title()}: ")
                    
                    start_y_inline_multicell = pdf.get_y()
                    pdf.multi_cell(remaining_width, line_height_very_small_text, value_str, align="L")
                    height_taken_inline_multicell = pdf.get_y() - start_y_inline_multicell
                    print(f"  Item '{key}': Height taken {height_taken_inline_multicell:.2f} mm. Current Y: {pdf.get_y():.2f} mm")
                    pdf.ln(0.5) # Extremely minimal spacing

            # Minimal space before the chart
            pdf.ln(1) 

            # --- Chart placement (Inside the loop, for current genotype) ---
            if i < len(list_of_chart_buffers) and list_of_chart_buffers[i]:
                chart_buffer = list_of_chart_buffers[i]
                chart_path = "chart_temp.png"
                img = None
                try:
                    with open(chart_path, "wb") as f:
                        f.write(chart_buffer.getbuffer())
                    
                    try:
                        img = Image.open(chart_path)
                        original_img_width_px, original_img_height_px = img.size
                        image_width_on_page = content_width * 0.55 # EVEN MORE REDUCED CHART SIZE (e.g., 55% of content width)
                        
                        estimated_chart_height_mm = (original_img_height_px / original_img_width_px) * image_width_on_page
                        # Minimal padding buffer
                        estimated_chart_height_with_padding = estimated_chart_height_mm + 2 # Minimal padding

                        print(f"\n--- Chart Placement Debug (Genotype {i+1}) ---")
                        print(f"Current Y before chart check: {pdf.get_y():.2f} mm")
                        print(f"Estimated Chart Height (including its padding): {estimated_chart_height_with_padding:.2f} mm")
                        
                        # Remaining space on the page, ensuring enough for chart AND footer.
                        # Footer takes ~10mm line height, plus 5mm bottom margin = 15mm.
                        remaining_space_for_content_before_footer = pdf.h - pdf.get_y() - pdf.b_margin 
                        
                        print(f"Available Y space from current Y to bottom margin: {remaining_space_for_content_before_footer:.2f} mm")

                        # If remaining space is less than what the chart needs PLUS a small buffer for safety, add a new page.
                        # The 5mm buffer here is crucial to prevent the chart from *just* overflowing and causing a blank page.
                        if remaining_space_for_content_before_footer < (estimated_chart_height_with_padding + 5): 
                            print(f"DEBUG: Condition met: Adding new page for chart. Remaining space ({remaining_space_for_content_before_footer:.2f}) < Minimum required ({estimated_chart_height_with_padding + 5:.2f}).")
                            pdf.add_page()
                            pdf.ln(5) # Minimal top margin on new page for chart
                            print(f"New page for chart. Current Y: {pdf.get_y():.2f} mm")
                        else:
                            print("DEBUG: Chart fits on current page and remaining space is sufficient.")

                        # Calculate X position to center the image
                        x_position = pdf.l_margin + (content_width - image_width_on_page) / 2
                        
                        pdf.image(chart_path, x=x_position, w=image_width_on_page)
                        pdf.ln(1) # Minimal space after image
                        print(f"Chart added. Current Y: {pdf.get_y():.2f} mm")

                    finally:
                        if img:
                            img.close()

                except Exception as e:
                    print(f"ERROR: Could not add chart for Genotype {i+1} to PDF: {e}")
                    pdf.set_font("Arial", size=8)
                    pdf.multi_cell(content_width, line_height_very_small_text, f"Error: Could not render risk level chart for Genotype {i+1}.", align="C")
                finally:
                    # Clean up the temporary chart file
                    if os.path.exists(chart_path):
                        try:
                            os.remove(chart_path)
                        except PermissionError as pe:
                            print(f"WARNING: Could not remove temporary chart file '{chart_path}': {pe}")
                            print("This might happen if the file is still locked by an external process. You may need to manually delete it later.")
                        except Exception as e_remove:
                            print(f"ERROR: Unexpected error when removing '{chart_path}': {e_remove}")
            # --- End Chart Placement for current genotype ---
    
    # --- Footer ---
    # The footer will always attempt to be at -15mm from the bottom of the CURRENT page.
    # Because of the tighter content packing and page break logic, this should now be on the
    # last content page, without triggering a blank page just for the footer.
    pdf.set_y(-15) 
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, f"Page {pdf.page_no()}/{{nb}}", align="C")
    pdf.alias_nb_pages() # This is crucial for {{nb}} to show total pages

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# Streamlit UI (No changes needed here as it passes list_of_data_dicts and list_of_chart_buffers)
st.set_page_config(page_title="NutriGene", page_icon="🧬", layout="centered")

# --- Custom Dark Font + Light Background Style ---
st.markdown("""
    <style>
    body, .main {
        background-color: #f0f4f8;
        color: #1a1a1a !important;
    }

    html, body, div, span, app, h1, h2, h3, h4, h5, h6, p, a, li, td, th, label, input, select, option, textarea {
        color: #1a1a1a !important;
    }

    .main-title {
        font-size: 40px;
        font-weight: 900;
        text-align: center;
        color: #1b3b5f !important;
        margin-bottom: 5px;
    }

    .subtext {
        text-align: center;
        font-size: 18px;
        color: #333 !important;
        margin-bottom: 30px;
    }

    .snp-input-label {
        font-size: 18px;
        font-weight: 600;
        color: #1a1a1a !important;
        margin-top: 15px;
    }

    .footer {
        margin-top: 60px;
        text-align: center;
        font-size: 13px;
        color: #555 !important;
        border-top: 1px solid #ccc;
        padding-top: 20px;
    }

    .streamlit-expanderHeader {
        color: #333 !important;
        font-weight: 700;
    }

    .streamlit-expanderContent {
        color: #1a1a1a !important;
    }

    /* --- Input Field Styling --- */
    /* Removed conflicting and incorrect color declarations */
    .stTextInput > div > div > input { /* This targets the input field where you type */
        background-color: #f8f8f8 !important; /* Light grey/off-white background for input box */
        color: #1a1a1a !important; /* Dark text for entered value, visible on light background */
        border: 2px solid #1b3b5f !important; /* Dark blue border */
        border-radius: 5px;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input::placeholder { /* For placeholder text */
        color: #555555 !important; /* Medium grey for placeholder, visible on light background */
        opacity: 1; /* Ensure full opacity for placeholder */
    }

    .stTextInput > div > div > input:focus {
        border-color: #2a5a8a !important; /* Lighter blue border on focus */
        box-shadow: 0 0 0 0.1rem rgba(27, 59, 95, 0.5) !important; /* Subtle blue glow on focus */
        outline: none !important;
    }
    /* --- End Input Field Styling --- */


    /* --- Button Styling --- */
    .stButton > button {
        background-color: #2a5a8a; /* Dark blue background */
        color: #ffffff !important; /* White text */
        border: 2px solid #1b3b5f !important; /* Solid border matching background, made thicker */
        border-radius: 5px; /* Slightly rounded corners */
        padding: 10px 20px; /* More padding */
        font-size: 16px; /* Larger font size */
        font-weight: bold; /* Bold text */
        cursor: pointer; /* Pointer cursor on hover */
        transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease; /* Smooth transition */
        outline: none !important; /* Remove default outline */
    }

    .stButton > button:hover {
        background-color: #50c7c7; /* Slightly lighter blue on hover */
        color: #ffffff !important;
        border-color: #2a5a8a !important; /* Hover border matches hover background */
    }

    .stButton > button:focus {
        border-color: #2a5a8a !important; /* Lighter blue border on focus */
        box-shadow: 0 0 0 0.1rem rgba(27, 59, 95, 0.5) !important; /* Subtle blue glow on focus */
        outline: none !important; /* Remove default outline */
    }
    /* --- End Button Styling --- */

    .css-1c7y2kd {  /* Used in data text sometimes */
        color: #1a1a1a !important;
    }
     /* --- Download Button Specific Styling --- */
    .stDownloadButton > button { /* This targets the button element within a download button container */
        background-color: #28a745 !important; /* Green background */
        color: #ffffff !important; /* White text */
        border: 2px solid #218838 !important; /* Darker green border */
        box-shadow: 0 4px 8px rgba(0,123,255,0.2); /* Subtle blueish shadow for distinction */
    }

    .stDownloadButton > button:hover {
        background-color: #218838 !important; /* Darker green on hover */
        border-color: #1e7e34 !important; /* Even darker green border on hover */
        color: #ffffff !important; /* Keep white text */
        box-shadow: 0 6px 12px rgba(0,123,255,0.3);
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Title & Subtitle ----------
st.markdown('<div class="main-title">🧬 NutriGene</div>', unsafe_allow_html=True)
st.markdown('<div class="subtext">Explore your genetic makeup and nutritional insights using SNP data</div>', unsafe_allow_html=True)

# ---------- ℹ️ About Section ----------
with st.expander("About"):
    st.markdown("""
    **NutriGene SNP Analyzer** is a personalized nutrigenomics tool.  
    It allows you to enter known SNP IDs (like `rs1801133`) and learn:
    - 🧬 The genotype and health relevance  
    - 🥦 Key nutrients affected by your genes  
    - 🍛 Pakistani food recommendations  
    - ⚠️ A **Risk Level** score with a visual chart  

    ✅ PDF report generation is available for download.
    """)

# ---------- SNP Input ----------
st.markdown('<p class="snp-input-label">🔍 Enter SNP ID (e.g., rs1801133):</p>', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    snp_input = st.text_input("", placeholder="Type SNP ID here...")

# ---------- Analyze Button ----------
center_btn_col = st.columns([1, 1, 1])[1]
with center_btn_col:
    if st.button("🔬 Analyze SNP", use_container_width=True):
        snp_id_input = snp_input.strip().lower()
        match_df = snp_df[snp_df["SNP"].str.lower() == snp_id_input]

        if not match_df.empty:
            list_of_data_dicts = match_df.to_dict('records') 
            list_of_chart_buffers = []

            for i, data_record in enumerate(list_of_data_dicts):
                risk = data_record.get("Risk Level", "UNKNOWN")
                chart_buf = save_risk_chart(risk)
                list_of_chart_buffers.append(chart_buf)

            st.success(f"✅ Match Found for SNP ID: {snp_id_input.upper()}")

            for i, data_record in enumerate(list_of_data_dicts):
                st.markdown("---")
                st.subheader(f"🧬 Genotype: **{data_record.get('Genotype', 'N/A')}**")

                data_cols = st.columns(2)
                for idx, (key, value) in enumerate(data_record.items()):
                    if key.lower() != 'snp':
                        with data_cols[idx % 2]:
                            st.markdown(f"**{key.replace('_', ' ').title()}**: {value}")

                if i < len(list_of_chart_buffers):
                    st.image(list_of_chart_buffers[i], caption=f"📊 Risk Level: {data_record.get('Risk Level', 'N/A')}")

            # PDF Report
            pdf_bytes = generate_pdf_report(list_of_data_dicts, list_of_chart_buffers)
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"nutrigene_report_{snp_id_input}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error(f"❌ No matching SNP found for ID: **{snp_id_input.upper()}**. Please check and try again.")

# ---------- Footer ----------
st.markdown('<div class="footer">© 2025 NutriGene — Developed by Eman & Memoona | Powered by Streamlit</div>', unsafe_allow_html=True)
