# Smart Media Privacy Web App  
A privacy-focused image processing web application built with **Python, Flask, OpenCV, and Tesseract OCR**.  
Users can upload an image and apply advanced privacy filters like **face blur**, **full image blur**, or **text-based sensitive information masking**.

🌐 **Live Demo:**  
https://smart-media-privacy.onrender.com

---

## 🚀 Features

### 🔹 1. Face Blur  
Detects human faces using **OpenCV Haar Cascades** and applies selective Gaussian blur on detected regions.

### 🔹 2. Full Image Blur  
Applies global Gaussian blur on the entire image with an adjustable blur intensity slider.

### 🔹 3. OCR Text Blur (Sensitive Info Detection)  
Uses **Tesseract OCR** to extract text from the image and automatically detects sensitive items such as:  
- Email addresses  
- Phone numbers  
- Number-like patterns (card-like / ID-like)

Detected text regions are blurred while keeping the rest of the image clear.

### 🔹 4. Blur Intensity Control  
Choose between **light**, **normal**, or **strong** blur levels.

### 🔹 5. Processing History  
Stores each processed operation in a **SQLite database**, including:  
- File name  
- Mode selected  
- Blur level  
- Timestamp  
- Sensitive items detected  
- Download link for blurred image  

### 🔹 6. Side-by-Side Comparison  
Shows **Original vs Processed** images on result page.

---

## 🛠️ Tech Stack

| Component | Technology |
|----------|------------|
| Backend | Python, Flask |
| Image Processing | OpenCV |
| OCR | Tesseract OCR + pytesseract |
| Database | SQLite |
| Deployment | Render |
| Frontend | HTML, CSS (Flask templates) |

---

## 📁 Project Structure
Smart_media_Privacy/
│
├── app.py
├── requirements.txt
├── Procfile
├── history.db
├── uploads/
├── templates/
│ ├── home.html
│ ├── result.html
│ └── history.html
└── haarcascade_frontalface_default.xml

---

## ▶️ How to Run Locally

### 1. Clone the repo
git clone https://github.com/vibhaa24/Smart_media_Privacy.git
cd Smart_media_Privacy

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Run the app
python app.py

App runs at:  
`http://127.0.0.1:5000`

---

## 🌐 Deployment  
Deployed on **Render** using:

**Build Command:**
pip install -r requirements.txt

**Start Command:**
gunicorn app:app

---

## 📸 Sample Output

- Face blur  
- Full blur  
- OCR text blur with sensitive info masked  
- Side-by-side image comparison  

(You can add screenshots of your app here for extra impact!)

---

## 🎯 Why This Project is Special

This project demonstrates real-world skills in:

- Computer Vision  
- OCR processing  
- Regex-based sensitivity detection  
- Backend development  
- Template rendering  
- Deployment pipelines  
- Handling real user uploads  
- Data storage (SQLite)  

Perfect for resumes, GitHub portfolios, and interviews.

---

## 👩‍💻 Developer  
**Vibha Pandey**  
Python Developer | AI Enthusiast | Web App Builder

---








