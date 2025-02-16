# models.py
from django.db import models

class JobListing(models.Model):
    company = models.CharField(max_length=255, null=True)
    company_url = models.URLField(max_length=500, null=True)
    job_title = models.CharField(max_length=255, null=True)
    job_url = models.URLField(max_length=500, null=True)
    location = models.CharField(max_length=255, null=True)
    posted_date = models.CharField(max_length=100, null=True)
    job_description = models.TextField(null=True)
    applicant_count = models.CharField(max_length=100, null=True)
    level = models.CharField(max_length=100, null=True)
    employment_type = models.CharField(max_length=100, null=True)
    industry = models.CharField(max_length=255, null=True)
    job_function = models.CharField(max_length=255, null=True)
    salary = models.CharField(max_length=255, null=True)

    class Meta:
        ordering = ['-id']