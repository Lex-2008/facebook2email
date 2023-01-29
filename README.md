Facebook2email
==============

Forward posts in selected groups to your email.
Uses [undetected-chromedriver][] in docker.
Inspired by [Facebook-Scraper-Bot-And-Forwarder][].

[undetected-chromedriver]: https://github.com/ultrafunkamsterdam/undetected-chromedriver
[Facebook-Scraper-Bot-And-Forwarder]: https://github.com/gaurav-321/Facebook-Scraper-Bot-And-Forwarder

Features
--------

* Uses permanent Chrome profile,
in which you can login to Facebook and view private groups
(although this can be changed, ofc)
* Sends text of new posts by email
* Optionally attaches their screenshots to emails
* Is expected to be driven by cron
(doesn't have its own task scheduler - is it a feature or anti-feature?)

Requirements
------------

Docker on x86 machine with enough RAM to run Chrome and open Facebook (I use 2GB VPS).
I assume Linux, but you might succeed on other platforms.

Installation
------------

Clone this repo, copy config.ini-example to config.ini, edit it to your liking.

### Running Chrome manually

In order to view private groups,
you need to login to Facebook.

If your Docker is modern enough, run this command:

	docker run --rm -it -v ${PWD}:/data -p 5900:5900 --shm-size=2g ultrafunk/undetected-chromedriver bash

If your Docker is so old that it doesn't have `--shm-size` argument,
use `df` to find your shared memory partition
(`/dev/shm`, `/tmp/shm`, `/run/shm`, or something like this)
and run it like this:

	docker run --rm -it -v ${PWD}:/data -p 5900:5900 -v /dev/shm:/dev/shm ultrafunk/undetected-chromedriver bash

Otherwise, docker creates only 64Mb of shared memory partition in the container, and Chrome crashes on Facebook.

In bash prompt, type this:

	x11vnc & python

It will start VNC server and open Python for you.
x11vnc will send output to your terminal,
so hit Enter few times to get to Python prompt.

If you use proxy server to connect to Facebook, type this in Python prompt
(replace `socks5://localhost:1234` with your actual proxy server):

	import undetected_chromedriver as uc;
	chrome_options = uc.ChromeOptions();
	chrome_options.add_argument('--proxy-server=socks5://localhost:1234');
	driver = uc.Chrome(options=chrome_options, advanced_elements=True, user_data_dir='/data/profile')

Otherwise, type this:

	import undetected_chromedriver as uc;
	driver = uc.Chrome(advanced_elements=True, user_data_dir='/data/profile')

You can adjust other arguments to `uc.Chrome` to your liking,
for example remove `user_data_dir` to use a temporary profile,
or add [some other undetected-chromedriver][o] arguments.

[o]: https://github.com/ultrafunkamsterdam/undetected-chromedriver/blob/master/undetected_chromedriver/__init__.py#L133

After that, use your favourite VNC viewer to connect to the machine you're running docker on
(`localhost` if you're running it on your local machine), port 5900.
You will see a chrome running.

You can use it normally and drive from command line at the same time!

Useful command: `driver.current_url` to get current URL,
if your VNC client doesn't support copy-pasting.

After you're done, quit Python and Docker container by Ctrl+D.

Usage
-----

Add this command to your crontab:

	docker run --rm -it -v ${PWD}:/data --shm-size=2g ultrafunk/undetected-chromedriver /data/script.py

Replacing `${PWD}` with path to this repo
(it must contain `script.py` file).
If your Docker is too old and doesn't support `--shm-size` argument,
replace it with `-v ...:/dev/shm`,
like shown earlier:

	docker run --rm -it -v ${PWD}:/data -v /dev/shm:/dev/shm ultrafunk/undetected-chromedriver /data/script.py
