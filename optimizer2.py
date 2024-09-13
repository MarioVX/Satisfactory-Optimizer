# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 12:05:04 2021

@author: Mario
"""
import numpy as np
from scipy.optimize import linprog

# ----- general settings -----
MinerMK = 3  # 1 to 3
BeltMK = 5  # 1 to 5
PipeMK = 2  # 1 or 2
GeysersOccupied = (3, 9, 6)  # impure, normal, pure
FreeExtraPower = 0.0  # not including Geysers
PumpsPerPipe = 0.0  # 1 per mk1 + 2 per mk2

MinerBasePower = {1: 5, 2: 12, 3: 30}
MinerBaseSpeed = np.array([[30, 60, 120], [60, 120, 240], [120, 240, 480]])
BeltCapacity = {1: 60, 2: 120, 3: 270, 4: 480, 5: 780}
PipeCapacity = {1: 300, 2: 600}
FreePower = sum(GeysersOccupied[i] * 100.0 * 2
                ** i for i in range(3)) + FreeExtraPower

RecipesByName = dict()
Recipes = list()
Items = ["Water", ]
Buildings = dict()
LimResources = set()


class Building:
    def __init__(self, Name: str, PowerBase: float, Clock=1.0, PowerExponent=1.6):
        self.name = Name
        self._base = PowerBase
        self._exponent = PowerExponent
        self.clock = Clock

    def power(self) -> float:
        return self._base * self.clock**self._exponent

    def ratemult(self) -> float:
        return self.clock


def regB(name: str, powerbase: float):
    global Buildings
    Buildings[name] = Building(name, powerbase)
    return None

regB("Water Extractor", 20.0)
regB("Constructor", 4.0)
regB("Assembler", 15.0)
regB("Manufacturer", 55.0)
regB("Packager", 10.0)
regB("Refinery", 30.0)
regB("Blender", 75.0)
regB("Particle Accelerator IPC", 375.0)
regB("Particle Accelerator NP", 1000.0)
regB("Particle Accelerator PP", 500.0)
regB("Smelter", 4.0)
regB("Foundry", 16.0)
regB("AWESOME Sink", 30.0)


class PowerBuilding(Building):
    def __init__(self, Name: str, PowerBase: float, Clock=1.0, PowerExponent=1 / 1.3):
        super().__init__(Name, PowerBase, Clock=Clock, PowerExponent=PowerExponent)

    def ratemult(self) -> float:
        return self.clock**self._exponent


def regPB(name: str, powerbase: float, exp=1 / 1.3):
    global Buildings
    Buildings[name] = PowerBuilding(name, powerbase, PowerExponent=exp)


regPB("Coal Generator", -75.0)
regPB("Fuel Generator", -150.0)
regPB("Nuclear Power Plant", -2500.0, exp=0.7564707973660301)

# ----- building clock speed settings -----
Buildings["Water Extractor"].clock = 1.0
Buildings["Constructor"].clock = 1.0
Buildings["Assembler"].clock = 1.0
Buildings["Manufacturer"].clock = 1.0
Buildings["Packager"].clock = 1.0
Buildings["Refinery"].clock = 1.0
Buildings["Blender"].clock = 1.0
Buildings["Particle Accelerator IPC"].clock = 1.0
Buildings["Particle Accelerator NP"].clock = 1.0
Buildings["Particle Accelerator PP"].clock = 1.0
Buildings["Smelter"].clock = 1.0
Buildings["Foundry"].clock = 1.0
Buildings["Coal Generator"].clock = 1.0
Buildings["Fuel Generator"].clock = 1.0
Buildings["Nuclear Power Plant"].clock = 1.0

Nodes = dict()


def regN(resource: str, nodes: tuple):
    if nodes == (0, 0, 0):
        return None
    global Items, Nodes, LimResources
    if resource not in Items:
        Items.append(resource)
    if resource not in LimResources:
        LimResources.add(resource)
    Nodes[resource] = nodes
    return None


# ----- Resource Nodes -----
regN("Limestone", (12, 47, 27))
regN("Iron Ore", (33, 41, 46))
regN("Copper Ore", (9, 28, 12))
regN("Caterium Ore", (0, 8, 8))
regN("Coal", (6, 29, 15))
regN("Crude Oil", (10, 12, 8))
regN("Sulfur", (1, 7, 3))
regN("Bauxite", (5, 6, 6))
regN("Raw Quartz", (0, 11, 5))
regN("Uranium", (1, 3, 0))
#regN("S.A.M. Ore", (8,5,0))

Wells = dict()


def regW(resource: str, nodes: tuple):
    if nodes == (0, 0, 0):
        return None
    global Items, Wells, LimResources
    if resource not in Items:
        Items.append(resource)
    if (resource not in LimResources) and (resource != "Water"):
        LimResources.add(resource)
    if resource not in Wells:
        Wells[resource] = list()
    Wells[resource].append(nodes)
    return None


# ----- Resource Wells -----
#regW("Crude Oil", (0, 3, 3))  # Red Bamboo Fields
#regW("Crude Oil", (6, 0, 0))  # Swamp
#regW("Nitrogen Gas", (0, 2, 5))  # Red Oasis
#regW("Nitrogen Gas", (0, 1, 6))  # Rocky Desert
#regW("Nitrogen Gas", (0, 0, 7))  # Jungle Spires
#regW("Nitrogen Gas", (0, 0, 10))  # Eastern Dune Forest
#regW("Nitrogen Gas", (0, 2, 4))  # Blue Crater
#regW("Nitrogen Gas", (2, 2, 4))  # Abyss Cliffs
# regW("Water", (2,1,4)) # Dune Desert (north)
# regW("Water", (0,0,6)) # Dune Desert (south)
# regW("Water", (1,2,4)) # Desert Canyons
# regW("Water", (0,0,6)) # Eastern Dune Forest (north)
# regW("Water", (2,6,0)) # Eastern Dune Forst (south)
# regW("Water", (2,0,5)) # Grass Fields
# regW("Water", (0,1,6)) # Snaketree Forest
# regW("Water", (0,0,7)) # Red Jungle

# ----- Recipes -----


class Recipe:
    def __init__(self, name: str, inputs: dict, outputs: dict, building: str):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.building = Buildings[building]
    
    def power(self) -> float:
        return self.building.power()
    
    def rate(self, item: str) -> float:
        v = 0.0
        if item in self.inputs:
            v += self.inputs[item] * self.building.ratemult()
        if item in self.outputs:
            v -= self.outputs[item] * self.building.ratemult()
        return v


def MinerSpeed(purity: str, clock: float) -> float:
    if purity == 'impure':
        i = 0
    elif purity == 'normal':
        i = 1
    elif purity == 'pure':
        i = 2
    else:
        raise ValueError("Invalid purity")
    if not (clock >= 0.0 and clock <= 2.5):
        raise ValueError("Invalid clock speed")
    return MinerBaseSpeed[MinerMK - 1][i] * clock


def limitExtract(resource: str) -> float:
    if resource not in LimResources:
        raise ValueError("Requesting limit of a resource that isn't registered as limited.")
    total = 0.0
    if resource in Nodes:
        if resource == "Crude Oil":
            total += sum(Nodes["Crude Oil"][i] * min(PipeCapacity[PipeMK], 60*2.5*2**i) for i in range(3))
        else:
            total += sum(Nodes[resource][i] * min(BeltCapacity[BeltMK], 2.5 * MinerBaseSpeed[MinerMK - 1, i]) for i in range(3))
    if resource in Wells:
        for w in Wells[resource]:
            total += sum(w[i] * min(PipeCapacity[PipeMK], 30*2.5*2**i) for i in range(3))
    return total


def extractOre(resource: str, quota: float) -> list:
    if resource not in Nodes:
        raise ValueError("No registered nodes of this resource")
    if quota > limitExtract(resource):
        raise ValueError("Demanded quota too high")
    nodes = Nodes[resource]
    purity = ('impure', 'normal', 'pure')
    clock_limits = tuple(
        min(2.5, BeltCapacity[BeltMK] / MinerSpeed(x, 1.0)) for x in purity)
    stdquota = quota / MinerSpeed('impure', 1.0)
    z = stdquota / (nodes[0] + nodes[1] * 2**(8 / 3) + nodes[2] * 4**(8 / 3))
    if z * 4**(5 / 3) <= clock_limits[2]:
        clocks = tuple(z * 2**(5 / 3 * i) for i in range(3))
    else:
        z = (stdquota - 4 * clock_limits[2] * nodes[2]
             ) / (nodes[0] + nodes[1] * 2**(8 / 3))
        if z * 2**(5 / 3) <= clock_limits[1]:
            clocks = (z, z * 2**(5 / 3), clock_limits[2])
        else:
            z = (stdquota - 4 * clock_limits[2] * nodes[2] -
                 2 * clock_limits[1] * nodes[1]) / (nodes[0])
            clocks = (z, clock_limits[1], clock_limits[2])
    for i in range(3):
        if nodes[i] == 0:
            clocks = list(clocks)
            clocks[i] = 0.0
            clocks = tuple(clocks)
    assert abs(sum(nodes[i] * clocks[i] * 2
               ** i for i in range(3)) - stdquota) < 10**(-7)
    power = sum(nodes[i] * MinerBasePower[MinerMK] * clocks[i]**1.6 for i in range(3))
    return [clocks, power]


def extractWater(resource, quota: float) -> list:
    m_final = Buildings["Water Extractor"].power() / (120 * Buildings["Water Extractor"].clock) + 4.0 * PumpsPerPipe / PipeCapacity[PipeMK]
    # TODO: resource wells for Water are not yet considered here.
    return [list(), m_final * quota]


def extractNitrogen(resource, quota: float) -> list:
    # TODO
    pass


def extractOil(resource, quota: float) -> list:
    # TODO
    pass


def derivative(func, resource, quota, quota_max, eps=0.5):
    if quota_max is not None:
        if quota == quota_max:
            return (func(resource, quota)[1] - func(resource, quota - eps)[1]) / eps
        if quota == 0:
            return func(resource, eps)[1] / eps
        e = min(abs(quota - quota_max), eps, quota)
        return (func(resource, quota+e)[1] - func(resource, quota-e)[1]) / (2*e)
    else:
        if quota == 0:
            return func(resource, eps)[1] / eps
        e = min(eps, quota)
        return (func(resource, quota+e)[1] - func(resource, quota-e)[1]) / (2*e)


class ExtractRecipe(Recipe):
    def __init__(self, resource: str, extractfunc):
        self.name = "extract_"+("".join(resource.split()))
        self.resource = resource
        self.inputs = dict()
        self.outputs = {resource:1.0,}
        self._extractfunc = extractfunc
    
    def limit(self) -> float:
        return limitExtract(self.resource)
    
    def power(self, guessedquota: float) -> float:
        if self.resource == "Water":
            if guessedquota < -10**(-6):
                raise ValueError("negative guessed quota")
            return max(0.01,derivative(self._extractfunc, "Water", max(guessedquota,10**(-6)), None))
        else:
            if guessedquota > self.limit()+10**(-6) or guessedquota < -10**(-6):
                raise ValueError("invalid guessed quota")
            return max(0.01,derivative(self._extractfunc, self.resource, max(10**(-6), min(guessedquota, self.limit())), self.limit()))
    
    def offset(self, guessedquota: float) -> float:
        if self.resource == "Water":
            if guessedquota < -10**(-6):
                raise ValueError("negative guessed Water quota: "+str(guessedquota))
            return self._extractfunc("Water", max(10**(-6),guessedquota))[1] - max(10**(-6),guessedquota) * self.power(guessedquota)
        if guessedquota > self.limit()+10**(-6) or guessedquota < -10**(-6):
            raise ValueError("invalid guessed quota for "+self.resource+": "+str(guessedquota))
        return self._extractfunc(self.resource, max(10**(-6), min(guessedquota, self.limit())))[1] - max(10**(-6), min(guessedquota, self.limit())) * self.power(guessedquota)
    
    def rate(self, item: str) -> float:
        if item == self.resource:
            return -1.0
        else:
            return 0.0

def regER(resource: str, extractfunc=extractOre):
    if resource not in Nodes.keys() | Wells.keys() | {"Water",}:
        raise ValueError("resource not registered as obtainable")     
    r = ExtractRecipe(resource, extractfunc)
    global Recipes, RecipesByName
    RecipesByName[r.name] = r
    Recipes.append(r)
    return None

# ----- extraction recipes -----
regER("Water", extractfunc=extractWater)
#regER("Nitrogen Gas", extractfunc=extractNitrogen)
#regER("Crude Oil", extractfunc=extractOil)
for res in (LimResources - {"Nitrogen Gas", "Crude Oil"}):
    regER(res)

def regR(name: str, inputs: dict, outputs: dict, building: str):
    r = Recipe(name, inputs, outputs, building)
    global RecipesByName, Recipes, Items
    for x in inputs.keys() | outputs.keys():
        if x not in Items:
            Items.append(x)
    if r.name in RecipesByName:
        raise ValueError("duplicate recipe name")
    RecipesByName[r.name] = r
    Recipes.append(r)
    return None

# ----- power recipes -----
regR("power_Coal", {"Coal":60/4.0, "Water":45}, dict(), "Coal Generator")
regR("power_CompactedCoal", {"Compacted Coal":60/8.4, "Water":45}, dict(), "Coal Generator")
regR("power_PetroleumCoke", {"Petroleum Coke":60/2.4, "Water":45}, dict(), "Coal Generator")
regR("power_Fuel", {"Fuel":60/5.0}, dict(), "Fuel Generator")
regR("power_LiquidBiofuel", {"Liquid Biofuel":60/5.0}, dict(), "Fuel Generator")
regR("power_Turbofuel", {"Turbofuel":4.5}, dict(), "Fuel Generator")
regR("power_UraniumFuelRod", {"Uranium Fuel Rod":0.2, "Water":300},{"Uranium Waste":10}, "Nuclear Power Plant")
regR("power_PlutoniumFuelRod", {"Plutonium Fuel Rod":0.1, "Water":300},{"Plutonium Waste":1}, "Nuclear Power Plant")


# ----- processing recipes -----
regR("r_IronIngot", {"Iron Ore":30}, {"Iron Ingot":30}, "Smelter")


# ----- alternate recipes -----
# ---- T1 ----
regR("a_IronWire", {"Iron Ingot":12.5},{"Wire":22.5},"Constructor")
regR("a_CastScrew", {"Iron Ingot":12.5},{"Screw":50.0},"Constructor")
# -- + MAM --
regR("a_CateriumWire", {"Caterium Ingot":15.0},{"Wire":120.0},"Constructor")

# ---- T2 ----
regR("a_BoltedIronPlate",{"Iron Plate":90, "Screw":250},{"Reinforced Iron Plate":15},"Assembler")
regR("a_StitchedIronPlate",{"Iron Plate":18.75, "Wire":37.5},{"Reinforced Iron Plate":5.625}, "Assembler")
regR("a_BoltedFrame", {"Reinforced Iron Plate":7.5, "Screw":140}, {"Modular Frame":5}, "Assembler")
regR("a_CopperRotor", {"Copper Sheet":22.5, "Screw":195}, {"Rotor":11.25}, "Assembler")
# -- + MAM --
regR("a_FusedWire", {"Copper Ingot":12, "Caterium Ingot":3}, {"Wire":90}, "Assembler")
regR("a_FusedQuickwire", {"Copper Ingot":37.5, "Caterium Ingot":7.5}, {"Quickwire":90}, "Assembler")
regR("a_CheapSilica", {"Raw Quartz":11.25, "Limestone":18.75}, {"Silica":26.25}, "Assembler")
regR("a_FineConcrete", {"Silica":7.5, "Limestone":30}, {"Concrete":25}, "Assembler")

# ---- T3 Coal Power ----
regR("a_Biocoal", {"Biomass":37.5}, {"Coal":45}, "Assembler")
regR("a_Charcoal", {"Wood":15}, {"Coal":150}, "Assembler")
# -- + MAM --
regR("a_CompactedCoal", {"Coal":25, "Sulfur":25}, {"Compacted Coal":25}, "Assembler")
regR("a_FineBlackPowder", {"Sulfur":7.5, "Compacted Coal":3.75}, {"Black Powder":15}, "Assembler")

# ---- T3 Basic Steel Production ----
regR("a_IronAlloyIngot", {"Iron Ore":20, "Copper Ore":20}, {"Iron Ingot":50}, "Foundry")
regR("a_CopperAlloyIngot", {"Copper Ore":50, "Iron Ore":25}, {"Copper Ingot":100}, "Foundry")
regR("a_SolidSteelIngot", {"Iron Ingot":40, "Coal":40}, {"Steel Ingot":60}, "Foundry")
regR("a_SteelRod", {"Steel Ingot":12}, {"Iron Rod":48}, "Constructor")
regR("a_SteelScrew", {"Steel Beam":5},{"Screw":260}, "Constructor")
regR("a_SteeledFrame", {"Reinforced Iron Plate":2, "Steel Pipe":10}, {"Modular Frame":3}, "Assembler")
regR("a_SteelRotor", {"Steel Pipe":10, "Wire":30}, {"Rotor":5}, "Assembler")
# -- + MAM --
regR("a_CompactedSteelIngot", {"Iron Ore":22.5, "Compacted Coal":11.25}, {"Steel Ingot":37.5}, "Foundry")

# ---- T4 Advanced Steel Production ----
regR("a_EncasedIndustrialPipe", {"Steel Pipe":28, "Concrete":20}, {"Encased Industrial Beam":4}, "Assembler")
# -- + MAM --
regR("a_QuickwireStator", {"Steel Pipe":16, "Quickwire":60}, {"Stator":8}, "Assembler")

# ---- T5 Oil Processing ----
regR("a_PureCopperIngot", {"Copper Ore":15, "Water":10}, {"Copper Ingot":37.5}, "Refinery")
regR("a_SteamedCopperSheet", {"Copper Ingot":22.5, "Water":22.5}, {"Copper Sheet":22.5}, "Refinery")
regR("a_WetConcrete", {"Limestone":120, "Water":100},{"Concrete":80}, "Refinery")
regR("a_PureIronIngot", {"Iron Ore":35, "Water":20}, {"Iron Ingot":65}, "Refinery")
regR("a_CoatedCable", {"Wire":37.5, "Heavy Oil Residue":15}, {"Cable":67.5}, "Refinery")
regR("a_InsulatedCable", {"Wire":45, "Rubber":30}, {"Cable":100}, "Assembler")
regR("a_ElectrodeCircuitBoard", {"Rubber":30, "Petroleum Coke":45}, {"Circuit Board":5}, "Assembler")
regR("a_RubberConcrete", {"Limestone":50, "Rubber":10}, {"Concrete":45}, "Assembler")
regR("a_HeavyOilResidue", {"Crude Oil":30}, {"Heavy Oil Residue":40, "Polymer Resin":20}, "Refinery")
regR("a_CoatedIronPlate", {"Iron Ingot":50, "Plastic":10}, {"Iron Plate":75}, "Assembler")
regR("a_SteelCoatedPlate", {"Steel Ingot":7.5, "Plastic":5}, {"Iron Plate":45}, "Assembler")
regR("a_RecycledPlastic", {"Rubber":30, "Fuel":30}, {"Plastic":60}, "Refinery")
regR("a_PolymerResin", {"Crude Oil":60}, {"Polymer Resin":130, "Heavy Oil Residue":20}, "Refinery")
regR("a_AdheredIronPlate", {"Iron Plate":11.25, "Rubber":3.75}, {"Reinforced Iron Plate":3.75}, "Assembler")
regR("a_RecycledRubber", {"Plastic":30, "Fuel":30}, {"Rubber":60}, "Refinery")
regR("a_CokeSteelIngot", {"Iron Ore":75, "Petroleum Coke":75}, {"Steel Ingot":100}, "Foundry")
# -- + MAM --
regR("a_PureCateriumIngot", {"Caterium Ore":24, "Water":24}, {"Caterium Ingot":12}, "Refinery")
regR("a_PureQuartzCrystal", {"Raw Quartz":67.5, "Water":37.5}, {"Quartz Crystal":52.5}, "Refinery")
regR("a_QuickwireCable", {"Quickwire":7.5, "Rubber":5}, {"Cable":27.5}, "Assembler")
regR("a_CateriumCircuitBoard", {"Plastic":12.5, "Quickwire":37.5}, {"Circuit Board":8.75}, "Assembler")
regR("a_PolyesterFabric", {"Polymer Resin":80, "Water":50}, {"Fabric":5}, "Refinery")
regR("a_SiliconCircuitBoard", {"Copper Sheet":27.5, "Silica":27.5}, {"Circuit Board":12.5}, "Assembler")
regR("a_Turbofuel", {"Fuel":22.5, "Compacted Coal":15}, {"Turbofuel":18.75}, "Refinery")
regR("a_TurboHeavyFuel", {"Heavy Oil Residue":37.5, "Compacted Coal":30}, {"Turbofuel":30}, "Refinery")

# ---- T5 Alternative Fluid Transport ----
regR("a_DilutedPackagedFuel", {"Heavy Oil Residue":30, "Packaged Water":60}, {"Packaged Fuel":60}, "Refinery")
regR("a_CoatedIronCanister", {"Iron Plate":30, "Copper Sheet":15}, {"Empty Canister":60}, "Assembler")
regR("a_SteelCanister", {"Steel Ingot":60}, {"Empty Canister":40}, "Constructor")

# ---- T5 Industrial Manufacturing ----
regR("a_PlasticSmartPlating", {"Reinforced Iron Plate":2.5, "Rotor":2.5, "Plastic":7.5}, {"Smart Plating":5}, "Manufacturer")
regR("a_FlexibleFramework", {"Modular Frame":3.75, "Steel Beam":22.5, "Rubber":30}, {"Versatile Framework":7.5}, "Manufacturer")
regR("a_HeavyEncasedFrame", {"Modular Frame":7.5, "Encased Industrial Beam":9.375, "Steel Pipe":33.75, "Concrete":20.625}, {"Heavy Modular Frame":2.8125}, "Manufacturer")
regR("a_HeavyFlexibleFrame", {"Modular Frame":18.75, "Encased Industrial Beam":11.25, "Rubber":75, "Screw":390}, {"Heavy Modular Frame":3.75}, "Manufacturer")
regR("a_AutomatedMiner", {"Motor":1, "Steel Pipe":4, "Iron Rod":4, "Iron Plate":2}, {"Portable Miner":1}, "Manufacturer")
# -- + MAM --
regR("a_CrystalBeacon", {"Steel Beam":2, "Steel Pipe":8, "Crystal Oscillator":0.5}, {"Beacon":10}, "Manufacturer")
regR("a_SiliconHigh-SpeedConnector", {"Quickwire":90, "Silica":37.5, "Circuit Board":3}, {"High-Speed Connector":3}, "Manufacturer")
regR("a_InsulatedCrystalOscillator", {"Quartz Crystal":18.75, "Rubber":13.125, "AI Limiter":1.875}, {"Crystal Oscillator":1.875}, "Manufacturer")
regR("a_SeismicNobelisk", {"Black Powder":12, "Steel Pipe":12, "Crystal Oscillator":1.5},  {"Nobelisk":6}, "Manufacturer")
regR("a_High-SpeedWiring", {"Stator":3.75, "Wire":75, "High-Speed Connector":1.875}, {"Automated Wiring":7.5}, "Manufacturer")
regR("a_RigourMotor", {"Rotor":3.75, "Stator":3.75, "Crystal Oscillator":1.25}, {"Motor":7.5}, "Manufacturer")
regR("a_CateriumComputer", {"Circuit Board":26.25, "Quickwire":105, "Rubber":45}, {"Computer":3.75}, "Manufacturer")
regR("a_CrystalComputer", {"Circuit Board":7.5, "Crystal Oscillator":2.8125}, {"Computer":2.8125}, "Manufacturer")

# ---- T7 Bauxite Refinement ----

# ---- T7 Aeronautical Engineering ----

# ---- T8 Advanced Aluminum ----

# ---- T8 Nuclear Power ----

# ---- T8 Leading-edge ----

# ---- T8 Particle Enrichment ----

class MilestoneRecipe(Recipe):
    def __init__(self, name: str, requirements: dict):
        self.name = name
        self.inputs = requirements
        self.outputs = dict()
    
    def power(self):
        return 0.0
    
    def rate(self, item: str) -> float:
        if item in self.inputs:
            return self.inputs[item]
        return 0.0


def regMR(name: str, requirements: dict):
    r = MilestoneRecipe(name, requirements)
    global RecipesByName, Recipes, Items
    for x in r.inputs.keys():
        if x not in Items:
            Items.append(x)
    if r.name in RecipesByName:
        raise ValueError("duplicate recipe name")
    RecipesByName[r.name] = r
    Recipes.append(r)
    return None

# ----- Milestone recipes -----
#regMR("ProjectAssembly1", {"Smart Plating":50})
#regMR("ProjectAssembly2", {"Smart Plating":500, "Versatile Framework":500, "Automated Wiring":100})
#regMR("ProjectAssembly3", {"Versatile Framework":2500, "Modular Engine":500, "Adaptive Control Unit":100})
#regMR("ProjectAssembly4", {"Assembly Director System":4000, "Magnetic Field Generator":4000, "Thermal Propulsion Rocket":1000, "Nuclear Pasta":1000})
#regMR("M01", {"Iron Rod":10})
#regMR("M02", {"Iron Rod":20, "Iron Plate":10})


class SinkRecipe(Recipe):
    def __init__(self, item: str, points: int):
        self.name = "sink_"+("".join(item.split()))
        self.inputs = {item:1,}
        self.outputs = {"AWESOME points":points}
    
    def power(self):
        return 30.0
    
    def rate(self, item: str) -> float:
        if item in self.inputs:
            return BeltCapacity[BeltMK]
        if item == "AWESOME points":
            return -self.outputs["AWESOME points"] * BeltCapacity[BeltMK]

def regS(item: str, points: int):
    r = SinkRecipe(item, points)
    global RecipesByName, Recipes, Items
    for x in r.inputs.keys():
        if x not in Items:
            Items.append(x)
    if r.name in RecipesByName:
        raise ValueError("duplicate recipe name")
    RecipesByName[r.name] = r
    Recipes.append(r)
    return None

# ----- Sink items -----
regS("Iron Ore",1)
regS("Limestone",2)
regS("Iron Ingot",2)
regS("Screw",2)
regS("Coal",3)
regS("Leaves",3)
regS("Copper Ore",3)
regS("Iron Rod",4)
regS("Iron Plate",6)
regS("Copper Ingot",6)
regS("Wire",6)
regS("Caterium Ore",7)
regS("Steel Ingot",8)
regS("Bauxite",8)
regS("Spiked Rebar",8)
regS("Color Cartridge",10)
regS("Flower Petals",10)
regS("Mycelia",10)
regS("Sulfur",11)
regS("Polymer Resin",12)
regS("Biomass",12)
regS("Concrete",12)
regS("Raw Quartz",15)
regS("Quickwire",17)
regS("Petroleum Coke",20)
regS("Silica",20)
regS("Steel Pipe",24)
regS("Cable",24)
regS("Copper Sheet",24)
regS("Aluminum Scrap",27)
regS("Compacted Coal",28)
regS("Wood",30)
regS("Uranium",35)
regS("Caterium Ingot",42)
regS("Solid Biofuel",48)
regS("Black Powder",50)
regS("Quartz Crystal",50)
regS("Empty Canister",60)
regS("Portable Miner",60)
regS("Rubber",60)
regS("Steel Beam",64)
regS("Medicinal Inhaler",67)
regS("Copper Powder",72)
regS("Plastic",75)
regS("Reinforced Iron Plate",120)
regS("Packaged Water",130)
regS("Aluminum Ingot",131)
regS("Fabric",140)
regS("Rotor",140)
regS("Encased Uranium Cell",147)
regS("Packaged Sulfuric Acid",152)
regS("Packaged Alumina Solution",160)
regS("Packaged Oil",180)
regS("Packaged Heavy Oil Residue",180)
regS("Empty Fluid Tank",225)
regS("Stator",240)
regS("Alclad Aluminum Sheet",266)
regS("Packaged Fuel",270)
regS("Packaged Nitrogen Gas",312)
regS("Beacon",320)
regS("Packaged Liquid Biofuel",370)
regS("Aluminum Casing",393)
regS("Modular Frame",408)
regS("Packaged Nitric Acid",412)
regS("Battery",465)
regS("Smart Plating",520)
regS("Packaged Turbofuel",570)
regS("Parachute",608)
regS("Encased Industrial Beam",632)
regS("Rifle Cartridge",664)
regS("Circuit Board",696)
regS("Gas Filter",830)
regS("Color Gun",860)
regS("AI Limiter",920)
regS("Nobelisk",980)
regS("Versatile Framework",1176)
regS("Automated Wiring",1440)
regS("Motor",1520)
regS("Factory Cart",1552)
regS("Xeno-Zapper",1880)
regS("Rebar Gun",1968)
regS("Electromagnetic Control Rod",2560)
regS("Iodine Infused Filter",2718)
regS("Chainsaw",2760)
regS("Heat Sink",2804)
regS("Crystal Oscillator",3072)
regS("Object Scanner",3080)
regS("High-Speed Connector",3776)
regS("Blade Runners",4988)
regS("Zipline",5284)
regS("Modular Engine",9960)
regS("Heavy Modular Frame",11520)
regS("Cooling System",12006)
regS("Magnetic Field Generator",15650)
regS("Computer",17260)
regS("Xeno-Basher",18800)
regS("Radio Control Unit",32908)
regS("Jetpack",35580)
regS("Nobelisk Detonator",39520)
regS("Uranium Fuel Rod",44092)
regS("Hazmat Suit",54100)
regS("Gas Mask",55000)
regS("Fused Modular Frame",62840)
regS("Adaptive Control Unit",86120)
regS("Rifle",99160)
regS("Supercomputer",99576)
regS("Plutonium Fuel Rod",153184)
regS("Turbo Motor",242720)
regS("Pressure Conversion Cube",257312)
regS("Hover Pack",413920)
regS("Nuclear Pasta",543424)
regS("Assembly Director System",543632)
regS("Thermal Propulsion Rocket",732956)

np.set_printoptions(precision=2, suppress=True)

def solve(target: str):
    c = np.zeros(len(Recipes))
    if target == "AWESOME points" or target in Items:
        for i in range(len(Recipes)):
            c[i] = Recipes[i].rate(target)
    elif target in RecipesByName:
        c[Recipes.index(target)] = 1
    else:
        raise ValueError("Target not recognized.")
    x = np.zeros(len(Recipes))
    A_ub = np.zeros((1+len(LimResources),len(Recipes)))
    b_ub = np.zeros(1+len(LimResources))
    b_ub[0] = FreePower
    A_eq = np.zeros((len(Items),len(Recipes)))
    b_eq = np.zeros(len(Items))
    j =1
    for i in range(len(Recipes)):
        r = Recipes[i]
        if type(r) == ExtractRecipe:
            if r.resource != "Water":
                x[i] = limitExtract(r.resource)
                b_ub[j] = limitExtract(r.resource)
                A_ub[j,i] = 1
                j += 1
            else:
                x[i] = 13426
            A_ub[0,i] = r.power(x[i])
            b_ub[0] += r.offset(x[i])
        else:
            A_ub[0,i] = r.power()
        for item in r.inputs.keys() | r.outputs.keys():
            if item != target and item != "AWESOME points":
                A_eq[Items.index(item),i] = r.rate(item)
    print(A_ub[0,:10])
    print(b_ub[0])
    res = linprog(c, A_ub, b_ub, A_eq, b_eq, method='highs-ds')
    print("Status:",res.status)
    assert res.status == 0
    dx = res.x
    for i in range(len(dx)):
        dx[i] = max(dx[i], 0.0)
    recompute = False
    for i in range(len(Recipes)):
        r = Recipes[i]
        if type(r) == ExtractRecipe:
            if r.resource == "Water":
                if abs(r.offset(x[i]) - r.offset(dx[i])) > 0.01:
                    recompute = True
            else:
                if abs(x[i] - dx[i]) > 0.01:
                    recompute = True
    x = dx
    while recompute:
        b_ub[0] = FreePower
        for i in range(len(Recipes)):
            r = Recipes[i]
            if type(r) == ExtractRecipe:
                A_ub[0,i] = r.power(x[i])
                b_ub[0] += r.offset(x[i])
        print(A_ub[0,:10])
        print(b_ub[0])
        res = linprog(c, A_ub, b_ub, A_eq, b_eq, method='highs-ds')
        if res.status != 0:
            print("Not successful, status instead:", res.status)
        assert res.status == 0
        print("Objective value:",-res.fun)
        dx = res.x
        for i in range(len(Recipes)):
            dx[i] = max(dx[i], 0.0)
        recompute = False
        for i in range(len(Recipes)):
            r = Recipes[i]
            if type(r) == ExtractRecipe:
                if abs(r.offset(x[i]) - r.offset(dx[i])) > 0.01:
                    recompute = True
        x = res.x
    val = -res.fun
    recps = dict()
    for i in range(len(Recipes)):
        if x[i] > 0.0:
            recps[Recipes[i].name] = x[i]
    recps = dict((x,recps[x]) for x in sorted(recps))
    return [recps, val]
