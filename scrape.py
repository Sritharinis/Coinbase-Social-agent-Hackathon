from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time
import os

# Initialize the WebDriver with a specific user data directory
options = webdriver.ChromeOptions()
user_data_dir = f"--user-data-dir=./chrome_user_data_{os.getpid()}"  # Unique directory for each process
options.add_argument(user_data_dir)
# options.add_argument('--headless')  # Uncomment for headless mode
driver = webdriver.Chrome(options=options)

# Specify the CSV file path
csv_file_path = 'twitter_data.csv'

# Check if the file exists and delete it
if os.path.exists(csv_file_path):
    os.remove(csv_file_path)


# Function to log into Twitter
def twitter_login(username, password):
    driver.get("https://x.com/i/flow/login?")
    try:
        wait = WebDriverWait(driver, 10)
        username_input = wait.until(EC.presence_of_element_located((By.NAME, 'text')))
        username_input.send_keys(username)
        username_input.send_keys(Keys.RETURN)
        time.sleep(2)

        password_input = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
        time.sleep(2)
    except Exception as e:
        print(f"Login failed: {e}")
        
# Function to extract followers
def extract_followers(username):
    followers_url = f"https://x.com/{username}/followers"
    driver.get(followers_url)
    time.sleep(2)

    # Scroll to load followers
    try:
        followers_link = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//span[text()='Followers']"))
        )
        followers_link.click()
        time.sleep(2)

        # Load all followers
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        followers = soup.find_all('span', class_="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3")
        follower_usernames = [f.get_text(strip=True) for f in followers if f.get_text(strip=True).startswith('@')]

        # Save followers to CSV
        with open(f'{username}_followers.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Username'])
            for follower in follower_usernames:
                writer.writerow([follower])

        print(f"Extracted {len(follower_usernames)} followers for {username}")
    except Exception as e:
        print(f"Error extracting followers: {e}")
        
# Function to scrape data from specified posts
def scrape_posts(post_urls):
    results = []
    for url in post_urls:
        driver.get(url)
        time.sleep(2)  # Allow time for the page and JavaScript to load

 
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = soup.find_all('article', {'data-testid': 'tweet'})

        # Extract comments
        for article in articles:
            try:
                # Locate the username and comment text within the article
                user_handles = article.find_all('span', class_="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3")
                user_handle = next((handle.text for handle in user_handles if handle.text.startswith('@')), None)
                comment_text = article.find('div', {'data-testid': 'tweetText'}).get_text(strip=True)
                if user_handle:
                    results.append({'Post URL': url, 'Type': 'Comment', 'User Handle': user_handle, 'Content': comment_text})
            except Exception as e:
                print(f"Failed to extract comment: {e}")

        # Expand engagement sections and scrape engagement data
        try:
            engagements_link = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//span[text()='View post engagements']"))
            )
            engagements_link.click()
            time.sleep(2)

            for engagement_type in ["Quotes", "Likes", "Reposts"]:
                engagement_link = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, f"//span[text()='{engagement_type}']"))
                )
                engagement_link.click()
                time.sleep(2)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                user_ids = soup.find_all('span', class_="css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3")
                
                for user_id in user_ids:
                    user_handle = user_id.text.strip()
                    if user_handle.startswith('@'):
                        results.append({'Post URL': url, 'Type': engagement_type, 'User Handle': user_handle, 'Content': ''})
        except Exception as e:
            print(f"Error processing engagements for post at {url}: {e}")

        # Save data to CSV after each post is processed
        with open('twitter_data.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Post URL', 'Type', 'User Handle', 'Content'])
            if file.tell() == 0:  # write header only at the start
                writer.writeheader()
                
            writer.writerows(results)
            writer.writerow({})  # This adds an empty row after processing each post

        results = []  # Reset for next post


# Credentials (replace with real credentials)
USERNAME = 'ArivRz5'
PASSWORD = 'Admin@1234~'



# Login and scrape data
twitter_login(USERNAME, PASSWORD)
post_urls = [
    "https://x.com/ArivRz5/status/1885581951043805195",
    "https://x.com/ArivRz5/status/1885581887013605615",
    "https://x.com/ArivRz5/status/1885581765236187182"
]
extract_followers(USERNAME)
scrape_posts(post_urls)

# Close the browser
driver.quit()
