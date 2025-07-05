import os
from selenium import webdriver
from linkedin_scraper import Person, actions


class UserProfileTools:
    def __init__(self):
        self.driver = webdriver.firefox

    def fetch_user_profile(self, linkedin_url):
        try:
            self._login_linked_in()
            lead_info = dict()
            person = Person(linkedin_url, driver=self.driver)
            lead_info['name'] = person.name
            lead_info['company'] = person.company
            lead_info['Designation'] = person.job_title
            lead_info['about'] = person.about
            lead_info['years_of_experience'] = self._get_years_of_experience(person.experiences)
            return lead_info
        except Exception as error:
            print(f"An error occurred while fetching user profile: {error}")
            return None

    def _login_linked_in(self):
        driver = webdriver.Chrome()
        email = os.getenv("LINKEDIN_USER")
        password = os.getenv("LINKEDIN_PASSWORD")
        actions.login(driver, email, password)

    def _convert_months_to_years_months(self, total_months):
        years = total_months // 12
        months = total_months % 12
        return years, months

    def _parse_duration(self, duration):
        years, months = 0, 0
        if 'yr' in duration:
            years = int(duration.split('yr')[0].strip())
        if 'mo' in duration:
            months_part = duration.split('yr')[-1].strip()
            months = int(months_part.split('mo')[0].strip())

        return years * 12 + months

    def _get_years_of_experience(self, experiences):
        durations = [experience.duration for experience in experiences]
        durations = [
            '0 yr 6 mo' if duration == 'Less than a year' else
            duration.replace(' yrs', ' yrs').replace(' yrs', ' yr').replace(' mos', ' mos').replace(' mos', ' mo')
            for duration in durations if duration is not None
        ]
        # Calculate total duration in months
        total_months = sum(self._parse_duration(dur) for dur in durations)

        # Convert total months back to years and months
        total_years, total_months = self._convert_months_to_years_months(total_months)

        # Display result
        print(f"Total Duration: {total_years} yr {total_months} mos")

        return f"Total Duration: {total_years} yr {total_months} mos"
