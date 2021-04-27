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
import plotly.express as px
from flask import Flask, render_template, request
import plotly.graph_objs as go

CACHE_FILENAME = "imdb_cache.json"
CACHE_DICT = {}

BASEURL = "https://www.imdb.com"

##### SET UP CACHE #####

def open_cache():
    '''
    Opens the cache file if it exists and loads the JSON into
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
    '''
    Saves the current state of the cache to disk

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
    '''
    Check the cache for a saved result. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    Parameters
    ----------
    baseurl: string
        The URL for the website.
    cache_dict: dict
        Dictionary with cache results.

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

##### CRAWL AND SCRAPE IMDb FOR MOVIE AND DIRECTOR INFORMATION #####

def build_movie_url_dict():
    ''' 
    Make a dictionary that maps movie titles to movie title url from "https://www.imdb.com/chart/top-english-movies"

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
    '''
    Make a dictionary that maps movie rank on top 250 list to movie title from "https://www.imdb.com/chart/top-english-movies"

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
    Get values from movie site urls. Information to gather: Title, Release Year, Runtime, Genre, 
    Director, Worldwide Gross, Gross USA, Budget, IMDb Rating, Ranking in Top 250 list, movie site URL. 

    Parameters
    ----------
    movie_url: string
        URL for movie page on IMDb

    Returns
    -------
    dictionary movie information
        keys are labels and value is the scraped information from web page
        e.g. {'Title':'The Shawshank Redemption', 'Release Year': 1994, ...}
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

    # Get worldwide gross, runtime, budget, and gross USA from Box Office section
    try:
        usa_text ='Gross USA'
        for all_txt in soup.find_all("div", class_="txt-block"):
            find_usa = all_txt.get_text(strip=True).split(':')
            if find_usa[0] == usa_text:
                gross_usa = find_usa[1].split('(')[0][1:].replace(',','')
        gross_usa
    except:
        gross_usa = "No info"

    try:
        budget_text ='Budget'
        for all_txt in soup.find_all("div", class_="txt-block"):
            find_budget = all_txt.get_text(strip=True).split(':')
            if find_budget[0] == budget_text:
                if '$' not in find_budget[1]:
                    budget = "No info"
                else:
                    budget = find_budget[1].split('(')[0][1:].replace(',','')
        budget
    except:
        budget = "No info"

    try:
        gross_text ='Cumulative Worldwide Gross'
        for all_txt in soup.find_all("div", class_="txt-block"):
            find_gross = all_txt.get_text(strip=True).split(':')
            if find_gross[0] == gross_text:
                worldwide_gross = find_gross[1].split('(')[0][1:].replace(',','')
        worldwide_gross
    except:
        worldwide_gross = "No info"

    try:
        runtime_text ='Runtime'
        for all_txt in soup.find_all("div", class_="txt-block"):
            find_runtime = all_txt.get_text(strip=True).split(':')
            if find_runtime[0] == runtime_text:
                runtime = find_runtime[1].split(' ')[0]
        runtime
    except:
        runtime = "No info"

    # Get IMDb Rating
    rating = soup.find(itemprop='ratingValue').text

    # Create a dictionary with key, value pairs with the above info
    movie_info_dict = {
        'title': title,
        'releaseYear': release,
        'runtimeMins': runtime,
        'genre': genre,
        'director': director,
        'worldwideGross': worldwide_gross,
        'grossUSA': gross_usa,
        'budget': budget,
        'imdbRating': rating,
        'listRank': rank,
        'url': movie_url,
    }

    return movie_info_dict

def build_director_url_dict(movie_url):
    '''
    Make a dictionary that maps director names to director urls from movie pages.

    Parameters
    ----------
    movie_url: string
        URL for movie page on IMDb

    Returns
    -------
    dict
        key is a director name and value is the director page url
        e.g. {'The Shawshank Redemption':'https://www.imdb.com/title/tt0111161', ...}
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

##### WRITE DICTIONARIES TO CSV #####

def write_csv(filename, data):
    '''
    Write <data> to the .csv file specified by <filename>

    Parameters
    ----------
    filename: string
        the name of the csv file which will store the data
    data: list
        list of dictionaries to convert to csv

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
    Create database to hold information for movies and directors with two tables: movieInfo and director.

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''

    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()

    # drop tables first to prevent issues during testing
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
            runtimeMins INTEGER,
            genre VARCHAR(255),
            directorId INTEGER,
            worldwideGross BIGINT,
            grossUSA INTEGER,
            budget INTEGER,
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
        VALUES (NULL,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    # Open movies csv file and skip header
    with open("movie_info.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile)
        #skip header row
        next(csvreader)

        #Connect id from director table to movieInfo table on director name/id 
        for row in csvreader:
            cur.execute(get_director_id, (row[4],))
            result = cur.fetchone()
            if result:
                directorId = result[0]

            #Insert data from csv into database table
            cur.execute(insert_data, (
                row[0], #title
                row[1], #releaseYear
                row[2], #runtimeMins
                row[3], #genre
                directorId,
                row[5], #worldwideGross
                row[6], #grossUSA
                row[7], #budget
                row[8], #imdbRating
                row[9], #ranking
                row[10], #url
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


##### BUILD FLASK #####

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1

# Set up home page (index.html)
@app.route('/', methods=['GET', 'POST'])
def index():
    '''
    Create index.html page and dropdown content.

    Parameters
    ----------
    None

    Returns
    -------
    index.html page, genre, title, rating, and country dropdown values.
    '''
    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()
    q_genre = '''
    SELECT DISTINCT(genre) FROM movieInfo
    '''
    cur.execute(q_genre)
    genres = ['None'] + [r[0] for r in cur.fetchall()]

    q_title = '''
    SELECT title FROM movieInfo ORDER BY title
    '''
    cur.execute(q_title)
    titles = ['(choose a movie)'] + [res[0] for res in cur.fetchall()]

    cur.execute(q_title)
    titles2 = ['None'] + [res[0] for res in cur.fetchall()]

    q_rating = '''
        SELECT DISTINCT(imdbRating) FROM movieInfo
    '''
    cur.execute(q_rating)
    ratings = ['(select a rating)'] + [result[0] for result in cur.fetchall()]

    q_country = '''
        SELECT DISTINCT(birthCountry) FROM director WHERE birthCountry != "No info" ORDER BY birthCountry
    '''
    cur.execute(q_country)
    countries = ['None'] + [rt[0] for rt in cur.fetchall()]

    return render_template('index.html', genres=genres, titles=titles, ratings=ratings, countries=countries, titles2=titles2)

def get_top_movies(num=None, genre=None):
    '''
    Get the top X number of movies from the movie database and filter on genre.

    Parameters
    ----------
    num: int
        User inputted number for number of results they want.
    genre: str
        User selected genre from dropdown for filtering by genre.

    Returns
    -------
    list of top movie query results for each title in top movie query, including listRank, title, releaseYear, genre, 
    director name, worldwideGross, budget, imdbRating, and movie url
    '''
    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()
    limit_results = f"LIMIT {num}"
    select = request.form.get('genres')
    if select == 'None':
        movie_genre = ''
    elif select != 'None':
        movie_genre = f'WHERE genre = "{select}"'
    
    query = f'''
        SELECT listRank, title, releaseYear, genre, name, worldwideGross, budget, imdbRating, m.url
        FROM movieInfo m
        JOIN director d
        ON m.directorId = d.id
        {movie_genre}
        {limit_results}
    '''

    top_movies = cur.execute(query).fetchall()
    conn.close()
    return top_movies

#for visualization 2
def get_boxoffice_values(title=None):
    '''
    Get the box office numerical values for movies from the movie database.

    Parameters
    ----------
    title: str
        User selected title for the title they want box office information on.

    Returns
    -------
    list of worldwideGross, grossUSA, and budget for a title.
    '''
    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()
    title = request.form.get('titles')
    movie_title = f'''WHERE title = "{title}"'''
    query = f'''
        SELECT worldwideGross, grossUSA, budget
        FROM movieInfo
        {movie_title}
    '''

    cur.execute(query)
    num_movie_info = [r for r in cur.fetchone()]
    conn.close()
    return num_movie_info

def get_compare_boxoffice_values(title=None):
    '''
    Get the box office numerical values for a movie from the movie database to compare with another movie.

    Parameters
    ----------
    title: str
        User selected title for the title they want box office information on.

    Returns
    -------
    list of worldwideGross, grossUSA, and budget for a title.
    '''
    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()
    titles2 = request.form.get('titles2')
    movie_title = f'''WHERE title = "{titles2}"'''
    query = f'''
        SELECT worldwideGross, grossUSA, budget
        FROM movieInfo
        {movie_title}
    '''

    cur.execute(query)
    movie_info = [r for r in cur.fetchone()]
    conn.close()
    return movie_info

def spec_movie_info(title=None):
    '''
    Get the listRank, title, releaseYear, director name, worldwideGross, grossUSA, budget, and url for a movie title chosen by the user .

    Parameters
    ----------
    title: str
        User selected title for the title they want box office information on.

    Returns
    -------
    list of listRank, title, releaseYear, d.name, worldwideGross, grossUSA, budget, and url for a movie title.
    '''

    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()

    movie_title = f'''WHERE title = "{title}"'''
    query = f'''
        SELECT listRank, title, releaseYear, d.name, worldwideGross, grossUSA, budget, m.url
        FROM movieInfo m
        JOIN director d
        ON m.directorId = d.id
        {movie_title}
    '''

    specific_movie = cur.execute(query).fetchall()
    conn.close()
    return specific_movie

# for visualization 3
def get_ratings(rating=None):
    '''
    Get the listRank, title, releaseYear, genre, runtimeMins, director name, worldwideGross, and budget 
    of movies with a user's chosen rating input.

    Parameters
    ----------
    rating: float
        User selected rating.

    Returns
    -------
    list of listRank, title, releaseYear, genre, runtimeMins, director name, worldwideGross, budget, and movie url for movies meeting the user's chosen IMDb rating.
    '''

    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()
    rating = request.form.get('ratings')
    movie_rating = f'''WHERE imdbRating = "{rating}"'''
    query = f'''
        SELECT listRank, title, releaseYear, genre, runtimeMins, d.name, worldwideGross, budget, m.url
        FROM movieInfo m
        JOIN director d
        ON m.directorId = d.id
        {movie_rating} AND budget != "No info" AND worldwideGross != "No info"
    '''
    rating_info = cur.execute(query).fetchall()
    conn.close()
    return rating_info

def get_top_directors(num=None, country=None):
    '''
    Get a list of top X number of directors based on user input with birth country as a filter.

    Parameters
    ----------
    num: int
        User inputted number for top X value.
    country: str
        User selected birth country to filter results.

    Returns
    -------
    list of name, birthYear, birthCountry, trademark, directorCredits, url for directors meeting the user's inputs.
    '''
    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()
    limit_results = f"LIMIT {num}"
    select = request.form.get('countries')
    if select == 'None':
        d_country = ''
    elif select != 'None':
        d_country = f'WHERE birthCountry = "{select}"'
    
    query = f'''
        SELECT name, birthYear, birthCountry, trademark, directorCredits, url
        FROM director
        {d_country}
        ORDER BY directorCredits DESC
        {limit_results}
    '''

    top_directors = cur.execute(query).fetchall()
    conn.close()
    return top_directors

@app.route('/top_movies', methods=['GET', 'POST'])
def table_view():
    '''
    Create top_movies.html page and use user inputted values to get a table of top X movies.

    Parameters
    ----------
    None

    Returns
    -------
    top_movies page, results (list of top movies), user inputted number, user inputted genre, and value for number of rows in your search result.
    '''
    num = request.form['rank']
    genre = request.form.get('genres')
    if genre == 'None':
        genre = None
    results = get_top_movies(num=num, genre=genre)

    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()

    select = request.form.get('genres')

    if select == 'None':
        movie_genre = ''
    elif select != 'None':
        movie_genre = f'WHERE genre = "{select}"'
    limit_results = f"LIMIT {num}"

    query_rows = f'''
        SELECT COUNT(*)
        FROM (
            SELECT * 
            FROM movieInfo
            {movie_genre}
            {limit_results}
        )
    '''

    result = cur.execute(query_rows).fetchone()
    row_count = result[0]

    return render_template('top_movies.html', results=results, num=num, genre=genre, row_count=row_count)

# Visualization 2: Radar plots to compare movies across different dimensions.
@app.route('/radar_chart', methods=['GET', 'POST'])
def get_radar_chart():
    '''
    Create a radar plot for one or two movies depending on user input of movie titles.

    Parameters
    ----------
    None

    Returns
    -------
    radar_chart.html page, movie titles, radar_plot, list of search results (results, comp_result) for tables
    '''
    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()

    #Get header row from table
    cur.execute("SELECT * FROM movieInfo")
    head = [tuple[0] for tuple in cur.description]
    boxoffice_header = []
    boxoffice_header.append(head[6])
    boxoffice_header.append(head[7])
    boxoffice_header.append(head[8])

    movie_title = request.form.get('titles')

    comp_title = request.form.get('titles2')

    #Plot radar chart depending on user input
    r = get_boxoffice_values(title=movie_title)
    theta = boxoffice_header

    if comp_title != 'None':
        r2 = get_compare_boxoffice_values(title=comp_title)
        theta = boxoffice_header

    if comp_title == 'None':
        data = [go.Scatterpolar(name=movie_title,
        r = r, theta = theta, fill = 'toself', line = dict(color = '#F5C518'))]

        fig = go.Figure(data=data)
        radar_plot = fig.to_html(full_html=False)
    elif comp_title == movie_title:
        data = [go.Scatterpolar(name=movie_title,
        r = r, theta = theta, fill = 'toself', line = dict(color = '#F5C518'))]

        fig = go.Figure(data=data)
        radar_plot = fig.to_html(full_html=False)
    else: 
        data = [go.Scatterpolar(name=movie_title,
        r = r, theta = theta, fill = 'toself', line = dict(color = '#F5C518'), ),
        go.Scatterpolar(name=comp_title,
        r = r2, theta = theta, fill = 'toself', line = dict(color = '#1848f5'))
        ]

        fig = go.Figure(data=data)
        radar_plot = fig.to_html(full_html=False)

    #tables
    movie_title = request.form.get('titles')
    results = spec_movie_info(title=movie_title)

    comp_result = spec_movie_info(title=comp_title)

    return render_template('radar_chart.html', title=movie_title, boxoffice_url=radar_plot, results=results, comp_result=comp_result, comp_title=comp_title)

#Visualization 3: view ratings table and scatterplot
@app.route('/ratings', methods=['GET', 'POST'])
def rating_view():
    '''
    Create a table view and bar plot based on user input of IMDb Rating. Bar plot will show budget and worldwide gross against rank in original top 250 list.
    The table view gives more information about the titles that have the user's chosen IMDb Rating.

    Parameters
    ----------
    None

    Returns
    -------
    'ratings.html' page, list of rank, worldwide Gross, budget, and titles for movies of a chosen IMDb Rating, user inputted rating, # of results returned from user input, 
    list of ranks resulting from user input, list of worldwide gross resulting from user input, bar plot)
    '''
    #ratings table
    rating = request.form.get('ratings')

    results = get_ratings(rating=rating)

    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()
    rating = request.form.get('ratings')
    movie_rating = f'''WHERE imdbRating = "{rating}"'''
    
    query_rows = f'''
        SELECT COUNT(*)
        FROM movieInfo
        {movie_rating}
    '''

    result = cur.execute(query_rows).fetchone()
    row_count = result[0]

    query_trg = f'''
        SELECT listRank, worldwideGross, budget, title
        FROM movieInfo
        {movie_rating} AND budget != "No info" AND worldwideGross != "No info"
    '''

    #bar plot to compare budget and worldwide gross against rank.
    cur.execute(query_trg)
    rank_list = [result[0] for result in cur.fetchall()]
    cur.execute(query_trg)
    gross_list = [result[1] for result  in cur.fetchall()]
    cur.execute(query_trg)
    budget_list = [result[2] for result  in cur.fetchall()]
    cur.execute(query_trg)
    title_list = [result[3] for result  in cur.fetchall()]
    conn.close()


    d = {'title': title_list, 'gross': gross_list, 'rank': rank_list, 'budget': budget_list}
    df = pd.DataFrame(data=d)

    fig = px.bar(df, x = 'rank', y = ['budget', 'gross'], hover_name= 'title', color_discrete_map={
        'budget': '#1848f5',
        'gross': '#F5C518'
    })
    fig.update_layout(xaxis_title="Rank", yaxis_title="Amount in USD")
    bar_plot = fig.to_html(full_html=False)

    return render_template('ratings.html', results=results, rating=rating, row_count=row_count, rlist=rank_list, glist=gross_list, url=bar_plot)

#Visualization 4
@app.route('/directors', methods=['GET', 'POST'])
def director_view():
    '''
    Create a table view and bar plot based on user input of top X directors (from the top 250 list of movies) based on the number of their directing credits. Bar plot shows the number of directing credits a director has and from which country they are from.
    The table view gives more information about the directors that fall in the user's chosen number of results and country filter.

    Parameters
    ----------
    None

    Returns
    -------
    'directors.html' page, list of directors and information about them, user's chosen number of results, actual number of returned results, country user chooses, bar plot to show # of directing credits for directors)
    '''
    num = request.form['d_rank']
    country = request.form.get('c')
    if country == 'None':
        country = None
    results = get_top_directors(num=num, country=country)

    conn = sqlite3.connect('movie.db')
    cur = conn.cursor()

    select = request.form.get('countries')

    if select == 'None':
        d_country = ''
    elif select != 'None':
        d_country = f'WHERE birthCountry = "{select}"'
    limit_results = f"LIMIT {num}"

    query_rows = f'''
        SELECT COUNT(*)
        FROM (
            SELECT * 
            FROM director
            {d_country}
            {limit_results}
        )
    '''
    result = cur.execute(query_rows).fetchone()
    row_count = result[0]

    query_credit = f'''
        SELECT name, directorCredits, birthCountry
        FROM director
        {d_country}
        {limit_results}
    '''

    cur.execute(query_credit)
    name_list = [result[0] for result in cur.fetchall()]
    cur.execute(query_credit)
    credit_list = [result[1] for result in cur.fetchall()]
    cur.execute(query_credit)
    country_list = [result[2] for result in cur.fetchall()]
    conn.close()


    d = {'name': name_list, 'credits': credit_list, 'country': country_list}
    df = pd.DataFrame(data=d)

    #scatterplot
    fig = px.bar(df, x = 'name', y = 'credits', color='country')
    fig.update_layout(xaxis_title="Director Name", yaxis_title="# of Directing Credits")
    url = fig.to_html(full_html=False)

    return render_template('directors.html', results=results, num=num, country=country, row_count=row_count, url=url)


#reload pages to make sure plots update
@app.after_request
def add_header(response):
    '''
    Control cache so that it doesn't store a cache so plots and charts can stay up to date as users change their inputs for results.

    Parameters
    ----------
    response
        webpage response

    Returns
    -------
    response
    '''
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

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

    # create_db()
    # update_director_table()
    # update_movie_table()

    print('starting Flask app', app.name)
    app.run(debug=True)



