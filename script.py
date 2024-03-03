#!/usr/bin/env python

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os, os.path, random, re, time
import glob, hashlib, configparser, smtplib
from email.message import EmailMessage

def randomsleep(section, name):
    print('sleeping')
    time.sleep(random.randint(
        config.getint(section, name+'_sleep_min', fallback=5),
        config.getint(section, name+'_sleep_max', fallback=10)))

config = configparser.ConfigParser(interpolation=None)
config.read('/data/config.ini')

# sleep before startup
randomsleep('global', 'start')

os.makedirs('/data/posts', exist_ok=True)

for lockfile in glob.glob('/data/profile/Singleton*'):
    os.remove(lockfile)

chrome_options = uc.ChromeOptions()
if 'chrome_proxy' in config['global']:
    chrome_options.add_argument('--proxy-server=' + config['global']['chrome_proxy'])
print('starting')
driver = uc.Chrome(options=chrome_options, advanced_elements=True, user_data_dir='/data/profile')

for section in config.sections():
    if section == 'global' or section == 'DEFAULT':
        continue

    url = 'https://facebook.com/groups/%s/' % config[section]['facebook_group']
    print('opening')
    driver.get(url)
    randomsleep(section, 'open')
    driver.save_screenshot('data/%s.png' % section)

    print('working')
    new_posts=[]
    msg = EmailMessage()
    msg['Subject'] = config[section]['mail_subject']
    msg['From'] = config[section]['mail_from']
    msg['To'] = config[section]['mail_to']
    posts = driver.find_elements(By.CSS_SELECTOR, 'div[role="article"]')
    # TODO: send email with warning if len(posts) < 3
    print('working on %d posts' % len(posts))
    for post_div in posts:
        post_text_divs=post_div.find_elements(By.CSS_SELECTOR, 'div[data-ad-preview]')
        if post_text_divs and post_text_divs[0].text:
            post_text = post_text_divs[0].text
        else:
            post_text = post_div.text
        post_links = post_div.find_elements(By.TAG_NAME,'a')
        post_urls = [x.attrs['href'].split('?')[0] for x in post_links if 'href' in x.attrs and '/posts/' in x.attrs['href']]
        if post_urls:
            post_url = post_urls[0]
            post_id = re.search('posts/([0-9]*)', post_url).group(1)
        else:
            post_url = hashlib.md5(post_text.encode()).hexdigest()
            post_id = post_url
        # for screenshot
        post_parent = post_div #.find_element(By.XPATH,"./..")

        post_file='/data/posts/%s-%s.txt' % (config[section]['facebook_group'], post_id)

        print('DEBUG: post %s:\n%s\n' % (post_url, post_text))

        if not os.path.exists(post_file):
            new_posts.append('%s\n%s' % (post_url, post_text))
            with open(post_file, 'w') as f:
                f.write(post_text)
            if config.getboolean(section, 'screenshots', fallback=False):
                driver.execute_script('arguments[0].scrollIntoView(false)',post_parent)
                #randomsleep(section, 'scroll')
                msg.add_attachment(post_parent.screenshot_as_png, maintype='image',subtype='png')
    
    if not posts:
        new_posts=['No posts detected, none at all']

    new_posts_text='\n==========================================================================\n'.join(new_posts)

    if new_posts:
        print('sending')
        if config.getboolean(section, 'screenshots', fallback=False):
            msg.add_attachment(new_posts_text, disposition='inline')
        else:
            msg.set_content(new_posts_text)
        with smtplib.SMTP(config[section]['smtp_server']) as s:
            s.send_message(msg)

