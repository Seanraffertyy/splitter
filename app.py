from flask import Flask, request, send_file
import fitz  # PyMuPDF
import os
import tempfile
from zipfile import ZipFile

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <h2>PDF Signature Page Extractor</h2>
    <p>Upload a PDF. This tool will extract and group signature-related pages.</p>
    <form method="post" action="/split" enctype="multipart/form-data">
        <input type="file" name="pdf" required><br><br>
        <input type="submit" value="Extract and Group Signature Pages">
    </form>
    '''

@app.route('/split', methods=['POST'])
def split_pdf():
    pdf_file = request.files['pdf']
    if not pdf_file:
        return "No file uploaded."

    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, pdf_file.filename)
    pdf_file.save(input_path)

    doc = fitz.open(input_path)
    output_dir = os.path.join(temp_dir, "groups")
    os.makedirs(output_dir)

    # Page groupings (0-based index for PyMuPDF)
    grouped_pages = {
        "Acknowledgement of Receipt of Harassment-Free Standard": [46],
        "Contractor Acknowledgement of The SLB Code of Conduct": [47],
        "Contractor Information Security Standard Acknowledgement": [48],
        "Confidential Agreement (Non Disclosure)": [49, 50],
        "Non-Employee Access Agreement": [51, 52, 53, 54, 55],
        "SLB Policies Contingent Worker Acknowledgment Form": [56],
    }

    base_name = os.path.splitext(pdf_file.filename)[0]
    filenames = []

    for title, pages in grouped_pages.items():
        new_doc = fitz.open()
        for i in pages:
            if i < len(doc):
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
        output_path = os.path.join(output_dir, f"{base_name} {title}.pdf")
        new_doc.save(output_path)
        new_doc.close()
        filenames.append(output_path)

    zip_path = os.path.join(temp_dir, "signature_documents.zip")
    with ZipFile(zip_path, 'w') as zipf:
        for file_path in filenames:
            zipf.write(file_path, os.path.basename(file_path))

    doc.close()
    return send_file(zip_path, as_attachment=True, download_name=f"{base_name} Documents.zip")

if __name__ == "__main__":
    app.run(debug=True)

