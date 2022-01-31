import numpy as np
import pandas as pd
from sqlalchemy import true
from items import Item
from typing import List
from constants import GAME_TICKS_PER_SECOND, MANA_PER_ATK, MAX_TICK_ATK_SPEED
from parse_data import get_champions

CHAMPIONS_DF = get_champions()

# Cases to handle for abilities:

# For some champions, the ability is channeled. 
# For some champions,  the ability is series of auto attacks (Urgot)
# Ability is a physical attack that can partially Crit (without bonus damage)
# Ability empowers the next auto attack (Garen)
# Ability has a passive effect.


# Plan: 
# 1. Each champion must implement ability active and ability passive effect
# 2. Each champion has channels_ability flag, if true, we use ability_channeled, else use ability method.
# 3. Each champion has ability channeled; outputs damage every X game ticks just like an attack
# 4. Each champion has ability damage over time - this is non-channeled damage


# Implement Urgot and see what the best items are.

class ChannelingAbilityTracker:
    def __init__(self, starting_state: int, max_procs: int, rate: int):
        self.starting_state = starting_state
        self.max_procs = max_procs
        self.rate = rate

        self.num_procs = 0

    def trigger_ability(self, champion):
        trigger = (champion.state - self.starting_state) % self.rate == 0
        if self.num_procs == self.max_procs:
            champion.is_currently_casting = False
            champion.last_attack = champion.state
        if trigger:
            self.num_procs += 1
            print(self.num_procs)
        return trigger
        

def parse_ability_effect(ability_dict: dict):
    vars = ability_dict['variables']
    parsed = {}
    for var in vars:
        parsed[var['name']] = var['value']
    return parsed

class Champion:
    def __init__(self, class_name: str, items: List[Item] = [], level: int = 1, channels_ability: bool = False, physical_ability: bool = False):
        attributes = CHAMPIONS_DF[CHAMPIONS_DF.python_name == class_name].iloc[0]

        level_multipliers = {1: 1, 2: 1.8, 3: 3.24} # "common knowledge"
        self.level = level
        self.attributes = attributes
        print(f'attributes: {attributes}')
        self.ability_effect = parse_ability_effect(self.attributes['ability'])
        # print(f'ability effects: {self.ability_effect}')

        self.traits = attributes['traits']
        self.base_armor = attributes['armor']
        self.base_crit_chance = attributes['critChance']
        self.base_crit_multiplier = attributes['critMultiplier']
        self.base_damage = attributes['damage'] * level_multipliers[level]
        self.base_hp = attributes['hp'] * level_multipliers[level]
        self.initial_mana = attributes['initialMana']
        self.base_magic_resist = attributes['magicResist']
        self.max_mana = attributes['mana']
        self.base_range = attributes['range']
        self.base_as = attributes['attackSpeed']

        self.channels_ability = channels_ability
        self.physical_ability = physical_ability

        if physical_ability:
            self.ability_can_crit = True
        else:
            self.ability_can_crit = False
            

        # game state trackers
        self.buffs = []
        self.current_mana = self.initial_mana  
        self.state = 0   
        self.last_attack = 0   
        self.is_dead = False
        self.is_incapacitated = False
        self.items = items

        # these need to be set for channeling champions
        self.casting_tracker = None
        self.max_procs = 0
        self.rate = 0
        self.is_currently_casting = False

        # mutable attributes
        self.as_multiplier = 1
        self.ap_multiplier = 1


        # initialize current offensive stats
        self.current_as = self.base_as
        self.current_ad = self.base_damage
        self.current_crit_chance = self.base_crit_chance
        self.current_crit_multiplier = self.base_crit_multiplier
        self.current_hp = self.base_hp
        self.ticks_per_attack = int((1 / self.current_as) * GAME_TICKS_PER_SECOND)

        # initialize current defensive stats
        self.current_armor = self.base_armor
        self.current_mr = self.base_magic_resist

        for item in items:
            item.apply_equip_effect(self)

        self.taken_action = False

    def get_stats(self):
        return {'AD': round(self.current_ad, 2), 
        'AP': self.ap_multiplier,
        'Attack Speed': round(self.current_as, 2), 
        'Crit Chance': self.current_crit_chance, 
        'Crit Damage Multiplier': round(self.current_crit_multiplier, 2),
        'Initial Mana': self.current_mana,
        'HP': self.current_hp}

    def get_ability_attr(self, key):
        return self.ability_effect[key][self.level]

    def add_crit_chance(self, bonus_crit_chance):
        self.current_crit_chance += bonus_crit_chance / 100

    def add_crit_damage(self, bonus_crit_damage):
        self.base_crit_multiplier += bonus_crit_damage / 100

    def add_as(self, bonus_as): 
        self.as_multiplier += bonus_as / 100 # bonus_as is expressed in tens by default
        self.current_as = self.as_multiplier * self.base_as
        self.ticks_per_attack = int((1 / self.current_as) * GAME_TICKS_PER_SECOND)

    def add_ap(self, bonus_ap):
        self.ap_multiplier += bonus_ap / 100
        self.current_ap = self.ap_multiplier * 100

    def add_ad(self, bonus_ad):
        self.current_ad += bonus_ad

    def add_mana(self, bonus_mana):
        self.current_mana += bonus_mana
        self.current_mana = min(self.current_mana, self.max_mana)

    def set_mana(self, mana):
        self.current_mana = min(mana, self.max_mana)

    def set_casting_tracker(self, max_procs, rate):
        self.casting_tracker = ChannelingAbilityTracker(self.state, max_procs, rate)
        print(f'initialized casting tracker with state {self.state}')

    def action(self, defending_champion):
        if self.is_dead:
            return 0
        self.apply_buff()
        self.remove_buff()
        if not self.is_incapacitated:
            if self.channels_ability:
                dmg = self.cast_channel_ability()
            else:
                dmg = self.cast_ability(defending_champion) # TODO: figure out movement and casting abilities.
            # if dmg != 0:
            #     return dmg
            # self.move()
            if not self.taken_action:
                dmg = self.attack(defending_champion)
        self.advance_state()
        return dmg

    def take_damage(self, damage):
        if self.is_dead:
            return
        
        self.current_hp -= damage['ad'] * (100/(100 + self.current_armor))
        self.current_hp -= damage['ap'] * (100/(100 + self.current_mr))
        self.current_hp -= damage['true']

        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_dead = True

        

    def roll_for_crit(self, damage):
        if np.random.uniform() < self.current_crit_chance:
            self.did_crit = True
            return damage * self.current_crit_multiplier
        self.did_crit = False
        return damage

    @staticmethod
    def accumulate_damage(total_damage, new_damage):
        return {x: total_damage.get(x, 0) + new_damage.get(x, 0) for x in total_damage}

    def attack(self, defending_champion):
        total_damage = {'ad': 0, 'ap': 0, 'true': 0}
        if self.state - self.last_attack == self.ticks_per_attack:
            self.last_attack = self.state
            total_damage = self.accumulate_damage(total_damage, {'ad': self.roll_for_crit(self.current_ad), 'ap': 0, 'true': 0})
            # print(f'state: {self.state}, mana: {self.current_mana}')
            self.set_mana(self.current_mana + MANA_PER_ATK)
            for item in self.items:
                total_damage = self.accumulate_damage(total_damage, item.apply_onhit_effect(self, defending_champion))
        return total_damage

    def move(self):
        # implement moving logic if out of range
        return False

    def resolve_ability_item_effects(self, defending_champion):
        if self.physical_ability:
            for item in self.items:
                item.apply_onhit_effect(self, defending_champion)

    def resolve_after_ability_effects(self):
        for item in self.items:
            item.apply_after_ability_effect(self)

    def cast_ability(self, defending_champion):
        # 1. calc ability dmg (without bonus). 
        # 2. if AP and JG OR AD, calc crit
        # 3. add bonus damage.
        # 4. 
        if self.current_mana == self.max_mana:
            self.set_mana(0)
            dmg = self.ability_base_damage()
            self.apply_buff()
            self.resolve_ability_item_effects(defending_champion)
            self.resolve_after_ability_effects()
            self.taken_action = True
            return dmg
        return 0

    def cast_channel_ability(self):
        if self.current_mana == self.max_mana:
            print('in here')
            self.set_mana(0)
            self.set_casting_tracker(self.max_procs, self.rate)
            self.resolve_after_ability_effects() # for now it is okay to resolve this at the beginning, since it's just Blue Buff
            self.is_currently_casting = True
        else:
            if self.is_currently_casting:
                self.taken_action = True 
                if self.casting_tracker.trigger_ability(self):
                    dmg = self.calculate_total_ability_damage()
                    self.apply_buff()
                    self.resolve_ability_item_effects()
                    return dmg
        return 0


    def ability_base_damage(self): # implement this in subclass
        pass

    def ability_bonus_damage(self):
        return 0

    # this includes debuffs as well.
    def apply_buff(self):
        pass

    def remove_buff(self):
        pass

    def advance_state(self):
        self.state += 1
        self.taken_action = False

    def equip_item(self, item):
        self.items.append(item)

    def unequip_item(self, item_idx):
        self.items.pop(item_idx)


class Darius(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level)


class Ziggs(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level)

    def ability_base_damage(self):
        return self.ap_multiplier * self.get_ability_attr('Damage')


class TwistedFate(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level)

    def ability_base_damage(self):
        return self.ap_multiplier * self.get_ability_attr('BaseDamage')


class Graves(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level)

    def ability_base_damage(self):
        return self.ap_multiplier * self.get_ability_attr('Damage')


class Ezreal(Champion): # todo: implement stacking buff from attack.
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level, physical_ability=True)
        self.stacks = 0

    def ability_base_damage(self):
        physical_damage = self.current_ad * self.get_ability_attr('PercentAD')
        physical_damage += self.get_ability_attr('BonusDamage')
        physical_damage = self.roll_for_crit(physical_damage)
        return {'ad': physical_damage, 'ap': 0, 'true': 0}

    def apply_buff(self):
        if self.stacks < self.get_ability_attr('MaxStacks'):
            self.add_as(self.get_ability_attr('ASBoost'))
            self.stacks += 1


class Caitlyn(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level)

    def ability_base_damage(self):
        return self.ap_multiplier * self.get_ability_attr('Damage')
        

class Zyra(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level)

    def ability_base_damage(self):
        return self.ap_multiplier * self.get_ability_attr('Damage')


class Zilean(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level)

    def ability_base_damage(self):
        return self.ap_multiplier * self.get_ability_attr('Damage')


class Twitch(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level, physical_ability=True)

    def ability_base_damage(self):
        return self.damage * self.get_ability_attr('PercentAttackDamage')

    def ability_bonus_damage(self):
        return self.get_ability_attr('BaseDamage')


class Kassadin(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level)

    def ability_base_damage(self):
        return self.get_ability_attr('Damage') * self.ap_multiplier


class Urgot(Champion):
    def __init__(self, items: List[Item] = [], level: int = 1):
        class_name = self.__class__.__name__
        super().__init__(class_name, items=items, level=level, channels_ability=True, physical_ability=True)
        self.max_procs = self.get_ability_attr('Duration') * self.get_ability_attr('AttacksPerSecond')
        self.rate = GAME_TICKS_PER_SECOND / self.get_ability_attr('AttacksPerSecond')

    def ability_base_damage(self):
        """For the next @ModifiedDuration@ seconds, Urgot attacks the closest enemy at a fixed rate of @AttacksPerSecond@ attacks per second. 
        Each attack deals <scaleAD>@DamagePerShot@</scaleAD> %i:scaleAD% %i:scaleAS% physical damage. 
        (This Ability's damage scales with Attack Damage and Attack Speed.)"""
        return self.get_ability_attr('ADRatio') * self.damage + self.get_ability_attr('ASRatio') * 100 * self.attack_speed




if __name__ == '__main__':
    # champ = Urgot()
    # num_seconds = 20
    # total_damage = 0
    # debug = True

    # for i in range(num_seconds * 100):
    #     action = champ.action()
    #     if debug and action != 0:
    #         print(action)
    #     total_damage += action

    # print(total_damage)

    from items import LastWhisper
    champ = Urgot()
    print(champ.current_crit_chance)
    champ = Urgot(items=[LastWhisper()])
    print(champ.current_crit_chance)