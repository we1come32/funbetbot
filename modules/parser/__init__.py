from selenium import webdriver
from . import parimatch

browser = webdriver.Firefox()
browser.set_page_load_timeout(40)


