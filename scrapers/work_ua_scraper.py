import time
from typing import List

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.scraper_interface import ResumeScraper


class WorkUaScraper(ResumeScraper):
    def __init__(
        self,
        job_position: str,
        base_url: str = "https://www.work.ua/employer/",
        years_of_experience: int = None,
        skills: List[str] = None,
        location: str = None,
        salary_expectation: int = None,
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
        if self.years_of_experience is not None:
            self._filter_by_years_of_experience(driver)

    def apply_filters(self, driver):
        filter_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#filter-mobile-menu"))
        )
        filter_button.click()

        self.get_filters(driver)

        filter_apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#filters-apply"))
        )
        filter_apply_button.click()

    def scrape(self):
        driver = self.get_driver()
        driver.get(self.base_url)

        self._input_job_position(driver)
        self._input_city(driver)
        time.sleep(1)
        self._click_search_button(driver)
        time.sleep(1)
        self.apply_filters(driver)
        time.sleep(1)

        all_links = self._get_all_pages(driver)
        self.get_detail_info(all_links, driver)

    def _input_job_position(self, driver):
        position_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#search"))
        )
        position_input.clear()
        position_input.send_keys(self.job_position)
        position_input.send_keys(Keys.ENTER)

    def _input_city(self, driver):
        city_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#city"))
        )
        city_input.click()

        city_input.send_keys(Keys.CONTROL + "a")
        city_input.send_keys(Keys.BACKSPACE)

        city_input.send_keys(self.location)
        city_input.send_keys(Keys.ENTER)

    def _click_search_button(self, driver):
        search_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#sm-but"))
        )
        search_button.click()

    def _filter_by_years_of_experience(self, driver):
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#experience_selection"))
        )

        experience_options = driver.find_elements(
            By.CSS_SELECTOR, "#experience_selection li"
        )

        index_mapping = {
            1: 1,
            2: 2,
            3: 3,
            4: 3,
            5: 3,
        }

        if self.years_of_experience > 5:
            target_index = len(experience_options) - 1
        elif self.years_of_experience == 0:
            target_index = 0
        else:
            target_index = index_mapping.get(self.years_of_experience, None)

        if target_index is not None and target_index < len(experience_options):
            checkbox_label = experience_options[target_index].find_element(
                By.TAG_NAME, "label"
            )
            checkbox_input = checkbox_label.find_element(By.TAG_NAME, "input")
            driver.execute_script("arguments[0].click();", checkbox_input)

    def __get_resume_links_from_page(self, driver):
        resume_links = driver.find_elements(
            By.CSS_SELECTOR,
            "div.card.card-hover.card-search.resume-link.card-visited.wordwrap a[href]",
        )
        links = [
            link.get_attribute("href")
            for link in resume_links
            if link.get_attribute("href")
        ]
        return links

    def _get_all_pages(self, driver, all_links: List[str] = []):
        all_links = []

        while True:
            resume_links = driver.find_elements(
                By.CSS_SELECTOR,
                "div.card.card-hover.card-search.resume-link.card-visited.wordwrap a[href]",
            )
            links = [
                link.get_attribute("href")
                for link in resume_links
                if link.get_attribute("href")
            ]
            all_links.extend(links)

            try:
                next_buttons = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (
                            By.CSS_SELECTOR,
                            "ul.pagination li.no-style.add-left-default a.link-icon",
                        )
                    )
                )

                next_button = None
                for button in next_buttons:
                    if "disabled" not in button.get_attribute("class"):
                        next_button = button
                        break

                if not next_button:
                    print("The 'Next' button is inactive or not found, finished.")
                    break

                next_url = next_button.get_attribute("href")
                driver.get(next_url)
                time.sleep(1)

            except Exception as e:
                print("Error clicking 'Next' button:", e)
                break

        return all_links

    def get_title(self, driver):
        try:
            h2_element = driver.find_element(By.CSS_SELECTOR, "h2.mt-lg")
            h2_text = h2_element.text

            title_parts = h2_text.split(" ")
            title = " ".join(title_parts[:-1])
            salary = title_parts[-1] if title_parts else None

            return title.strip(), salary.strip()
        except Exception as e:
            print("Error getting title:", e)
            return None, None

    def get_skills(self, driver):
        try:
            skills = []
            skills_header = driver.find_element(By.CSS_SELECTOR, "h2.mb-sm")
            if skills_header and skills_header.text.strip() == "Knowledge and Skills":
                skill_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    "ul.list-unstyled.my-0.flex.flex-wrap li span.ellipsis",
                )
                skills = [element.text.strip() for element in skill_elements]
            return skills
        except Exception as e:
            print("Error getting skills:", e)
            return []

    def get_detail_info(self, all_links, driver):
        data = []
        for link in set(all_links):
            driver.get(link)
            title, salary = self.get_title(driver)
            resume = link
            years_of_experience = self.years_of_experience
            skills = self.get_skills(driver)
            location = self.location
            salary_expectation = salary if salary else self.salary_expectation

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
    scraper = WorkUaScraper(
        job_position="python developer", years_of_experience=0, location="Lviv"
    )
    scraper.scrape()
