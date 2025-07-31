import scrapy
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from uic_scraper.items import UicProgramItem

class UICProgramsSpider(scrapy.Spider):
    name = "uic_spider"
    
    # ✅ Main program URLs
    start_urls = [
        "https://business.uic.edu/graduate/degrees/master-science-accounting/",
        "https://business.uic.edu/graduate/degrees/master-science-finance/",
        "https://business.uic.edu/graduate/degrees/master-business-administration/",
        "https://business.uic.edu/graduate/degrees/master-science-business-analytics/",
        "https://business.uic.edu/graduate/degrees/master-science-management-information-systems/",
        "https://business.uic.edu/graduate/degrees/cmba/",
        "https://business.uic.edu/graduate/degrees/master-of-science-in-supply-chain-and-operations-management/",
        "https://business.uic.edu/graduate/degrees/master-science-marketing/"
    ]

    # ✅ Matching catalog URLs
    requirement_urls = {
    "Master of Science in Business Analytics": "https://catalog.uic.edu/gcat/colleges-schools/business-administration/bus-anal/ms/",
    "Master of Science in Management Information Systems": "https://catalog.uic.edu/gcat/colleges-schools/business-administration/mis/ms/",
    "Master of Science in Accounting": "https://catalog.uic.edu/gcat/colleges-schools/business-administration/actg/ms/",
    "Master of Science in Finance": "https://catalog.uic.edu/gcat/colleges-schools/business-administration/fin/ms/",
    "Master of Science in Marketing": "https://catalog.uic.edu/gcat/colleges-schools/business-administration/mktg/ms/",
    "Master of Business Administration": "https://catalog.uic.edu/gcat/colleges-schools/business-administration/mba/mba/",
    "Master of Science in Supply Chain and Operations Management": "https://catalog.uic.edu/gcat/colleges-schools/business-administration/supply-chain-operations-mgmt/ms/"
    }

    def __init__(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def parse(self, response):
        """Parse the main program page with Selenium"""
        self.driver.get(response.url)
        time.sleep(2)

        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        item = UicProgramItem()
        item["program_url"] = response.url
        item["program_name"] = soup.find("title").get_text(strip=True)
        item["full_page_content"] = soup.get_text(separator=" ", strip=True)

        # ✅ Clean title to match dictionary
        cleaned_title = item["program_name"].split("|")[0].strip()
        req_url = self.requirement_urls.get(cleaned_title)

        if req_url:
            yield scrapy.Request(
                url=req_url,
                callback=self.parse_requirements,
                meta={"item": item}
            )
        else:
            item["requirement_page_content"] = "N/A"
            yield item

    def parse_requirements(self, response):
        """Parse the catalog requirement page with Selenium"""
        item = response.meta["item"]

        try:
            self.driver.get(response.url)
            time.sleep(2)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            item["requirement_page_content"] = soup.get_text(separator=" ", strip=True)
        except Exception as e:
            item["requirement_page_content"] = f"Error loading requirements: {e}"

        yield item

    def closed(self, reason):
        """Close the Selenium WebDriver when done"""
        self.driver.quit()