import re
import spacy
import streamlit as st
import streamlit.components.v1 as components
from spacy.util import filter_spans

# Load spaCy model with error handling
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("SpaCy English model required. Run in terminal: `python -m spacy download en_core_web_sm`")
    st.stop()

# Configuration
ROLE_PATTERNS = [
    (r"\bpatient's mother\b", "[MOTHER_NAME]"),
    (r"\bpatient\b", "[PATIENT_NAME]"),
    (r"\bDr\.?\b", "[DOCTOR_NAME]"),
    (r"\bnurse\b", "[NURSE_NAME]"),
    (r"\bfather\b", "[FATHER_NAME]"),
]

def replace_names_with_roles(text):
    """Replace names with role-based placeholders maintaining context"""
    doc = nlp(text)
    replacements = {}

    for ent in filter_spans(doc.ents):
        if ent.label_ == "PERSON":
            context_window = text[max(0, ent.start_char - 50):ent.start_char].lower()
            for pattern, placeholder in ROLE_PATTERNS:
                if re.search(pattern, context_window):
                    replacements[ent.text] = placeholder
                    break
            else:
                replacements[ent.text] = "[OTHER_NAME]"

    # Replace longest names first to prevent partial matches
    sorted_names = sorted(replacements.keys(), key=len, reverse=True)
    anonymized = text
    
    for name in sorted_names:
        words = name.split()
        if not words:
            continue
            
        # Create regex pattern with word boundaries
        pattern = r'\b' + r'\b[\s\-]+\b'.join(map(re.escape, words)) + r'\b'
        anonymized = re.sub(
            pattern, 
            replacements[name], 
            anonymized, 
            flags=re.IGNORECASE
        )
    
    return anonymized

def copy_button(text):
    """Create a copy button using HTML components"""
    return components.html(
        f"""
        <textarea id="copyContent" style="display:none;">{text}</textarea>
        <button onclick="navigator.clipboard.writeText(document.getElementById('copyContent').value)"
            style="
                margin:5px 0;
                padding:0.4rem 1rem;
                background:#4CAF50;
                color:white;
                border:none;
                border-radius:4px;
                cursor:pointer;
                transition:all 0.3s;
            "
            onmouseover="this.style.opacity=0.8"
            onmouseout="this.style.opacity=1">
            📋 Copy to Clipboard
        </button>
        """
    )

def main():
    """Streamlit UI configuration"""
    st.set_page_config(page_title="Text Anonymizer", layout="wide")
    
    st.title("🔒 Medical Text Anonymizer")
    st.markdown("""
    <style>
    .stTextArea textarea { font-family: monospace; }
    .stAlert { font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Text")
        input_text = st.text_area(
            "Paste sensitive text here:", 
            height=400,
            placeholder="Example:\nPatient John Smith presented with...\nHis mother Emily Jones accompanied..."
        )

    with col2:
        st.subheader("Anonymized Output")
        
        if st.button("🚀 Anonymize Text", use_container_width=True):
            if not input_text.strip():
                st.warning("Please input text to anonymize")
            else:
                with st.spinner("Processing... (may take a moment for large texts)"):
                    anonymized = replace_names_with_roles(input_text)
                    
                    st.text_area(
                        "Anonymized content:", 
                        value=anonymized,
                        height=400,
                        key="output"
                    )
                    
                    st.success("✅ Text anonymized successfully!")
                    copy_button(anonymized)

if __name__ == "__main__":
    main()