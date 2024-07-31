import csv
import os
from abc import ABC, abstractmethod
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class ResumeScraper(ABC):
    def __init__(
        self,
        base_url: str,
        job_position: str,
        years_of_experience: int = None,
        skills: List[str] = None,
        location: List[str] = None,
        salary_expectation: int = None,
        criterias: List[str] = None,
    ):
        self.base_url = base_url
        self.job_position = job_position
        self.years_of_experience = years_of_experience
        self.skills = skills
        self.location = location
        self.salary_expectation = salary_expectation
        self.criterias = criterias
        self._driver = None

    def __enter__(self):
        self.__setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __setup_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self._driver = webdriver.Chrome(options=chrome_options)

    def get_driver(self):
        if not self._driver:
            self.__setup_driver()
        return self._driver

    def close(self):
        self._driver.quit()

    @abstractmethod
    def get_filters(self, driver):
        pass

    @abstractmethod
    def apply_filters(self, driver):
        pass

    @abstractmethod
    def scrape(self):
        pass

    @staticmethod
    def save_to_file(data: List[dict], filename: str):
        file_exists = os.path.isfile(filename)

        existing_links = set()
        if file_exists:
            try:
                with open(filename, mode="r", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    existing_links = set(row["resume"] for row in reader)
            except Exception as e:
                print(f"Failed to read existing file for uniqueness check: {e}")

        new_data = [item for item in data if item["resume"] not in existing_links]

        if not new_data:
            print("No new unique candidates to add.")
            return

        try:
            with open(filename, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "title",
                        "resume",
                        "years_of_experience",
                        "skills",
                        "location",
                        "salary_expectation",
                    ],
                )

                if not file_exists:
                    writer.writeheader()

                writer.writerows(new_data)
            print(f"Data successfully added to the file: {filename}")
        except Exception as e:
            print(f"Failed to add data to file: {e}")
