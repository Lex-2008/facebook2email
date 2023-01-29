#!/usr/bin/env python

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os, os.path, random, re, time
import glob, configparser, smtplib
from email.message import EmailMessage

def randomsleep(section, name):
    rand_sleep = random.randint(config.getint(section, name+'_sleep_min', fallback=5), config.getint(section, name+'_sleep_max', fallback=10))
    print('sleeping %d sec' % rand_sleep)
    time.sleep(rand_sleep)

config = configparser.ConfigParser(interpolation=None)
config.read('/data/config.ini')

# sleep before startup
randomsleep('global', 'start')

os.makedirs('/data/posts', exist_ok=True)

for lockfile in glob.glob('/data/profile/Singleton*'):
    os.remove(lockfile)

chrome_options = uc.ChromeOptions();
if 'chrome_proxy' in config['global']:
    chrome_options.add_argument('--proxy-server=' + config['global']['chrome_proxy']);
print('starting')
driver = uc.Chrome(options=chrome_options, advanced_elements=True, user_data_dir='/data/profile')

for section in config.sections():
    if section == 'global' or section == 'DEFAULT':
        continue

    url = 'https://www.facebook.com/groups/%s?sorting_setting=CHRONOLOGICAL' % config[section]['facebook_group']
    print('opening '+url)
    driver.get(url)
    randomsleep(section, 'open')

    print('scrolling')
    driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
    randomsleep(section, 'loadscroll')

    print('working')
    new_posts=[]
    msg = EmailMessage()
    msg['Subject'] = config[section]['mail_subject']
    msg['From'] = config[section]['mail_from']
    msg['To'] = config[section]['mail_to']
    for a in driver.find_elements(By.CSS_SELECTOR, 'div[data-ad-preview="message"]'):
        post_text=a.text
        # TODO: or one .. less?
        # TODO: climb one .. at a time, checking that .text differs, or .children() has >1 child
        b=a.find_element(By.XPATH,"./../../..");
        c=b.find_elements(By.TAG_NAME,'a')
        post_url=next(x.attrs['href'].split('?')[0] for x in c if '/posts/' in x.attrs['href'])
        post_id=re.search('posts/([0-9]*)', post_url).group(1)
        post_file='/data/posts/%s-%s.txt' % (config[section]['facebook_group'], post_id)
        if not os.path.exists(post_file):
            new_posts.append('%s\n%s' % (post_url, post_text))
            with open(post_file, 'w') as f:
                f.write(post_text)
            if config.getboolean(section, 'screenshots', fallback=False):
                driver.execute_script('arguments[0].scrollIntoView(false)',b)
                #randomsleep(section, 'scroll')
                msg.add_attachment(b.screenshot_as_png, maintype='image',subtype='png')

    new_posts_text='\n========================================================================\n'.join(new_posts)

    with open('/data/%s-new.txt' % section, 'w') as f:
        f.write(new_posts_text)

    if new_posts:
        print('sending')
        if config.getboolean(section, 'screenshots', fallback=False):
            msg.add_attachment(new_posts_text, disposition='inline')
        else:
            msg.set_content(new_posts_text)
        with smtplib.SMTP(config[section]['smtp_server']) as s:
            s.send_message(msg)

