import smtplib
import pandas as pd
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import threading
import time
import gradio as gr
from groq import Groq
import matplotlib.pyplot as plt
from PIL import Image
import io

# MongoDB setup
client = MongoClient('mongodb+srv://avra6269:OGUR0YhstHVgFo8g@cluster0.kpxtb.mongodb.net/Email?retryWrites=true&w=majority&appName=Cluster0')
db = client.email_app
emails_collection = db.emails
status_collection = db.status

# Groq API setup
groq_client = Groq(api_key="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")

# Function to read CSV or Google Sheet
def read_data(file):
    if file.endswith('.csv'):
        return pd.read_csv(file)
    return None


# Email sending function
def send_email(subject, body, to_email, company_name, smtp_server, smtp_port, smtp_user, smtp_password):
    try:
        # Email body generation with dynamic greeting
        # body = f"Dear {company_name},\n\n" + body
        
        # Set up SMTP server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        msg = f"Subject: {subject}\n\n{body}"
        server.sendmail(smtp_user, to_email, msg)
        server.quit()

        # Set delivery status to "Delivered" after the email is successfully sent
        delivery_status = "Delivered"
        opened = "Pending"  # This can be updated when a tracking mechanism is used
        

        # Update the email status in MongoDB to "Sent" and delivery status to "Delivered"
        store_email_status(to_email, "Sent", company_name=company_name, details=body, delivery_status=delivery_status, opened=opened)
        return "Sent"
    
    except Exception as e:
        # Extract the main error message by splitting on ' ' and taking the core error
        error_message = str(e)
        
        # Check if it’s an SMTP error with a structured message and extract the error code and message
        if 'Username and Password not accepted' in error_message:
            error_message = "Failed: 5.7.8 Username and Password not accepted"
        else:
            # Otherwise, take the first portion of the message before any extra details
            error_message = error_message.split("\n")[0]  # Take only the first line of the error message

        store_email_status(to_email, error_message, company_name=company_name, details=body)
        return error_message



# Function to store email status
def store_email_status(email, status, details=None, company_name=None, delivery_status="Pending", opened="N/A"):
    # If the email status is "Scheduled" or "Pending", we set delivery status to "Pending"
    if status in ["Scheduled", "Pending"]:
        delivery_status = "Pending"
    elif status == "Sent":
        # Once the email is sent, update delivery status to "Delivered"
        delivery_status = "Delivered"
    
    # Update or insert email status into MongoDB
    result = status_collection.update_one(
        {"email": email},  # Search by email
        {
            "$set": {  # Update the status and other fields
                "status": status,
                "details": details,
                "company_name": company_name,
                "delivery_status": delivery_status,
                "opened": opened,
                "timestamp": datetime.now()
            }
        },
        upsert=True  # If no document exists, insert a new one
    )

    # Optionally check if the document was updated or inserted
    if result.modified_count == 0 and result.upserted_id is not None:
        print(f"New email status inserted for {email}")
    else:
        print(f"Email status updated for {email}")




# Groq content generation function
# Function to clean up unwanted static text and generate the email content
def generate_email_content(prompt, data_row):
    # Replace placeholders in prompt with actual values from the data row
    for column in data_row.index:
        prompt = prompt.replace(f'{{{column}}}', str(data_row[column]))

    # Use Groq API to generate content
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama3-8b-8192",  # Choose appropriate model for your use case
        stream=False,
    )
    
    # Extract generated content
    generated_text = chat_completion.choices[0].message.content
    return generated_text.strip()

# Function to store email status
def store_email_status(email, status, details=None, company_name=None, delivery_status="N/A", opened="N/A"):
    status_collection.insert_one({
        'email': email,
        'status': status,
        'details': details,
        'company_name': company_name,
        'delivery_status': delivery_status,
        'opened': opened,
        'timestamp': datetime.now()
    })

# Function to schedule emails
def schedule_emails(email_data, smtp_user, smtp_password, smtp_server, smtp_port, prompt, schedule_time=None, throttle_rate=0):
    scheduler = BackgroundScheduler()

    # Ensure schedule_time is a datetime object
    if schedule_time and isinstance(schedule_time, (float, int)):
        schedule_time = datetime.fromtimestamp(schedule_time)
    
    if schedule_time and not isinstance(schedule_time, datetime):
        raise ValueError("schedule_time must be a datetime object or a valid timestamp")

    def send_scheduled_emails():
        for index, row in email_data.iterrows():
            to_email = row['Email']
            company_name = row.get('CompanyName', 'Unknown')
            
            # Mark the email as "Pending" right before sending
            store_email_status(to_email, "Pending", company_name=company_name)
            
            subject = "Custom Subject"
            body = generate_email_content(prompt, row)
            status = send_email(subject, body, to_email, company_name, smtp_server, smtp_port, smtp_user, smtp_password)
            
            # Update email status in MongoDB after sending
            store_email_status(to_email, status, details=body, company_name=company_name)

            if throttle_rate > 0:
                time.sleep(60 / throttle_rate)

    # Schedule the job, marking emails as "Scheduled" initially
    for _, row in email_data.iterrows():
        store_email_status(row['Email'], "Scheduled", company_name=row.get('CompanyName', 'Unknown'))

    if schedule_time:
        scheduler.add_job(send_scheduled_emails, 'date', run_date=schedule_time)
    else:
        scheduler.add_job(send_scheduled_emails, 'interval', minutes=1)
    
    scheduler.start()


# Function to fetch analytics data
def fetch_email_stats():
    total_sent = status_collection.count_documents({"status": "Sent"})
    total_failed = status_collection.count_documents({"status": {"$regex": "^Failed"}})
    total_scheduled = status_collection.count_documents({"status": "Scheduled"})
    total_pending = status_collection.count_documents({"status": "Pending"})
    return total_sent, total_failed, total_scheduled, total_pending

# Function to create and return a graph as an image
def generate_analytics_graph():
    sent, failed, scheduled, pending = fetch_email_stats()
    categories = ['Sent', 'Failed', 'Scheduled', 'Pending']
    counts = [sent, failed, scheduled, pending]
    
    fig, ax = plt.subplots()
    ax.bar(categories, counts, color=['green', 'red', 'orange', 'blue'])
    ax.set_xlabel('Status')
    ax.set_ylabel('Count')
    ax.set_title('Email Analytics')

    # Save the plot to a BytesIO object in PNG format
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)  # Close the figure to free memory
    
    # Convert BytesIO to an image Gradio can display
    image = Image.open(buf)
    return image

# Function to fetch real-time email status data
def fetch_email_status():
    records = status_collection.find()
    data = []
    for record in records:
        data.append({
            "CompanyName": record.get("company_name", "N/A"),
            "Email": record["email"],
            "Email Status": record["status"],
            "Delivery Status": record.get("delivery_status", "N/A"),
            "Opened": record.get("opened", "N/A")
        })
    return pd.DataFrame(data)

# Gradio UI and Dashboard
def create_gradio_interface():
    def upload_file(file):
        email_data = read_data(file.name)
        if email_data is not None:
            return email_data.head()
        return "Invalid file format. Please upload a valid CSV file."

    def connect_email(email_account, smtp_password, smtp_server, smtp_port):
        return f"Connected to {email_account}"

    def start_sending(file, email_account, smtp_password, smtp_server, smtp_port, prompt, schedule_time=None, throttle_rate=0):
        try:
            email_data = read_data(file.name)
            if email_data is None:
                return "Invalid file format. Please upload a valid CSV file."
            
            threading.Thread(target=schedule_emails, args=(email_data, email_account, smtp_password, smtp_server, smtp_port, prompt, schedule_time, throttle_rate)).start()
            
            return "Emails are being sent! Check the analytics dashboard for status."

        except Exception as e:
            return f"An error occurred: {str(e)}"

    def refresh_dashboard():
        sent, failed, scheduled, pending = fetch_email_stats()
        total_emails = sent + failed + scheduled + pending
        progress = (sent / total_emails * 100) if total_emails > 0 else 0
        return f"Total Sent: {sent}", f"Total Failed: {failed}", f"Total Scheduled: {scheduled}", f"Total Pending: {pending}", f"{progress:.2f}% Complete"

    def get_email_status():
        email_status_data = fetch_email_status()
        return email_status_data

    def get_analytics_graph():
        return generate_analytics_graph()

    # Gradio Interface components
    file_input = gr.File(label="Upload CSV File")
    email_account = gr.Textbox(label="Email Account")
    smtp_password = gr.Textbox(label="SMTP Password", type="password")
    smtp_server = gr.Textbox(label="SMTP Server", value="smtp.gmail.com")
    smtp_port = gr.Number(label="SMTP Port", value=587)
    prompt_input = gr.Textbox(label="Custom Email Prompt")
    schedule_time = gr.DateTime(label="Schedule Time (optional)")
    throttle_rate = gr.Number(label="Throttle Rate (emails per minute)", value=0)

    # Real-Time Analytics and Dashboard Components
    analytics_output = [gr.Text(label="Total Sent"), gr.Text(label="Total Failed"), gr.Text(label="Total Scheduled"), gr.Text(label="Total Pending")]
    progress_text = gr.Text(label="Progress")
    email_status_table = gr.DataFrame(headers=["CompanyName", "Email", "Email Status", "Delivery Status", "Opened"])
    analytics_graph = gr.Image(label="Analytics Graph")

    # Create Gradio interface
    gr_interface = gr.Interface(
        fn=start_sending,
        inputs=[file_input, email_account, smtp_password, smtp_server, smtp_port, prompt_input, schedule_time, throttle_rate],
        outputs="text"
    )

    # Real-time dashboard with email tracking
    gr_dashboard = gr.Interface(
        fn=refresh_dashboard,
        inputs=[],
        outputs=analytics_output + [progress_text],
        live=True
    )

    gr_email_status = gr.Interface(
        fn=get_email_status,
        inputs=[],
        outputs=email_status_table,
        live=True
    )

    gr_analytics_graph = gr.Interface(
        fn=get_analytics_graph,
        inputs=[],
        outputs=analytics_graph,
        live=True
    )

    # Use the correct method to create a tabbed interface
    return gr.TabbedInterface(
        [gr_interface, gr_dashboard, gr_email_status, gr_analytics_graph],
        ["Send Emails", "Dashboard", "Email Status", "Analytics Graph"]
    )

# Launch the Gradio app
app = create_gradio_interface()
app.launch()