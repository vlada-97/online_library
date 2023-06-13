import json
import os
from more_itertools import chunked
from livereload import Server

from jinja2 import Environment, FileSystemLoader, select_autoescape


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template.html')

    path = 'json'
    with open(os.path.join(path, 'books.json'), 'r', encoding='utf-8-sig') as j:
        books_content = json.load(j)

    pages_path = 'pages'
    os.makedirs(pages_path, mode=0o777, exist_ok=True)

    books_content = list(chunked(books_content, 20))
    total_pages = len(books_content)
    for index, book_content in enumerate(books_content, 1):
        book_content = list(
            chunked(book_content, 2))
        rendered_page = template.render(
            books_content=book_content, page_index=index, total_pages=total_pages)

        with open(f'{pages_path}/index{index}.html', 'w', encoding="utf-8") as file:
            file.write(rendered_page)

    print("Site rebuilt")


def main():
    try:
        on_reload()
        server = Server()
        server.watch('template.html', on_reload)
        server.serve(root='.', default_filename="./pages/index1.html")
    except(OSError) as ex:
        print(ex)

if __name__ == '__main__':
    main()
