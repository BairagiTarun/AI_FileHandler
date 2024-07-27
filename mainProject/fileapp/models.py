from django.db import models

class Tag(models.Model):
    tag_name = models.CharField(max_length=255, unique=True)

class File(models.Model):
    file_name = models.CharField(max_length=255)
    file_content = models.FileField(upload_to='uploaded_files/')
    content_hash = models.CharField(max_length=64)

class FileTag(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)