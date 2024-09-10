from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse, JsonResponse
from .models import File, Tag, FileTag
from .forms import UploadFileForm, SearchForm
from hashlib import sha256
import pdfplumber
import textract
import docx2txt
import spacy
from PIL import Image
import pytesseract
import os
import uuid
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from collections import defaultdict
import re  # Import for regex validation
import json  # Import for handling JSON data
from django.conf import settings

# Configure pytesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load spaCy NLP model
nlp = spacy.load('en_core_web_sm')


def extract_text_from_image(image_path):
    """Extracts text from an image file using OCR."""
    try:
        img = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(img)
        return extracted_text
    except Exception as e:
        return f"Error extracting text from image: {e}"


def pdf_reader(file_path):
    """Extracts text from a PDF file."""
    try:
        with pdfplumber.open(file_path) as pdf:
            all_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                all_text += text + "\n" if text else ""
            return all_text
    except Exception as e:
        return f"Error reading PDF: {e}"


def doc_reader(file_path):
    """Extracts text from DOC and DOCX files."""
    try:
        if file_path.name.endswith('.doc'):
            text = textract.process(file_path).decode('utf-8')
        else:
            text = docx2txt.process(file_path)
        return text
    except Exception as e:
        return f"Error reading document: {e}"


def generate_tags(content):
    """Generates tags from the content using NLP."""
    try:
        doc = nlp(content)
        tags = {token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop}
        return tags
    except Exception as e:
        print(f"Error generating tags: {e}")
        return set()


def rename_file_if_too_long(file_name, max_length=50):
    """Renames the file if its name exceeds the maximum length."""
    name, ext = os.path.splitext(file_name)
    if len(file_name) > max_length:
        trimmed_name = name[:max_length - len(ext) - 4] + "_" + str(uuid.uuid4())[:4] + ext
        return trimmed_name
    return file_name


def save_file(file_name, file_content, tags):
    """Saves the file and associates it with the provided tags."""
    try:
        file_name = rename_file_if_too_long(file_name, max_length=50)
        content_hash = sha256(file_content.read()).hexdigest()
        file_content.seek(0)  # Reset file pointer after reading
        
        # Save the file instance
        file_instance = File(file_name=file_name, file_content=file_content, content_hash=content_hash)
        file_instance.save()

        # Debugging: Log the saved file path
        saved_file_path = file_instance.file_content.path
        print(f"File saved at: {saved_file_path}")  # Debugging print
        
        # Verify that the file exists after saving
        if not os.path.exists(saved_file_path):
            print(f"Error: File was saved but does not exist at path: {saved_file_path}")  # Debugging print
            return  # Return early if file does not exist
        
        # Associate tags with the file
        for tag_name in tags:
            tag, created = Tag.objects.get_or_create(tag_name=tag_name)
            FileTag.objects.create(file=file_instance, tag=tag)
    except Exception as e:
        print(f"Error saving file: {e}")


def perform_search(query):
    """Performs a search on files based on the provided query."""
    search_tags = generate_tags(query)
    file_hit_count = defaultdict(int)
    for tag in search_tags:
        tag_file_hits = (
            FileTag.objects
            .filter(tag__tag_name=tag)
            .values_list('file', flat=True)
            .distinct()
        )
        for file_hit in tag_file_hits:
            file_hit_count[file_hit] += 1
    sorted_file_hits = sorted(
        file_hit_count.items(),
        key=lambda x: x[1],
        reverse=True
    )
    files = [File.objects.get(id=file_id) for file_id, _ in sorted_file_hits]
    return files


def upload_and_search(request):
    """Handles file uploads and search queries."""
    upload_form = UploadFileForm()
    search_form = SearchForm()
    files = []
    query = ""

    if request.method == 'POST':
        query = request.POST.get('query', '')
        if request.POST.get('action') == 'upload':
            upload_form = UploadFileForm(request.POST, request.FILES)
            if upload_form.is_valid():
                file = request.FILES['file']
                if file.name.endswith('.pdf'):
                    text = pdf_reader(file)
                elif file.name.endswith(('.doc', '.docx')):
                    text = doc_reader(file)
                elif file.name.endswith(('.jpg', 'png', 'jpeg')):
                    text = extract_text_from_image(file)

                # Generate tags and save file
                tags = generate_tags(text)
                save_file(file.name, file, tags)

                # Re-check saved files
                files = perform_search(query)
            else:
                print("Invalid upload form.")  # Debugging print
        elif request.POST.get('action') == 'search':
            search_form = SearchForm(request.POST)
            if search_form.is_valid():
                query = search_form.cleaned_data['query']
                files = perform_search(query)

    return render(request, 'fileapp/upload_and_search.html', {
        'upload_form': upload_form,
        'search_form': SearchForm(initial={'query': query}),
        'files': files,
        'query': query,
    })

@require_http_methods(["POST"])
def rename_file(request, file_id):
    """Renames a file based on user input."""
    try:
        # Fetch the file instance from the database
        file_instance = get_object_or_404(File, id=file_id)
        data = json.loads(request.body)  # Get JSON data from request
        new_name_base = data.get('new_name_base')

        # Check if new_name_base is provided
        if not new_name_base:
            return JsonResponse({'success': False, 'message': 'New name is required.'}, status=400)
        
        # Validate new_name_base: Ensure it doesn't contain invalid characters
        if not re.match(r'^[\w\-. ]+$', new_name_base):
            return JsonResponse({'success': False, 'message': 'Invalid new name. It must not contain special characters.'}, status=400)
        
        # Extract current extension from the existing file name
        old_ext = os.path.splitext(file_instance.file_content.name)[1]

        # Generate the new file name with the correct extension
        new_file_name = rename_file_if_too_long(new_name_base + old_ext)
        
        # Extract the current file name without the extension for comparison
        current_file_name_without_ext = os.path.splitext(file_instance.file_name)[0]

        # Check if the new file name (without extension) is the same as the old file name (without extension)
        if new_name_base == current_file_name_without_ext:
            # The new name is the same as the current name; no changes needed
            return JsonResponse({'success': True, 'new_name': file_instance.file_name})

        old_file_path = file_instance.file_content.path
        new_file_path = os.path.join(os.path.dirname(old_file_path), new_file_name)

        # Debugging: Print file paths
        print(f"Old path: {old_file_path}, New path: {new_file_path}")

        # Check if the old file path exists
        if not os.path.exists(old_file_path):
            print(f"Old file path does not exist: {old_file_path}. Attempting to refresh from DB.")  # Debugging print

            # Attempt to reload the file instance from the database in case of concurrent changes
            file_instance.refresh_from_db()
            old_file_path = file_instance.file_content.path  # Refresh the file path after reload

            # Check again if the refreshed old file path exists
            if not os.path.exists(old_file_path):
                print(f"File path still does not exist after refresh: {old_file_path}")  # Debugging print
                return JsonResponse({'success': False, 'message': f'Original file path does not exist: {old_file_path}'}, status=400)

        # Ensure the directory for new_file_path exists
        new_dir = os.path.dirname(new_file_path)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)

        # Check if new file path already exists to avoid conflicts
        if os.path.exists(new_file_path):
            return JsonResponse({'success': False, 'message': 'File with the new name already exists.'}, status=400)

        # Rename the file in the filesystem
        os.rename(old_file_path, new_file_path)
        print(f"File renamed successfully from {old_file_path} to {new_file_path}")  # Debugging print

        # Update the file instance in the database
        file_instance.file_name = new_file_name
        
        # Update the file content name with the correct relative path
        file_instance.file_content.name = os.path.relpath(new_file_path, settings.MEDIA_ROOT)
        file_instance.save()

        # Refresh the instance from the database to ensure correct paths
        file_instance.refresh_from_db()

        # Check if the file exists at the new location after saving
        if not os.path.exists(file_instance.file_content.path):
            print(f"Error: File was saved but does not exist at new path: {file_instance.file_content.path}")  # Debugging print
            return JsonResponse({'success': False, 'message': 'File not found after renaming.'}, status=500)

        return JsonResponse({'success': True, 'new_name': new_file_name})
    except Exception as e:
        # Log the error for debugging
        print(f"Error renaming file: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_http_methods(["POST"])
def delete_file(request, file_id):
    """Deletes a specified file."""
    try:
        # Fetch the file instance from the database
        file_instance = get_object_or_404(File, id=file_id)
        file_path = file_instance.file_content.path  # Get the file path from the file field

        # Check if the file exists in the filesystem before attempting to delete
        if os.path.exists(file_path):
            # Remove the file from the filesystem
            try:
                os.remove(file_path)
                print(f"File deleted from filesystem: {file_path}")  # Debugging print
            except Exception as e:
                print(f"Error deleting file from filesystem: {e}")  # Debugging print
                return JsonResponse({'success': False, 'message': f"Error deleting file from filesystem: {str(e)}"}, status=500)
        else:
            print(f"File does not exist in filesystem: {file_path}")  # Debugging print

        # Delete the file instance from the database
        file_instance.delete()
        print(f"File record deleted from database for file_id: {file_id}")  # Debugging print

        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error deleting file: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



def download_file(request, file_id):
    """Handles file download requests."""
    try:
        file_instance = get_object_or_404(File, id=file_id)
        file_path = file_instance.file_content.path
        file_name = file_instance.file_name
        
        # Check if file exists before serving it
        if not os.path.exists(file_path):
            return HttpResponse(f"Error: The requested file does not exist at path: {file_path}", status=404)

        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
    except Exception as e:
        print(f"Error downloading file: {e}")
        return HttpResponse(f"Error downloading file: {str(e)}", status=500)