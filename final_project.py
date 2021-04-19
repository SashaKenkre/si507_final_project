#################################
##### Name: Sasha Kenkre    #####
##### Uniqname: skenkre     #####
#################################

from bs4 import BeautifulSoup
import requests
import json
import csv
import pandas as pd
import sqlite3

from flask import Flask


CACHE_FILENAME = "imdb_cache.json"
CACHE_DICT = {}

BASEURL = "https://www.imdb.com"

##### SET UP CACHE #####

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

def make_request_with_cache(baseurl, cache_dict):
    '''Check the cache for a saved result for this baseurl+params:values combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    Parameters
    ----------
    baseurl: string
        The URL for the website.

    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
   
    if baseurl in CACHE_DICT.keys():
        print(f"Using cache")
        return CACHE_DICT[baseurl]

    else:
        print(f"Making a request")
        CACHE_DICT[baseurl] = requests.get(baseurl).text
        save_cache(CACHE_DICT)
        return CACHE_DICT[baseurl]

##### CRAWL AND SCRAPE IMDB FOR MOVIE AND DIRECTOR INFORMATION #####
def build_movie_url_dict():
    ''' Make a dictionary that maps movie titles to movie title url from "https://www.imdb.com/chart/top-english-movies"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a title name and value is the url
        e.g. {'the shawshank redemption':'https://www.imdb.com/title/tt0111161', ...}
    '''

    movie_dict = {}
    list_url = 'https://www.imdb.com/chart/top-english-movies'

    html = make_request_with_cache(list_url, CACHE_DICT)
    soup = BeautifulSoup(html, 'html.parser')

    search_div = soup.find('div', class_="lister")
    links_list = search_div.find_all(class_="titleColumn")
    for v in links_list:
        value = v.find('a')
        exten = value.get('href')
        movie_name = value.text.lower().strip()
        movie_dict[movie_name] = BASEURL+exten

    return movie_dict

def get_rankings_dict():
    ''' Make a dictionary that maps movie rank on top 250 list to movie title from "https://www.imdb.com/chart/top-english-movies"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a rank on list and value is the movie title
        e.g. {1: 'The Shawshank Redemption', 2: 'The Godfather', ...}
    '''
    list_url = 'https://www.imdb.com/chart/top-english-movies'

    html = make_request_with_cache(list_url, CACHE_DICT)
    soup = BeautifulSoup(html, 'html.parser')

    ranking_dict = {}

    #Get list of <td> elements for ranks and titles
    ranks = soup.find_all('td', class_='posterColumn')
    titles = soup.find_all('td', class_='titleColumn')

    title_list = []
    for name in titles:
        title = name.find('a').text
        title_list.append(title)

    rank_list = []
    for num in ranks:
        rank =  rank = num.find('span').get('data-value')
        rank_list.append(rank)
    
    for i in range(len(rank_list)):
        ranking_dict[rank_list[i]]=title_list[i]

    return ranking_dict


def get_movie_info(movie_url):
    ''' 
    Get values from movie site urls. Information to gather: Title, Release year, Genre, Cumulative Worldwide Gross, Director,
        IMDb Rating, Ranking in Top 250 list, movie site URL. 

    Parameters
    ----------
    movie_url: string
        URL for movie page on IMDb

    Returns
    -------
    dictionary movie information
        keys are labels and value is the scraped information from web page
        e.g. {'Title':'The Shawshank Redemtion', 'Release Year': 1994, ...}
    '''

    response = make_request_with_cache(movie_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    #Get rankings dictionary to access rankings for movies
    try:
        title = soup.find(class_='title_wrapper').find('h1', class_='').text[:-7].strip()
    except:
        title = soup.find(class_='title_wrapper').find('h1', class_='long').text[:-7].strip()

    #Use title (value in dict) to compare to rankings dictionary and pull correct rank (key)
    ranks = get_rankings_dict()
    for k, v in ranks.items():
        if v.lower() == title.lower():
            rank = k

    release = soup.find(class_='title_wrapper').find(id='titleYear').text[1:5]
    genre = soup.find(class_='title_wrapper').find(class_="subtext").find('a').text
    director = soup.find(class_='credit_summary_item').find('a').text.title().strip()

    # Get worldwide gross from Box Office section
    try:
        gross_text ='Cumulative Worldwide Gross'
        for all_txt in soup.find_all("div", class_="txt-block"):
            find_gross = all_txt.get_text(strip=True).split(':')
            if find_gross[0] == gross_text:
                worldwide_gross = find_gross[1]
        worldwide_gross
    except:
        worldwide_gross = "No info"

    # Get IMDb Rating
    rating = soup.find(itemprop='ratingValue').text

    # Create a dictionary with key, value pairs with the above info
    movie_info_dict = {
        'title': title,
        'releaseYear': release,
        'genre': genre,
        'director': director,
        'worldwideGross': worldwide_gross,
        'imdbRating': rating,
        'listRank': rank,
        'url': movie_url,
    }

    return movie_info_dict

def build_director_url_dict(movie_url):
    ''' Make a dictionary that maps director name to director url from movie pages"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a director name and value is the url
        e.g. {'the shawshank redemption':'https://www.imdb.com/title/tt0111161', ...}
    '''

    director_dict = {}

    response = make_request_with_cache(movie_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    director_name = soup.find(class_='credit_summary_item').find('a').text.title().strip()
    url_exten = soup.find(class_='credit_summary_item').find('a').get('href')
    director_url = BASEURL+url_exten
    director_dict[director_name] = director_url

    return director_dict

def get_director_info(director_url):
    ''' 
    Get values from director site urls. Information to gather: Name, birth year, birth country, trademark, director credits,
        director's site URL. 

    Parameters
    ----------
    director_url: string
        URL for director's page on IMDb

    Returns
    -------
    dictionary movie information
        keys are labels and value is the scraped information from web page
        e.g. {'Name':'Frank Darabont', 'birthYear': 1959, ...}
    '''
    response = make_request_with_cache(director_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    try:
        if soup.find('div', class_='name-overview-widget'):
            name_info = soup.find('div', class_='name-overview-widget')
            name = name_info.find(class_='itemprop').text.strip()
        elif soup.find(class_='article name-overview').find('h1').find('span'):
            name = soup.find(class_='article name-overview').find('h1').find('span').text
    except:
        name = 'No info'

    # try/except in case information is missing
    try:
        birth_info = soup.find(id='name-born-info')
        birthYear = birth_info.find_all('a')[-2].text.strip()
        birthplace = birth_info.find_all('a')[-1].text.strip()
        if birthplace.split(',')[-1].strip():
            country = birthplace.split(',')[-1].strip()
            if country[-1] == ']':
                country = country[:-1]
                if '[' in country:
                    country = country[:]+']'
    except:
        birthYear = "No info"
        country = "No info"

    try:
        trademark = soup.find(id='dyk-trademark').text[11:].split('See more')[0].strip()
    except:
        trademark = "No info"

    try:
        credit = soup.find(id='filmo-head-director').text.split('(')[1][:-2].split(' ')[0]
    except:
        credit = "No info"

    director_info_dict = {
        'name': name,
        'birthYear': birthYear,
        'birthCountry': country,
        'trademark': trademark,
        'directorCredits': credit,
        'url': director_url,
    }

    return director_info_dict

def write_csv(filename, data):
    '''
    Write <data> to the .csv file specified by <filename>
    Parameters
    ----------
    filename: string 
        the name of the csv file which will store the data
    data: list

    Returns
    -------
    None
    '''

    keys = data[0].keys()
    a_file = open(filename, "w")
    dict_writer = csv.DictWriter(a_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(data)
    a_file.close()


### BUILD DATABASE & TABLES ###

def create_db():
    '''
    Create database for movies and directors with two tables: movieInfo and director.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''

    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()

    drop_movie_table = '''
        DROP TABLE IF EXISTS movieInfo;
    '''

    drop_director_table = '''
        DROP TABLE IF EXISTS director;
    '''

    director_table = '''
        CREATE TABLE director (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            birthYear INTEGER,
            birthCountry VARCHAR(255),
            trademark VARCHAR(500),
            directorCredits INTEGER,
            url VARCHAR(255)
        )
    '''

    movie_table = '''
        CREATE TABLE movieInfo (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title VARCHAR(255),
            releaseYear INTEGER,
            genre VARCHAR(255),
            directorId INTEGER,
            wordwideGross BIGINT,
            imdbRating INTEGER,
            listRank INTEGER,
            url VARCHAR(255),
            FOREIGN KEY(directorId) REFERENCES director(id)
            );
    '''

    cur.execute(drop_movie_table)
    cur.execute(drop_director_table)
    cur.execute(movie_table)
    cur.execute(director_table)

    conn.commit()
    conn.close()


def update_movie_table():
    '''
    Add information from movie_info.csv to populate the movieInfo table in the movie database. 
    Connect with director table to pull in foreign key information for directorId column.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
    
    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()
    
    # SET UP QUERIES
    get_director_id = '''
        SELECT id
        FROM director
        WHERE name = ?
    '''

    insert_data = '''
        INSERT INTO movieInfo
        VALUES (NULL,?, ?, ?, ?, ?, ?, ?, ?)
    '''

    # Open movies csv file and skip header
    with open("movie_info.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)

        #Connect id from director table to director name 
        for row in csvreader:
            cur.execute(get_director_id, (row[3],))
            result = cur.fetchone()
            if result:
                directorId = result[0]

            #Insert data from csv into database table
            cur.execute(insert_data, (
                row[0], #title
                row[1], #releaseYear
                row[2], #genre
                directorId,
                row[4], #worldwideGross
                row[5], #imdbRating
                row[6], #ranking
                row[7], #url
            ))

    conn.commit()
    conn.close()

def update_director_table():
    '''
    Add information from directors.csv to populate the director table in the movie database.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''

    directors = pd.read_csv('directors.csv', header=0)
    conn = sqlite3.connect('movie.db')
    directors.to_sql('director', conn, if_exists='append', index=False)


### BUILD FLASK ###

app = Flask(__name__)

# Practice
@app.route('/')
def hello():
    return 'Hello, World!'



if __name__ == "__main__":
    CACHE_DICT = open_cache()
    movie_dict = build_movie_url_dict()

    rankings = get_rankings_dict()

    # movies = []
    # directors = []

    # for mov_url in movie_dict.values():
    #     movie_instance = get_movie_info(mov_url)
    #     movies.append(movie_instance)
    #     director_dict = build_director_url_dict(mov_url)
    #     for val in director_dict.values():
    #         director_instance = get_director_info(val)
    #         if director_instance not in directors:
    #             directors.append(director_instance)
    # write_csv('movie_info.csv', movies)
    # write_csv('directors.csv', directors)

    create_db()
    update_director_table()
    update_movie_table()


