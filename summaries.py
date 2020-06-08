import requests
import bs4
import re
import shutil
# from tqdm import tqdm
from pathlib import Path


def make_soup(url, headers=None, features='lxml'):
    result = requests.get(url, headers=headers)
    if result.status_code != 200:
        # print("Error - Status code:", result.status_code)
        return None
    src = result.content
    soup = bs4.BeautifulSoup(src, features=features)
    return soup


def remove_cites(string):
    return re.sub("\[.+\]", "", string)


class Book():
    def __init__(self, title, author=None, year=None, series=None, number=None):
        self.title = title
        self.author = author
        self.year = year
        self.series = series
        self.number = number

    def summarize_chapter(self, n):
        if n == 0:
            url = f"https://awoiaf.westeros.org/index.php/{self.title.replace(' ', '_')}-Prologue"
        elif n == 1000:
            url = f"https://awoiaf.westeros.org/index.php/{self.title.replace(' ', '_')}-Epilogue"
        else:
            url = f"https://awoiaf.westeros.org/index.php/{self.title.replace(' ', '_')}-Chapter_{n}"

        headers = {"Accept-Language": "en-US,en;q=0.5"}
        wiki = make_soup(url, headers=headers)
        if wiki is None:
            print(url)
            print(f"{self.title} has no Chapter {n}!")
            return
        # chapter title
        chapter_title = wiki.find('table', class_='infobox').tr.text.strip()
        title_split = chapter_title.split(' ')
        if (title_split[-1]).isupper():
            chapter_title = ' '.join(title_split[:-1])

        # print(chapter_title)
        # chapter summary
        synopsis_span = wiki.find('span', id='Synopsis')
        tag = synopsis_span.find_next('p')
        synopsis = ''
        while True:
            if isinstance(tag, bs4.element.Tag):
                if tag.name == 'div':
                    tag = tag.nextSibling
                elif (tag.name in ['h2', 'h3']):
                    break
                else:
                    # print(tag.text)
                    synopsis = synopsis + '\n' + tag.text
                    tag = tag.nextSibling
            elif tag is None:
                break
            else:
                tag = tag.nextSibling
        synopsis = remove_cites(synopsis).strip()
        # print(synopsis)
        return chapter_title, synopsis

    def to_latex(self, outpath=Path.cwd()):
        # make folder
        folder = self.title.replace(' ', '_')
        input_ = outpath / folder
        input_.mkdir(parents=True, exist_ok=True)

        # main.tex
        with open('main.tex') as f:
            newtext = f.read()

        for old, new in [("<TITLE>", self.title),
                         ("<AUTHOR>", self.author),
                         ("<YEAR>", self.year),
                         ("<BOOK X OF>", f"Book {self.number} of"),
                         ("<BOOK SERIES>", self.series)]:
            newtext = newtext.replace(old, new)

        main = outpath / folder / f"{folder}.tex"
        with main.open(mode='w') as f:
            f.write(newtext)

        # copy input folder
        shutil.copytree('input', outpath / folder / 'input')

        # chapters.tex
        with (outpath / folder / 'input' / 'chapters.tex').open(mode='w') as f:
            i = 0
            while(True):
                if i == 1001:
                    break
                summary = self.summarize_chapter(i)
                if summary is None:
                    if i >= 1000:
                        break
                    else:
                        i = 1000
                        continue
                else:
                    chapter_title, synopsis = summary
                    for old, new in [('{', '('), ('}', ')'), ('_', '-')]:
                        synopsis = synopsis.replace(old, new)
                    print(chapter_title)
                    f.write("\n\n")
                    f.write(f"{{\\let\\clearpage\\relax\\chapter*{{\\centering {chapter_title}}}}}\n")
                    f.write(f"{synopsis}")
                i += 1


if __name__ == '__main__':
    got = Book("A Game of Thrones", "George R. R. Martin", "1996", "A Song of Ice and Fire", "One")
    cok = Book("A Clash of Kings", "George R. R. Martin", "1999", "A Song of Ice and Fire", "Two")
    sos = Book("A Storm of Swords", "George R. R. Martin", "2000", "A Song of Ice and Fire", "Three")
    ffc = Book("A Feast for Crows", "George R. R. Martin", "2005", "A Song of Ice and Fire", "Four")
    dwd = Book("A Dance with Dragons", "George R. R. Martin", "2011", "A Song of Ice and Fire", "Five")

    got.to_latex()
    cok.to_latex()
    sos.to_latex()
    ffc.to_latex()
    dwd.to_latex()
