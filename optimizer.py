# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 01:41:22 2021

@author: Mario
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog

RecipesNameToIdx = dict()
RecipesIdxToName = list()
ItemsNameToIdx = {"Water": 0, }
ItemsIdxToName = ["Water", ]

MinerMK = 3
BeltMK = 5
PipeMK = 2
GeysersOccupied = (3, 9, 6)
FreePower = sum(GeysersOccupied[i] * 100.0 * 2**i for i in range(3))

MinerBasePower = {1: 5, 2: 12, 3: 30}
MinerBaseSpeed = np.array([[30, 60, 120], [60, 120, 240], [120, 240, 480]])
BeltCapacity = {1: 60, 2: 120, 3: 270, 4: 480, 5: 780}
PipeCapacity = {1: 300, 2: 600}


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


def MinerPower(clock: float) -> float:
    if not (clock >= 0.0 and clock <= 2.5):
        raise ValueError("Invalid clock speed: " + str(clock))
    return MinerBasePower[MinerMK] * clock**1.6


def MaxExtractOre(nodes: tuple) -> float:
    if len(nodes) != 3:
        raise ValueError("Nodes should be a tuple of length 3")
    v = ((nodes[0], 'impure'), (nodes[1], 'normal'), (nodes[2], 'pure'))
    return sum(x[0] * min(BeltCapacity[BeltMK], MinerSpeed(x[1], 2.5)) for x in v)


def ExtractionOre(nodes: tuple, quota: float) -> tuple:
    if ((type(nodes) != tuple) and (type(nodes) != list)) or len(nodes) != 3 or type(nodes[0]) != int or type(nodes[1]) != int or type(nodes[2]) != int:
        raise ValueError("invalid nodes")
    if quota > MaxExtractOre(nodes):
        raise ValueError("Demanded quota too high")
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
    power = sum(nodes[i] * MinerPower(clocks[i]) for i in range(3))
    return clocks, power


def ExtractionDerivative(nodes, quota, eps=0.001):
    if quota == MaxExtractOre(nodes):
        return (ExtractionOre(nodes, quota)[1] - ExtractionOre(nodes, quota - eps)[1]) / eps
    if quota == 0:
        return ExtractionOre(nodes, eps)[1] / eps
    e = min(abs(quota - MaxExtractOre(nodes)), eps, quota)
    return (ExtractionOre(nodes, quota + e)[1] - ExtractionOre(nodes, quota - e)[1]) / (2 * e)


def OreGraph(nodes: tuple, title):
    x = np.linspace(0, MaxExtractOre(nodes), 2000)
    y = list(ExtractionOre(nodes, i)[1] for i in x)
    plt.plot(x, y, linewidth=1)
    if title is not None:
        plt.title(title)
    plt.ylabel("power consumption [MW]")
    plt.xlabel("production quota [items per min]")
    plt.grid()
    if title is not None:
        plt.savefig(title + '.png', dpi=300)
    plt.show()


class Building:
    def __init__(self, Name: str, PowerBase: float, Clock=1.0, PowerExponent=1.6):
        self.name = Name
        self._base = PowerBase
        self._exponent = PowerExponent
        self.clock = Clock

    def power(self) -> float:
        return self._base * self.clock**self._exponent


class PowerBuilding(Building):
    def __init__(self, Name: str, PowerBase: float, Clock=1.0, PowerExponent=1 / 1.3):
        self.name = Name
        self._base = PowerBase
        self._exponent = PowerExponent
        self.clock = Clock


WaterExtractor = Building("Water Extractor", 20.0)
Constructor = Building("Constructor", 4.0)
Assembler = Building("Assembler", 15.0)
Manufacturer = Building("Manufacturer", 55.0)
Packager = Building("Packager", 10.0)
Refinery = Building("Refinery", 30.0)
Blender = Building("Blender", 75.0)
ParticleAcceleratorIPC = Building("Particle Accelerator IPC", 375.0)
ParticleAcceleratorNP = Building("Particle Accelerator NP", 1000.0)
ParticleAcceleratorPP = Building("Particle Accelerator PP", 500.0)
Smelter = Building("Smelter", 4.0)
Foundry = Building("Foundry", 16.0)
NuclearPowerPlant = PowerBuilding(
    "Nuclear Power Plant", -2500.0, PowerExponent=0.7564707973660301)
CoalGenerator = PowerBuilding("Coal Generator", -75.0)
FuelGenerator = PowerBuilding("Fuel Generator", -150.0)
Sink = Building("AWESOME Sink", 30.0)

# ----- WATER -----
WaterExtractor.clock = 1.0
PumpsPerPipe = 0.0


def WaterPowerCost():
    return (WaterExtractor.power() / (120.0 * WaterExtractor.clock) + 4.0 * PumpsPerPipe / PipeCapacity[PipeMK])


# ----- Resource Nodes -----
ResourceNodes = dict()
ResourceNodes["Coal"] = (6, 29, 15)
ResourceNodes["Iron Ore"] = (33, 41, 46)

for key in ResourceNodes:
    if key not in ItemsNameToIdx:
        idx = len(ItemsIdxToName)
        ItemsIdxToName.append(key)
        ItemsNameToIdx[key] = idx

# ----- Recipes -----


class Recipe:
    def __init__(self, inputs: dict, outputs: dict, building: Building):
        self.inputs = inputs
        self.outputs = outputs
        self.building = building
        global RecipesNameToIdx, RecipesIdxToName, ItemsNameToIdx, ItemsIdxToName
        for item in inputs.keys() | outputs.keys():
            if item not in ItemsNameToIdx:
                idx = len(ItemsIdxToName)
                ItemsIdxToName.append(item)
                ItemsNameToIdx[item] = idx
        idx = len(RecipesIdxToName)
        RecipesIdxToName.append(self)
        RecipesNameToIdx[self] = idx

    def power(self) -> float:
        return self.building.power()


class WaterExtractRecipe(Recipe):
    def __init__(self):
        self.inputs = dict()
        self.outputs = {"Water": 1.0, }
        self.building = WaterExtractor
        global RecipesNameToIdx, RecipesIdxToName
        idx = len(RecipesIdxToName)
        RecipesIdxToName.append(self)
        RecipesNameToIdx[self] = idx

    def power(self) -> float:
        return WaterPowerCost()


class ExtractRecipe(Recipe):
    num = 0

    def __init__(self, resource: str):
        self.inputs = dict()
        self.outputs = {resource: 1.0, }
        self.resource = resource
        m = MaxExtractOre(ResourceNodes[resource])
        self.slope = ExtractionDerivative(ResourceNodes[resource], m)
        self.offset = ExtractionOre(ResourceNodes[resource], m)[
            1] - self.slope * m
        idx = len(RecipesIdxToName)
        RecipesIdxToName.append(self)
        RecipesNameToIdx[self] = idx
        ExtractRecipe.num += 1

    def power(self) -> float:
        return self.slope

    def linearize(self, newquota: float):
        self.slope = ExtractionDerivative(
            ResourceNodes[self.resource], newquota)
        self.offset = ExtractionOre(ResourceNodes[self.resource], newquota)[
            1] - self.slope * newquota


extract_Water = WaterExtractRecipe()
extract_IronOre = ExtractRecipe("Iron Ore")
extract_Coal = ExtractRecipe("Coal")

r_IronIngot = Recipe({"Iron Ore": 30.0, }, {"Iron Ingot": 30.0, }, Smelter)

# ----- Power Recipes -----
power_Coal = Recipe({"Coal": 60 / 4, "Water": 45}, dict(), CoalGenerator)
power_CompactedCoal = Recipe(
    {"Compacted Coal": 60 / 8.4, "Water": 45}, dict(), CoalGenerator)
power_PetroleumCoke = Recipe(
    {"Petroleum Coke": 60 / 2.4, "Water": 45}, dict(), CoalGenerator)
power_Fuel = Recipe({"Fuel": 60 / 5, }, dict(), FuelGenerator)
#power_LiquidBiofuel = Recipe({"Liquid Biofuel":60/5,}, dict(), FuelGenerator)
power_Turbofuel = Recipe({"Turbofuel": 4.5, }, dict(), FuelGenerator)
power_UraniumFuelRod = Recipe({"Uranium Fuel Rod": 0.2, "Water": 300}, {
                              "Uranium Waste": 10}, NuclearPowerPlant)
#power_PlutoniumFuelRod = Recipe({"Plutonium Fuel Rod":0.1, "Water":300}, {"Plutonium Waste":1}, NuclearPowerPlant)


class SinkRecipe(Recipe):
    def __init__(self, item: str, points: int):
        self.inputs = {item: BeltCapacity[BeltMK], }
        self.outputs = {"AWESOME points": points * BeltCapacity[BeltMK], }
        self.building = Sink
        global RecipesNameToIdx, RecipesIdxToName, ItemsNameToIdx, ItemsIdxToName
        if item not in ItemsNameToIdx:
            idx = len(ItemsIdxToName)
            ItemsIdxToName.append(item)
            ItemsNameToIdx[item] = idx
        if "AWESOME points" not in ItemsNameToIdx:
            idx = len(ItemsIdxToName)
            ItemsIdxToName.append("AWESOME points")
            ItemsNameToIdx["AWESOME points"] = idx
        idx = len(RecipesIdxToName)
        RecipesIdxToName.append(self)
        RecipesNameToIdx[self] = idx


# ----- Sink items -----
sink_IronOre = SinkRecipe("Iron Ore", 1)
sink_Coal = SinkRecipe("Coal", 3)
sink_IronIngot = SinkRecipe("Iron Ingot", 2)

# ----- solution -----
assert ItemsIdxToName[-1] == "AWESOME points"
target = "AWESOME points"
c = np.zeros(len(RecipesIdxToName))
for i in range(len(RecipesIdxToName)):
    if target in RecipesIdxToName[i].outputs:
        c[i] = -RecipesIdxToName[i].outputs[target]
    if target in RecipesIdxToName[i].inputs:
        c[i] = RecipesIdxToName[i].inputs[target]
A_ub = np.zeros((1 + ExtractRecipe.num, len(RecipesIdxToName)))
for i in range(len(RecipesIdxToName)):
    A_ub[0, i] = RecipesIdxToName[i].power()
b_ub = np.zeros(1 + ExtractRecipe.num)
b_ub[0] = FreePower
for i in range(ExtractRecipe.num):
    A_ub[1 + i, i + 1] = 1
    b_ub[1 +
         i] = MaxExtractOre(ResourceNodes[RecipesIdxToName[i + 1].resource])
    b_ub[0] += RecipesIdxToName[1 + i].offset
A_eq = np.zeros((len(ItemsIdxToName) - 1, len(RecipesIdxToName)))
for recipe in RecipesIdxToName:
    for item in recipe.inputs:
        if item != "AWESOME points":
            A_eq[ItemsNameToIdx[item], RecipesNameToIdx[recipe]
                 ] = recipe.inputs[item]
    for item in recipe.outputs:
        if item != "AWESOME points":
            A_eq[ItemsNameToIdx[item], RecipesNameToIdx[recipe]] = - \
                recipe.outputs[item]
b_eq = np.zeros(len(ItemsIdxToName) - 1)
res = linprog(c, A_ub, b_ub, A_eq, b_eq, method='revised simplex')
x = res.x
recompute = False
for i in range(ExtractRecipe.num):
    if abs(x[1 + i] - MaxExtractOre(ResourceNodes[RecipesIdxToName[1 + i].resource])) > 0.001:
        recompute = True
        RecipesIdxToName[1 + i].linearize(x[1 + i])
while recompute:
    for i in range(len(RecipesIdxToName)):
        A_ub[0, i] = RecipesIdxToName[i].power()
    b_ub[0] = FreePower
    for i in range(ExtractRecipe.num):
        b_ub[0] += RecipesIdxToName[1 + i].offset
    res = linprog(c, A_ub, b_ub, A_eq, b_eq, method='revised simplex')
    recompute = False
    for i in range(ExtractRecipe.num):
        if abs(x[1 + i] - res.x[1 + i]) > 0.001:
            recompute = True
            RecipesIdxToName[1 + i].linearize(res.x[1 + i])
    x = res.x
val = -res.fun
