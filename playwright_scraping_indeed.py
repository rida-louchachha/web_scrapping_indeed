from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import pandas as pd
import os
import random

def scrape_indeed(playwright):
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir=os.path.abspath("my_verified_browser"),  # Persistent session
        channel="chrome",
        headless=False,
        viewport={"width": 1280, "height": 800},
    )

    page = browser.new_page()
    stealth_sync(page)  # 👈 Apply stealth here

    page_count = 0
    jobs = []

    while page_count < 2:
        print(f"[INFO] Scraping listing page {page_count + 1}")
        page.goto(f'https://www.indeed.com/jobs?q=python+developer&start={page_count * 10}')
        page.wait_for_timeout(random.randint(5000, 8000))

        if "captcha" in page.url or "detected unusual traffic" in page.content():
            print("[❌] CAPTCHA or bot detection triggered. Please solve it manually.")
            page.wait_for_timeout(60000)

        vacancies = page.locator('.cardOutline')

        for vacancy in vacancies.element_handles():
            try:
                title_el = vacancy.query_selector("h2")
                link_el = vacancy.query_selector("a")
                if title_el and link_el:
                    title = title_el.inner_text()
                    url = "https://www.indeed.com" + link_el.get_attribute("href")
                    jobs.append({"Title": title, "URL": url})
            except Exception as e:
                print(f"[ERROR] Job parsing failed: {e}")

        page_count += 1

    all_items = []

    for job in jobs:
        print(f"[INFO] Scraping details: {job['Title']}")
        try:
            page.goto(job["URL"])
            page.wait_for_timeout(random.randint(3000, 5000))

            item = {
                "Title": job['Title'],
                "URL": job['URL'],
                "CompanyName": "",
                "Location": "",
                "Salaryinfo": ""
            }

            company = page.get_by_test_id("inlineHeader-companyName")
            if company.count() > 0:
                item["CompanyName"] = company.nth(0).inner_text()

            location = page.get_by_test_id("inlineHeader-companyLocation")
            if location.count() > 0:
                item["Location"] = location.nth(0).inner_text()

            salary = page.get_by_test_id("jobsearch-OtherJobDetailsContainer")
            if salary.count() > 0:
                item["Salaryinfo"] = salary.nth(0).inner_text()

            all_items.append(item)

        except Exception as e:
            print(f"[ERROR] Failed to scrape job detail page: {e}")

    browser.close()
    return all_items


with sync_playwright() as playwright:
    jobs = scrape_indeed(playwright)
    df = pd.DataFrame(jobs)
    df.to_excel("jobs.xlsx", index=False)
    print("[✅] Scraping complete. Data saved to jobs.xlsx.")
