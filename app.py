from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
import io
import zipfile
import os

app = Flask(__name__)

# Page groups with their corresponding output file name suffixes
page_groups = [
    ([46], "Acknowledgement of Receipt of Harassment-Free Standard"),
    ([47], "Contractor Acknowledgement of The SLB Code of Conduct"),
    ([48], "Contractor Information Security Standard Acknowledgement"),
    ([49, 50], "Confidential Agreement (Non Disclosure)"),
    ([51, 52, 53, 54, 55], "Non-Employee Access Agreement"),
    ([56], "SLB Policies Contingent Worker Acknowledgment Form")
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/split', methods=['POST'])
def split_pdfs():
    uploaded_files = request.files.getlist("pdfs")
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file in uploaded_files:
            if file.filename == "":
                continue

            original_name = os.path.splitext(file.filename)[0]
            pdf = fitz.open(stream=file.read(), filetype="pdf")

            for pages, suffix in page_groups:
                output_pdf = fitz.open()
                for page_num in pages:
                    if page_num < len(pdf):
                        output_pdf.insert_pdf(pdf, from_page=page_num, to_page=page_num)
                output_stream = io.BytesIO()
                output_pdf.save(output_stream)
                output_pdf.close()
                output_stream.seek(0)

                output_filename = f"{original_name}_{suffix}.pdf"
                zip_file.writestr(output_filename, output_stream.read())

    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name="split_documents.zip", mimetype='application/zip')
