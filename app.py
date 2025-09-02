import streamlit as st
import pandas as pd
import os
from datetime import datetime
from crewai import Crew
from mortgage_crew import MortgageCrew
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
from typing import List, Optional
from pydantic import BaseModel, Field

# Initialize Crew
crew_instance = MortgageCrew()
crew = crew_instance.crew()

# Pydantic Models
class ApplicantData(BaseModel):
    name: str = Field(..., description="Applicant's full name")
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    address: str = Field(..., description="Residential address")
    income: float = Field(..., description="Annual income in GBP")
    assets: float = Field(..., description="Total asset value in GBP")
    credit_score: int = Field(..., description="Credit score (300-850)")
    property_value: float = Field(..., description="Appraised property value in GBP")
    discrepancies: List[str] = Field(default_factory=list, description="List of issues or inconsistencies")

class UnderwritingDecision(BaseModel):
    approved: bool = Field(..., description="Loan approval status")
    score: float = Field(..., description="Creditworthiness score (0-100)")
    explanation: str = Field(..., description="Detailed decision explanation based on Five C’s")
    ltv_ratio: float = Field(..., description="Loan-to-value ratio (%)")
    dti_ratio: float = Field(..., description="Debt-to-income ratio (%)")

class DocumentValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether all required documents and fields are present")
    missing_documents: List[str] = Field(default_factory=list, description="List of missing document types")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing fields")

# Simulated Crew Output Function
def run_crew(validation_only=False):
    try:
        op = crew.kickoff(inputs={'validation_only': validation_only})
        if validation_only:
            return type('CrewResult', (), {'tasks_output': [
                type('TaskOutput', (), {'output': op.tasks_output[0].pydantic})
            ]})
        else:
            return type('CrewResult', (), {'tasks_output': [
                type('TaskOutput', (), {'output': op.tasks_output[0].pydantic}),
                type('TaskOutput', (), {'output': op.tasks_output[1].pydantic}),
                type('TaskOutput', (), {'output': op.tasks_output[2].pydantic})
            ]})
    except Exception as e:
        st.error(f"Failed to process: {str(e)}")
        return None

# PDF Generation Function
def generate_pdf_report(result):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Mortgage Loan Application Report", styles['Title']))
    story.append(Spacer(1, 12))

    applicant_data = result.tasks_output[1].output
    data = [
        ["Field", "Value"],
        ["Name", applicant_data.name],
        ["Date of Birth", applicant_data.dob],
        ["Address", applicant_data.address or "Not provided"],
        ["Annual Income (GBP)", str(applicant_data.income)],
        ["Total Assets (GBP)", str(applicant_data.assets)],
        ["Credit Score", str(applicant_data.credit_score)],
        ["Property Value (GBP)", str(applicant_data.property_value)],
        ["Discrepancies", ", ".join(applicant_data.discrepancies) if applicant_data.discrepancies else "None"]
    ]
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    underwriting_data = result.tasks_output[2].output
    story.append(Paragraph("Underwriting Decision", styles['Heading2']))
    story.append(Paragraph(f"Approved: {'Yes' if underwriting_data.approved else 'No'}", styles['BodyText']))
    story.append(Paragraph(f"Score: {underwriting_data.score}/100", styles['BodyText']))
    story.append(Paragraph(f"LTV Ratio: {underwriting_data.ltv_ratio}%", styles['BodyText']))
    story.append(Paragraph(f"DTI Ratio: {underwriting_data.dti_ratio}%", styles['BodyText']))
    story.append(Paragraph(f"Explanation: {underwriting_data.explanation}", styles['BodyText']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# Display Functions
def display_applicant_data(applicant_data, key_suffix=""):
    st.header("Applicant Data")
    df = pd.DataFrame([
        ("Name", applicant_data.name),
        ("Date of Birth", applicant_data.dob),
        ("Address", applicant_data.address or "Not provided"),
        ("Annual Income (GBP)", applicant_data.income),
        ("Total Assets (GBP)", applicant_data.assets),
        ("Credit Score", applicant_data.credit_score),
        ("Property Value (GBP)", applicant_data.property_value),
        ("Discrepancies", ", ".join(applicant_data.discrepancies) if applicant_data.discrepancies else "None")
    ], columns=["Field", "Value"])

    st.markdown(
        f"""
        <div style='overflow-x: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background-color: #F5F6FA;'>
            <table style='width: 100%; border-collapse: collapse;'>
                <thead>
                    <tr style='background-color: #FF4444; color: #FFFFFF;'>
                        <th style='padding: 12px;'>{df.columns[0]}</th>
                        <th style='padding: 12px;'>{df.columns[1]}</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([
                        f"<tr style='border-bottom: 1px solid #FFD700;'>"
                        f"<td style='padding: 12px; color: #2E2E2E;'>{row[0]}</td>"
                        f"<td style='padding: 12px; color: #2E2E2E;'>{row[1]}</td>"
                        f"</tr>"
                        for row in df.itertuples(index=False)
                    ])}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_underwriting_decision(underwriting_data, key_suffix=""):
    st.header("Underwriting Decision")
    st.write(f"**Approved**: {'Yes' if underwriting_data.approved else 'No'}")
    st.write(f"**LTV Ratio**: {underwriting_data.ltv_ratio}%")
    st.write(f"**DTI Ratio**: {underwriting_data.dti_ratio}%")

    score = min(max(underwriting_data.score, 0), 100)
    circumference = 2 * 3.14159 * 70
    progress = (score / 100) * circumference
    offset = circumference - progress

    st.markdown(
        f"""
        <div class="score-pulse-container">
            <svg class="score-ring" width="160" height="160">
                <circle class="background-ring" cx="80" cy="80" r="70" />
                <circle class="progress-ring" cx="80" cy="80" r="70" 
                        stroke-dasharray="{circumference}" 
                        stroke-dashoffset="{offset}" />
            </svg>
            <div class="score-text">{score}<span>/100</span></div>
        </div>
        <p style='text-align: center; color: #2E2E2E; margin-top: 10px;'>Creditworthiness Score</p>
        """,
        unsafe_allow_html=True
    )

    with st.expander("Detailed Explanation"):
        st.markdown(f"<div style='color: #2E2E2E;'>{underwriting_data.explanation}</div>", unsafe_allow_html=True)

# Main UI
st.set_page_config(page_title="Mortgage Loan Application Dashboard", layout="centered")
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #F5F6FA;
        color: #2E2E2E;
        font-family: "Inter", "Helvetica Neue", Arial, sans-serif;
    }
    h1, .stTitle, .stTitle > h1 {
        color: #FFFFFF;
        text-shadow: 1px 1px 3px rgba(255, 68, 68, 0.5);
        font-size: 2.5em;
    }
    h2, .stHeader, .stHeader > h2 {
        color: #FFFFFF;
        text-shadow: 1px 1px 2px rgba(255, 68, 68, 0.4);
    }
    .header {
        text-align: center;
        padding: 20px;
        border-bottom: 2px solid #FFD700;
        background-color: #FF4444;
    }
    .upload-container {
        background-color: #FFFFFF;
        border: 2px solid #FF4444;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .upload-container:hover {
        border-color: #CC0000;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    .stButton>button {
        background-color: #FF4444;
        color: #FFFFFF;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #CC0000;
    }
    .score-pulse-container {
        position: relative;
        width: 160px;
        height: 160px;
        border-radius: 50%;
        margin: 20px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: pulse-glow 2s infinite ease-in-out;
        background-color: #FFFFFF;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .score-ring {
        transform: rotate(-90deg);
    }
    .background-ring {
        fill: none;
        stroke: #F5F6FA;
        stroke-width: 10;
    }
    .progress-ring {
        fill: none;
        stroke: #FF4444;
        stroke-width: 10;
        stroke-linecap: round;
    }
    .score-text {
        position: absolute;
        font-size: 2em;
        font-weight: bold;
        color: #FF4444;
    }
    .score-text span {
        font-size: 0.5em;
        color: #2E2E2E;
    }
    @keyframes pulse-glow {
        0% { box-shadow: 0 0 5px rgba(255, 68, 68, 0.3); }
        50% { box-shadow: 0 0 15px rgba(255, 68, 68, 0.6); }
        100% { box-shadow: 0 0 5px rgba(255, 68, 68, 0.3); }
    }
    .modal {
        display: block;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0,0,0,0.4);
    }
    .modal-content {
        background-color: #FFFFFF;
        margin: 15% auto;
        padding: 20px;
        border: 2px solid #FF4444;
        border-radius: 10px;
        width: 70%;
        max-width: 500px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .modal-header {
        font-size: 1.5em;
        font-weight: bold;
        color: #FF4444;
        margin-bottom: 10px;
    }
    .modal-body {
        color: #2E2E2E;
        margin-bottom: 20px;
    }
    .modal-close {
        background-color: #FF4444;
        color: #FFFFFF;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
        cursor: pointer;
        float: right;
    }
    .modal-close:hover {
        background-color: #CC0000;
    }
    </style>
    <script>
        function closeModal() {
            document.getElementById('validationModal').style.display = 'none';
        }
    </script>
    """,
    unsafe_allow_html=True
)

st.title("Mortgage Loan Application Processing")

# File Upload Section
st.markdown('<div class="upload-container">', unsafe_allow_html=True)
st.subheader("Upload Documents")
st.write("Required: ID (e.g., passport), payslip, bank statement, property appraisal")

if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []
if 'validation_result' not in st.session_state:
    st.session_state['validation_result'] = None
if 'processing_result' not in st.session_state:
    st.session_state['processing_result'] = None

uploaded_files = st.file_uploader(
    "Upload documents (PDF, JPG, JPEG, PNG)",
    type=["pdf", "jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="file_uploader"
)

if uploaded_files:
    st.session_state['uploaded_files'] = uploaded_files

if st.session_state['uploaded_files']:
    os.makedirs("./documents", exist_ok=True)
    file_paths = []
    for uploaded_file in st.session_state['uploaded_files']:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{uploaded_file.name}"
        file_path = os.path.join("./documents", unique_filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_paths.append((unique_filename, file_path, uploaded_file.size))

    if file_paths:
        with st.spinner("Validating documents..."):
            validation_result = run_crew(validation_only=True)
            if validation_result:
                st.session_state['validation_result'] = validation_result
                st.session_state['file_paths'] = [(name, path, size) for name, path, size in file_paths]

if 'validation_result' in st.session_state and st.session_state['validation_result']:
    validation_data = st.session_state['validation_result'].tasks_output[0].output
    if not validation_data.is_valid:
        st.error("Incomplete or invalid documents. Please upload the following:")
        if validation_data.missing_documents:
            st.write("**Missing Documents**: " + ", ".join(validation_data.missing_documents))
        if validation_data.missing_fields:
            st.write("**Missing Fields**: " + ", ".join(validation_data.missing_fields))
        
        # Display popup warning with corrected list rendering
        missing_docs_html = ''.join([f'<li>{doc}</li>' for doc in validation_data.missing_documents]) if validation_data.missing_documents else '<li>None</li>'
        missing_fields_html = ''.join([f'<li>{field}</li>' for field in validation_data.missing_fields]) if validation_data.missing_fields else '<li>None</li>'
        
        st.markdown(
            f"""
            <div id="validationModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">Document Validation Error</div>
                    <div class="modal-body">
                        <p><strong>Incomplete or invalid documents detected.</strong></p>
                        <p>Please upload the following to proceed:</p>
                        <p><strong>Missing Documents:</strong></p>
                        <ul>
                            {missing_docs_html}
                        </ul>
                        <p><strong>Missing Fields:</strong></p>
                        <ul>
                            {missing_fields_html}
                        </ul>
                    </div>
                    <button class="modal-close" onclick="closeModal()">Close</button>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.success("Documents validated successfully! Processing application...")
        with st.spinner("Processing mortgage application..."):
            processing_result = run_crew(validation_only=False)
            if processing_result:
                st.session_state['processing_result'] = processing_result

if 'processing_result' in st.session_state and st.session_state['processing_result']:
    result = st.session_state['processing_result']
    tabs = st.tabs(["All", "Applicant Data", "Underwriting Decision", "Download Report"])

    with tabs[0]:
        display_applicant_data(result.tasks_output[1].output, key_suffix="all")
        display_underwriting_decision(result.tasks_output[2].output, key_suffix="all")
    with tabs[1]:
        display_applicant_data(result.tasks_output[1].output, key_suffix="applicant")
    with tabs[2]:
        display_underwriting_decision(result.tasks_output[2].output, key_suffix="underwriting")
    with tabs[3]:
        st.download_button(
            "Download PDF Report",
            data=generate_pdf_report(result),
            file_name="mortgage_loan_report.pdf",
            mime="application/pdf"
        )

st.markdown('</div>', unsafe_allow_html=True)
st.markdown(
    """
    <footer>
        <p style="color: #2E2E2E;">© 2025 DCode | Mortgage Application Dashboard v1.0</p>
    </footer>
    """,
    unsafe_allow_html=True
)