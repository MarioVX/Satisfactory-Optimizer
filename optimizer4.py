# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 13:45:23 2022

@author: Mario
"""

import symbsimp
from sympy import Rational

Milestones : dict[str,'Milestone'] = {}

class Milestone:
    def __init__(self, name: str, prerequisite: str, cost: dict[str,int]):
        global Milestones
        if prerequisite is not None and prerequisite not in Milestones:
            raise KeyError("Unrecognized prerequisite: " + prerequisite)
        self.name = name
        if prerequisite is None:
            self.prerequisite = None
        else:
            self.prerequisite : Milestone = Milestones[prerequisite]
        self.cost = cost
        Milestones[name] = self
        return None
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        return (isinstance(other, Milestone) and self.name == other.name) or (isinstance(other, str) and self.name == other)
    
    def __hash__(self):
        return hash(self.name)

# --- Tier 1 ---
Milestone("Base Building", None, {"Concrete":200, "Iron Plate":100, "Iron Rod":100})
Milestone("Logistics", None, {"Iron Plate":150, "Iron Rod":150})
Milestone("Field Research", None, {"Wire":300, "Screw":300, "Iron Plate":100})
# --- Tier 2 ---
Milestone("Part Assembly", None, {"Cable":200, "Iron Rod":200, "Screw":500, "Iron Plate":300})
Milestone("Obstacle Clearing", None, {"Screw":500, "Cable":100, "Concrete":100})
Milestone("Jump Pads", None, {"Rotor":50, "Iron Plate":300, "Cable":150})
Milestone("Resource Sink Bonus Program", None, {"Concrete":400, "Wire":500, "Iron Rod":200, "Iron Plate":200})
Milestone("Logistics Mk.2", None, {"Reinforced Iron Plate":50, "Concrete":200, "Iron Rod":300, "Iron Plate":300})
# --- Project Assembly 1 ---
Milestone("Platform", "Part Assembly", {"Smart Plating":50})
# --- Tier 3 ---
Milestone("Coal Power", "Platform", {"Reinforced Iron Plate":150, "Rotor":50, "Cable":300})
Milestone("Vehicular Transport", "Platform", {"Modular Frame":25, "Rotor":100, "Cable":200, "Iron Rod":400})
Milestone("Basic Steel Production", "Platform", {"Modular Frame":50, "Rotor":150, "Concrete":300, "Wire":1000})
# --- Tier 4 ---
Milestone("Advanced Steel Production", "Platform", {"Steel Pipe":200, "Rotor":200, "Wire":1500, "Concrete":300})
Milestone("Improved Melee Combat", "Platform", {"Rotor":25, "Reinforced Iron Plate":50, "Wire":1500, "Cable":200})
Milestone("Hyper Tubes", "Platform", {"Copper Sheet":300, "Steel Pipe":300, "Encased Industrial Beam":50})
Milestone("Logistics Mk.3", "Platform", {"Steel Beam":200, "Steel Pipe":100, "Concrete":500})
# --- Project Assembly 2 ---


Buildings : dict[str, 'Building'] = {}

class Building:
    def __init__(self, name: str, power_base: int, requirement: str, clock=Rational(1,1), exponent=Rational(8,5)):
        self.name = name
        self._base = power_base
        self._exponent = exponent
        self.clock = clock
        if requirement is None:
            self.requirement = None
        else:
            self.requirement : Milestone = Milestones[requirement]
        global Buildings
        Buildings[name] = self
        return None
    
    def power(self):
        return self._base * self.clock**self._exponent
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        return (isinstance(other, Building) and self.name == other.name) or (isinstance(other, str) and self.name == other)
    
    def __hash__(self):
        return hash(self.name)

Building("Constructor", 4, None)
Building("Smelter", 4, None)
Building("Assembler", 15, "Part Assembly")


Items : list[str] = []
Fluids = ("Water", "Crude Oil", "Heavy Oil Residue", "Fuel", "Turbofuel", "Liquid Biofuel", "Alumina Solution", "Sulfuric Acid", "Nitrogen Gas", "Nitric Acid")
Recipes : dict[str, 'Recipe'] = {}

class Recipe:
    def __init__(self, name: str, alt: bool, inputs: dict[str, int], building: str, duration: int, outputs: dict[str, int], requirements: list[str]):
        global Recipes, Items
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        for i in inputs.keys() | outputs.keys():
            if i not in Items:
                Items.append(i)
        if building not in Buildings:
            raise KeyError("unrecognized building")
        self.building = Buildings[building]
        self.duration = duration
        self.requirements : list[Milestone] = list(Milestones[x] for x in requirements)
        self.alt = alt
        Recipes[name] = self
        return None

# --- T0 standard ---
Recipe("r_IronIngot", False, {"Iron Ore":1}, "Smelter", 2, {"Iron Ingot":1}, [])
Recipe("r_IronRod", False, {"Iron Ingot":1}, "Constructor", 4, {"Iron Rod":1}, [])
Recipe("r_IronPlate", False, {"Iron Ingot":3}, "Constructor", 6, {"Iron Plate":2},[])
Recipe("r_CopperIngot", False, {"Copper Ore":1}, "Smelter", 2, {"Copper Ingot":2}, [])
Recipe("r_Wire", False, {"Copper Ingot":1}, "Constructor", 4, {"Wire":2}, [])
Recipe("r_Cable", False, {"Wire":2}, "Constructor", 2, {"Cable":1}, [])
Recipe("r_Screw", False, {"Iron Rod":1}, "Constructor", 6, {"Screw":4}, [])
Recipe("r_ReinforcedIronPlate", False, {"Iron Plate":6, "Screw":12}, "Assembler", 12, {"Reinforced Iron Plate":1}, [])
# --- T0 alt ---
Recipe("a_IronWire", True, {"Iron Ingot":5}, "Constructor", 24, {"Wire":9}, [])
Recipe("a_CastScrew", True, {"Iron Ingot":5}, "Constructor", 24, {"Screw":20}, [])
Recipe("a_BoltedIronPlate", True, {"Iron Plate":18, "Screw":50}, "Assembler", 12, {"Reinforced Iron Plate":3}, [])
Recipe("a_StitchedIronPlate", True, {"Iron Plate":10, "Wire":20}, "Assembler", 32, {"Reinforced Iron Plate":3}, [])
# --- T2 standard ---
Recipe("r_CopperSheet", False, {"Copper Ingot":2}, "Constructor", 6, {"Copper Sheet":1}, ["Part Assembly",])
Recipe("r_Rotor", False, {"Iron Rod":5, "Screw":25}, "Assembler", 15, {"Rotor":1}, ["Part Assembly",])
Recipe("r_ModularFrame", False, {"Reinforced Iron Plate":3, "Iron Rod":12}, "Assembler", 60, {"Modular Frame":2}, ["Part Assembly",])
Recipe("r_SmartPlating", False, {"Reinforced Iron Plate":1, "Rotor":1}, "Assembler", 30, {"Smart Plating":1}, ["Part Assembly",])
# --- T2 alt ---
Recipe("a_CopperRotor", True, {"Copper Sheet":6, "Screw":52}, "Assembler", 16, {"Rotor":3}, ["Part Assembly",])
Recipe("a_BoltedFrame", True, {"Reinforced Iron Plate":3, "Screw":56}, "Assembler", 24, {"Modular Frame":2}, ["Part Assembly",])

class ProgressState:
    def __init__(self, predecessor: 'ProgressState'):
        if predecessor is None:
            self.unlocked_milestones : list[str] = []
            self.next_milestones : list[str] = []
            self.nodes = dict[str,dict[str,int]] = {}
            self.wells = dict[str,dict[tuple[int],int]] = {}
        else:
            self.unlocked_milestones = predecessor.unlocked_milestones.copy()
            self.next_milestones = predecessor.next_milestones.copy()
            self.nodes = dict((res, predecessor.nodes[res].copy()) for res in predecessor.nodes)
            self.wells = dict((res, predecessor.wells[res].copy()) for res in predecessor.wells)