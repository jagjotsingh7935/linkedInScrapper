# Generated by Django 5.1.6 on 2025-02-16 14:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobApp', '0002_joblisting_delete_job'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='joblisting',
            name='application_deadline',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='application_type',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='benefits',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='company_description',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='company_size',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='followers_count',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='qualifications',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='recruiters',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='required_skills',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='workplace_type',
        ),
    ]
