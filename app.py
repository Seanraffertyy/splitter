from flask import Flask, request, send_file
import fitz  # PyMuPDF
import os
import tempfile
from zipfile import ZipFile

from email_generator import generate_emails
from gmail_service import create_draft

app = Flask(__name__)

generated_emails = []

@app.route("/email-tool")
def email_tool():
    return '''
    <h2>Email Draft Generator</h2>

    <form action="/upload-email" method="post" enctype="multipart/form-data">

    Candidate Excel File:
    <input type="file" name="candidates" required><br><br>

    Recruiter Lookup File:
    <input type="file" name="recruiters" required><br><br>

    <button type="submit">Generate Preview</button>

    </form>

    <br><br>
    <a href="/">Back to Tools</a>
    '''

@app.route("/upload-email", methods=["POST"])
def upload_email():

    global generated_emails

    candidates = request.files["candidates"]
    recruiters = request.files["recruiters"]

    temp_dir = tempfile.mkdtemp()

    candidate_path = os.path.join(temp_dir, candidates.filename)
    recruiter_path = os.path.join(temp_dir, recruiters.filename)

    candidates.save(candidate_path)
    recruiters.save(recruiter_path)

    generated_emails = generate_emails(candidate_path, recruiter_path)

    html = "<h2>Email Preview</h2><table border=1>"
    html += "<tr><th>To</th><th>CC</th><th>Subject</th></tr>"

    for email in generated_emails:
        html += f"<tr><td>{email['to']}</td><td>{email['cc']}</td><td>{email['subject']}</td></tr>"

    html += "</table><br>"

    html += '''
    <form action="/create-drafts" method="post">
        <button type="submit">Create Gmail Drafts</button>
    </form>

    <br><a href="/">Back</a>
    '''

    return html

@app.route("/create-drafts", methods=["POST"])
def create_drafts():

    service = get_gmail_service()

    for email in generated_emails:

        create_draft(
            service,
            email["to"],
            email["cc"],
            email["subject"],
            email["body"]
        )

    return "<h3>Drafts Created Successfully!</h3><a href='/'>Back to Home</a>"

@app.route('/')
def index():
    return '''
    <h2>Internal Tools</h2>

    <h3>PDF Signature Page Extractor</h3>
    <form method="post" action="/split" enctype="multipart/form-data">
        <input type="file" name="pdf" required><br><br>
        <button type="submit" name="mode" value="default">Split SLB Docs</button>
        <button type="submit" name="mode" value="customer">Split Halliburton Docs</button>
    </form>

    <br><hr><br>

    <h3>Email Draft Generator</h3>
    <p>Generate candidate email drafts from Excel.</p>
    <a href="/email-tool">
        <button>Open Email Generator</button>
    </a>
    '''


@app.route('/split', methods=['POST'])
def split_pdf():
    pdf_file = request.files['pdf']
    if not pdf_file:
        return "No file uploaded."

    mode = request.form.get('mode', 'default')

    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, pdf_file.filename)
    pdf_file.save(input_path)

    doc = fitz.open(input_path)
    output_dir = os.path.join(temp_dir, "groups")
    os.makedirs(output_dir)

    base_name = os.path.splitext(pdf_file.filename)[0]
    filenames = []

    # Default mode: original groupings
    if mode == 'default':
        grouped_pages = {
            "Acknowledgement of Receipt of Harassment-Free Standard": [46],
            "Contractor Acknowledgement of The SLB Code of Conduct": [47],
            "Contractor Information Security Standard Acknowledgement": [48],
            "Agreement Concerning Confidential Info IP US": [49, 50],
            "Non-Employee Access Agreement": [51, 52, 53, 54, 55],
            #"Candidate Declaration Form for Recruitment Fees": [56],
            "Contract Temporary Worker Acknowledgement": [57],
            "Addendum A Drug-Free Workplace Policy": [58],
            "US Conflict of Interest": [59],
            "Candidate Declaration Form for Recruitment Fees": [59],
        }

    # New mode: customer packet grouping
    elif mode == 'customer':
        grouped_pages = {
            "Customer Drug, Alcohol and Contraband Addendum": [13],
            "US Intellectual Property and Confidentiality Agreement": [14, 15, 16, 17],
            "Arbitration Agreement": [51, 52, 53, 54, 55, 56],
            "Emergency Contact Information Sheet": [57],
            "Drug Abuse & Alcohol Screening Search Program Verification": [76],
            "Motive Consent Form": [77, 78, 79],
        }

    else:
        return "Invalid mode selected.", 400

    # Generate PDFs
    for title, pages in grouped_pages.items():
        new_doc = fitz.open()
        for i in pages:
            if i < len(doc):
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
        output_path = os.path.join(output_dir, f"{base_name} {title}.pdf")
        new_doc.save(output_path)
        new_doc.close()
        filenames.append(output_path)

    zip_name = f"{base_name}.zip"
    zip_path = os.path.join(temp_dir, zip_name)

    with ZipFile(zip_path, 'w') as zipf:
        for file_path in filenames:
            zipf.write(file_path, os.path.basename(file_path))

    doc.close()
    return send_file(zip_path, as_attachment=True, download_name=zip_name)


if __name__ == "__main__":
    app.run(debug=True)

