import argparse
import json
import os
import pathlib
import sys
import time
import urllib
import json

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def get_book(url, id):
    params = {
        'id': id
    }
    response = requests.get(
        url, verify=None, allow_redirects=False, params=params)
    response.raise_for_status()
    check_for_redirect(response)
    return response


def check_for_redirect(response):
    if response.history:
        raise requests.exceptions.HTTPError


def download_txt(response, book_name, path='books'):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    response.raise_for_status()
    check_for_redirect(response)

    filepath = os.path.join(
        path, f"{sanitize_filename(book_name)}.txt")
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(response.text)
    return f"Книга: {filepath}"


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title = soup.select_one("head title").text.split('-')[0].rstrip()
    author = soup.select_one("head title").text.split(
        '-')[1].split(',')[0].rstrip()
    image = soup.select_one('.bookimage img')['src'].rstrip()
    img_short = soup.select_one('.bookimage img')['src'].split('/')[2].rstrip()

    comments = soup.select('.texts')
    book_comments = {}
    for count, tags in enumerate(comments):
        tags = tags.select('span.black')
        for tag in tags:
            book_comments.update({
                f'comment_{count}': tag.text
            })

    genres_search = soup.select('span.d_book')
    book_genres = {}
    for genre in genres_search:
        genres = genre.select('a')
        for key, item in enumerate(genres):
            item = item.text.split(',')
            book_genres.update({
                f'genre_{key+1}': item[0]
            })

    book_components = {
        'image': img_short,
        'book_name': title,
        'author_name': author,
        'genres': book_genres,
        'comments': book_comments
    }
    return book_components, image


def save_json(book_components, path='json'):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(path, 'books.json'), 'w+', encoding='utf-8-sig') as f:
        json.dump(book_components, f, ensure_ascii=False, indent=4)


def download_image(book_id, book_image, path='images'):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    image_url = urllib.parse.urljoin(
        f'https://tululu.org/b{book_id}/', book_image)
    resource = requests.get(image_url)
    resource.raise_for_status()

    img_url = urllib.parse.urlparse(image_url)
    img_name = img_url.path.split('/')[2]
    with open(os.path.join(path, img_name), 'wb') as file:
        file.write(resource.content)


class InvalidBookType(Exception):
    def __init__(self, response, message='Book Type is None! Parsing the next book'):
        self.response = response
        self.message = message
        super().__init__(self.message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_id", default=1, type=int,
                        help="Bot work break hours.")
    parser.add_argument("--end_id", default=12, type=int,
                        help="Bot work break hours.")
    parser.add_argument("--dest_folder", default='books', type=str,
                        help="Directory path.")
    parser.add_argument("--skip_imgs", action='store_true',
                        help="Don't download images.")
    parser.add_argument("--skip_txt", action='store_true',
                        help="Don't download texts.")
    parser.add_argument("--json_path", default='json', type=str,
                        help="Directory json file path.")
    args = parser.parse_args()
    start_id = args.start_id
    end_id = args.end_id
    dest_folder = args.dest_folder
    json_path = args.json_path

    books_content = []
    for book_id in range(start_id, end_id):
        try:
            response = get_book(f'https://tululu.org/b{book_id}/', book_id)
            if not response.content:
                raise InvalidBookType(response)
            book_content, book_image = parse_book_page(response)
            books_content.append(book_content)
            book_name = book_content['book_name']
            if not args.skip_imgs:
                download_image(book_id, book_image, dest_folder)

            if not args.skip_txt:
                download_txt(get_book(
                    f'https://tululu.org/txt.php', book_id), book_name, dest_folder)
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as ex:
            sys.stderr.write(ex)
            time.sleep(60)
        except InvalidBookType as ex:
            print(ex)
            continue
    save_json(books_content, json_path)
