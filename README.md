# SmartFile

## Overview

**SmartFile** is a Django-based web application designed for managing files with advanced functionalities like uploading, searching, viewing, and downloading. The application supports multiple file types, including PDFs, Word documents, and images, and extracts text content from these files to generate searchable tags. These tags enable users to efficiently search and retrieve files within the system.

## Features

- **File Upload:** Users can upload files in various formats, including PDFs, Word documents, and images.
- **Text Extraction:** Extracts text from uploaded files using tools like `pdfplumber`, `textract`, `docx2txt`, and `pytesseract` (for OCR on images).
- **Tag Generation:** Automatically generates tags from the extracted text using natural language processing (NLP) with SpaCy.
- **Search Functionality:** Allows users to search for files based on the generated tags.
- **File Viewing:** Provides in-browser viewing of files, with different rendering methods depending on the file type.
- **File Downloading:** Enables users to download files stored in the system.

## Technologies Used

- **Django:** The web framework used to build the application.
- **Python Libraries:**
  - `pdfplumber` for extracting text from PDF files.
  - `textract` and `docx2txt` for extracting text from Word documents.
  - `PIL (Pillow)` and `pytesseract` for OCR and image text extraction.
  - `SpaCy` for natural language processing and tag generation.
- **HTML/CSS:** For building the user interface and styling.
- **JavaScript:** For dynamic file previews and handling front-end interactions.

## Project Structure

- **`views.py`:** Contains the core logic for handling file uploads, text extraction, tag generation, search functionality, and file downloads.
- **`models.py`:** Defines the database schema for storing files, tags, and the many-to-many relationships between them.
- **`forms.py`:** Manages forms for file uploads and search queries.
- **`urls.py`:** Maps views to specific URL patterns for routing.
- **Templates (`.html` files):** Render the user interface for uploading, searching, viewing, and downloading files.
- **Static Files (`styles.css`):** Provides the CSS for styling the application.

## Installation

### Prerequisites

- Python 3.x
- Django 3.x or higher
- Tesseract OCR (for image text extraction)
- Virtual environment setup (recommended)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/smartfile.git
   cd smartfile
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database:**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the application:**
   Open your browser and navigate to `http://127.0.0.1:8000/`.

### Tesseract OCR Installation

Ensure Tesseract is installed on your system and the path to the executable is correctly set in `view.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust this path as needed
```

## Usage

### Uploading Files
1. Navigate to the main page.
2. Use the "Upload File" form to select and upload your file.
3. The application will process the file, extract text, generate tags, and store the file.

### Searching Files
1. Use the "Search Files" form to enter a search query.
2. The application will return a list of files matching the search tags.
3. Click on a file to view or download it.

### Viewing and Downloading Files
- Files can be viewed in the browser if supported (e.g., PDFs, images).
- Files can be downloaded directly using the "Download" button.

## Contributing

Contributions to **SmartFile** are welcome! If you have any ideas or enhancements, feel free to submit a pull request or open an issue.

### How to Contribute

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add your feature'`).
5. Push to the branch (`git push origin feature/your-feature`).
6. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgments

- The Django community for the robust framework.
- The developers of the Python libraries used in this project.
- Open-source contributors for making the tools and resources available.

---

Feel free to customize the README to better fit your project's specific details, such as the repository URL and additional setup instructions.
