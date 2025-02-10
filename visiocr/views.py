
from django.shortcuts import render
from django.http import JsonResponse
from .serializers import OCRDataSerializer
from .models import OCRData  # Import your model
import pytesseract
import cv2
import numpy as np
import re
import sqlite3
import qrcode
from io import BytesIO
import base64
from django.template.loader import render_to_string
from django.http import HttpResponse
import pdfkit

# Configure Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(img, enable_preprocessing=True):
    if not enable_preprocessing:
        return img
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, threshed = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((1, 1), np.uint8)
    processed_img = cv2.dilate(threshed, kernel, iterations=1)
    return processed_img

def perform_ocr(img):
    try:
        text = pytesseract.image_to_string(img, lang='eng+hin')
        return text.strip()
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ""

def identify_document_type(text):
    pan_pattern = r'[A-Z]{5}\d{4}[A-Z]{1}'
    aadhaar_pattern = r'\d{4}\s\d{4}\s\d{4}'
    if re.search(pan_pattern, text):
        return "PAN Card"
    elif re.search(aadhaar_pattern, text):
        return "Aadhaar Card"
    else:
        return "Unknown"

def extract_pan_details(text):
    pan_number_pattern = r'[A-Z]{5}\d{4}[A-Z]{1}'
    name_pattern = r'(?:Name\s*:\s*|IH name\s*|Name\s*|Father\'s Name\s*:\s*)([A-Z\s]+)'
    dob_pattern = r'(\d{2}/\d{2}/\d{4})'
    pan_number = re.search(pan_number_pattern, text).group(0) if re.search(pan_number_pattern, text) else "Not Found"
    name = re.search(name_pattern, text).group(1).strip() if re.search(name_pattern, text) else "Not Found"
    dob = re.search(dob_pattern, text).group(1) if re.search(dob_pattern, text) else "Not Found"
    return {"Document Type": "PAN Card", "ID Number": pan_number, "Name": name, "Date of Birth": dob}

def extract_aadhaar_details(text):
    aadhaar_pattern = r'\d{4}\s\d{4}\s\d{4}'
    name_pattern = r'([A-Z][a-z]+\s[A-Z][a-z]+)'
    dob_pattern = r'(\d{2}/\d{2}/\d{4})'
    id_number = re.search(aadhaar_pattern, text).group(0) if re.search(aadhaar_pattern, text) else "Not Found"
    person_name = re.search(name_pattern, text).group(0).strip() if re.search(name_pattern, text) else "Not Found"
    dob = re.search(dob_pattern, text).group(1) if re.search(dob_pattern, text) else "Not Found"
    return {"Document Type": "Aadhaar Card", "ID Number": id_number, "Name": person_name, "Date of Birth": dob}

def extract_information(text):
    doc_type = identify_document_type(text)
    if doc_type == "PAN Card":
        return extract_pan_details(text)
    elif doc_type == "Aadhaar Card":
        return extract_aadhaar_details(text)
    else:
        return {"Document Type": "Unknown", "ID Number": "Not Found", "Name": "Not Found", "Date of Birth": "Not Found"}

def prompt_for_missing_data(data):
    for key, value in data.items():
        if value == "Not Found":
            user_input = input(f"{key} is missing. Please enter the {key}: ")
            data[key] = user_input.strip()
    return data

def store_data_in_db(data):
    print("Storing data:", data)
    ocr_data = OCRData(
        document_type=data["Document Type"],
        id_number=data["ID Number"],
        name=data["Name"],
        dob=data["Date of Birth"]
    )
    ocr_data.save()  # Use Django's save method

def download_pdf(request):
    latest_data = OCRData.objects.last()

    if not latest_data:
        return HttpResponse("No data available to download.", status=404)

    # Prepare data for visitor pass
    data = {
        "Document Type": latest_data.document_type,
        "ID Number": latest_data.id_number,
        "Name": latest_data.name,
        "Date of Birth": latest_data.dob
    }
    
    # Generate QR code for PDF
    qr_info = f"{data['Document Type']} | ID: {data['ID Number']} | Name: {data['Name']} | DOB: {data['Date of Birth']}"
    qr = qrcode.make(qr_info)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Render visitor pass HTML with QR code and data
    html_content = render_to_string('visitor_pass.html', {'data': data, 'qr_code_base64': qr_code_base64})
    
    # Generate PDF from HTML
    pdf_file = pdfkit.from_string(html_content, False)
    
    # Return PDF as downloadable file
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="visitor_pass.pdf"'
    return response
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('document'):
        # Get the image file and manual data inputs
        image_file = request.FILES['document']
        email = request.POST.get('email', 'Not Provided')
        mobile_number = request.POST.get('mobile_number', 'Not Provided')
        validity_time = request.POST.get('validity_time', 'Not Provided')

        # Convert image file to a format compatible with cv2
        np_image = np.frombuffer(image_file.read(), np.uint8)
        img = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        
        # Preprocess the image and perform OCR
        processed_img = preprocess_image(img)
        text = perform_ocr(processed_img)
        
        # Extract the information from the OCR text
        data = extract_information(text)
        
        # Prompt user to fill in missing values manually
        data = prompt_for_missing_data(data)
        
        # Store the data in the database
        store_data_in_db(data)

        # Generate QR code with extracted data
        qr_info = f"{data['Document Type']} | ID: {data['ID Number']} | Name: {data['Name']} | DOB: {data['Date of Birth']}"
        qr = qrcode.make(qr_info)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Prepare the context with extracted and manually entered data
        context = {
            "data": {
                "Document_Type": data.get("Document Type", "Not Found"),
                "ID_Number": data.get("ID Number", "Not Found"),
                "Name": data.get("Name", "Not Found"),
                "Date_of_Birth": data.get("Date of Birth", "Not Found"),
                "Email": email,
                "Mobile_Number": mobile_number,
                "Validity_Time": validity_time,
            },
            "qr_code_base64": qr_code_base64
        }

        # Render the visitor_pass.html with all data
        return render(request, 'visitor_pass.html', context)

    return render(request, 'upload.html')





