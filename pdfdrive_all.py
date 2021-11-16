# Any Bugs or Any Suggestions
# -> gyshn@pm.me <-

import concurrent.futures as fu
import sys
import requests as req
import os

try:
    from bs4 import BeautifulSoup as Soup
except ImportError:
    os.system('pip install bs4')
    from bs4 import BeautifulSoup as Soup
try:
    from tqdm import tqdm
except ImportError:
    os.system('pip install tqdm')
    from tqdm import tqdm


PREFIX = 'https://www.pdfdrive.com/'
DIR_LINK = 'https://www.pdfdrive.com/download.pdf?id={}&h={}&u=cache&ext=pdf'
BASE = 'Pdf Drive/'

SUGGEST = 'https://www.pdfdrive.com/search/complete?'

# seperated by -
SUGGESTED_FIRST_PAGE = 'https://www.pdfdrive.com/{}-books.html'
SUGGESTED_OTHER_PAGES = 'https://www.pdfdrive.com/search?q={}&pagecount=&pubyear=&searchin=&page={}'

# seperated by +
NOT_SUGGESTED_FIRST_PAGE = 'https://www.pdfdrive.com/search?q={}&pagecount=&pubyear=&searchin=&em=&more=true'
# seperated by %20
NOT_SUGGESTED_OTHER_PAGES = 'https://www.pdfdrive.com/search?q={}&pagecount=&pubyear=&searchin=&em=&more=true&page={}}'

# 16/11/2021 - added suggestions for more accurate results


def suggest(search):

    parts = search.split()
    if len(parts) != 1:
        temp = ' '.join(parts[:-1]) + ' ' + parts[-1][:-2]
    else:
        temp = parts[0][:-1]

    params = {
        'query': temp,
    }

    r = req.get(SUGGEST, params=params)

    suggestions = r.json()['suggestions']
    if search in suggestions:
        return True, search
    else:
        while True:
            for index, each in enumerate(suggestions):
                print(index, '-', each)
            try:
                x = int(input("-1 - just my search\n-2 - search again \nSuggest ->"))
                if x == -1:
                    return False, search
                if x == -2:
                    return suggest(input("Search > "))

                if x < 0 or x >= len(suggestions):
                    print('Index Error')
                    continue
                return True, suggestions[x]
            except Exception as e:
                print(e)
                continue


def canGoForward(soup):
    try:
        if soup.find('div', class_='Zebra_Pagination').find_all('li')[-1].text == 'Next':
            return soup.find('div', class_='Zebra_Pagination').find_all('li')[-1].a['href'] != 'javascript:void(0)'
        return False
    except Exception as e:
        print(e)
        return False


def selectedDownloads():
    os.system('cls' if os.name == 'nt' else 'clear')
    session = req.Session()

    use_suggested, keyword = suggest(input("Search > "))

    folder_path = BASE + keyword + '/'
    if not os.path.isdir(folder_path):
        os.mkdir(folder_path)

    current_page = 1

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        if current_page == 1:
            if use_suggested:
                link = SUGGESTED_FIRST_PAGE.format(keyword.replace(' ', '-'))
                goBack = False
            else:
                link = NOT_SUGGESTED_FIRST_PAGE.format(keyword.replace(' ', '+'))
                goBack = False
        else:
            if use_suggested:
                link = SUGGESTED_OTHER_PAGES.format(keyword.replace(' ', '+'), current_page)
                goBack = True
            else:
                link = NOT_SUGGESTED_OTHER_PAGES.format(keyword.replace(' ', '%20'), current_page)
                goBack = True

        results, goForward = page_scrape(link, session)

        if len(results) == 0:
            print('No Any Books :-(')
            return

        for index, each in enumerate(results):
            each['path'] = folder_path

            summary = f'''
            Index       - {index}
            Name        - {each.get('name')}
            Link        - {each.get('link')}
            Size        - {each.get('size')}
            Pages       - {each.get('pages')}
            Released    - {each.get('released')}
            Downloads   - {each.get('downloads')}

            '''
            print(summary)

        helpMenu = '\texit -> Exit\n\tmain -> Main Menu'
        if goBack:
            helpMenu += '\n\t back -> Go Back'
        if goForward:
            helpMenu += '\n\t go -> Go Forward'

        while True:
            choice = input(helpMenu + '\n  > ').lower().strip()
            if choice == 'back':
                if goBack:
                    current_page -= 1
                    break
                else:
                    print('Go Back isn\'t allowed!')

            elif choice == 'go':
                if goForward:
                    current_page += 1
                    break
                else:
                    print('Go Forward isn\'t allowed!')

            elif choice == 'exit':
                session.close()
                exit(0)
                sys.exit(0)

            elif choice == 'main':
                session.close()
                return

            selected = []
            for item in choice.split():
                if '-' in item:
                    try:
                        start = int(item.split('-')[0])
                        end = int(item.split('-')[1])

                        if start < 0 or end < 0 or start > end:
                            print(f'Error range\n\tStart - {start}\n\tEnd - {end}')
                            continue

                        for i in range(start, end):
                            selected.append([results[i], session])
                    except Exception as e:
                        print(e)
                else:
                    try:
                        num = int(item)
                        selected.append([results[num], session])
                    except Exception as e:
                        print(e)
            if len(selected) != 0:
                with fu.ThreadPoolExecutor() as ee:
                    rs = list(tqdm(ee.map(downloadBook, selected), total=len(selected)))

                size = round(sum(rs) * 1e-6, 2)
                print(f'Downloaded - {size} MB')


def downloadInRange():
    os.system('cls' if os.name == 'nt' else 'clear')
    session = req.Session()

    use_suggested, keyword = suggest(input("Search > "))
    folder_path = BASE + keyword + '/'

    if not os.path.isdir(folder_path):
        os.mkdir(folder_path)

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        helpCommands = '\texit -> Exit\n\tmain -> Main Menu\n(split pages by - )\n>'
        choice = input(helpCommands).lower().strip()

        if choice == 'exit':
            session.close()
            exit(0)
            sys.exit(0)

        elif choice == 'main':
            session.close()
            return

        if '-' not in choice:
            print("Split pages by - ")
            continue

        parts = choice.split('-')
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())

            if start < 0 or end < 0 or start > end:
                print('Range Error!')
                continue

            for i in range(start, end + 1):
                if i > 80:
                    return 
                if i == 1:
                    if use_suggested:
                        page_link = SUGGESTED_FIRST_PAGE.format(keyword.replace(' ', '-'))
                    else:
                        page_link = NOT_SUGGESTED_FIRST_PAGE.format(keyword.replace(' ', '+'))
                else:
                    if use_suggested:
                        page_link = SUGGESTED_OTHER_PAGES.format(keyword.replace(' ', '+'), i)
                    else:
                        page_link = NOT_SUGGESTED_OTHER_PAGES.format(keyword.replace(' ', '%20'), i)

                result, goForward = page_scrape(page_link, session)

                to_download = []
                for each in result:
                    each['path'] = folder_path
                    to_download.append([each, session])

                with fu.ThreadPoolExecutor() as pool:
                    rs = list(tqdm(pool.map(downloadBook, to_download), total=len(to_download), desc=f'Page - {i} ',
                                   unit='Book'))

                size = round(sum(rs) * 1e-6, 2)
                print(f'Page - {i}  Downloaded - {size} MB')

        except Exception as e:
            print(e)
    
    return


def downloadAll():
    session = req.Session()

    use_suggested, keyword = suggest(input("Search > "))
    os.system('cls' if os.name == 'nt' else 'clear')
    folder_path = BASE + keyword + '/'

    if not os.path.isdir(folder_path):
        os.mkdir(folder_path)

    pageNo = 1
    goForward = True
    while goForward:
        if pageNo > 80:
            break
        if pageNo == 1:
            if use_suggested:
                link = SUGGESTED_FIRST_PAGE.format(keyword.replace(' ', '-'))
            else:
                link = NOT_SUGGESTED_FIRST_PAGE.format(keyword.replace(' ', '+'))
        else:
            if use_suggested:
                link = SUGGESTED_OTHER_PAGES.format(keyword.replace(' ', '+'), pageNo)
            else:
                link = NOT_SUGGESTED_OTHER_PAGES.format(keyword.replace(' ', '%20'), pageNo)

        results, canGo = page_scrape(link, session)

        to_download = []

        for each in results:
            each['path'] = folder_path
            to_download.append([each, session])
        if not canGo:
            goForward = False

        with fu.ThreadPoolExecutor() as pool:
            res = list(tqdm(pool.map(downloadBook, to_download), total=len(to_download), desc=f'Page - {pageNo} ',
                            unit='Book'))

        size = round(sum(res) * 1e-6, 2)
        print(f'Page - {pageNo}  Downloaded - {size} MB')

        pageNo += 1

    session.close()
    return


def get_h_value(rq):
    soup = Soup(rq.content, 'html5lib')
    script = soup.find_all('script')[6]
    script = str(script)

    try:
        return script.split(',session:')[1].split("'")[1]
    except Exception as e:
        print(e)
        return None


def page_scrape(link, session):
    r = session.get(link)
    soup = Soup(r.content, 'html5lib')

    container = soup.find('div', class_='files-new')
    books_source = container.find_all('li')

    books = []
    for each_source in books_source:
        try:
            link = PREFIX + each_source.a['href']
        except TypeError:
            continue

        name = each_source.img['alt']

        properties = {'fi-size hidemobile': 'size',
                      'fi-pagecount': 'pages',
                      'fi-year': 'released',
                      'fi-hit': 'downloads'
                      }
        one_book = {'name': name.strip(),
                    'link': link.strip(),
                    }

        for attribute in properties.keys():
            if each_source.find('span', class_=attribute):
                one_book[properties[attribute]] = each_source.find('span', class_=attribute).text.strip()

        books.append(one_book)

    return books, canGoForward(soup)


def downloadBook(values):
    bookDic = values[0]
    session = values[1]

    name = bookDic['name'].split(':')[0].strip().replace('/', '').replace(':', '')
    link = bookDic['link']
    path = bookDic['path']

    r = session.get(link)
    if r.status_code != 200:
        return 0

    soup = Soup(r.content, 'html5lib')
    try:
        download_page_link = PREFIX + soup.find('span', id='download-button').a['href']

    except Exception as exception:
        print(exception)
        return 0

    while os.path.isfile(path + name + '.pdf'):
        name += '_'

    r = session.get(download_page_link)
    if r.status_code != 200:

        return 0

    book_id = link.split('-')[-1].split('.')[0][1:]
    book_h_value = get_h_value(r)

    if book_h_value is None:
        return 0

    # dir = 'https://www.pdfdrive.com/download.pdf?id=180663309&h=41191927a7d7b5d61399e368145a703b&u=cache&ext=pdf'
    direct_link = DIR_LINK.format(book_id, book_h_value)

    pdf = session.get(direct_link)

    pdf_path = path + name + '.pdf'
    with open(pdf_path, 'wb') as f:
        f.write(pdf.content)
    os.path.getsize(path + name + '.pdf')

    return os.path.getsize(pdf_path)


def main():
    while True:

        helpCommands = f'''
        1. Selected Download
        2. Download in Range
        3. Download ALL
        4. Exit
        >'''
        choice = input(helpCommands)

        if choice == '1':
            selectedDownloads()
        elif choice == '2':
            downloadInRange()
        elif choice == '3':
            downloadAll()
        elif choice == '4':
            exit(0)
            sys.exit(0)
        else:
            print('Unknown')

        os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    if not os.path.isdir(BASE):
        os.mkdir(BASE)

    main()
