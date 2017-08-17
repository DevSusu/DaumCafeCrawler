import unittest
import win32con
import win32api
import pickle
import os
import re
import datetime
from PIL import ImageGrab
from openpyxl import Workbook
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

"""source from
https://github.com/theskumar/python-dotenv/blob/master/dotenv/main.py
"""
def load_env():
    env_path = '.bambada.env'
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue

            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip()

            os.environ.setdefault(k,v)

    print("setting env complete")

load_env()

class CrawlBambada(unittest.TestCase):

    def setUp(self):
        self.width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        self.height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        self.left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        self.top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

        self.driver = webdriver.Firefox()
        self.driver.set_window_position(self.left,self.top)
        self.driver.set_window_size(self.width/7*5,self.height)

        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(["연번","게시일자","게시시간","수정일자","수정시간","게시장소","제목","작성자","URL","조회수","내용","비고"])

        self.env = {
            'ID' : os.environ.get("ID"),
            'PW' : os.environ.get("PW"),
            'URL' : os.environ.get("URL"),
            'BOARD' : os.environ.get("BOARD"),
            'FOLDER' : os.environ.get("FOLDER"),
            'ARTICLE_URL' : os.environ.get("ARTICLE_URL"),
            'START' : int(os.environ.get("START")),
            'TXT' : os.environ.get("TXT"),
        }
        self.block_size = 100

    def restart_driver(self):
        self.driver.quit()
        self.driver = webdriver.Firefox()
        self.driver.set_window_position(self.left,self.top)
        self.driver.set_window_size(self.width/7*5,self.height)

    def login(self):
        driver = self.driver
        driver.get("http://www.bambada.kr/index.html")

        id_input = driver.find_element_by_css_selector('input[name="mb_id"]')
        id_input.send_keys(self.env['ID'])

        pw_input = driver.find_element_by_css_selector('input[name="mb_password"]')
        pw_input.send_keys(self.env['PW'])

        driver.find_element_by_css_selector('a[href="javascript:actLogin();"]').click()

        WebDriverWait(driver, 3).until(EC.title_contains('밤바다넷'))

    def board(self):
        driver = self.driver
        driver.get(self.env['URL'])

        last_page_table = driver.find_element_by_id("BOARD_PAGE")
        last_page_btn = last_page_table.find_element_by_css_selector('td[height="10"] > a[href]:last-child')
        last_page_btn.click()

        driver.implicitly_wait(2)

        last_page = int(re.search(r"page=(\d+)", driver.current_url)[1])
        self.article_ids = []

        for page in range(last_page,0,-1):
            driver.get(self.env['URL'] + '&page={}'.format(page))

            links = driver.find_elements_by_css_selector('a.list[href]')

            id_regex = r"wr_id=(?P<id>[0-9]+)"
            for link in links:
                self.article_ids.append(
                    int(re.search(
                        id_regex,
                        link.get_attribute('href')
                    )[1])
                )

    def save_article_ids(self):
        with open(self.env['TXT'],"w") as f:
            f.write("\n".join(str(e) for e in self.article_ids))

    def read_article_ids(self):
        with open(self.env['TXT'],"r") as f:
            id_text = f.read()

        self.article_ids = id_text.split("\n")

    def article(self, start):
        driver = self.driver

        # for idx,wr_id in enumerate([2499]):
        for idx,wr_id in enumerate(self.article_ids[start:]):

            if idx >= self.block_size:
                break

            self.post_num = start+idx+1
            post_url = self.env['ARTICLE_URL'].format(wr_id)
            driver.get(post_url)

            row = [start+idx+1]

            subject = driver.find_element_by_css_selector("td > span.subject").text
            board_name = self.env['BOARD']
            date_time = driver.find_element_by_css_selector("td.date[valign='bottom']").text
            author = driver.find_element_by_css_selector("a > span.member").text
            view_cnt = driver.find_element_by_css_selector("div#VIEW_DATE td.list").text[5:]

            dates = date_time.split("|")[1:]
            created_date = dates[0].strip()[6:]

            if len(dates) == 1:
                updated_date = created_date
            else:
                updated_date = dates[1].strip()[5:]

            row += created_date.split(" ")
            row += updated_date.split(" ")
            row += [board_name,subject,author,post_url,view_cnt]

            # screenshot until comments show up
            comment_start = int(driver.find_element_by_id('VIEW_COMMENT').rect['y'])
            img_idx = 0
            for y_position in range(int(self.height*2/3), comment_start, int(self.height*2/3)):
                driver.execute_script("window.scrollTo(0, {0})".format(y_position))
                img_idx += 1
                self.take_screenshot(img_idx)

            self.ws.append(row)

    def take_screenshot(self, index, filename=None):
        if filename is None:
            filename = "screenshot/"
            filename += self.env['BOARD'] + '-' + str(self.post_num) + '-{0}.jpg'.format(index)

        ss = ImageGrab.grab(bbox=(self.left, self.top, self.width/7*5, self.height))
        ss.save(filename)

    def test_1(self):
        self.login()
        self.board()
        self.article_ids.sort()
        self.save_article_ids()
        self.read_article_ids()

        for i in range(self.env['START'], len(self.article_ids), self.block_size):
            self.article(i)
            self.wb.save("{0}_backup_{1}.xlsx".format(self.env['BOARD'], datetime.datetime.now().strftime('%y%m%d%H%M')))
            self.restart_driver()
            self.login()

    def save_excel(self):
        self.wb.save("{0}_backup_{1}.xlsx".format(self.env['BOARD'], datetime.datetime.now().strftime('%y%m%d%H%M')))

    def tearDown(self):
        # in case test was stopped by sudden error
        self.save_excel()
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
