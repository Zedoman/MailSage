# Custom Email-Sending Application [MailSage](https://huggingface.co/spaces/Zedoman/Email_Sender)

This is a professional email-sending application built using Python and Gradio. The application allows users to send customized emails, schedule email deliveries, monitor email statuses, and generate email analytics graphs. The backend utilizes MongoDB for storing email statuses, while Groq's API is used for content generation. The system is designed for scalability and real-time updates.<br>

## Features <br>
- **Email Sending:** Send customized emails to recipients from a CSV file. <br>
- **Content Generation:** Use Groq's API to generate email content based on a customizable prompt and data from a CSV. <br>
- **Email Scheduling:** Schedule emails for future delivery or send them immediately with throttling options.<br>
- **Real-Time Analytics:** View email send status, delivery status, and opened status, along with a live progress bar. <br>
- **Email Status Tracking:** Track the status of emails, including success/failure, delivery, and whether they were opened.<br>
- **Graphical Analytics:** Visualize email send statistics with bar charts showing the total count of Sent, Failed, Scheduled, and Pending emails.<br>

## Requirements<br>
- Python 3.x<br>
- `gradio` for the frontend interface <br>
- `pandas` for handling CSV data <br>
- `pymongo` for MongoDB integration<br>
- `apscheduler` for scheduling email tasks<br>
- `matplotlib` for generating analytics graphs<br>
- `groq` for content generation<br>
- `PIL` for image handling<br>
- SMTP server details for sending emails (e.g., Gmail)<br>

## Setup <br>

### Step 1: Install Dependencies <br>
Ensure you have the required Python packages installed:
    ```bash
    pip install gradio pandas pymongo apscheduler matplotlib pillow groq

### Step 2: MongoDB Setup <br>
You must have a MongoDB instance set up. The connection is configured to a MongoDB Atlas cluster in the code. If using your own MongoDB setup, update the connection string as needed.

### Step 3: Groq API Setup <br>
Sign up for a Groq API key (https://groq.com) and set up the key in the groq_client initialization:
    ```bash
    groq_client = Groq(api_key="your-groq-api-key")


### Step 4: SMTP Setup<br>
To send emails via SMTP, you'll need your email server credentials (e.g., Gmail):<br>

smtp_server: SMTP server (default is smtp.gmail.com).<br>
smtp_port: SMTP port (default is 587).<br>
smtp_user: Your email address.<br>
smtp_password: Your email password or app password if using Gmail.<br>

### Step 5: Running the Application<br>
After setting up the necessary configurations, run the Python script to launch the Gradio interface:<br>
    ```bash
    python app.py


### Gradio Interface<br>
Once the application is running, you'll see the following sections in the Gradio UI:<br>

### 1. Send Emails<br>
Upload CSV File: Upload a CSV file containing the recipient's email address and any other relevant data.<br>
Email Account: Enter the SMTP email account (e.g., Gmail).<br>
SMTP Password: Provide the SMTP password (use app password if using Gmail).<br>
SMTP Server: SMTP server (default is smtp.gmail.com).<br>
SMTP Port: The port number for SMTP (default is 587).<br>
Custom Email Prompt: A prompt to customize the content of the emails using Groq's content generation.<br>
Schedule Time: Optionally, schedule when emails should be sent.<br>
Throttle Rate: Set the maximum number of emails to send per minute.<br>
### 2. Dashboard<br>
Displays real-time email statistics, such as:<br>
Total Sent<br>
Total Failed<br>
Total Scheduled<br>
Total Pending<br>
A progress bar shows the completion percentage of sent emails.<br>
### 3. Email Status<br>
Displays the status of all sent emails, including:<br>
Company Name<br>
Email Address<br>
Email Status (Sent/Failed/Pending)<br>
Delivery Status (Pending, Delivered, etc.)<br>
Opened (Pending, Opened)<br>
### 4. Analytics Graph
A bar chart visualizing email statistics:<br>
Sent<br>
Failed<br>
Scheduled<br>
Pending<br>


### Example Workflow
Upload CSV: Upload a CSV file with recipient email addresses and relevant details (e.g., Company Name, etc.). <br>
| CompanyName | Location      | Email             | Products               |
|-------------|---------------|-------------------|-------------------------|
| ABC Corp    | New York      | hbjarko@gmail.com | Product A, Product B   |
| XYZ Ltd     | Los Angeles   | 12346arjo@gmail.com | Product C, Product D |

Create Prompt: Enter a custom prompt for email content, using placeholders for dynamic fields (e.g., {CompanyName}). <br>
**Example:**

Dear **{CompanyName}** from **{Location}**,

We are excited to offer the following products: **{Products}**. Please let us know if you are interested in any of them.

Best regards,  
Your Company

Send Emails: Choose to send emails immediately or schedule them for a later time. <br>
Monitor Status: Check the real-time status of each email and view the analytics dashboard. <br>
Track Analytics: View the status of sent emails and visualize it in the Analytics Graph. <br>

### MongoDB Structure<br>
The application stores the following information in MongoDB:<br>

Emails Collection: Stores details of each email sent, including recipient address, company name, and status.<br>
Status Collection: Tracks the status of emails (e.g., Sent, Failed, Scheduled) and the delivery/open status.<br>


### Notes
Groq API: You may need to adjust the API usage depending on your subscription level and API limits.<br>
Email Rate Limiting: Be cautious when setting the throttle rate to avoid triggering your email service's rate limits.<br>
