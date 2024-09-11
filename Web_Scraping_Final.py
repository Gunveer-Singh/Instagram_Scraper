from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urlparse




###### All inputs from the User #######

print("This is just for Educational and Showcase Purposes, we do not wish to violate any guidelines of Instagram or any other Social Media Platforms!")
print()

decision = input("Do you want to Download ==> a   or   Save the Links in the Text file ==> b: ").strip().lower()


main_dir = input("Kindly enter the download directory: ")
folder_name = input("Kindly enter the folder name: ")    
download_dir = os.path.join(main_dir,folder_name) 

print()
my_username = input("Enter your own Instagram Username: ")
my_password = input("Enter your own Instagram Password: ")
print()
target_acc = input("Enter the account name you want to scrape: ")
user_input = int(input("How many followers you want to scrape?: "))

if decision == b:
    os.makedirs(download_dir, exist_ok=True)

target_link = "https://www.instagram.com/"+target_acc

driver = webdriver.Chrome()

driver.get("https://www.instagram.com")

username = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))

username.clear()
username.send_keys(my_username)
password.clear()
password.send_keys(my_password)


button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()

not_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Not Now")]')))

not_button.click()

driver.get(target_link)

TIMEOUT = 15

driver.get(f'https://www.instagram.com/{target_acc}/')
time.sleep(3.5)
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers')]"))).click()
time.sleep(2)
print(f"[Info] - Scraping followers for {target_acc}...")

users = set()

while len(users) < user_input:
    followers = driver.find_elements(By.XPATH, "//a[contains(@href, '/')]")

    for i in followers:
        if i.get_attribute('href'):
            users.add(i.get_attribute('href').split("/")[3])
        else:
            continue

    ActionChains(driver).send_keys(Keys.END).perform()
    time.sleep(1)

users = list(users)[:user_input] 

print(f"[Info] - Saving followers for {target_acc}...")
with open(f'{download_dir}\\{target_acc}_followers.txt', 'a') as file:
    file.write('\n'.join(users) + "\n")


driver.get(target_link)


initial_height = driver.execute_script("return document.body.scrollHeight")

soups = []

while True:
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    time.sleep(5)
    
    html = driver.page_source
    
    soups.append(BeautifulSoup(html, 'html.parser'))
   
    current_height = driver.execute_script("return document.body.scrollHeight")

    if current_height == initial_height:
        break  

    initial_height = current_height  


post_urls = []

for soup in soups:
    
    anchors = soup.find_all('a', href=True)
    
    post_urls.extend([anchor['href'] for anchor in anchors if anchor['href'].startswith(("/p/", "/reel/"))])

unique_post_urls = list(set(post_urls))

print(f"before: {len(post_urls)}, after: {len(unique_post_urls)}")

json_list = []

query_parameters = "__a=1&__d=dis"

for url in unique_post_urls:
    try:
        current_url = driver.current_url
        
        modified_url = "https://www.instagram.com/" + url + "?" + query_parameters

        driver.get(modified_url)

        time.sleep(1)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//pre'))
        )
        
        pre_tag = driver.find_element(by=By.XPATH, value='//pre')
        
        json_script = pre_tag.text
        
        json_parsed = json.loads(json_script)
        
        json_list.append(json_parsed)
    except (NoSuchElementException, TimeoutException, json.JSONDecodeError) as e:
        print(f"Error processing URL {url}: {e}")




all_urls = []
all_dates = []


for json_data in json_list:
    
    item_list = json_data.get('items', [])
    
    for item in item_list:
        date_taken = item.get('taken_at')  

        carousel_media = item.get('carousel_media', [])
        
        for media in carousel_media:
            
            image_url = media.get('image_versions2', {}).get('candidates', [{}])[0].get('url')
            
            if image_url:
                all_urls.append(image_url)
                all_dates.append(date_taken)
                print(f"carousel image added")
            
            video_versions = media.get('video_versions', [])
            if video_versions:
                video_url = video_versions[0].get('url')
                if video_url:
                    
                    all_urls.append(video_url)
                    all_dates.append(date_taken)
                    print(f"carousel video added")

        image_url = item.get('image_versions2', {}).get('candidates', [{}])[0].get('url')
        if image_url:
            
            all_urls.append(image_url)
            all_dates.append(date_taken)
            print(f"single image added")

        video_versions = item.get('video_versions', [])
        if video_versions:
            video_url = video_versions[0].get('url')
            if video_url:
                all_urls.append(video_url)
                all_dates.append(date_taken)
                print(f"video added")
                

print(len(all_urls))


if decision == "a":
    os.makedirs(download_dir, exist_ok=True)

    image_dir = os.path.join(download_dir, "images")
    video_dir = os.path.join(download_dir, "videos")
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)

    image_counter = 1
    video_counter = 1

    for index, url in enumerate(all_urls, 0):
        response = requests.get(url, stream=True)

        url_path = urlparse(url).path
        file_extension = os.path.splitext(url_path)[1]

        if file_extension.lower() in {'.jpg', '.jpeg', '.png', '.gif'}:
            file_name = f"{all_dates[index]}-img-{image_counter}.png"
            destination_folder = image_dir
            image_counter += 1
        elif file_extension.lower() in {'.mp4', '.avi', '.mkv', '.mov'}:
            file_name = f"{all_dates[index]}-vid-{video_counter}.mp4"
            destination_folder = video_dir
            video_counter += 1
        else:
            
            file_name = f"{all_dates[index]}{file_extension}"
            destination_folder = download_dir

        file_path = os.path.join(destination_folder, file_name)
    
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        print(f"Downloaded: {file_path}")

    print(f"Downloaded {len(all_urls)} files to {download_dir}")


elif decision == "b":
    f = open(f"{download_dir}\\{target_acc}_urls.txt","a+")
    for url in all_urls:
        f.write("\n"+url+"\n")

    f.close()













