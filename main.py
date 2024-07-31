from scrapers.work_ua_scraper import WorkUaScraper
from scrapers.robota_ua_scraper import RobotaUaScraper

from utils import rate_candidates


if __name__ == "__main__":
    with RobotaUaScraper(
        job_position="python developer",
        years_of_experience=7,
        location="lviv",
        salary_expectation=[40000],
    ) as robota_scraper:
        robota_scraper.scrape()
        robota_scraper.close()

    with WorkUaScraper(
        job_position="python developer", years_of_experience=7, location="Lviv"
    ) as word_scraper:
        word_scraper.scrape()
        word_scraper.close()

    rate_candidates(
        "job_positions.csv",
        [
            "Python",
            "Django",
            "Linux",
            "PostgreSQL",
            "Flask",
        ],
        "sorted_resumes.csv",
    )
