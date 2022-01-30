from sys import flags
from constants import CDRAGON_ASSET_PATH, DATA_PATH, SET_NUM
import pandas as pd
import json

def dds_to_cdragon(path: str):
    path = path.replace('ASSETS/', '')
    path = path.lower().replace('.dds', '.png')
    return f'{CDRAGON_ASSET_PATH}/{path}'

def flatten_and_transform_champion_dict(champion: dict):
    stats = champion.pop('stats')
    champion['icon'] = dds_to_cdragon(champion['icon'])
    champion.update(stats)
    return champion

def get_champions():
    data = json.load(open(DATA_PATH, 'rb'))
    champions = data['sets'][SET_NUM]['champions']
    flattened_champions = [flatten_and_transform_champion_dict(champion) for champion in champions]
    champions = pd.DataFrame.from_records(flattened_champions)
    champions['python_name'] = champions['name'].apply(lambda x: x.replace(' ', '').replace("'", ''))
    return champions


def get_items():
    data = json.load(open(DATA_PATH, 'rb'))
    items = data['items']
    items = pd.DataFrame.from_records(items)
    items['cdragon_path'] = items['icon'].apply(dds_to_cdragon)
    items['python_name'] = items['name'].apply(lambda x: x.replace(' ', '').replace("'", ''))
    return items

if __name__ == '__main__':
    print(get_champions())