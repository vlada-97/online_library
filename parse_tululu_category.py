import argparse
import time
import urllib

import requests
from bs4 import BeautifulSoup

from main import (
    InvalidBookType,
    check_for_redirect,
    download_image,
    download_txt,
    get_book,
    parse_book_page,
    save_json,
)


def get_books_links(start_page, end_page):
    book_links = []
    for page in range(start_page, end_page):
        try:
            response = get_book(f"https://tululu.org/l55/{page}", page)
            response.raise_for_status()
            check_for_redirect(response)
            soup = BeautifulSoup(response.text, "lxml")
            book_numbers = soup.select("body .d_book")
            for book_num in book_numbers:
                book_url = urllib.parse.urljoin(
                    f"https://tululu.org/l55/{book_num}",
                    book_num.select_one("a")["href"],
                )
                response = requests.get(book_url)
                response.raise_for_status()
                check_for_redirect(response)

                book_links.append(book_url)
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
        ) as ex:
            print(ex)
            time.sleep(60)
        except InvalidBookType as ex:
            print(ex)
            continue
    return book_links


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_page", default=1,
                        type=int, help="First book page.")
    parser.add_argument("--end_page", default=12,
                        type=int, help="Last book page.")
    parser.add_argument(
        "--dest_folder", default="books", type=str, help="Directory path."
    )
    parser.add_argument(
        "--skip_imgs", action="store_true", help="Don't download images."
    )
    parser.add_argument("--skip_txt", action="store_true",
                        help="Don't download texts.")
    parser.add_argument(
        "--json_path", default="json", type=str, help="Directory json file path."
    )
    args = parser.parse_args()
    start_page = args.start_page
    end_page = args.end_page
    dest_folder = args.dest_folder
    json_path = args.json_path

    books_content = []
    links = get_books_links(start_page, end_page)
    for book_url in links:
        try:
            response = requests.get(book_url)
            if not response.content:
                raise InvalidBookType(response)
            response.raise_for_status()
            check_for_redirect(response)

            book_content, book_image = parse_book_page(response)
            books_content.append(book_content)
            book_name = book_content["book_name"]
            book_page_num = (
                urllib.parse.urlparse(book_url).path.split(
                    "/")[1].split("b")[1]
            )

            if not args.skip_imgs:
                download_image(book_page_num, book_image, dest_folder)
            if not args.skip_txt:
                download_txt(
                    get_book(f"https://tululu.org/txt.php", book_page_num),
                    book_name,
                    dest_folder,
                )
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
        ) as ex:
            print(ex)
            time.sleep(60)
        except InvalidBookType as ex:
            print(ex)
            continue
    save_json(books_content, json_path)
