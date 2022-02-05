from parse_data import get_items
from fnvhash import fnv1a_32
import numpy as np
from enum import Enum

# TODO: write unit tests for items.

ITEMS_DF = get_items()

def var_to_hash(var: str):
    return '{' + hex(fnv1a_32(str.encode(var.lower())))[2:] + '}'

class ItemComponent(Enum):
    RECURVE_BOW = 'bow'
    CHAIN_VEST = 'vest'
    GIANTS_BELT = 'belt'
    TEAR_OF_THE_GODDESS = 'tear'
    SPARRING_GLOVES = 'glove'
    NEGATRON_CLOAK = 'cloak'
    BF_SWORD = 'bf'
    NEEDLESSLY_LARGE_ROD = 'rod'


class Item:
    def __init__(self, class_name: str):
        # print(f'class_name: {class_name}')
        item = ITEMS_DF[ITEMS_DF.python_name == class_name].iloc[0]
        # print(f'item: {item}')
        self.effects = item.effects
        print(self.effects)
        print('Armor' in self.effects)
        self.as_key = 'AS'
        self.crit_chance_key = 'CritChance'
        self.ap_key = 'AP'
        self.ad_key = 'AD'
        self.mana_key = 'Mana'
        self.armor_key = 'Armor'
        self.crit_damage_key = var_to_hash('CritDamageAmp')
        self.health_key = 'Health'
        self.mr_key = 'MagicResist'


        self.unique = item['unique']
        self.icon = item['icon']
        self.name = item['name']
        self.components = []

    def apply_equip_effect(self, champion):
        if self.ap_key in self.effects:
            champion.add_ap(self.effects[self.ap_key])
        if self.ad_key in self.effects:
            champion.add_ad(self.effects[self.ad_key])
        if self.as_key in self.effects:
            champion.add_as(self.effects[self.as_key])
        if self.mana_key in self.effects:
            champion.add_mana(self.effects[self.mana_key])
        if self.crit_chance_key in self.effects:
            champion.add_crit_chance(self.effects[self.crit_chance_key])
        if self.crit_damage_key in self.effects:
            champion.add_crit_damage(self.effects[self.crit_damage_key])
        if self.armor_key in self.effects:
            champion.add_armor(self.effects[self.armor_key])
            print('added armor')
        if self.health_key in self.effects:
            champion.add_health(self.effects[self.health_key])
        if self.mr_key in self.effects:
            champion.add_mr(self.effects[self.mr_key])

    def apply_after_equip_effect(self, champion):
        pass

    def apply_onhit_effect(self, attacking_champion, defending_champion):
        pass

    def apply_modify_ability_dmg_effect(self, champion, dmg):
        return dmg

    def apply_after_ability_effect(self, champion):
        pass

    def apply_timed_effect(self, champion):
        pass


# AP items

class HexTechGunblade(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.BF_SWORD, ItemComponent.NEEDLESSLY_LARGE_ROD]

class Morellonomicon(Item): # TODO: implement non-stacking damage over time.
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.GIANTS_BELT, ItemComponent.NEEDLESSLY_LARGE_ROD]

class RabadonsDeathcap(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.NEEDLESSLY_LARGE_ROD, ItemComponent.NEEDLESSLY_LARGE_ROD]

class GuinsoosRageblade(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.RECURVE_BOW, ItemComponent.NEEDLESSLY_LARGE_ROD]

    # def apply_equip_effect(self, champion):
    #     champion.set_ap(champion.ap + self.effects['AP'])
    #     self.as_bonus = self.effects['AttackSpeedPerStack']/100 * champion.base_as # TODO: figure out order of items.
    #     # print(f"Guinsoo's attack speed bonus: {self.as_bonus}")
    #     champion.set_attack_speed(champion.attack_speed + self.effects['AS']/100)

    def apply_onhit_effect(self, champion):
        champion.add_attack_speed(self.effects['AttackSpeedPerStack'])
        

class IonicSpark(Item): # TODO: need defenders / positioning for this to work
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.NEEDLESSLY_LARGE_ROD, ItemComponent.NEGATRON_CLOAK]

class JeweledGauntlet(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.crit_damage_key = var_to_hash('CritDamageAmp')
        self.components = [ItemComponent.NEEDLESSLY_LARGE_ROD, ItemComponent.SPARRING_GLOVES]
    
    def apply_modify_ability_dmg_effect(self, champion, dmg):
        if np.random.uniform() < champion.crit_chance:
            dmg *= champion.crit_multiplier
        return dmg

class ArchangelsStaff(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.interval_key = var_to_hash('IntervalSeconds')
        self.ap_per_interval_key = var_to_hash('APPerInterval')  
        self.components = [ItemComponent.NEEDLESSLY_LARGE_ROD, ItemComponent.TEAR_OF_THE_GODDESS]      

    def apply_timed_effect(self, champion, state):
        if state % self.effects[self.interval_key] == 0:
            champion.add_ap(self.effects[self.ap_per_interval_key]) 

# AD/AP items 

class InfinityEdge(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.crit_key = var_to_hash('BonusCritDmgPerCritAbove100')
        self.components = [ItemComponent.BF_SWORD, ItemComponent.SPARRING_GLOVES]

    def apply_after_equip_effect(self, champion): # TODO: will need to be changed if champion gains crit dynamically.
        champion.crit_multiplier += (champion.crit_chance - 1)*self.effects[self.crit_key]


class SpearofShojin(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        mana_key = var_to_hash('FlatManaRestore')
        self.mana_restore_amount = self.effects[mana_key]
        self.components = [ItemComponent.BF_SWORD, ItemComponent.TEAR_OF_THE_GODDESS]

    def apply_onhit_effect(self, champion):
        champion.set_mana(champion.current_mana + self.mana_restore_amount)

class StatikkShiv(Item): # TODO: hits multiple enemies
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.RECURVE_BOW, ItemComponent.TEAR_OF_THE_GODDESS]

class BlueBuff(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.TEAR_OF_THE_GODDESS, ItemComponent.TEAR_OF_THE_GODDESS]
        # self.mana_ratio_key = var_to_hash('ManaRatio')

    def apply_after_ability_effect(self, champion):
        champion.add_mana(self.effects['ManaRestore'])

class RapidFirecannon(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)        
        self.components = [ItemComponent.RECURVE_BOW, ItemComponent.RECURVE_BOW]

class TitansResolve(Item): # TODO: finish this item
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.CHAIN_VEST, ItemComponent.RECURVE_BOW]

        self.stack_amount = self.effects[var_to_hash('StackingAD')]
        self.max_stack = self.effects[var_to_hash('StackCap')]
        self.stacks = 0

    def apply_onhit_effect(self, champion):
        if self.stacks < self.max_stack:
            champion.damage += self.stack_amount
            champion.set_ap(champion.ap + self.stack_amount)
            self.stacks += 1

class Deathblade(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.BF_SWORD, ItemComponent.BF_SWORD]

    def apply_equip_effect(self, champion):
        champion.add_ad(self.effects[var_to_hash(f'@Tooltip{champion.level}StarBonusAD@')])

class LastWhisper(Item): # TODO: need to implement defenders for this to be viable
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.RECURVE_BOW, ItemComponent.SPARRING_GLOVES]
        self.effect_start = None
        self.effect_end = None

    def apply_onhit_effect(self, attacking_champion, defending_champion):
        if attacking_champion.did_crit:
            self.effect_start = attacking_champion.state
            print(f'lw effect triggered state: {attacking_champion.state}')
            defending_champion.current_armor *= 0.3
            self.effect_end = self.effect_start + 500
        if attacking_champion.state == self.effect_end:
            print(f'lw effect ended state: {attacking_champion.state}')
            self.effect_start = None
            self.effect_end = None
            defending_champion.current_armor /= 0.3 # return armor back to normal

        return {'ad': 0, 'ap': 0, 'true': 0}

class GiantSlayer(Item): # TODO: need to implement defenders for this to be viable
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.BF_SWORD, ItemComponent.RECURVE_BOW]

class ZekesHerald(Item): # TODO: need to implement defenders for this to be viable
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.BF_SWORD, ItemComponent.GIANTS_BELT]

class Bloodthirster(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.BF_SWORD, ItemComponent.NEGATRON_CLOAK]  

class RunaansHurricane(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)
        self.components = [ItemComponent.RECURVE_BOW, ItemComponent.NEGATRON_CLOAK]


class HandOfJustice(Item): # TODO: need to simulate multiple times for this to be accurate.
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.SPARRING_GLOVES, ItemComponent.TEAR_OF_THE_GODDESS]


    def apply_equip_effect(self, champion):
        if np.random.uniform() < 0.5:
            champion.damage += self.effects[var_to_hash('BaseAD')]
            champion.set_ap(champion.ap + self.effects[var_to_hash('BaseSP')])
        else:
            champion.damage += self.effects[var_to_hash('TooltipBonus')]
            champion.set_ap(champion.ap + self.effects[var_to_hash('TooltipBonus')])

        
class ChaliceOfPower(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.NEGATRON_CLOAK, ItemComponent.TEAR_OF_THE_GODDESS]

class GuardianAngel(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.CHAIN_VEST, ItemComponent.BF_SWORD]


# defensive items 

class BrambleVest(Item): # TODO: implement crit canceling
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.CHAIN_VEST, ItemComponent.CHAIN_VEST]

class SunfireCape(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.CHAIN_VEST, ItemComponent.GIANTS_BELT]

class Zephyr(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.NEGATRON_CLOAK, ItemComponent.GIANTS_BELT]

class WarmogsArmor(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.GIANTS_BELT, ItemComponent.GIANTS_BELT]

class DragonsClaw(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.NEGATRON_CLOAK, ItemComponent.NEGATRON_CLOAK]

class LocketOfTheIronSolari(Item):
    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)  
        self.components = [ItemComponent.CHAIN_VEST, ItemComponent.NEEDLESSLY_LARGE_ROD]

    def apply_equip_effect(self, champion):
        hp_key = var_to_hash(f'{champion.level}StarShieldValue')
        champion.add_health(self.effects[hp_key])
        
if __name__ == "__main__":
    rabs = RabadonsDeathcap()