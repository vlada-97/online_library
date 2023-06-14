import argparse
import json
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def on_reload():
    books_on_page = 20
    rows_on_page = 2
    env = Environment(
        loader=FileSystemLoader("."), autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("template.html")

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="json",
                        type=str, help="Json file path.")
    args = parser.parse_args()
    path = args.path
    with open(os.path.join(path, "books_content.json"), "r", encoding="utf-8-sig") as j:
        books_content = json.load(j)

    pages_path = "pages"
    os.makedirs(pages_path, mode=0o777, exist_ok=True)

    books_content_on_pages = list(chunked(books_content, books_on_page))
    total_pages = len(books_content_on_pages)
    for index, book_content in enumerate(books_content_on_pages, 1):
        book_rows_content = list(chunked(book_content, rows_on_page))
        rendered_page = template.render(
            books_content=book_rows_content, page_index=index, total_pages=total_pages
        )

        with open(f"{pages_path}/index{index}.html", "w", encoding="utf-8") as file:
            file.write(rendered_page)


def main():
    on_reload()
    server = Server()
    server.watch("template.html", on_reload)
    server.serve(root=".", default_filename="./pages/index1.html")


if __name__ == "__main__":
    main()
