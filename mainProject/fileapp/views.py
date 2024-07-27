from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseServerError,JsonResponse
from .models import File, Tag, FileTag
from .forms import UploadFileForm, SearchForm
import pdfplumber
from pdfminer.high_level import extract_text
import textract
import docx2txt
from hashlib import sha256
import spacy
import mimetypes
import os
from django.conf import settings
from PIL import Image
import pytesseract

# Path to the Tesseract executable (change this as per your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
nlp = spacy.load('en_core_web_sm')

def extract_text_from_image(image_path):
    img = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(img)
    return extracted_text

def pdf_reader(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            all_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                all_text += text + "\n"  # Add a newline between pages

            return all_text
    except Exception as e:
        return


def doc_reader(file_path):
    try:
        if file_path.name.endswith('.doc'):
            text = textract.process(file_path).decode('utf-8')
        else:
            text = docx2txt.process(file_path)
        return text
    except Exception as e:
        return str(e)


def generate_tags(content):
    doc = nlp(content)
    tags = {token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop}
    return tags


def save_file(file_name, file_content, tags):
    content_hash = sha256(file_content.read()).hexdigest()
    file = File(file_name=file_name, file_content=file_content, content_hash=content_hash)
    file_instance=file.save()
    for tag_name in tags:
        tag, created = Tag.objects.get_or_create(tag_name=tag_name)
        FileTag.objects.create(file=file, tag=tag)


def upload_and_search(request):
    if request.method == 'POST':
        upload_form = UploadFileForm(request.POST, request.FILES)
        search_form = SearchForm(request.POST)

        if 'upload' in request.POST:
            if upload_form.is_valid():
                file = request.FILES['file']
                if file.name.endswith('.pdf'):
                    text = pdf_reader(file)
                elif file.name.endswith(('.doc', '.docx')):
                    text = doc_reader(file)
                elif file.name.endswith(('.jpg','png','jpeg')):
                    text = extract_text_from_image(file)
                tags = generate_tags(text)
                save_file(file.name, file, tags)
                return redirect('upload_and_search')

        if 'search' in request.POST:
            if search_form.is_valid():
                query = search_form.cleaned_data['query']
                files = File.objects.filter(filetag__tag__tag_name__icontains=query).distinct()
                return render(request, 'fileapp/upload_and_search.html',
                              {'upload_form': upload_form, 'search_form': search_form, 'files': files})
    else:
        upload_form = UploadFileForm()
        search_form = SearchForm()

    return render(request, 'fileapp/upload_and_search.html', {'upload_form': upload_form, 'search_form': search_form})


def view_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    return render(request, 'fileapp/view_file.html', {'file': file})


def download_file(request, file_id):
    try:
        file = get_object_or_404(File, id=file_id)
        file_path = file.file_content.path
        file_name = file.file_name

        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                mime_type, _ = mimetypes.guess_type(file_path)
                response = HttpResponse(fh.read(), content_type=mime_type)
                response['Content-Disposition'] = f'attachment; filename="{file_name}"'
                return response
        else:
            raise FileNotFoundError(f'The file "{file_name}" does not exist at "{file_path}".')
    except Exception as e:
        return HttpResponseServerError(f'Error downloading file: {str(e)}')
