from selenium import webdriver 
from pyvirtualdisplay import Display

display = Display(visible=0, size=(800, 600))
display.start()

driver = webdriver.Firefox() #NO PROXY
driver.set_page_load_timeout(30)
