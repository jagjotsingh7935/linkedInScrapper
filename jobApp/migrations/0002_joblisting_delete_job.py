# Generated by Django 5.1.6 on 2025-02-16 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobListing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(max_length=255, null=True)),
                ('company_url', models.URLField(max_length=500, null=True)),
                ('job_title', models.CharField(max_length=255, null=True)),
                ('job_url', models.URLField(max_length=500, null=True)),
                ('location', models.CharField(max_length=255, null=True)),
                ('workplace_type', models.CharField(max_length=100, null=True)),
                ('posted_date', models.CharField(max_length=100, null=True)),
                ('application_deadline', models.CharField(max_length=100, null=True)),
                ('job_description', models.TextField(null=True)),
                ('benefits', models.TextField(null=True)),
                ('company_description', models.TextField(null=True)),
                ('company_size', models.CharField(max_length=100, null=True)),
                ('followers_count', models.CharField(max_length=100, null=True)),
                ('applicant_count', models.CharField(max_length=100, null=True)),
                ('application_type', models.CharField(max_length=100, null=True)),
                ('required_skills', models.TextField(null=True)),
                ('qualifications', models.TextField(null=True)),
                ('level', models.CharField(max_length=100, null=True)),
                ('employment_type', models.CharField(max_length=100, null=True)),
                ('industry', models.CharField(max_length=255, null=True)),
                ('job_function', models.CharField(max_length=255, null=True)),
                ('salary', models.CharField(max_length=255, null=True)),
                ('recruiters', models.TextField(null=True)),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.DeleteModel(
            name='Job',
        ),
    ]
