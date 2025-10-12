# AI-Powered Document Editor

An intelligent, AI-powered application built with Streamlit and the Gemini API that transforms complex text-editing instructions into precise, targeted replacements within uploaded PDF documents.

## 🌟 Overview
The **AI-Powered Document Editor** solves the tedious problem of manually locating and correcting specific text elements across large documents.  
Instead of searching, copying, and pasting, users simply upload a PDF and provide natural language instructions (e.g., *"Change all instances of 'Acme Corp' to 'Acme Solutions Ltd.' in Section 3,"* or *"Reword the last paragraph for a general audience"*).

**Gemini** interprets the intent, identifies the exact location (or context), and generates the precise replacement text, which the **Streamlit** application then applies to create a corrected, downloadable PDF.

---

## ✨ Key Features

- **Intelligent Editing:** Uses Google’s Gemini large language model to understand nuanced, high-level editing commands.  
- **PDF Upload & Processing:** Securely upload single or multiple PDF documents via the interactive Streamlit interface.  
- **Precise Replacement:** Generates exact text replacements, ensuring minimal disruption to the document's layout and formatting.  
- **Contextual Awareness:** Gemini maintains context of the entire document to ensure suggested edits are appropriate and accurate based on surrounding text.  
- **Interactive Review:** Displays proposed changes before final application, allowing users to accept or modify AI’s suggestions.  
- **Downloadable Output:** Generates a new, corrected PDF file available for instant download.  

---

## 🛠️ Technology Stack

| Technology | Purpose |
|-------------|----------|
| **Streamlit** | Frontend for creating a responsive, interactive web application interface in pure Python. |
| **Gemini API** | Generative AI engine for natural language understanding and text generation/replacement. |
| **Python** | Core programming language for the application logic. |
| **PyPDF2 / PyMuPDF (fitz)** | Libraries used for reading PDF structure, extracting text, and applying text manipulation. |

---

## 🚀 Getting Started
Follow these steps to set up and run the **AI-Powered Document Editor** locally.

### Prerequisites
- **Python 3.9+**  
- **Git**

---

## ⚙️ Setup Instructions

Follow these steps to set up and run the **AI-Powered Document Editor** locally.

---

### 1. Clone the Repository
Clone the project repository from GitHub and navigate into it:

```bash
git clone https://github.com/sbshihab24/AI-Powered-Document-Editor.git
cd AI-Powered-Document-Editor
###  2. Set up the Environment
# Create environment
python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows (Command Prompt)
venv\Scripts\activate.bat

