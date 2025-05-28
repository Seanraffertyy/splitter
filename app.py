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
    <p>Upload a PDF. This tool will extract pages 47, 48, 49, 51, 52, 53, 54, and 57.</p>
    <form method="post" action="/split" enctype="multipart/form-data">
        <input type="file" name="pdf" required><br><br>
        <input type="submit" value="Extract Signature Pages">
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
    output_dir = os.path.join(temp_dir, "pages")
    os.makedirs(output_dir)

    # Pages to export (0-based index)
    pages_to_export = [46, 47, 48, 50, 51, 52, 53, 56]
    filenames = []

    for i in pages_to_export:
        if i < len(doc):
            out_path = os.path.join(output_dir, f"page_{i+1}.pdf")
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            new_doc.save(out_path)
            new_doc.close()
            filenames.append(out_path)

    zip_path = os.path.join(temp_dir, "signature_pages.zip")
    with ZipFile(zip_path, 'w') as zipf:
        for f in filenames:
            zipf.write(f, os.path.basename(f))

    doc.close()
    return send_file(zip_path, as_attachment=True, download_name="signature_pages.zip")

if __name__ == "__main__":
    app.run(debug=True)
