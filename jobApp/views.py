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

def get_job_details(job_id, headers):
    """Extract all available details for a single job posting."""
    job_url = f'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
    job_data = {
        'company': None,
        'company_url': None,
        'job_title': None,
        'job_url': None,
        'location': None,
        'posted_date': None,
        'job_description': None,
        'applicant_count': None,
        'level': None,
        'employment_type': None,
        'job_function': None,
        'salary': None,
        'skills': []  # New field for skills
    }
    
    try:
        resp = requests.get(job_url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Company name and URL
        company_card = soup.find("div", {"class": "top-card-layout__card"})
        if company_card:
            company_link = company_card.find("a")
            if company_link:
                if company_link.find("img"):
                    job_data["company"] = company_link.find("img").get("alt", "").strip()
                job_data["company_url"] = company_link.get("href", "").strip()

        # Job title and URL
        title_section = soup.find("div", {"class": "top-card-layout__entity-info"})
        if title_section:
            title_link = title_section.find("a")
            if title_link:
                job_data["job_title"] = title_link.text.strip()
                job_data["job_url"] = title_link.get("href", "").strip()

        # Location
        location_elem = soup.find("span", {"class": "topcard__flavor--bullet"})
        if location_elem:
            job_data["location"] = location_elem.text.strip()

        # Posted date
        posted_elem = soup.find("span", {"class": "posted-time-ago__text"})
        if posted_elem:
            job_data["posted_date"] = posted_elem.text.strip()

        # Job description
        desc_elem = soup.find("div", {"class": "show-more-less-html__markup"})
        if desc_elem:
            job_data["job_description"] = desc_elem.text.strip()

        # Applicant count
        applicant_elem = soup.find("span", {"class": "num-applicants__caption"})
        if applicant_elem:
            job_data["applicant_count"] = applicant_elem.text.strip()

        # Job criteria (level, type, industry, function)
        criteria_list = soup.find("ul", {"class": "description__job-criteria-list"})
        if criteria_list:
            criteria_items = criteria_list.find_all("li")
            for item in criteria_items:
                header = item.find("h3")
                value = item.find("span")
                if header and value:
                    header_text = header.text.strip().lower()
                    if "seniority" in header_text:
                        job_data["level"] = value.text.strip()
                    elif "employment type" in header_text:
                        job_data["employment_type"] = value.text.strip()
                    elif "industry" in header_text:
                        job_data["industry"] = value.text.strip()
                    elif "job function" in header_text:
                        job_data["job_function"] = value.text.strip()

        # Salary
        salary_elem = soup.find("span", {"class": "compensation__salary"})
        if salary_elem:
            job_data["salary"] = salary_elem.text.strip()
        elif job_data.get("job_description"):
            description_text = job_data["job_description"].lower()
            salary_pattern = r'\$[\d,]+(?:\.\d+)?(?:\s*-\s*\$[\d,]+(?:\.\d+)?)?(?:\s*(?:per year|annually|yearly))?'
            match = re.search(salary_pattern, description_text)
            if match:
                job_data["salary"] = match.group(0)

        # Skills
        skills_section = soup.find("section", {"class": "skills-section"})
        if skills_section:
            print(f"Found skills section for job ID {job_id}")
            skills_items = skills_section.find_all("li", {"class": "job-details-skill-match-status-list__skill"})
            for skill_item in skills_items:
                skill_name = skill_item.find("span", {"class": "job-details-skill-match-status-list__skill-name"})
                if skill_name:
                    job_data["skills"].append(skill_name.text.strip())
        else:
            print(f"No skills section found for job ID {job_id}. Checking job description for skills.")
            # Fallback: Try to extract skills from the job description
            if job_data.get("job_description"):
                description_text = job_data["job_description"].lower()
                # Example: Look for common skill keywords in the description
                common_skills = ["python", "java", "javascript", "sql", "aws", "machine learning", "data analysis"]
                for skill in common_skills:
                    if skill in description_text:
                        job_data["skills"].append(skill)

    except Exception as e:
        print(f"Error processing job ID {job_id}: {e}")
        return None

    return job_data

class JobSearchView(APIView):
    def post(self, request):
        keywords = request.data.get('keywords', '').strip()
        location = request.data.get('location', '').strip()
        job_limit = int(request.data.get('job_limit', 100))
        
        if not keywords or not location:
            return Response(
                {"error": "Both keywords and location are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if job_limit < 1 or job_limit > 3000:
            return Response(
                {"error": "Job limit must be between 1 and 3000"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        base_url = create_linkedin_url(keywords, location)
        job_ids = get_job_ids(base_url, headers, job_limit)
        
        jobs_data = []
        for i, job_id in enumerate(job_ids, 1):
            print(f"\rProcessing job {i}/{len(job_ids)}", end="")
            job_data = get_job_details(job_id, headers)
            
            if job_data and job_data.get('job_title') and job_data.get('location'):
                # Split keywords and location into words for more flexible matching
                keyword_terms = set(keywords.lower().split())
                location_terms = set(location.lower().split())
                
                job_title_lower = job_data['job_title'].lower()
                job_location_lower = job_data['location'].lower()
                
                # Check if any of the keyword terms match in the job title
                title_matches = any(term in job_title_lower for term in keyword_terms)
                
                # Check if any of the location terms match in the job location
                location_matches = any(term in job_location_lower for term in location_terms)
                
                if title_matches and location_matches:
                    jobs_data.append(job_data)

        if not jobs_data:
            return Response({
                "message": f"No jobs found for {keywords} in {location}",
                "jobs": []
            })

        return Response({
            "message": f"Found {len(jobs_data)} matching jobs",
            "jobs": jobs_data
        })
    
    
class DownloadCSVView(APIView):
    def post(self, request):
        jobs_data = request.data
        if not jobs_data or not isinstance(jobs_data, list):
            return Response(
                {"error": "Invalid data format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        df = pd.DataFrame(jobs_data)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="jobs_data.csv"'
        df.to_csv(path_or_buf=response, index=False)
        return response