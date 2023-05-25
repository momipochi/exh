import json
import logging
import os.path
import random
import sys
import time

import requests
from bs4 import BeautifulSoup
from lxml import etree

gallery_page_url = sys.argv[1]


my_dir = ""
if len(sys.argv) > 2:
    my_dir = sys.argv[2]


default_album_json = f"{my_dir}exh.json"
default_download_location = "D:/dr/ref/exh"
default_archive_location = f"{default_download_location}/metadata.json"
cookie = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "utf-8",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,la;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Cookie": "ipb_member_id=4872233; ipb_pass_hash=3c7affc6aeba7ca114a67b617925b937; igneous=7722c34fc; sl=dm_1; sk=cpxprbvsbstbemk35d1a83mpx7sk",
    "DNT": "1",
    "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
}


def get_login_session(username, password):
    login_url = ""
    login_data = {"UserName": username, "PassWord": password, "CookieDate": 1}
    r = requests.Session()
    return r


def get_gallery_page_icons(url):
    r = requests.get(url, headers=cookie, timeout=30)
    time.sleep(2)
    soup = BeautifulSoup(r.text, "html.parser")
    icons = soup.find_all("div", {"class": "gdtl"})
    icons_src = [i.img["src"] for i in icons]
    return icons_src


def get_gallery_page_number(url):
    r = requests.get(url, headers=cookie, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    table_content = soup.find_all("td", {"class": "gdt2"})
    for t in table_content:
        if "pages" in t.text:
            # print(t.text)
            str = t.text.split(" ")
            return int(str[0]) // 20 + 1
    return 1


def download_image(url, dir):
    if os.path.isfile(dir):
        return

    img_bytes = requests.get(url, timeout=30).content
    r_header = requests.head(url)


    with open(dir, "wb") as img_file:
        img_file.write(img_bytes)
    time.sleep(2)


def get_image_url(url):
    r = requests.get(url, headers=cookie, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    img = soup.find_all("div", {"id": "i3"})[0].img["src"]
    return img


def get_processed_icon_hash(url):
    str = url.split("/")
    str_hash = str[6]
    return str_hash[0:10]


def get_processed_gallery_number(url):
    str = url.split("/")
    # print(str[4])
    return str[4]


def main_operation(url, dir):
    global domain_url_s
    page_numbers = get_gallery_page_number(url)
    gallery_number = get_processed_gallery_number(url)
    img_number = 1
    print(f"Downloading: {url}\nTo: {dir}\n")
    for i in range(page_numbers):
        icon_list = get_gallery_page_icons(f"{url}?p={i}")
        for j in icon_list:
            new_dir = f"{dir}{img_number}.jpg"
            try:
                hashed_icon = get_processed_icon_hash(j)
                s_url = f"{domain_url_s}{hashed_icon}/{gallery_number}-{img_number}"
                s_url = get_image_url(s_url)
                download_image(s_url, new_dir)
                img_number += 1
            except:
                log_fail(img_number,dir)
                img_number += 1
                continue


def log_fail(num, dire):
    logger = logging.basicConfig(
        filename=f"{dire}fails.log", filemode="a", level=logging.INFO
    )
    logger.info(f"Failed to download - {num}")


def write_album(url, directory, file, curr_json={}):
    print(f"Writing new album")
    album = curr_json
    album[url] = directory
    album_json = json.dumps(album)
    file.write(album_json)
    file.close()


def addNewAlbum(url, dir):
    try:
        file = open(default_album_json, "r")
        json_obj = json.loads(file.read())
        file.close()
        if url in json_obj:
            print("You have this album already")
            os._exit(1)
        directory = dir
        w_file = open(default_album_json, "w+")
        print("Adding new album")
        write_album(url, directory, w_file, json_obj)
    except:
        print("This is the first file or error")
        directory = dir
        w_file = open(default_album_json, "w")
        write_album(url, directory, w_file)


def replace_title(title):
    t = title
    t = t.replace("@", "-")
    t = t.replace("/", "-")
    t = t.replace("\\", "-")
    t = t.replace("<", "-")
    t = t.replace(">", "-")
    t = t.replace('"', "-")
    t = t.replace(":", "-")
    t = t.replace("?", "-")
    t = t.replace("|", "-")
    t = t.replace("*", "-")
    return t


def album_archive(url, dir):

    if not os.path.isfile(default_archive_location):
        f = open(default_archive_location, "w")
        f.close()

    try:
        file = open(default_archive_location, "r")
        json_obj = json.loads(file.read())
        file.close()
        if url in json_obj:
            print("You have this archive already")
            return
        w_file = open(default_archive_location, "w+")
        print("Adding new archive")
        write_album(dir, url, w_file, json_obj)
    except:
        print("This is the first archive or error")
        w_file = open(default_archive_location, "w")
        write_album(dir, url, w_file)


def first_load(url, dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
    if not os.path.isfile(default_album_json):
        f = open(default_album_json, "w")
        f.close()
    album_archive(url, dir)
    curr_url = url
    main_all_urls = []
    while True:
        main_all_urls.append(curr_url)
        r = requests.get(curr_url, headers=cookie, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        try:
            new_url = soup.find_all(id="unext")[0]["href"]
            curr_url = new_url
        except:
            print("No more pages, download initializing")
            break

    all_urls = []
    all_dirs = []
    for e in main_all_urls:
        r = requests.get(e, headers=cookie, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        album_links = soup.find_all("div", {"class": "gl1t"})
        for a in album_links:
            all_urls.append(a.a["href"])
            dir_title = replace_title(a.a.div.text)
            all_dirs.append((f"{dir}{dir_title} {random.getrandbits(128)}/").strip())
    all_urls.reverse()
    all_dirs.reverse()
    print("Start download")
    for a in range(len(all_urls)):
        try:
            file = open(default_album_json, "r")
            json_obj = json.loads(file.read())
            file.close()
            if all_urls[a] in json_obj:
                print("Already exist..skipping")
                continue
            addNewAlbum(all_urls[a], all_dirs[a])
        except:
            addNewAlbum(all_urls[a], all_dirs[a])

        if not os.path.exists(all_dirs[a]):
            os.makedirs(all_dirs[a])
        print("Downloading album...")
        main_operation(all_urls[a], all_dirs[a])


def verify_album_and_fix():
    albums = os.listdir(default_download_location)
    file = open(f"{default_download_location}/exclude.txt","r")
    lines = file.readlines()
    file.close()
    try:
        for a in albums:
            if not os.path.isdir(f"{default_download_location}/{a}"):
                continue
            file = open(f"{default_download_location}/{a}/{default_album_json}", "r")
            json_obj = json.loads(file.read())
            file.close()
            for key in json_obj:
                if key in lines:
                    print(f"Skipped {key} : {json_obj[key]}")
                    continue
                try:
                    actual_length = fetch_album_length(key)
                    current_length = len(os.listdir(json_obj[key]))
                    if int(actual_length) != int(current_length):
                        print(f"The following album:\n{key}\n{json_obj[key]}\ndoes not match the actual length.\nActual length:{actual_length}\nCurrent length:{current_length}\n")
                        main_operation(key,json_obj[key])
                        current_length = len(os.listdir(json_obj[key]))
                        print(f"The updated size is now: {current_length}")
                    time.sleep(2)
                except Exception as ex:
                    print(ex.with_traceback())
                    print("Something went wrong during album verification")
                    continue
    except Exception as e:
        print(e.with_traceback())
        print("Something went wrong during album verification")
        os._exit(1)


def fetch_album_length(url):
    r = requests.get(url, headers=cookie, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    size = soup.find_all("td", {"class": "gdt2"})[5].text.split(" ")[0]
    return int(size)


domain_url_s = ""
domain_url_g = ""



def start_scrape(url, dir):
    if url == "-u":
        update()
    elif url == "-fix":
        
        verify_album_and_fix()
    else:
        first_load(url, dir)


def update():
    global default_album_json
    try:
        file = open(default_archive_location, "r")
        json_obj = json.loads(file.read())
        file.close()

        for key, val in json_obj.items():
            print(val, key)
            default_album_json = f"{key}exh.json"
            print(default_album_json)
            first_load(val, key)
    except:
        print("Update went wrong")
        os._exit(1)


start_scrape(gallery_page_url, dir)

