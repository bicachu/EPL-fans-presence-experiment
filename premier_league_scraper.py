from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import re

errors = []
season = []
stats_check = ['possession_%', 'shots_on_target', 'shots', 'touches', 'passes',
               'tackles', 'clearances', 'corners', 'offsides', 'yellow_cards',
               'red_cards', 'fouls_conceded']


# match id references for curating dataset #
#  46605 - first match of 19-20 season
#  46984 - last match of 19-20 season
#  58897 - first match of 19-20 season
#  59174 - last match available in 20-21 season (3/15/21)


for id in tqdm(range(46605, 59174 + 1)):
    # opening the connection and grabbing the page
    my_url = f'https://www.premierleague.com/match/{id}'
    option = Options()
    option.headless = True
    driver = webdriver.Chrome(options=option)
    driver.get(my_url)
    sleep(5)
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '/html/body/section/div/div'))).click()
    driver.maximize_window()
    sleep(5)

    # scraping the data
    try:

        date = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((
            By.XPATH, '//*[@id="mainContent"]/div/section/div[2]/section/div[1]/div/div[1]/div[1]'))).text
        date = datetime.strptime(date, '%a %d %b %Y').strftime('%Y-%m-%d')  # ('%m-%d-%Y')

        home_team = driver.find_element_by_xpath(
            '//*[@id="mainContent"]/div/section/div[2]/section/div[3]/div/div/div[1]/div[1]/a[2]/span[1]').text
        away_team = driver.find_element_by_xpath(
            '//*[@id="mainContent"]/div/section/div[2]/section/div[3]/div/div/div[1]/div[3]/a[2]/span[1]').text

        full_time_scores = driver.find_element_by_xpath(
            '//*[@id="mainContent"]/div/section/div[2]/section/div[3]/div/div/div[1]/div[2]/div/div').text

        half_time_scores = driver.find_element_by_xpath(
            '//*[@id="mainContent"]/div/section[2]/div[2]/section/div[3]/div/div/div[2]/div').text

        home_HT_score = half_time_scores[11:].split('-')[0]
        away_HT_score = half_time_scores[11:].split('-')[1]

        home_FT_score = full_time_scores.split('-')[0]
        away_FT_score = full_time_scores.split('-')[1]

        home_events_path = '//*[@id="mainContent"]/div/section[2]/div[2]/section/div[3]/div/div/div[4]/div[1]'
        away_events_path = '//*[@id="mainContent"]/div/section[2]/div[2]/section/div[3]/div/div/div[4]/div[2]'

        home_events = driver.find_element_by_xpath(home_events_path)
        away_events = driver.find_element_by_xpath(away_events_path)
        home_events_count = len(home_events.find_elements_by_xpath('./div'))
        away_events_count = len(away_events.find_elements_by_xpath('./div'))

        home_goals_mins = []
        for i in range(1, home_events_count + 1):
            event_str = driver.find_element_by_xpath(home_events_path + f'/div[{i}]').text
            event_str = re.sub(" \+\d{1,2}", "", event_str)  # remove any extra time minutes
            if 'Goal' in event_str or 'penalty.scored' in event_str:
                minutes = re.findall(r'\d+', event_str)
                minutes = list(map(int, minutes))
                home_goals_mins.extend(minutes)

        away_goals_mins = []
        for j in range(1, away_events_count + 1):
            event_str = driver.find_element_by_xpath(away_events_path + f'/div[{j}]').text
            event_str = re.sub(" \+\d{1,2}", "", event_str)  # remove any extra time minutes
            if 'Goal' in event_str or 'penalty.scored' in event_str:
                minutes = re.findall(r'\d+', event_str)
                minutes = list(map(int, minutes))
                away_goals_mins.extend(minutes)

        elem = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@class='tablist']//li[@data-tab-index='2']")))

        elem.click()
        sleep(5)
        dfs = pd.read_html(driver.page_source)
        stats = dfs[-1]
        driver.quit()

    except:
        driver.quit()
        errors.append(id)
        continue

    # handling the stats
    home_stats = {}
    away_stats = {}

    home_series = stats[home_team]
    away_series = stats[away_team]
    stats_series = stats['Unnamed: 1']

    for row in zip(home_series, stats_series, away_series):
        stat = row[1].replace(' ', '_').lower()
        home_stats[stat] = row[0]
        away_stats[stat] = row[2]

    stats_check = ['possession_%', 'shots_on_target', 'shots', 'touches', 'passes',
                   'tackles', 'clearances', 'corners', 'offsides', 'yellow_cards',
                   'red_cards', 'fouls_conceded']

    for stat in stats_check:
        if stat not in home_stats.keys():
            home_stats[stat] = 0
            away_stats[stat] = 0

    # storing the data
    match = [id, date, home_team, away_team, home_HT_score, away_HT_score, home_FT_score, away_FT_score,
             home_goals_mins, away_goals_mins, home_stats['possession_%'], away_stats['possession_%'],
             home_stats['shots_on_target'], away_stats['shots_on_target'], home_stats['shots'], away_stats['shots'],
             home_stats['touches'], away_stats['touches'], home_stats['passes'], away_stats['passes'],
             home_stats['tackles'], away_stats['tackles'], home_stats['clearances'], away_stats['clearances'],
             home_stats['corners'], away_stats['corners'], home_stats['offsides'], away_stats['offsides'],
             home_stats['yellow_cards'], away_stats['yellow_cards'], home_stats['red_cards'], away_stats['red_cards'],
             home_stats['fouls_conceded'], away_stats['fouls_conceded']]

    season.append(match)

    print(f'ID {id} scraped.')

# exporting the data
columns = ['match_id', 'date', 'home_team', 'away_team', 'home_ht_score', 'away_ht_score', 'home_ft_score',
           'away_ft_score',
           'home_goals_mins', 'away_goals_mins']

for stat in stats_check:
    columns.append(f'home_{stat}')
    columns.append(f'away_{stat}')

dataset = pd.DataFrame(season, columns=columns)
dataset.to_csv('data/premier_league_matches.csv', index=False)
dataset.to_pickle('data/premier_league_matches.pkl')
print('.csv file exported.')
print(f'Number of errors: {len(errors)}')
print('Errors:\n')
print(errors)
