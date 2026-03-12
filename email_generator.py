import pandas as pd
from jinja2 import Template


def generate_emails(candidate_file, recruiter_file):

    candidates = pd.read_excel(candidate_file)
    recruiters = pd.read_excel(recruiter_file)

    recruiter_map = dict(zip(recruiters["Candidate Name"], recruiters["Recruiter Email"]))

    with open("templates/email_template.txt") as f:
        template = Template(f.read())

    emails = []

    for _, row in candidates.iterrows():

        name = row["Candidate Name"]
        email = row["Email"]
        pay_rate = row["Base Pay Rate"]
        shift = row["Shift"]
        position = row["Position"]

        recruiter_email = recruiter_map.get(name)

        body = template.render(
            name=name,
            pay_rate=pay_rate,
            shift=shift,
            position=position
        )

        subject = f"Offer for {position}"

        emails.append({
            "to": email,
            "cc": recruiter_email,
            "subject": subject,
            "body": body
        })

    return emails