
import os                      
from dotenv import load_dotenv 
load_dotenv()                 

import streamlit as st
import fitz # PyMuPDF

import json
import io
import requests
import time
import os

# --- Gemini API Configuration ---
# 1. Use st.secrets (for Streamlit Cloud) or os.environ (for local .env)
# The key for the secret should be 'GEMINI_API_KEY'
try:
    # Try reading from Streamlit Secrets (for deployment)
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (KeyError, AttributeError):
    # Fallback to os.environ (for local .env or system environment)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # Optional: Display a warning if the key is missing in both places
    st.error("GEMINI_API_KEY not found. Please configure it in Streamlit Secrets or your local .env file.")
    st.stop()

GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
# Build the URL with the retrieved API key
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
# --- End of Gemini API Configuration ---


# --- Core AI Interaction Function ---
def ai_edit_text(document_text, user_instruction):
    """
    Uses the Gemini API to intelligently determine the find and replace strings.

    Args:
        document_text (str): The full text extracted from the PDF.
        user_instruction (str): The user's instruction for the edit (e.g., "Change $25.44 to $35.67").

    Returns:
        list: A list of replacement objects or None if an error occurs.
    """
    st.info("AI Analysis in progress... Determining exact changes.")

    # 1. System Instruction: Define the AI's role and output format strictly.
    system_prompt = (
        "You are a highly specialized text extraction and replacement AI. "
        "Your task is to analyze the provided document text and the user's edit instruction. "
        "You must identify the exact text string currently present in the document that needs to be replaced ('find_text') "
        "and the exact new text string that should replace it ('replace_text'). "
        "Respond ONLY with a single JSON array containing objects with these two keys. "
        "Do not include any other commentary, formatting, or text outside the JSON structure. "
        "Ensure the 'find_text' and 'replace_text' are minimal and precise for accurate PDF manipulation. "
        "Example output for the instruction 'Change the rate from $25.44 to $35.67': "
        '[{"find_text": "$25.44", "replace_text": "$35.67"}]'
    )

    # 2. User Prompt: Combine the document content and the instruction.
    user_query = f"DOCUMENT CONTENT:\n---\n{document_text}\n---\nUSER INSTRUCTION: {user_instruction}\n"

    # 3. Define the structured JSON output schema
    json_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "find_text": {"type": "STRING", "description": "The exact current text string to locate and replace."},
                "replace_text": {"type": "STRING", "description": "The exact new text string to insert in place of the old one."}
            },
            "required": ["find_text", "replace_text"]
        }
    }

    # 4. Construct the API payload
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": json_schema
        }
    }

    # 5. Call the API with exponential backoff for robustness
    max_retries = 3
    delay = 1

    for attempt in range(max_retries):
        try:
            response = requests.post(
                GEMINI_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )

            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            result = response.json()
            json_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text')

            if json_text:
                # The response is a JSON string of the array
                replacements = json.loads(json_text)
                if isinstance(replacements, list) and all(isinstance(r, dict) and 'find_text' in r and 'replace_text' in r for r in replacements):
                    return replacements
                else:
                    st.error("AI returned invalid JSON structure.")
                    return None
            else:
                st.error(f"AI response content missing. Full response: {result}")
                return None

        except requests.exceptions.RequestException as e:
            st.warning(f"API request failed (Attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                st.error("Maximum retries reached. Failed to communicate with the Gemini API.")
                return None
        except json.JSONDecodeError:
            st.error(f"Could not parse AI response as JSON. Raw output: {json_text}")
            return None
    return None

# --- PDF Editing Function ---
def process_pdf_edit(uploaded_file, replacements):
    """
    Performs the actual text replacement in the PDF using PyMuPDF (fitz).
    """
    # Read the uploaded file into a BytesIO buffer
    pdf_bytes = uploaded_file.getvalue()
    input_pdf_buffer = io.BytesIO(pdf_bytes)

    # Open the PDF document using fitz
    doc = fitz.open(stream=input_pdf_buffer.read(), filetype="pdf")

    total_changes = 0
    replacement_log = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        for rep in replacements:
            find_text = rep['find_text']
            replace_text = rep['replace_text']

            # Find all instances of the text
            text_instances = page.search_for(find_text)

            if text_instances:
                for rect in text_instances:
                    # 1. Redact (erase) the old text using the text's bounding box (rect)
                    # This securely removes the original text content from the PDF
                    page.add_redact_annot(rect, text="")
                    
                    # 2. Apply redactions immediately
                    page.apply_redactions()

                    # 3. Insert the new text. We try to use a standard font (Helvetica)
                    # to keep the document look consistent.
                    # We insert at the bottom-left corner of the redacted area (rect.x0, rect.y1)
                    page.insert_text(
                        (rect.x0, rect.y1 - 2),  # Slightly adjust y for better alignment
                        replace_text,
                        fontname="helv",  # Standard font is best for reliable insertion
                        fontsize=rect.height * 0.9, # Try to match the original text size
                        color=(0, 0, 0) # Black color
                    )
                    total_changes += 1
                    replacement_log.append(f"Page {page_num + 1}: Replaced '{find_text}' with '{replace_text}'")

    if total_changes == 0:
        st.warning("AI identified changes, but no matching text was found in the PDF. Check the AI's output or the original PDF text content.")
        return None, []

    # Save the modified document to a new BytesIO buffer
    output_pdf_buffer = io.BytesIO()
    doc.save(output_pdf_buffer)
    doc.close()
    
    return output_pdf_buffer.getvalue(), replacement_log

# --- Streamlit UI ---

st.set_page_config(page_title="AI Document Editor", layout="centered")
st.title("📄 AI-Powered Document Editor")
st.markdown("Upload a text-searchable PDF and provide an instruction to modify its content (e.g., change a number, date, or name).")
st.markdown("The AI (Gemini) will identify the exact text to replace, and the app will edit the PDF layer and provide the modified document.")

# 1. File Uploader
uploaded_file = st.file_uploader(
    "Upload a Text-Searchable PDF",
    type="pdf",
    key="pdf_uploader"
)

# 2. Prompt Input
user_prompt = st.text_input(
   "Enter your edit instruction (e.g., 'Correct typos, update dates, or modify values as needed')",
    key="edit_prompt"
)

# 3. Process Button
if st.button("✨ Apply AI Edit and Generate PDF", type="primary"):
    if not uploaded_file:
        st.error("Please upload a PDF file first.")
    elif not user_prompt:
        st.error("Please provide an instruction for the AI edit.")
    else:
        # Step A: Extract text for AI analysis
        try:
            doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n--- Page Break ---\n"
            doc.close()
            
            st.session_state['full_text'] = full_text

        except Exception as e:
            st.error(f"Error extracting text from PDF. Make sure it is not a scanned image: {e}")
            st.stop()

        # Step B: Get structured replacement instructions from AI
        replacements = ai_edit_text(st.session_state['full_text'], user_prompt)

        if replacements:
            st.success("✅ AI successfully identified the required changes.")
            
            # Display the AI's decision
            st.subheader("🤖 AI Replacement Plan:")
            st.json(replacements)

            # Step C: Perform the actual PDF edit
            with st.spinner("Applying changes and re-generating PDF..."):
                modified_pdf_bytes, log = process_pdf_edit(uploaded_file, replacements)
                
                if modified_pdf_bytes:
                    st.subheader("🎉 Modified PDF Ready!")
                    
                    # Display log
                    st.markdown("**Changes Made:**")
                    for entry in log:
                        st.text(f"- {entry}")

                    # 4. Download Button
                    st.download_button(
                        label="⬇️ Download Edited PDF",
                        data=modified_pdf_bytes,
                        file_name="edited_" + uploaded_file.name,
                        mime="application/pdf"
                    )
                else:
                    st.error("PDF modification failed. Please check the console for details or try a different file/prompt.")
        else:
            st.error("AI failed to provide valid replacement instructions. Please refine your prompt.")

st.sidebar.header("How It Works")
st.sidebar.markdown(
    """
1. **Extract:** The app extracts the text layer from the PDF.  
2. **Analyze (Gemini):** The PDF text and instructions are sent to the Gemini API for necessary changes.  
3. **Edit (PyMuPDF):** Using the AI’s results, the app locates and updates the text in the exact location on the page.  
4. **Download:** A new, edited PDF is generated for you.  

**Note:** For complex, scanned, or image-only PDFs, text extraction or replacement may not be possible.

"""
)