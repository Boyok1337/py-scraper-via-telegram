import time
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.scraper_interface import ResumeScraper


class RobotaUaScraper(ResumeScraper):
    def __init__(
        self,
        job_position: str,
        base_url: str = "https://robota.ua/candidates/",
        salary_expectation: List[int] = [],
        years_of_experience: int = None,
        skills: List[str] = None,
        location: str = None,
        criterias: List[str] = None,
    ):
        super().__init__(
            base_url,
            job_position,
            years_of_experience,
            skills,
            location,
            salary_expectation,
            criterias,
        )

    def get_filters(self, driver):
        filters = []
        if self.years_of_experience is not None:
            filters.append(self._filter_by_years_of_experience(driver))
        if self.skills:
            filters.append(self._filter_by_skills(driver))
        if self.salary_expectation:
            filters.append(self._filter_by_salary(driver))
        return filters

    def apply_filters(self, driver):
        request_url = self.base_url + "".join(self.job_position)
        request_url = request_url + "/"
        if self.location:
            request_url = request_url + self._filter_by_location(driver) + "?"
        else:
            request_url = request_url + "?"
        filters = "&".join(filter(None, self.get_filters(driver)))
        return request_url + filters

    def scrape(self):
        driver = self.get_driver()
        url = self.apply_filters(driver)
        driver.get(url)
        time.sleep(15)
        all_links = self.__get_all_pages(driver)
        self.get_detail_info(all_links, driver)

    def _filter_by_years_of_experience(self, driver):
        value = 0

        if self.years_of_experience:
            if self.years_of_experience == 0:
                value = 0
            elif self.years_of_experience == 1:
                value = 1
            elif self.years_of_experience in range(2, 5):
                value = 2
            elif self.years_of_experience in range(5, 10):
                value = 3
            elif self.years_of_experience in range(10, 99):
                value = 4
            return f'experienceIds=%5B"{value}"%5D'

        return None

    def _filter_by_location(self, driver):
        if self.location:
            return self.location
        return None

    def _filter_by_salary(self, driver):
        minimum = (
            self.salary_expectation[0]
            if len(self.salary_expectation) > 0
            and self.salary_expectation[0] is not None
            else "null"
        )
        maximum = (
            self.salary_expectation[1]
            if len(self.salary_expectation) > 1
            and self.salary_expectation[1] is not None
            else "null"
        )
        return f'salary=%7B"from"%3A{minimum}%2C"to"%3A{maximum}%7D'

    def __get_resume_links_from_page(self, driver):
        candidate_links = driver.find_elements(By.CSS_SELECTOR, "a.santa-no-underline")
        urls = [link.get_attribute("href") for link in candidate_links]
        return urls

    def __get_all_pages(self, driver):
        all_links = []
        while True:
            time.sleep(1)
            links = self.__get_resume_links_from_page(driver)
            all_links.extend(links)

            next_page = driver.find_elements(By.CSS_SELECTOR, "a.next")
            if not next_page:
                break

            next_page[0].click()

        return self.filter_candidate_links(all_links)

    @staticmethod
    def filter_candidate_links(links: List[str]) -> List[str]:
        return [
            link for link in links if link.startswith("https://robota.ua/candidates/")
        ]

    def get_title(self, driver):
        try:
            title_element = driver.find_element(
                By.CSS_SELECTOR,
                ".santa-mt-10.santa-typo-secondary.santa-text-black-700",
            )
            title = title_element.text
            return title
        except Exception as e:
            return self.job_position

    def get_skills(self, driver):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//h3[text()='Key Information']")
                )
            )
            section_element = driver.find_element(
                By.XPATH, "//h3[text()='Key Information']"
            )
            ul_element = section_element.find_element(
                By.XPATH, "./following-sibling::div/ul"
            )
            li_elements = ul_element.find_elements(By.CSS_SELECTOR, "li")
            skills = [li.text for li in li_elements]
            return skills
        except Exception as e:
            print(f"Error extracting skills: {e}")
            return []

    def get_salary_expectation(self, driver):
        try:
            salary_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "alliance-employer-resume-brief-info .santa-text-black-700",
                    )
                )
            )

            salary_text = salary_element.text.strip()

            return salary_text

        except Exception as e:
            print(f"Failed to get salary expectation: {e}")
            return None

    def get_detail_info(self, all_links, driver):
        data = []
        for link in all_links:
            title = self.get_title(driver)
            resume = link
            years_of_experience = self.years_of_experience
            skills = self.get_skills(driver)
            location = self.location
            salary_expectation = self.get_salary_expectation(driver)

            data.append(
                {
                    "title": title,
                    "resume": resume,
                    "years_of_experience": years_of_experience,
                    "skills": ", ".join(skills),
                    "location": location,
                    "salary_expectation": salary_expectation,
                }
            )

        self.save_to_file(data, "job_positions.csv")


if __name__ == "__main__":
    with RobotaUaScraper(
        job_position="python developer",
        years_of_experience=7,
        location="lviv",
        salary_expectation=[40000],
    ) as scraper:
        scraper.scrape()
        scraper.close()
