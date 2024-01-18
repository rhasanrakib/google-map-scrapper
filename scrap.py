from selenium import webdriver
import pandas as pd
from parsel import Selector
import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
import urllib.parse
import traceback
# use the path to the driver you downloaded from previous steps
chromedrive_path = './chromedriver'


json_file_path = './json_title_link/'
review_file_path = './json_reviews/'

if not os.path.exists(json_file_path):
    os.makedirs(json_file_path)
if not os.path.exists(review_file_path):
    os.makedirs(review_file_path)


def file_input(path_file_name: str):
    df = pd.read_csv(path_file_name)
    df = df.fillna('no_data')
    return df


def csv_to_dict_list(df):
    arr = []
    for index, row in df.iterrows():
        id = row['sn']
        lat = row['lat']
        lon = row['lon']
        if row['lat'] == 'no_data' or row['lon'] == 'no_data':
            print("empty lat or lan in id ", id)
            continue
        search_key = row['search_key'] if row['search_key'] != 'no_data' else 'At this place'
        arr.append({
            'id': id,
            'lat': lat,
            'lon': lon,
            'search_key': search_key
        })
    return arr


def making_url(lat, lon, search_key: str):
    search_key = search_key.replace(' ', '+')
    url = f'https://www.google.com/maps/search/{search_key}/@{lat},{lon}'
    return url


def is_end_reached(div_xpath, driver):
    return driver.execute_script(f"return document.evaluate('{div_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.scrollHeight <= document.evaluate('{div_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.scrollTop + document.evaluate('{div_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.offsetHeight;")


def run_driver_selenium(url, id):
    driver = webdriver.Chrome()
    results = []

    driver.get(url)
    page_content = driver.page_source
    div_xpath = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]'
    while not is_end_reached(div_xpath, driver):
        driver.execute_script(
            f"document.evaluate('{div_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.scrollBy(0, 200);")
        time.sleep(1)

    response = Selector(page_content)
    # //*[@id="QA0Szd"]/div/div/div[1]/div[2]
    for el in response.xpath('//div[contains(@aria-label, "Results for")]/div/div[./a]'):
        results.append({
            'link': el.xpath('./a/@href').extract_first(''),
            'title': el.xpath('./a/@aria-label').extract_first('')
        })

    with open(f'{json_file_path}{id}.json', 'w') as json_file:
        json.dump(results, json_file, indent=4)
    driver.quit()
    return results


def run_driver_sync_playwright(url, id):
    making_res = []
    with sync_playwright() as pw:
        # creates an instance of the Chromium browser and launches it
        browser = pw.chromium.launch(headless=True)
        # creates a new browser page (tab) within the browser instance
        page = browser.new_page()
        page.goto(url)
        # scrolling
        for i in range(4):
            # tackle the body element
            html = page.inner_html('body')

            # create beautiful soup element
            soup = BeautifulSoup(html, 'html.parser')

            # select items
            categories = soup.select('.hfpxzc')
            last_category_in_page = categories[-1].get('aria-label')

            # scroll to the last item
            last_category_location = page.locator(
                f"text={last_category_in_page}")
            last_category_location.scroll_into_view_if_needed()

        # get links of all categories after scroll
        links = [item.get('href') for item in soup.select('.hfpxzc')]

        for ii in soup.select('[aria-label*="Results for"]'):
            titlesHtml = ii.select('.qBF1Pd.fontHeadlineSmall')
        titles = [element.get_text(strip=True) for element in titlesHtml]

        for i in range(0, len(titles)):
            making_res.append({
                'title': titles[i],
                'link': links[i],
                'id': id
            })

        with open(f'{json_file_path}{id}.json', 'w') as json_file:
            json.dump(making_res, json_file, indent=4)
    return making_res


def reviews_scrap(items):
    review_items = []
    with sync_playwright() as pw:
        # creates an instance of the Chromium browser and launches it
        browser = pw.chromium.launch(headless=False)
        # creates a new browser page (tab) within the browser instance
        page = browser.new_page()
        for item in items:
            try:
                page.goto(item['link'])
                time.sleep(4)
                page_url = page.url
                pts = page_url.split('/')[-1]
                # lat lon
                latitude = pts.split('!3d')[1].split('!')[0]
                longitude = pts.split('!4d')[1].split('!')[0]
                
                # load all reviews
                page.locator("text='Reviews'").first.click()
                time.sleep(4)

                # create new soup
                html = page.inner_html('body')

                # create beautiful soup element
                soup = BeautifulSoup(html, 'html.parser')
                
                rating_elm = soup.select('.jANrlb .fontDisplayLarge')
                ratings = [rating.text for rating in rating_elm]
                # scrape reviews
                reviews = soup.select('.MyEned')
                reviews = [review.find('span').text for review in reviews]

                review_string = ';'.join(reviews)
                review_items.append({
                    'title': item['title'],
                    'reviews': review_string,
                    'id': item['id'],
                    'latitude': latitude,
                    'longitude': longitude,
                    'avg_ratings': ratings[0] if len(ratings) else 0
                })
            except Exception as e:
                print(
                    f'skipping {item["title"]} crawling due to an exception {e}')
                traceback.print_exc()
    return review_items


def main():
    df = file_input('./location.csv')
    location_dict_list = csv_to_dict_list(df)
    for dt in location_dict_list:
        url = making_url(dt['lat'], dt['lon'], dt['search_key'])
        title_link = run_driver_sync_playwright(url, dt['id'])
        # print(title_link)
        reviews = reviews_scrap(title_link)
        with open(f'{review_file_path}{dt["id"]}.json', 'w') as json_file:
            json.dump(reviews, json_file, indent=4)


main()
