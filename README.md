# Web Scraping and Data Visualizations for IMDb's Top 250 English Movies

This is a final project for SI 507 at UMSI for Winter 2021.
    
This project looks at [IMDb's Top 250 English-language movies](https://www.imdb.com/chart/top-english-movies) as rated by IMDb Users. You will be able to learn more about the movies in the list and the directors of those movies. This project provides data visualization through Flask and Plotly.

# Data Sources
1. [Top 250 English Rated Movies from IMDb.com](https://www.imdb.com/chart/top-english-movies)
2. Each movie’s page on IMDb.com (i.e. [The Shawshank Redemption](https://www.imdb.com/title/tt0111161/))
3. Each movie’s director’s IMDb.com page (i.e. [Frank Darabont](https://www.imdb.com/name/nm0001104/))

# Required Python Packages
* beautifulsoup4 4.9.3
* bs4 0.0.1
* Flask 1.1.2
* pandas 1.2.1
* plotly 4.14.3
* requests 2.25.1

# How to Run the Program

**Step 1: Install packages**
```
$ pip3 install -r requirements.txt
```
You can install the provided requirements.txt file. You may need to adjust the code above for installing the packages depending on your OS. 

**Step 2: Download files and run final_project.py**
```
$ python3 final_project.py
```
Download the files provided in this repo and make sure all files and folders are stored in the same place. Then, run the final_project.py file to get the below link. 

**Step 3: Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)**

Go to the link provided ([http://127.0.0.1:5000/](http://127.0.0.1:5000/)) in your terminal after running final_project.py. This will give you access the webpage to interact with the program and its visualization capabilities.

There are four different options to visualize data from the data source. You can input your choices to get different visualizations for each option. The data visualizations include:
1. Top X number of movies in the list based on genre
2. Compare two movies across their box office numbers
3. Compare budget and worldwide gross for movies with the same IMDb rating
4. Top X number of directors from the list based on birth country


