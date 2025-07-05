1q
import time

from bs4 import BeautifulSoup
import os
from selenium import webdriver
from linkedin_scraper import actions


class CompanyProfileTool:
    def __init__(self):
        pass

    def fetch_company_profile(self, company_name):
        try:
            time.sleep(10)
            driver = webdriver.Firefox()
            email = os.getenv("LINKEDIN_USER")
            password = os.getenv("LINKEDIN_PASSWORD")
            actions.login(driver, email, password)
            company_info = dict()
            company_url = f"https://www.linkedin.com/company/{company_name}/about/"
            driver.get(company_url)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            about_section = soup.find('section', {
                'class': 'artdeco-card org-page-details-module__card-spacing artdeco-card org-about-module__margin-bottom'})
            # overview_header = about_section.find('h2', {'class': 'text-heading-xlarge'}).text.strip()
            overview_text = about_section.find('p', {
                'class': 'break-words white-space-pre-wrap t-black--light text-body-medium'}).text.strip()
            details = about_section.find('dl', {'class': 'overflow-hidden'})
            for dt, dd in zip(details.find_all('dt'), details.find_all('dd')):
                key = dt.find('h3').text.strip()
                value = dd.text.strip()
                if dd.find('a'):  # Check if there's a link in the value
                    value = dd.find('a')['href']
                company_info[key] = value
            company_info["overview_text"] = overview_text
            # print(company_info)
            driver.quit()
            return company_info
        except Exception as error:
            print(f"An error occurred while fetching company profile: {error}")
            return None



