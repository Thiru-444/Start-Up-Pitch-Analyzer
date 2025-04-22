import streamlit as st
import PyPDF2
import docx
import io
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# --- Page Configuration ---
st.set_page_config(
    page_title="Startup Pitch Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Enhanced UI ---
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stApp {
        background-color: #121212; /* Dark background */
        color: #e0e0e0; /* Light text for dark background */
    }
    h1, h2, h3 {
        color: #90caf9; /* Light blue for dark mode */
    }
    .analysis-section {
        background-color: #1e1e1e; /* Darker section background */
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        color: #e0e0e0; /* Light text */
    }
    .section-header {
        color: #90caf9; /* Light blue for dark mode */
        font-weight: bold;
        font-size: 1.1em;
        border-bottom: 2px solid #333333; /* Darker border */
        padding-bottom: 8px;
        margin-bottom: 15px;
    }
    .stButton button {
        background-color: #1976d2; /* Blue button */
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #2196f3; /* Lighter blue on hover */
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .sidebar .stButton button {
        width: 100%; /* Make sidebar button full width */
    }
    .stTextArea textarea {
        font-family: monospace;
        background-color: #2d2d2d; /* Dark textarea */
        color: #e0e0e0; /* Light text */
        border-radius: 8px;
    }
    /* Style for file uploader */
    .stFileUploader {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 2px dashed #444;
        transition: all 0.3s ease;
    }
    .stFileUploader:hover {
        border-color: #90caf9;
    }
    /* Style for expanders */
    .streamlit-expanderHeader {
        background-color: #1e1e1e;
        color: #90caf9;
        border-radius: 8px;
        padding: 10px !important;
    }
    .streamlit-expanderContent {
        background-color: #1e1e1e;
        color: #e0e0e0;
        border-radius: 0 0 8px 8px;
        padding: 15px !important;
    }
    /* Style for info/success/error/warning boxes */
    .stAlert {
        background-color: #1e1e1e;
        border-radius: 8px;
    }

    /* Card-like sections for analysis results */
    .result-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 4px solid #1976d2;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    /* File details card */
    .file-details-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        border-left: 4px solid #90caf9;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #1976d2 !important;
    }

    /* Analysis results styling */
    .analysis-result h2 {
        color: #90caf9;
        border-bottom: 2px solid #333;
        padding-bottom: 8px;
        margin-top: 25px;
    }
    .analysis-result h3 {
        color: #64b5f6;
        margin-top: 20px;
    }
    .analysis-result p {
        line-height: 1.6;
    }

    /* Download button styling */
    .download-button {
        margin-top: 20px;
        text-align: center;
    }
    .download-button button {
        background-color: #388e3c !important;
        transition: all 0.3s ease;
    }
    .download-button button:hover {
        background-color: #4caf50 !important;
        transform: translateY(-2px);
    }

    /* Sidebar animation */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    .sidebar-animation {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }

    .rocket-animation {
        font-size: 40px;
        animation: float 3s ease-in-out infinite;
    }

    /* Loading container that stays visible */
    .loading-container {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.7);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .loading-spinner {
        width: 80px;
        height: 80px;
        margin-bottom: 20px;
    }

    .loading-spinner:after {
        content: " ";
        display: block;
        width: 64px;
        height: 64px;
        margin: 8px;
        border-radius: 50%;
        border: 6px solid #1976d2;
        border-color: #1976d2 transparent #1976d2 transparent;
        animation: loading-spinner 1.2s linear infinite;
    }

    @keyframes loading-spinner {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loading-text {
        color: white;
        font-size: 18px;
        text-align: center;
    }

    /* Status indicator in sidebar */
    .api-status-animation {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 15px 0;
    }

    .pulse {
        display: inline-block;
        width: 15px;
        height: 15px;
        border-radius: 50%;
        background: #4CAF50;
        box-shadow: 0 0 0 rgba(76, 175, 80, 0.4);
        animation: pulse 2s infinite;
        margin-right: 10px;
    }

    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(76, 175, 80, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
        }
    }
</style>
""", unsafe_allow_html=True)


# --- Text Extraction Functions ---
def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file object."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"  # Add newline between pages
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None


def extract_text_from_docx(docx_file):
    """Extracts text from a DOCX file object."""
    try:
        doc = docx.Document(docx_file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return None


# --- Gemini API Interaction ---
def analyze_pitch(pitch_text, api_key):
    """Analyzes pitch text using Google Gemini API."""
    if not api_key:
        return "❌ Error: Gemini API key not configured. Please set the GEMINI_API_KEY environment variable."

    try:
        genai.configure(api_key=api_key)
        # Use a known valid model like 'gemini-1.5-flash' or 'gemini-pro'
        model = genai.GenerativeModel('gemini-1.5-flash')  # Or 'gemini-pro'

        prompt = f"""You are an expert startup pitch deck analyst for venture capitalists.

Analyze the provided startup pitch text thoroughly and extract the following key information. Present the output clearly, using the specified headings. Be concise but comprehensive for each section. If information for a section is not found, state "Information not found in the provided text".

1.  **Problem Statement:** What specific problem is the startup solving? Who experiences this problem?
2.  **Solution Offered:** What is the startup's product or service? How does it solve the identified problem?
3.  **Target Market:** Who are the primary customers? What is the estimated size or characteristics of this market?
4.  **Unique Value Proposition (UVP):** What makes the startup's solution different or better than existing alternatives? What is its key differentiator?
5.  **Business Model:** How does the startup plan to make money? (e.g., SaaS, transaction fees, advertising, hardware sales)
6.  **Traction & Validation:** Is there any evidence that the solution works or that customers want it? (e.g., users, revenue, pilots, LOIs, partnerships)
7.  **Go-To-Market Strategy:** How does the startup plan to reach its target market and acquire customers?
8.  **Team:** Brief overview of the key team members and their relevant experience.
9.  **Ask:** What is the startup seeking in this round? (e.g., funding amount, key hires, strategic partnerships)

--- START OF PITCH TEXT ---
{pitch_text}
--- END OF PITCH TEXT ---

Provide the analysis below using markdown formatting with the specified headings (e.g., `**Problem Statement:**`).
"""
        response = model.generate_content(prompt)
        # Accessing the text part correctly (handle potential streaming/parts)
        if hasattr(response, 'parts') and response.parts:
            return response.parts[0].text
        elif hasattr(response, 'text'):
            # Fallback in case the structure is simpler or there's no content
            return response.text
        else:
            st.warning(
                "Could not find text in the expected place in the Gemini response. Returning the full response object.")
            return str(response)  # Return string representation if unsure

    except AttributeError as ae:
        # Handle cases where the response structure might differ slightly
        if hasattr(response, 'text'):
            return response.text
        else:
            st.error(f"❌ Error parsing Gemini response structure: {ae}. Response object: {response}")
            return f"❌ Error parsing Gemini response structure: {ae}"
    except Exception as e:
        # Catch other potential API errors (authentication, rate limits, etc.)
        st.error(f"❌ Error analyzing pitch with Gemini: {e}")
        # Check for specific authentication errors if possible (needs inspection of google.generativeai exceptions)
        if "API key not valid" in str(e):
            st.error("Please check if your GEMINI_API_KEY is correct and active.")
        return f"❌ Error analyzing pitch with Gemini: {str(e)}"


# --- Format Analysis Results ---
def format_analysis_results(analysis_text):
    """Format the analysis results into a more readable format with styling"""
    # Split the text by section headers
    sections = [
        "Problem Statement", "Solution Offered", "Target Market",
        "Unique Value Proposition", "Business Model", "Traction & Validation",
        "Go-To-Market Strategy", "Team", "Ask"
    ]

    formatted_html = '<div class="analysis-result">'

    # Add title
    formatted_html += '<h2>Pitch Analysis Results</h2>'

    # Process the raw text
    current_text = analysis_text

    for section in sections:
        # Look for the section header in various formats
        patterns = [
            f"**{section}:**",
            f"**{section}**:",
            f"### {section}:",
            f"### {section}"
        ]

        section_start = None
        for pattern in patterns:
            if pattern in current_text:
                section_start = current_text.find(pattern)
                break

        if section_start is not None:
            # Extract section content
            section_text = current_text[section_start:]

            # Find the end of this section (start of next section or end of text)
            section_end = len(section_text)
            for next_section in sections:
                if next_section != section:
                    for pattern in patterns:
                        pattern_modified = pattern.replace(section, next_section)
                        next_start = section_text.find(pattern_modified)
                        if next_start > 0 and next_start < section_end:
                            section_end = next_start

            section_content = section_text[:section_end].strip()

            # Clean up the section header from the content
            for pattern in patterns:
                if pattern in section_content:
                    section_content = section_content.replace(pattern, "").strip()

            # Add the formatted section to the HTML
            formatted_html += f'<div class="result-card">'
            formatted_html += f'<h3>{section}</h3>'
            formatted_html += f'<p>{section_content}</p>'
            formatted_html += '</div>'

    formatted_html += '</div>'
    return formatted_html


# --- Persistent Loading Animation ---
def show_loading_animation():
    """Display a persistent loading animation that stays visible"""
    loading_placeholder = st.empty()
    loading_placeholder.markdown(
        """
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <div class="loading-text">Analyzing your pitch...</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    return loading_placeholder


# --- Sidebar with Animated Icon ---
with st.sidebar:
    st.title("Configuration")

    # Add animated rocket in sidebar
    st.markdown(
        """
        <div class="sidebar-animation">
            <div class="rocket-animation">🚀</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # API Status with just the animation (no text)
    if api_key:
        st.markdown(
            """
            <div class="api-status-animation">
                <div class="pulse"></div>
                <span>API Ready</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="api-status-animation">
                <div style="width: 15px; height: 15px; border-radius: 50%; background: #F44336; margin-right: 10px;"></div>
                <span>API Not Configured</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This tool uses Google's Gemini AI to analyze startup pitch documents and extract key information relevant to investors.

    The analysis covers:
    - Problem Statement
    - Solution Offered
    - Target Market
    - Unique Value Proposition
    - Business Model
    - Traction & Validation
    - Go-To-Market Strategy
    - Team Information
    - Funding Ask
    """)
    st.markdown("---")

    # Add a visually appealing sidebar footer
    st.markdown(
        """
        <div style="position: absolute; bottom: 20px; left: 20px; right: 20px; text-align: center;">
            <p style="color: #90caf9; font-size: 12px;">
                <span style="color: #666;">© 2025 Startup Analyzer</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Main App Interface ---
st.title("🚀 Startup Pitch Analyzer")
st.markdown("""
Upload your startup pitch deck (PDF or DOCX) to extract key insights based on standard investor criteria. 
Our AI-powered analysis helps you understand how VCs will evaluate your pitch.
""")

# Create a more visually appealing file uploader
uploaded_file = st.file_uploader(
    "Upload your pitch document",
    type=["pdf", "docx"],
    help="Supports PDF (.pdf) and Word (.docx) files."
)

pitch_text = None  # Initialize pitch_text

if uploaded_file is not None:
    file_details = {"Filename": uploaded_file.name, "Type": uploaded_file.type,
                    "Size (KB)": f"{uploaded_file.size / 1024:.2f}"}

    # Display file details in a more user-friendly card format
    st.markdown(
        f"""
        <div class="file-details-card">
            <h3>📄 File Details</h3>
            <p><strong>Filename:</strong> {file_details['Filename']}</p>
            <p><strong>Type:</strong> {file_details['Type']}</p>
            <p><strong>Size:</strong> {file_details['Size (KB)']} KB</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Process the uploaded file with a visual indicator
    with st.spinner("📄 Processing document..."):
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        # Read file bytes into memory - Use with statement for automatic closing
        with io.BytesIO(uploaded_file.getvalue()) as file_bytes:
            if file_extension == ".pdf":
                pitch_text = extract_text_from_pdf(file_bytes)
            elif file_extension == ".docx":
                pitch_text = extract_text_from_docx(file_bytes)
            else:
                # This case should ideally not be reached due to the 'type' filter, but good practice.
                st.error("Unsupported file format. Please upload a PDF or DOCX file.")

    if pitch_text:
        # Add Analyze button with enhanced styling
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button("🔍 Analyze Pitch", use_container_width=True)

        if analyze_button:
            if not api_key:
                st.error(
                    "❌ Gemini API key not found. Cannot analyze. Please set the `GEMINI_API_KEY` in your environment (e.g., in a `.env` file).")
            elif len(pitch_text.strip()) < 50:  # Basic check for meaningful content
                st.warning("⚠️ The extracted text seems very short. Analysis quality might be limited.")
                analysis_result = "❌ Error: Extracted text is too short to provide a meaningful analysis."
            else:
                # Show persistent loading animation
                loading_placeholder = show_loading_animation()

                # Perform the actual analysis
                analysis_result = analyze_pitch(pitch_text, api_key)

                # Remove loading animation when done
                loading_placeholder.empty()

            # Check analysis result *after* button press and potential API call
            if analysis_result:
                if not analysis_result.startswith("❌"):
                    st.success("✅ Analysis Complete!")

                    # Format and display the results in a more visually appealing way
                    formatted_results = format_analysis_results(analysis_result)
                    st.markdown(formatted_results, unsafe_allow_html=True)

                    # Offer download with enhanced styling
                    st.markdown("<div class='download-button'>", unsafe_allow_html=True)
                    try:
                        file_base_name = os.path.splitext(uploaded_file.name)[0]
                    except Exception:
                        file_base_name = "pitch_document"  # Fallback filename base

                    st.download_button(
                        label="⬇️ Download Full Analysis",
                        data=analysis_result,
                        file_name=f"{file_base_name}_analysis.txt",
                        mime="text/plain"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                else:
                    # Display the error message returned by analyze_pitch or the short text warning
                    st.error(analysis_result)  # Error message already formatted with ❌

            elif not analysis_result and pitch_text:  # If analysis failed without specific error message
                st.error("❌ Analysis failed. Received an empty or unexpected response from the API.")

    elif uploaded_file:  # If upload happened but text extraction failed
        st.error(
            "Could not extract text from the uploaded file. It might be corrupted, password-protected, or image-based.")

else:
    # Welcome message with better styling
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 20px; background-color: #1e1e1e; border-radius: 10px; margin: 20px 0;">
            <h2 style="color: #90caf9;">👋 Welcome to Startup Pitch Analyzer!</h2>
            <p style="font-size: 18px; margin: 20px 0;">
                Upload your pitch document to get AI-powered insights that help you understand how investors will evaluate your startup.
            </p>
            <div style="display: flex; justify-content: center; margin-top: 30px;">
                <div style="background-color: #2d2d2d; padding: 15px; border-radius: 8px; width: 80%; max-width: 600px;">
                    <p style="text-align: left; margin: 0;">
                        <span style="color: #64b5f6;">✓</span> Problem Statement Analysis<br>
                        <span style="color: #64b5f6;">✓</span> Solution Evaluation<br>
                        <span style="color: #64b5f6;">✓</span> Market Opportunity Assessment<br>
                        <span style="color: #64b5f6;">✓</span> Business Model Review<br>
                        <span style="color: #64b5f6;">✓</span> Competitive Advantage Identification
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
