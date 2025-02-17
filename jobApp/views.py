from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework import status
import pandas as pd
from django.http import HttpResponse
import json
import re
import requests
from bs4 import BeautifulSoup
import math
from urllib.parse import quote
from .models import JobListing
from .serializers import JobListingSerializer
import os
from django.conf import settings

# Import Vercel database wrapper from settings
VERCEL_DEPLOYMENT = os.getenv('VERCEL_DEPLOYMENT', False)
if VERCEL_DEPLOYMENT:
    from job.settings import VercelDatabase

def create_linkedin_url(keywords, location):
    """Create LinkedIn search URL with encoded parameters."""
    encoded_keywords = quote(keywords)
    encoded_location = quote(location)
    return f'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_keywords}&location={encoded_location}&start={{}}'

def get_job_ids(base_url, headers, job_limit=100):
    """Collect job IDs from search results."""
    job_ids = []
    page = 0
    
    while len(job_ids) < job_limit:
        try:
            res = requests.get(base_url.format(page * 25), headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            jobs_on_page = soup.find_all("li")
            
            if not jobs_on_page:
                break
                
            print(f"Found {len(jobs_on_page)} jobs on page {page+1}")
            
            for job in jobs_on_page:
                if len(job_ids) >= job_limit:
                    break
                    
                try:
                    base_card = job.find("div", {"class": "base-card"})
                    if base_card and base_card.get('data-entity-urn'):
                        jobid = base_card.get('data-entity-urn').split(":")[3]
                        job_ids.append(jobid)
                except Exception as e:
                    print(f"Error processing job: {e}")
                    continue
            
            page += 1
            
        except Exception as e:
            print(f"Error fetching page {page+1}: {e}")
            break
            
    return job_ids[:job_limit]

def get_recruiter_details(soup):
    """Extract recruiter profile links from LinkedIn job postings."""
    recruiters = []
    try:
        section = None
        section_headers = [
            "People you can reach out to",
            "Hiring Team",
            "Meet the team",
            "Recruiters"
        ]
        
        for header_text in section_headers:
            section = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] 
                               and header_text in tag.text)
            if section:
                break
                
        if not section:
            section = soup.find("div", {"class": "hirer-card__hirer-information"})
            
        if not section:
            section = soup.find("section", {"class": "people-you-can-know"})
            
        if section:
            container = section.find_next("div") if section.name in ['h2', 'h3', 'h4'] else section
            profile_links = container.find_all("a", class_="app-aware-link", limit=5)
            
            for link in profile_links:
                try:
                    if "search" in link.get("href", ""):
                        continue
                        
                    profile_url = link["href"].split("?")[0]
                    name = None
                    
                    name_elements = [
                        link.find("span", {"dir": "ltr"}),
                        link.find("span", class_="name"),
                        link.find("h3", class_="base-search-card__title"),
                        link.find("span", class_="entity-result__title-text")
                    ]
                    
                    for elem in name_elements:
                        if elem and elem.text.strip():
                            name = elem.text.strip()
                            break
                            
                    if name and profile_url and "/in/" in profile_url:
                        recruiters.append({
                            "name": name,
                            "profile_url": profile_url
                        })
                        
                except Exception as e:
                    print(f"Error processing recruiter link: {e}")
                    continue
                    
    except Exception as e:
        print(f"Error extracting recruiter links: {e}")
    
    return recruiters

def get_job_details(job_id, headers):
    """Extract all available details for a single job posting."""
    job_url = f'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
    job_data = {}
    
    try:
        resp = requests.get(job_url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        field_mappings = {
            "company": ("div", {"class": "top-card-layout__card"}, "a img", "alt"),
            "company_url": ("div", {"class": "top-card-layout__card"}, "a", "href"),
            "job_title": ("div", {"class": "top-card-layout__entity-info"}, "a", "text"),
            "job_url": ("div", {"class": "top-card-layout__entity-info"}, "a", "href"),
            "location": ("span", {"class": "topcard__flavor--bullet"}, None, "text"),
            "posted_date": ("span", {"class": "posted-time-ago__text"}, None, "text"),
            "job_description": ("div", {"class": "show-more-less-html__markup"}, None, "text"),
            "applicant_count": ("span", {"class": "num-applicants__caption"}, None, "text"),
        }
        
        for field, (tag, attrs, subtag, attr) in field_mappings.items():
            try:
                element = soup.find(tag, attrs)
                if subtag:
                    if " " in subtag:
                        for sub in subtag.split():
                            element = element.find(sub)
                    else:
                        element = element.find(subtag)
                
                if attr == "text":
                    value = element.text.strip() if element else None
                else:
                    value = element.get(attr) if element else None
                
                job_data[field] = value.strip() if value else None
            except:
                job_data[field] = None
        
        criteria_mappings = {
            "level": 0,
            "employment_type": 1,
            "industry": 2,
            "job_function": 3
        }
        
        try:
            criteria_list = soup.find("ul", {"class": "description__job-criteria-list"})
            if criteria_list:
                criteria_items = criteria_list.find_all("li")
                for field, index in criteria_mappings.items():
                    try:
                        if index < len(criteria_items):
                            job_data[field] = criteria_items[index].text.split(":")[-1].strip()
                        else:
                            job_data[field] = None
                    except:
                        job_data[field] = None
            else:
                for field in criteria_mappings:
                    job_data[field] = None
        except Exception as e:
            print(f"Error extracting job criteria: {e}")
            for field in criteria_mappings:
                job_data[field] = None
        
        try:
            salary_element = soup.find("span", {"class": "compensation__salary"})
            if salary_element:
                job_data["salary"] = salary_element.text.strip()
            elif job_data.get("job_description"):
                description_text = job_data["job_description"].lower()
                salary_pattern = r'\$[\d,]+(?:\.\d+)?(?:\s*-\s*\$[\d,]+(?:\.\d+)?)?(?:\s*(?:per year|annually|yearly))?'
                match = re.search(salary_pattern, description_text)
                job_data["salary"] = match.group(0) if match else None
            else:
                job_data["salary"] = None
        except Exception as e:
            print(f"Error extracting salary: {e}")
            job_data["salary"] = None
            
    except Exception as e:
        print(f"Error processing job ID {job_id}: {e}")
        return None
        
    return job_data

class JobSearchView(APIView):
    def post(self, request):
        try:
            keywords = request.data.get('keywords')
            location = request.data.get('location')
            job_limit = int(request.data.get('job_limit', 100))
            
            if not keywords or not location:
                return Response(
                    {"error": "Both keywords and location are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if job_limit < 1 or job_limit > 1000:
                return Response(
                    {"error": "Job limit must be between 1 and 1000"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            base_url = create_linkedin_url(keywords, location)
            job_ids = get_job_ids(base_url, headers, job_limit)
            
            def process_jobs():
                JobListing.objects.all().delete()
                jobs_data = []
                
                for i, job_id in enumerate(job_ids, 1):
                    print(f"\rProcessing job {i}/{len(job_ids)}", end="")
                    job_data = get_job_details(job_id, headers)
                    if job_data:
                        job_listing = JobListing.objects.create(**job_data)
                        jobs_data.append(job_listing)
                
                return jobs_data

            if VERCEL_DEPLOYMENT:
                with VercelDatabase():
                    jobs_data = process_jobs()
            else:
                jobs_data = process_jobs()

            serializer = JobListingSerializer(jobs_data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        try:
            if VERCEL_DEPLOYMENT:
                with VercelDatabase():
                    jobs = JobListing.objects.all()
                    serializer = JobListingSerializer(jobs, many=True)
            else:
                jobs = JobListing.objects.all()
                serializer = JobListingSerializer(jobs, many=True)
                
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DownloadCSVView(APIView):
    def get(self, request):
        try:
            if VERCEL_DEPLOYMENT:
                with VercelDatabase():
                    jobs = JobListing.objects.all()
                    serializer = JobListingSerializer(jobs, many=True)
            else:
                jobs = JobListing.objects.all()
                serializer = JobListingSerializer(jobs, many=True)
            
            df = pd.DataFrame(serializer.data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="jobs_data.csv"'
            
            df.to_csv(path_or_buf=response, index=False)
            return response
            
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )