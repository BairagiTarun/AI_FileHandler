document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('uploadForm');
    const uploadMessage = document.getElementById('uploadMessage');

    uploadForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const formData = new FormData(uploadForm);

        fetch(uploadForm.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                uploadMessage.textContent = 'File uploaded successfully!';
                uploadMessage.style.color = 'green';
                setTimeout(function () {
                    location.reload();
                }, 1500); // Refresh the page after 1.5 seconds
            } else {
                uploadMessage.textContent = 'File upload failed.';
                uploadMessage.style.color = 'red';
            }
        })
        .catch(error => {
            uploadMessage.textContent = 'An error occurred during file upload.';
            uploadMessage.style.color = 'red';
        });
    });
});
