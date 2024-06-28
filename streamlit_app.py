import streamlit as st
from pymongo import MongoClient
import fitz  # PyMuPDF
import docx
from datetime import datetime

st.set_page_config(page_title="Checklist", page_icon=":clipboard:")

MONGO_URI = st.secrets["mongo_uri"]
client = MongoClient(MONGO_URI)
db = client['Stig_checklist']
collection = db['checklist']

client_submissions = db['client_submissions']

st.title("Your Checklist Upload App")

# Functions to read different file types
def read_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def read_docx(file):
    doc = docx.Document(file)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text

def read_txt(file):
    text = file.read().decode("utf-8")
    return text

# Upload file in sidebar
uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    file_type = uploaded_file.name.split('.')[-1]
    if file_type == "pdf":
        content = read_pdf(uploaded_file)
    elif file_type == "docx":
        content = read_docx(uploaded_file)
    elif file_type == "txt":
        content = read_txt(uploaded_file)
    else:
        content = "Unsupported file type."
    
    # Save checklist to the database
    checklist = {
        "filename": uploaded_file.name,
        "content": content,
        "upload_date": datetime.now(),
        "assigned_clients": []
    }
    
    # insert only if the checklist is not already in the database
    if not collection.find_one({"filename": uploaded_file.name}):
        collection.insert_one(checklist)
    else:
        st.warning("Checklist with this name already uploaded.")

# Sidebar to display uploaded checklists
st.sidebar.title("Uploaded Checklists")
checklists = list(collection.find().sort("upload_date", -1))

if checklists:
    checklist_titles = [checklist["filename"] for checklist in checklists]
    selected_checklist = st.sidebar.radio("Select a checklist", checklist_titles)

    selected_content = None
    assigned_clients = []
    checklist_id = None
    for checklist in checklists:
        if checklist["filename"] == selected_checklist:
            selected_content = checklist["content"]
            assigned_clients = checklist.get("assigned_clients", [])
            checklist_id = checklist["_id"]
            break

    if selected_content:
        st.text_area("File Content", selected_content, height=500)
        
        # Display assigned clients
        st.write("Assigned Clients:", ", ".join(assigned_clients) if assigned_clients else "None")

        # Input to assign checklist
        new_client_key = st.text_input("Assign Checklist to Client (Enter Client Key)",)
        if st.button("Assign"):
            if new_client_key:
                collection.update_one(
                    {"_id": checklist_id},
                    {"$addToSet": {"assigned_clients": new_client_key}}
                )
                st.success(f"Checklist assigned to {new_client_key}")
            else:
                st.error("Client key cannot be empty.")

else:
    st.text("No checklists uploaded.")
    
    
for client_submission in client_submissions.find():
    with st.expander(f"Client Submission: {client_submission['client_id']} {client_submission['current_date']}",expanded=False):
        st.code(client_submission['submission'])
