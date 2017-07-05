import unittest
import win32con
import win32api
import pickle
import os
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
    env_path = '.env'
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

class DaumCafeSearch(unittest.TestCase):

    def setUp(self):
        self.width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        self.height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        self.left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        self.top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

        self.driver = webdriver.Firefox()
        self.driver.set_window_position(self.left,self.top)
        self.driver.set_window_size(self.width/3*2,self.height)

        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.append(["연번","게시일자","게시시간","게시장소","제목","작성자","URL","조회수","내용","비고"])

        self.env = {
            'ID' : os.environ.get("ID"),
            'PW' : os.environ.get("PW"),
            'URL' : os.environ.get("URL"),
            'BOARD' : os.environ.get("BOARD"),
        }

    def take_screenshot(self, index, filename=None):
        if filename is None:
            filename = "screenshot/"
            filename += self.board_name + '-' + str(self.post_num) + '-{0}.jpg'.format(index)

        ss = ImageGrab.grab(bbox=(self.left, self.top, self.width/3*2, self.height))
        ss.save(filename)

    def daum_login(self):
        driver = self.driver
        driver.get("https://logins.daum.net/accounts/loginform.do")

        id_input = driver.find_element_by_id("id")
        id_input.send_keys(self.env['ID'])

        pw_input = driver.find_element_by_id("inputPwd")
        pw_input.send_keys(self.env['PW'])
        pw_input.send_keys(Keys.RETURN)

        WebDriverWait(driver, 3).until(EC.title_is('Daum'))

        # TODO
        # check if logged in successfully
        self.assertIn("Daum", driver.title)

    """fetch_body
    needed because daum cafe page has frames
    """
    def fetch_body(self, driver):
        driver.switch_to.default_content()
        driver.switch_to.frame("down")

        return driver.find_element_by_css_selector("html > body")

    def crawl_main(self):
        driver = self.driver

        driver.get(self.env['URL'])
        self.assertIn("Daum 카페", driver.title)

        body = self.fetch_body(driver)
        left_menu = body.find_element_by_id("menu_folder_list")
        board_groups = left_menu.find_elements_by_xpath("//li[@class='depth1']")

        for idx,board_group in enumerate(board_groups):
            try:
                board_group_header = board_group \
                                    .find_element_by_link_text('동상이몽 자료실')

                # 동상이몽 자료실 찾은 경우
                boards = board_group.find_elements_by_xpath("//li[@class='icon_board ']")
                for board in boards:
                    if board.text in ['도촬 시리즈 2']:
                        self.crawl_board(board)

            except Exception as e:
                print(e)

    def crawl_board(self, board):
        self.board_name = board.text
        board.find_element_by_css_selector('a').click()

        driver = self.driver
        body = self.fetch_body(driver)
        tbody = body.find_element_by_xpath("//table/tbody")

        last_post_num = int(tbody.find_element_by_css_selector("tr[class] > td.num").text)
        board_url = driver.current_url

        # TODO
        # pagenate crawling because of memory problems
        for post_num in range(1,0,-1):
            post_url = board_url + '/{0}'.format(post_num)
            self.post_num = post_num
            self.crawl_post(post_url)

        self.wb.save("{0}.xlsx".format(self.board_name))

    def crawl_post(self, post_url):
        driver = self.driver
        driver.get(post_url)
        body = self.fetch_body(driver)
        row = [""]

        try:
            post_subject = body.find_element_by_xpath("//div[@class='article_subject line_sub']")
            post_info = body.find_element_by_xpath("//div[@class='article_writer']")
        except Exception as e:
            # page was not found
            return None

        subject = post_subject.find_element_by_xpath("//span[@class='b']").text
        board_name = post_subject.find_element_by_xpath("//a[@class='txt_sub']").text
        date_time = post_info.find_element_by_xpath("//span[@class='p11 ls0']").text
        author = post_info.find_element_by_xpath("//a[@class='txt_point p11']").text
        view_cnt = post_info.find_element_by_xpath("//span[@class='p11']").text[3:]

        row += date_time.split(" ")
        row += [board_name,subject,author,post_url,view_cnt]

        self.ws.append(row)

        # screenshot until comments show up
        comment_start = int(body.find_element_by_id('comment_wrap').rect['y'])
        img_idx = 0
        for y_position in range(int(self.height*2/3), comment_start, int(self.height*2/3)):
            driver.execute_script("window.scrollTo(0, {0})".format(y_position))
            img_idx += 1
            self.take_screenshot(img_idx)

        return None

    def test_all(self):
        self.daum_login()
        self.crawl_main()

    def tearDown(self):
        # in case test was stopped by sudden error
        self.wb.save("{0}_backup.xlsx".format(self.board_name))
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
