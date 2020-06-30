def send_email(to, subj, body):
    from smtplib import SMTP_SSL
    from email.message import EmailMessage
    from creds import smtp_email, smtp_password
    
    with SMTP_SSL("smtp.gmail.com") as s:
        s.login(smtp_email, smtp_password)
        e = EmailMessage()
        if(subj):
            e["Subject"] = subj
        e["To"] = to
        e["From"] = smtp_email
        e.set_content(body)
        s.send_message(e)

def send_email_with_attachment(to, subj, body, filename, file_full_path):
    from smtplib import SMTP_SSL
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    from creds import smtp_email, smtp_password
    t = MIMEText(body)
    f = MIMEApplication(open(file_full_path).read())
    f.add_header('Content-Disposition', 'attachment', filename=filename)
    m = MIMEMultipart()
    m.attach(t)
    m.attach(f)
    m["Subject"] = subj
    with SMTP_SSL("smtp.gmail.com") as s:
        s.login(smtp_email, smtp_password)
        s.sendmail(smtp_email, to, m.as_string())
    

def send_completion_email(to, sheet_id):
    msg = "You can find your aggregate scoresheet here:\n\nhttps://docs.google.com/spreadsheets/d/{}\n\nRemember to link all rooms from the aggregate scoresheet, and remember to link each room to the roster sheet (if you chose to use rosters)".format(sheet_id)
    send_email(to, "Your scoresheet generation is completed", msg)

def send_conversion_email(to, sqbs_filename, sqbs_full_path):
    msg = "You can find your sqbs file here: http://localhost/sqbs/{} or attached to this email".format(sqbs_filename)
    send_email_with_attachment(to, "Your sqbs conversion is completed", msg, sqbs_filename, sqbs_full_path)
    
def generate_filename(s, ext, timestamp = None):
    from hashlib import md5
    return md5(bytes(s, "utf-8")).hexdigest()[:10] + ("_" + str(timestamp) if timestamp else "") + ext

def validate_spreadsheet(s):
    import re
    url_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)',s)
    id_match = re.match(r'(^[a-zA-Z0-9-_]+$)',s)
    match = ""
    if(url_match):
        match = url_match.groups()[0]
    elif(id_match):
        match = id_match.groups()[0]
    if(len(match) > 20 and len(match) < 80):
        return match
    return None