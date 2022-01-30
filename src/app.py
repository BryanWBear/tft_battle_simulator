# from champions import Ziggs, Urgot
from items import Item, GuinsoosRageblade, RabadonsDeathcap, ArchangelsStaff, SpearofShojin, InfinityEdge, JeweledGauntlet, RapidFirecannon
from itertools import combinations, product
import numpy as np
import pandas as pd
import streamlit as st
from typing import List
from parse_data import get_items, get_champions
import importlib


def to_html(icons: pd.Series):
    return icons.apply(lambda name: f"<img src='{name}' style='display:block;margin-left:auto;margin-right:auto;width:100px;border:0;'><div style='text-align:center'>")

champions_module = importlib.import_module('champions')
df = get_champions()

name_to_api_name = {x: y for x, y in zip(df.name, df.apiName)}
api_name_to_name = {x: y for x, y in zip(df.apiName, df.name)}


st.header('Configure Attacker Parameters')
champion_name = st.selectbox('Select Attacking Champion', options=df.name)
champion_info = df[df.name == champion_name].iloc[0]

try:
    champion_class = getattr(champions_module, champion_name)
except:
    st.error('Champion is not Implemented')
    champion_class = None

st.image(champion_info.icon)
stars_dict = {'⭐': 1, '⭐⭐': 2, '⭐⭐⭐': 3}
num_stars = st.radio('Number of Stars', options=stars_dict)
num_stars = stars_dict[num_stars]
item_df = get_items()
items = [GuinsoosRageblade, RabadonsDeathcap, ArchangelsStaff, SpearofShojin, InfinityEdge, JeweledGauntlet, RapidFirecannon]
item_dict = {item().name: item for item in items}
selected_items = st.multiselect('Items to Equip', options=list(item_dict.keys()))
champion = champion_class(items=[item_dict[item]() for item in selected_items], level=num_stars)
st.write(champion.get_stats())
# num_seconds = st.sidebar.number_input('Number of Seconds To Run Simulation', min_value=1, max_value=30, value=20)
# item_df = item_df[item_df.name.isin(SET_ITEMS)]
# st.write(item_df)
# st.image(list(item_df.cdragon_path))

# def dmg_to_cum_series(damage, name=None):
#     s = pd.Series(np.cumsum(damage))
#     if name:
#         return s.rename(name)
#     return s

# def run_simulation(champion_class, item_set, num_seconds=20, num_simulations=10):
#     all_damages = []
#     for _ in range(num_simulations):
#         damages = []
#         champion = champion_class(items=item_set, level=num_stars)

#         for _ in range(num_seconds * 100):
#             damages.append(champion.action())

#         all_damages.append(damages)
#     return np.mean(np.array(all_damages), axis=0)

# def items_to_name(item_set: List[Item]):
#     # print(f'item set: {item_set}')
#     names = [item.name for item in item_set]
#     # print(names)
#     return ', '.join(names)
    
# dmg1 = run_simulation(champion_class, [JeweledGauntlet(), RabadonsDeathcap()], num_seconds=num_seconds)
# dmg2 = run_simulation(champion_class, [JeweledGauntlet(), InfinityEdge()], num_seconds=num_seconds)
# st.line_chart(dmg_to_cum_series(dmg1, name='jg rabs'))
# st.line_chart(dmg_to_cum_series(dmg2, name='jg iee'))

# if champion_class is not None:
#     st.write(champion_class)
#     items = [GuinsoosRageblade, RabadonsDeathcap, ArchangelsStaff, SpearofShojin, InfinityEdge, JeweledGauntlet, RapidFirecannon]
#     items = [cl() for cl in items]
#     # print([item.unique for item in items])
#     non_unique_items = [item for item in items if not item.unique]
#     # print(non_unique_items)

#     res = []

#     for item_set in combinations(items, 3):
#         names = items_to_name(item_set)
#         dmg = run_simulation(champion_class, item_set, num_seconds=num_seconds)
#         res.append(dmg_to_cum_series(dmg, name=names))

#     for non_unique_item, item in product(non_unique_items, items):
#         item_set = [non_unique_item, non_unique_item, item]
#         names = items_to_name(item_set)
#         dmg = run_simulation(champion_class, item_set, num_seconds=num_seconds)
#         res.append(dmg_to_cum_series(dmg, name=names))

#     regular_dmg = run_simulation(champion_class, [], num_seconds=num_seconds) 
#     res_df = pd.concat(res + [dmg_to_cum_series(regular_dmg, name='No Items')], axis=1)

#     selected = st.multiselect('Select Item Sets To Compare', options=res_df.columns, default=['No Items'])
#     st.line_chart(res_df[selected])

#     final_dmg = res_df.iloc[-1].T.reset_index()
#     final_dmg.columns = ['Item Set', 'Damage']
#     st.header('Best Items (Ordered by Total Unmitigated Damage)')
#     st.dataframe(final_dmg.sort_values('Damage', ascending=False))



# ziggs = Ziggs(items=[GuinsoosRageblade()])
# guinsoos_dmg = run_simulation(ziggs)

# ziggs = Ziggs(items=[RabadonsDeathcap()])
# rabs_dmg = run_simulation(ziggs)
# # st.line_chart(rabs_dmg)

# ziggs = Ziggs(items=[ArchangelsStaff()])
# arch_dmg = run_simulation(ziggs)


# simulations = [regular_dmg, guinsoos_dmg, rabs_dmg, arch_dmg]

# df = pd.concat([dmg_to_cum_series(x) for x in simulations], axis=1)
# raw_df = pd.concat([pd.Series(x) for x in simulations], axis=1)

# st.line_chart(df)
# st.line_chart(raw_df)
