"""
Created on Tue Nov 23 19:44:07 2021

@author: Reddit: u/MarioVX
For personal, non-commercial use only! Do not republish and alter without
my permission.

Requirements: numpy, scipy.optimize

Usage: use in interactive mode. assign a variable to solve("name of item or
recipe to maximize"). returns a list of two items, one is the resource
allocation dictionary, the other is the value of the objective function.

Settings that can be changed are littered throughout the code, I'm sorry.
To exclude recipes, comment out the respective line starting with reg BEFORE
running the script.

prettyprint(dict) will take a resource allocation dictionary and print it
prettily to the console.

flow(str, dict) gathers the in- and outflow of the given item in the given
resource allocation.

nlextract(str, float) takes a raw resource and a desired quota and outputs
optimal clock speed assignments and their total power cost.
"""
import numpy as np
from scipy.optimize import linprog
import warnings
warnings.filterwarnings("ignore")

# ----- general settings -----
MinerMK = 3  # 1 to 3
BeltMK = 5  # 1 to 5
PipeMK = 2  # 1 or 2
GeysersOccupied = (3, 9, 6)  # impure, normal, pure
FreeExtraPower = 0.0  # not including Geysers
PumpsPerPipe = 0.0  # 1 per mk1 + 2 per mk2
ExtractClockSteps = 500 # extractor's clock speed domain is divded in this many points. more: greater accuracy and computational expense
MinClock = 0.01

MinerBasePower = {1: 5, 2: 12, 3: 30}
MinerBaseSpeed = np.array([[30, 60, 120], [60, 120, 240], [120, 240, 480]])
BeltCapacity = {1: 60, 2: 120, 3: 270, 4: 480, 5: 780}
PipeCapacity = {1: 300, 2: 600}
GeothermalBasePower = 100.0 # on impure Geysir

def FreePower():
    return sum(GeysersOccupied[i] * GeothermalBasePower * 2**i for i in range(3)) + FreeExtraPower

RecipesByName = dict()
Recipes = list()
Items = ["Water", ] # only needs to include items for which we enforce generation=destruction, i.e. not AWESOME points.
Buildings = dict()
#LimResources = set()
ExtractBuildings = dict()


class Building:
    def __init__(self, Name: str, PowerBase: float, Clock=1.0, PowerExponent=1.321928):
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

class WaterExtractor(Building):
    def __init__(self):
        self.name = "Water Extractor"
        self._base = 20.0
        self._exponent = 1.321928
        self.clock = 1.0
    
    def power(self) -> float:
        return self._base * self.clock**self._exponent + (120.0 * self.clock / PipeCapacity[PipeMK]) * 4.0 * PumpsPerPipe

Buildings["Water Extractor"] = WaterExtractor()


class PowerBuilding(Building):
    def __init__(self, Name: str, PowerBase: float, Clock=1.0, PowerExponent=1):
        super().__init__(Name, PowerBase, Clock=Clock, PowerExponent=PowerExponent)

    def ratemult(self) -> float:
        return self.clock**self._exponent


def regPB(name: str, powerbase: float, exp=1):
    global Buildings
    Buildings[name] = PowerBuilding(name, powerbase, PowerExponent=exp)


regPB("Coal Generator", -75.0)
regPB("Fuel Generator", -150.0)
regPB("Nuclear Power Plant", -2500.0)


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

def setclocks(clock: float):
    for bn in ("Water Extractor", "Constructor", "Assembler", "Manufacturer", "Packager", "Refinery", "Blender",
               "Particle Accelerator IPC", "Particle Accelerator NP", "Particle Accelerator PP",
               "Smelter", "Foundry"):
        Buildings[bn].clock = clock
    return None

Nodes = dict()

def regN(resource: str, nodes: tuple):
    if sum(nodes) == 0:
        return None
    global Nodes
    if resource not in Nodes:
        Nodes[resource] = dict()
    for i in range(3):
        if nodes[i] > 0:
            if 2**i not in Nodes[resource]:
                Nodes[resource][2**i] = 0
            Nodes[resource][2**i] += nodes[i]
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
    if sum(nodes) == 0:
        return None
    global Wells
    if resource not in Wells:
        Wells[resource] = dict()
    val = sum(nodes[i]*2**i for i in range(3))
    if val not in Wells[resource]:
        Wells[resource][val] = 0
    Wells[resource][val] += 1
    return None

# ----- Resource Wells -----
regW("Crude Oil", (0, 3, 3))  # Red Bamboo Fields
regW("Crude Oil", (6, 0, 0))  # Swamp
regW("Nitrogen Gas", (0, 2, 5))  # Red Oasis
regW("Nitrogen Gas", (0, 1, 6))  # Rocky Desert
regW("Nitrogen Gas", (0, 0, 7))  # Jungle Spires
regW("Nitrogen Gas", (0, 0, 10))  # Eastern Dune Forest
regW("Nitrogen Gas", (0, 2, 4))  # Blue Crater
regW("Nitrogen Gas", (2, 2, 4))  # Abyss Cliffs
regW("Water", (2,1,4)) # Dune Desert (north)
regW("Water", (0,0,6)) # Dune Desert (south)
regW("Water", (1,2,4)) # Desert Canyons
regW("Water", (0,0,6)) # Eastern Dune Forest (north)
regW("Water", (2,6,0)) # Eastern Dune Forst (south)
regW("Water", (2,0,5)) # Grass Fields
regW("Water", (0,1,6)) # Snaketree Forest
regW("Water", (0,0,7)) # Red Jungle


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

class ExtractRecipe(Recipe):
    num = 0
    def __init__(self, building: str, resource: str, val: int, clock: float):
        if building not in ("Miner", "Oil Extractor", "Resource Well Pressurizer"):
            raise ValueError("Invalid building: "+building)
        if not ((clock >= MinClock) and (clock <= 2.5)):
            raise ValueError("Invalid clock setting:"+str(clock))
        self.building = building
        self.resource = resource
        self.val = val
        self.inputs = dict()
        self.outputs = {resource:None,}
        self.clock = clock
        if building == "Resource Well Pressurizer":
            if resource not in Wells:
                raise ValueError("Wells not found for resource: "+resource)
            if val not in Wells[resource]:
                raise ValueError("No "+resource+" well found with value: "+str(val))
            self._baseRate = 30.0 * val
            self._basePower = 150.0
            self.name = "extract_Well-" + "".join(resource.split()) + "-" + str(val) + "-@" + f"{clock*100:.7g}" + "%"
        else:
            if resource not in Nodes:
                raise ValueError("Nodes not found for resource: "+resource)
            if val not in Nodes[resource]:
                raise ValueError("No "+resource+" node found with rarity: "+str(val))
            if building == "Oil Extractor":
                self._baseRate = 60.0 * val
                self._basePower = 40.0
            else:
                self._baseRate = 30.0 * 2**(MinerMK-1) * val
                self._basePower = MinerBasePower[MinerMK]
            if val == 1:
                rarity = "impure"
            elif val == 2:
                rarity = "normal"
            elif val == 4:
                rarity = "pure"
            else:
                raise ValueError("Invalid rarity for resource "+resource)
            self.name = "extract_" + "".join(building.split()) + "-" + "".join(resource.split()) + "-" + rarity + "-@" + f"{clock*100:.7g}" + "%"
        ExtractRecipe.num += 1
        return None
    
    def power(self) -> float:
        if self.building == "Miner":
            self._basePower = MinerBasePower[MinerMK]
        return self._basePower * self.clock**1.321928
    
    def rate(self, item: str) -> float:
        if item != self.resource:
            return 0.0
        if self.building == "Miner":
            self._baseRate = 30.0 * 2**(MinerMK-1) * self.val
            lim = BeltCapacity[BeltMK]
            return -min(lim, self._baseRate * self.clock)
        elif self.building == "Oil Extractor":
            lim = PipeCapacity[PipeMK]
            return -min(lim, self._baseRate * self.clock)
        return -self._baseRate * self.clock

def maxExtractClock(resource: str, building: str, val: int) -> float:
    if resource not in ExtractBuildings:
        raise KeyError(resource+" has no registered extraction buildings.")
    if building not in ExtractBuildings[resource]:
        raise KeyError(building+" not in "+resource+"'s registered extraction buildings.")
    lim = 2.5
    if building == "Miner":
        lim = min(lim, BeltCapacity[BeltMK] / (30 * 2**(MinerMK-1) * val))
    elif building == "Oil Extractor":
        lim = min(lim, PipeCapacity[PipeMK] / (60 * val))
    return lim

def regER(resource: str, building: str):
    global ExtractBuildings, RecipesByName, Recipes, Items
    if resource not in ExtractBuildings:
        ExtractBuildings[resource] = list()
    if building not in ExtractBuildings[resource]:
        ExtractBuildings[resource].append(building)
    if resource not in Items:
        Items.append(resource)
    if building == "Resource Well Pressurizer":
        values = Wells[resource]
    else:
        values = Nodes[resource]
    for val in values:
        maxclock = maxExtractClock(resource, building, val)
        clocks = np.linspace(MinClock, maxclock, ExtractClockSteps)
        for c in clocks:
            r = ExtractRecipe(building, resource, val, c)
            if r.name in RecipesByName:
                raise ValueError("duplicate recipe name")
            RecipesByName[r.name] = r
            Recipes.append(r)
    return None

# ----- extraction recipes -----
regER("Iron Ore", "Miner")
regER("Copper Ore", "Miner")
regER("Limestone", "Miner")
regER("Caterium Ore", "Miner")
regER("Raw Quartz", "Miner")
regER("Sulfur", "Miner")
regER("Coal", "Miner")
regER("Crude Oil", "Oil Extractor")
regER("Bauxite", "Miner")
regER("Uranium", "Miner")
regER("Water", "Resource Well Pressurizer")
regER("Crude Oil", "Resource Well Pressurizer")
regER("Nitrogen Gas", "Resource Well Pressurizer")


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

regR("pump_Water", dict(), {"Water":120}, "Water Extractor")

# ----- power recipes -----
regR("power_Coal", {"Coal":60/4.0, "Water":45}, dict(), "Coal Generator")
regR("power_CompactedCoal", {"Compacted Coal":60/8.4, "Water":45}, dict(), "Coal Generator")
regR("power_PetroleumCoke", {"Petroleum Coke":60/2.4, "Water":45}, dict(), "Coal Generator")
regR("power_Fuel", {"Fuel":12.0}, dict(), "Fuel Generator")
# regR("power_LiquidBiofuel", {"Liquid Biofuel":12.0}, dict(), "Fuel Generator")
regR("power_Turbofuel", {"Turbofuel":4.5}, dict(), "Fuel Generator")
regR("power_UraniumFuelRod", {"Uranium Fuel Rod":0.2, "Water":240},{"Uranium Waste":10}, "Nuclear Power Plant")
regR("power_PlutoniumFuelRod", {"Plutonium Fuel Rod":0.1, "Water":240},{"Plutonium Waste":1}, "Nuclear Power Plant")

# ----- processing recipes -----
# ---- start ----
regR("r_IronIngot", {"Iron Ore":30}, {"Iron Ingot":30}, "Smelter")
regR("r_IronRod", {"Iron Ingot":15}, {"Iron Rod":15}, "Constructor")
regR("r_IronPlate", {"Iron Ingot":30}, {"Iron Plate":20}, "Constructor")

# ---- T0 2 ----
regR("r_CopperIngot", {"Copper Ore":30}, {"Copper Ingot":30}, "Smelter")
regR("r_Wire", {"Copper Ingot":15}, {"Wire":30}, "Constructor")
regR("r_Cable", {"Wire":60}, {"Cable":30}, "Constructor")

# ---- T0 3 ----
regR("r_Concrete", {"Limestone":45}, {"Concrete":15}, "Constructor")
regR("r_Screw", {"Iron Rod":10}, {"Screw":40}, "Constructor")
regR("r_ReinforcedIronPlate", {"Iron Plate":30, "Screw":60}, {"Reinforced Iron Plate":5}, "Assembler")

# ---- T0 6 ----
# regR("r_Biomass(Leaves)", {"Leaves":120}, {"Biomass":60}, "Constructor")
# regR("r_Biomass(Wood)", {"Wood":60}, {"Biomass":300}, "Constructor")

# ---- T2 Obstacle Clearing ----
# regR("r_SolidBiofuel", {"Biomass":120}, {"Solid Biofuel":60}, "Constructor")

# ---- T2 Part Assembly ----
regR("r_CopperSheet", {"Copper Ingot":20}, {"Copper Sheet":10}, "Constructor")
regR("r_Rotor", {"Iron Rod":20, "Screw":100}, {"Rotor":4}, "Assembler")
regR("r_ModularFrame", {"Reinforced Iron Plate":3, "Iron Rod":12}, {"Modular Frame":2}, "Assembler")
regR("r_SmartPlating", {"Reinforced Iron Plate":2, "Rotor":2}, {"Smart Plating":2}, "Assembler")

# ---- T3 Basic Steel Production ----
regR("r_SteelIngot", {"Iron Ore":45, "Coal":45}, {"Steel Ingot":45}, "Foundry")
regR("r_SteelBeam", {"Steel Ingot":60}, {"Steel Beam":15}, "Constructor")
regR("r_SteelPipe", {"Steel Ingot":30}, {"Steel Pipe":20}, "Constructor")
regR("r_VersatileFramework", {"Modular Frame":2.5, "Steel Beam":30}, {"Versatile Framework":5}, "Assembler")

# ---- T4 Advanced Steel Production ----
regR("r_EncasedIndustrialBeam", {"Steel Beam":24, "Concrete":30}, {"Encased Industrial Beam":6}, "Assembler")
regR("r_Stator", {"Steel Pipe":15, "Wire":40}, {"Stator":5}, "Assembler")
regR("r_Motor", {"Rotor":10, "Stator":10}, {"Motor":5}, "Assembler")
regR("r_AutomatedWiring", {"Stator":2.5, "Cable":50}, {"Automated Wiring":2.5}, "Assembler")
regR("r_HeavyModularFrame", {"Modular Frame":10, "Steel Pipe":30, "Encased Industrial Beam":10, "Screw":200}, {"Heavy Modular Frame":2}, "Manufacturer")

# ---- T5 Oil Processing ----
regR("r_Plastic", {"Crude Oil":30}, {"Plastic":20, "Heavy Oil Residue":10}, "Refinery")
regR("r_Rubber", {"Crude Oil":30}, {"Rubber":20, "Heavy Oil Residue":20}, "Refinery")
regR("r_Fuel", {"Crude Oil":60}, {"Fuel":40, "Polymer Resin":30}, "Refinery")
regR("r_ResidualFuel", {"Heavy Oil Residue":60}, {"Fuel":40}, "Refinery")
regR("r_ResidualPlastic", {"Polymer Resin":60, "Water":20}, {"Plastic":20}, "Refinery")
regR("r_ResidualRubber", {"Polymer Resin":40, "Water":40}, {"Rubber":20}, "Refinery")
regR("r_PetroleumCoke", {"Heavy Oil Residue":40}, {"Petroleum Coke":120}, "Refinery")
regR("r_CircuitBoard", {"Copper Sheet":15, "Plastic":30}, {"Circuit Board":7.5}, "Assembler")

# ---- T5 Alternative Fluid Transport ----
regR("r_EmptyCanister", {"Plastic":30}, {"Empty Canister":60}, "Constructor")
# regR("r_LiquidBiofuel", {"Solid Biofuel":90, "Water":45}, {"Liquid Biofuel":60}, "Refinery")
regR("r_PackagedFuel", {"Fuel":40, "Empty Canister":40}, {"Packaged Fuel":40}, "Packager")
regR("r_UnpackageFuel", {"Packaged Fuel":60}, {"Fuel":60, "Empty Canister":60}, "Packager")
regR("r_PackagedHeavyOilResidue", {"Heavy Oil Residue":30, "Empty Canister":30}, {"Packaged Heavy Oil Residue":30}, "Packager")
regR("r_UnpackageHeavyOilResidue", {"Packaged Heavy Oil Residue":20}, {"Heavy Oil Residue":20, "Empty Canister":20}, "Packager")
# regR("r_PackagedLiquidBiofuel", {"Liquid Biofuel":40, "Empty Canister":40}, {"Packaged Liquid Biofuel":40}, "Packager")
# regR("r_UnpackageLiquidBiofuel", {"Packaged Liquid Biofuel":60}, {"Liquid Biofuel":60, "Empty Canister":60}, "Packager")
regR("r_PackagedOil", {"Crude Oil":30, "Empty Canister":30}, {"Packaged Oil":30}, "Packager")
regR("r_UnpackageOil", {"Packaged Oil":60}, {"Crude Oil":60, "Empty Canister":60}, "Packager")
regR("r_PackagedTurbofuel", {"Turbofuel":20, "Empty Canister":20}, {"Packaged Turbofuel":20}, "Packager")
regR("r_UnpackageTurbofuel", {"Packaged Turbofuel":20}, {"Turbofuel":20, "Empty Canister":20}, "Packager")
regR("r_PackagedWater", {"Water":60, "Empty Canister":60}, {"Packaged Water":60}, "Packager")
regR("r_UnpackageWater", {"Packaged Water":120}, {"Water":120, "Empty Canister":120}, "Packager")

# ---- T5 Industrial Manufacturing ----
regR("r_Computer", {"Circuit Board":25, "Cable":22.5, "Plastic":45, "Screw":130}, {"Computer":2.5}, "Manufacturer")
regR("r_ModularEngine", {"Motor":2, "Rubber":15, "Smart Plating":2}, {"Modular Engine":1}, "Manufacturer")
regR("r_AdaptiveControlUnit", {"Automated Wiring":7.5, "Circuit Board":5, "Heavy Modular Frame":1, "Computer":1}, {"Adaptive Control Unit":1}, "Manufacturer")
regR("r_Beacon", {"Iron Plate":22.5, "Iron Rod":7.5, "Wire":112.5, "Cable":15}, {"Beacon":7.5}, "Manufacturer")

# ---- T5 Gas Mask ----
regR("r_GasFilter", {"Coal":37.5, "Rubber":15, "Fabric":15}, {"Gas Filter":7.5}, "Manufacturer")

# ---- T7 Bauxite Refinement ----
regR("r_AluminaSolution", {"Bauxite":120, "Water":180}, {"Alumina Solution":120, "Silica":50}, "Refinery")
regR("r_PackagedAluminaSolution", {"Alumina Solution":120, "Empty Canister":120}, {"Packaged Alumina Solution":120}, "Packager")
regR("r_UnpackageAluminaSolution", {"Packaged Alumina Solution":120}, {"Alumina Solution":120, "Empty Canister":120}, "Packager")
regR("r_AluminumScrap", {"Alumina Solution":240, "Coal":120}, {"Aluminum Scrap":360, "Water":120}, "Refinery")
regR("r_AluminumIngot", {"Aluminum Scrap":90, "Silica":75}, {"Aluminum Ingot":60}, "Foundry")
regR("r_AlcladAluminumSheet", {"Aluminum Ingot":30, "Copper Ingot":10}, {"Alclad Aluminum Sheet":30}, "Assembler")
regR("r_AluminumCasing", {"Aluminum Ingot":90}, {"Aluminum Casing":60}, "Constructor")
regR("r_RadioControlUnit", {"Aluminum Casing":40, "Crystal Oscillator":1.25, "Computer":1.25}, {"Radio Control Unit":2.5}, "Manufacturer")

# ---- T7 Hazmat Suit ----
regR("r_IodineInfusedFilter", {"Gas Filter":3.75, "Quickwire":30, "Aluminum Casing":3.75}, {"Iodine Infused Filter":3.75}, "Manufacturer")

# ---- T7 Aeronautical Engineering ----
regR("r_SulfuricAcid", {"Sulfur":50, "Water":50}, {"Sulfuric Acid":50}, "Refinery")
regR("r_PackagedSulfuricAcid", {"Sulfuric Acid":40, "Empty Canister":40}, {"Packaged Sulfuric Acid":40}, "Packager")
regR("r_UnpackageSulfuricAcid", {"Packaged Sulfuric Acid":60}, {"Sulfuric Acid":60, "Empty Canister":60}, "Packager")
regR("r_Battery", {"Sulfuric Acid":50, "Alumina Solution":40, "Aluminum Casing":20}, {"Battery":20, "Water":30}, "Blender")
regR("r_AssemblyDirectorSystem", {"Adaptive Control Unit":1.5, "Supercomputer":0.75}, {"Assembly Director System":0.75}, "Assembler")

# ---- T8 Advanced Aluminum Production ----
regR("r_EmptyFluidTank", {"Aluminum Ingot":60}, {"Empty Fluid Tank":60}, "Constructor")
regR("r_PackagedNitrogenGas", {"Nitrogen Gas":240, "Empty Fluid Tank":60}, {"Packaged Nitrogen Gas":60}, "Packager")
regR("r_UnpackageNitrogenGas", {"Packaged Nitrogen Gas":60}, {"Nitrogen Gas":240, "Empty Fluid Tank":60}, "Packager")
regR("r_HeatSink", {"Alclad Aluminum Sheet":37.5, "Copper Sheet":22.5}, {"Heat Sink":7.5}, "Assembler")
regR("r_CoolingSystem", {"Heat Sink":12, "Rubber":12, "Water":30, "Nitrogen Gas":150}, {"Cooling System":6}, "Blender")
regR("r_FusedModularFrame", {"Heavy Modular Frame":1.6, "Aluminum Casing":75, "Nitrogen Gas":37.5}, {"Fused Modular Frame":1.5}, "Blender")

# ---- T8 Nuclear Power ----
regR("r_EncasedUraniumCell", {"Uranium":50, "Concrete":15, "Sulfuric Acid":40}, {"Encased Uranium Cell":25, "Sulfuric Acid":10}, "Blender")
regR("r_ElectromagneticControlRod", {"Stator":6, "AI Limiter":4}, {"Electromagnetic Control Rod":4}, "Assembler")
regR("r_UraniumFuelRod", {"Encased Uranium Cell":20, "Encased Industrial Beam":1.2, "Electromagnetic Control Rod":2}, {"Uranium Fuel Rod":0.4}, "Manufacturer")
regR("r_MagneticFieldGenerator", {"Versatile Framework":2.5, "Electromagnetic Control Rod":1, "Battery":5}, {"Magnetic Field Generator":1}, "Manufacturer")

# ---- T8 Leading-edge Production ----
regR("r_TurboMotor", {"Cooling System":7.5, "Radio Control Unit":3.75, "Motor":7.5, "Rubber":45}, {"Turbo Motor":1.875}, "Manufacturer")
regR("r_ThermalPropulsionRocket", {"Modular Engine":2.5, "Turbo Motor":1, "Cooling System":3, "Fused Modular Frame":1}, {"Thermal Propulsion Rocket":1}, "Manufacturer")

# ---- T8 Particle Enrichment ----
regR("r_NitricAcid", {"Nitrogen Gas":120, "Water":30, "Iron Plate":10}, {"Nitric Acid":30}, "Blender")
regR("r_PackagedNitricAcid", {"Nitric Acid":30, "Empty Fluid Tank":30}, {"Packaged Nitric Acid":30}, "Packager")
regR("r_UnpackageNitricAcid", {"Packaged Nitric Acid":20}, {"Nitric Acid":20, "Empty Fluid Tank":20}, "Packager")
regR("r_Non-fissileUranium", {"Uranium Waste":37.5, "Silica":25, "Nitric Acid":15, "Sulfuric Acid":15}, {"Non-fissile Uranium":50, "Water":15}, "Blender")
regR("r_PlutoniumPellet", {"Non-fissile Uranium":100, "Uranium Waste":25}, {"Plutonium Pellet":30}, "Particle Accelerator PP")
regR("r_EncasedPlutoniumCell", {"Plutonium Pellet":10, "Concrete":20}, {"Encased Plutonium Cell":5}, "Assembler")
regR("r_PlutoniumFuelRod", {"Encased Plutonium Cell":7.5, "Steel Beam":4.5, "Electromagnetic Control Rod":1.5, "Heat Sink":2.5}, {"Plutonium Fuel Rod":0.25}, "Manufacturer")
regR("r_CopperPowder", {"Copper Ingot":300}, {"Copper Powder":50}, "Constructor")
regR("r_PressureConversionCube", {"Fused Modular Frame":1, "Radio Control Unit":2}, {"Pressure Conversion Cube":1}, "Assembler")
regR("r_NuclearPasta", {"Copper Powder":100, "Pressure Conversion Cube":0.5}, {"Nuclear Pasta":0.5}, "Particle Accelerator NP")

# ---- MAM Alien Organisms ----
# regR("r_Biomass(AlienCarapace)", {"Alien Carapace":15}, {"Biomass":1500}, "Constructor")
# regR("r_Biomass(AlienOrgans)", {"Alien Organs":7.5}, {"Biomass":1500}, "Constructor")
regR("r_SpikedRebar", {"Iron Rod":15}, {"Spiked Rebar":15}, "Constructor")

# ---- MAM Caterium ----
regR("r_CateriumIngot", {"Caterium Ore":45}, {"Caterium Ingot":15}, "Smelter")
regR("r_Quickwire", {"Caterium Ingot":12}, {"Quickwire":60}, "Constructor")
regR("r_AILimiter", {"Copper Sheet":25, "Quickwire":100}, {"AI Limiter":5}, "Assembler")
regR("r_High-SpeedConnector", {"Quickwire":210, "Cable":37.5, "Circuit Board":3.75},{"High-Speed Connector":3.75}, "Manufacturer")
regR("r_Supercomputer", {"Computer":3.75, "AI Limiter":3.75, "High-Speed Connector":5.625, "Plastic":52.5}, {"Supercomputer":1.875}, "Manufacturer")

# ---- MAM Flower Petals or T2 Resource Sink Bonus Program ----
# regR("r_ColorCartridge", {"Flower Petals":37.5}, {"Color Cartridge":75}, "Constructor")

# ---- MAM Mycelia ----
# regR("r_Biomass(Mycelia)", {"Mycelia":150}, {"Biomass":150}, "Constructor")
# regR("r_Fabric", {"Mycelia":15, "Biomass":75}, {"Fabric":15}, "Assembler")

# ---- MAM Power Slugs ----
# regR("r_PowerShard(1)", {"Blue Power Slug":7.5}, {"Power Shard":7.5}, "Constructor")
# regR("r_PowerShard(2)", {"Yellow Power Slug":5}, {"Power Shard":10}, "Constructor")
# regR("r_PowerShard(5)", {"Purple Power Slug":2.5}, {"Power Shard":12.5}, "Constructor")

# ---- MAM Quartz ----
regR("r_QuartzCrystal", {"Raw Quartz":37.5}, {"Quartz Crystal":22.5}, "Constructor")
regR("r_Silica", {"Raw Quartz":22.5}, {"Silica":37.5}, "Constructor")
regR("r_CrystalOscillator", {"Quartz Crystal":18.75, "Rubber":13.125, "Reinforced Iron Plate":2.5}, {"Crystal Oscillator":1}, "Manufacturer")

# ---- MAM Sulfur ----
regR("r_BlackPowder", {"Coal":7.5, "Sulfur":15}, {"Black Powder":7.5}, "Assembler")
regR("r_Nobelisk", {"Black Powder":15, "Steel Pipe":30}, {"Nobelisk":3}, "Assembler")
regR("r_RifleCartridge", {"Beacon":3, "Steel Pipe":30, "Black Powder":30, "Rubber":30}, {"Rifle Cartridge":15}, "Manufacturer")


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
# regR("a_Biocoal", {"Biomass":37.5}, {"Coal":45}, "Assembler")
# regR("a_Charcoal", {"Wood":15}, {"Coal":150}, "Assembler")
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
regR("a_TurboBlendFuel", {"Fuel":15, "Heavy Oil Residue":30, "Sulfur":22.5, "Petroleum Coke":22.5}, {"Turbofuel":45}, "Blender")
regR("a_SloppyAlumina", {"Bauxite":200, "Water":200}, {"Alumina Solution":240}, "Refinery")
regR("a_AlcladCasing", {"Aluminum Ingot":150, "Copper Ingot":75}, {"Aluminum Casing":112.5}, "Assembler")
regR("a_PureAluminumIngot", {"Aluminum Scrap":60}, {"Aluminum Ingot":30}, "Smelter")
regR("a_Electrode-AluminumScrap", {"Alumina Solution":180, "Petroleum Coke":60}, {"Aluminum Scrap":300, "Water":105}, "Refinery")
regR("a_DilutedFuel", {"Heavy Oil Residue":50, "Water":100}, {"Fuel":100}, "Blender")
regR("a_RadioControlSystem", {"Crystal Oscillator":1.5, "Circuit Board":15, "Aluminum Casing":90, "Rubber":45}, {"Radio Control Unit":4.5}, "Manufacturer")


# ---- T7 Aeronautical Engineering ----
regR("a_ClassicBattery", {"Sulfur":45, "Alclad Aluminum Sheet":52.5, "Plastic":60, "Wire":90}, {"Battery":30}, "Manufacturer")
regR("a_InstantScrap", {"Bauxite":150, "Coal":100, "Sulfuric Acid":50, "Water":60}, {"Aluminum Scrap":300, "Water":50}, "Blender")

# ---- T8 Advanced Aluminum ----
regR("a_OCSupercomputer", {"Radio Control Unit":9, "Cooling System":9}, {"Supercomputer":3}, "Assembler")
regR("a_RadioConnectionUnit", {"Heat Sink":15, "High-Speed Connector":7.5, "Quartz Crystal":45}, {"Radio Control Unit":3.75}, "Manufacturer")
regR("a_CoolingDevice", {"Heat Sink":9.375, "Motor":1.875, "Nitrogen Gas":45}, {"Cooling System":3.75}, "Blender")
regR("a_HeatExchanger", {"Aluminum Casing":30, "Rubber":30}, {"Heat Sink":10}, "Assembler")

# ---- T8 Nuclear Power ----
regR("a_ElectricMotor", {"Electromagnetic Control Rod":3.75, "Rotor":7.5}, {"Motor":7.5}, "Assembler")
regR("a_Super-StateComputer", {"Computer":3.6, "Electromagnetic Control Rod":2.4, "Battery":24, "Wire":54}, {"Supercomputer":2.4}, "Manufacturer")
# -- # MAM --
regR("a_ElectromagneticConnectionRod", {"Stator":8, "High-Speed Connector":4}, {"Electromagnetic Control Rod":8}, "Assembler")
regR("a_InfusedUraniumCell", {"Uranium":25, "Silica":15, "Sulfur":25, "Quickwire":75}, {"Encased Uranium Cell":20}, "Manufacturer")
regR("a_UraniumFuelUnit", {"Encased Uranium Cell":20, "Electromagnetic Control Rod":2, "Crystal Oscillator":0.6, "Beacon":1.2}, {"Uranium Fuel Rod":0.6}, "Manufacturer")

# ---- T8 Leading-edge ----
regR("a_TurboElectricMotor", {"Motor":6.5625, "Radio Control Unit":8.4375, "Electromagnetic Control Rod":4.6875, "Rotor":6.5625}, {"Turbo Motor":2.8125}, "Manufacturer")

# ---- T8 Particle Enrichment ----
regR("a_Heat-FusedFrame", {"Heavy Modular Frame":3, "Aluminum Ingot":150, "Nitric Acid":24, "Fuel":30}, {"Fused Modular Frame":3}, "Blender")
regR("a_TurboPressureMotor", {"Motor":7.5, "Pressure Conversion Cube":1.875, "Packaged Nitrogen Gas":45, "Stator":15}, {"Turbo Motor":3.75}, "Manufacturer")
regR("a_FertileUranium", {"Uranium":25, "Uranium Waste":25, "Nitric Acid":15, "Sulfuric Acid":25}, {"Non-fissile Uranium":100, "Water":40}, "Blender")
regR("a_InstantPlutoniumCell", {"Non-fissile Uranium":75, "Aluminum Casing":10}, {"Encased Plutonium Cell":10}, "Particle Accelerator IPC")
regR("a_PlutoniumFuelUnit", {"Encased Plutonium Cell":10, "Pressure Conversion Cube":0.5}, {"Plutonium Fuel Rod":0.5}, "Assembler")


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
regMR("ProjectAssembly4", {"Assembly Director System":4, "Magnetic Field Generator":4, "Thermal Propulsion Rocket":1, "Nuclear Pasta":1})
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
        else:
            return 0.0

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
#regS("Leaves",3)
regS("Copper Ore",3)
regS("Iron Rod",4)
regS("Iron Plate",6)
regS("Copper Ingot",6)
regS("Wire",6)
regS("Caterium Ore",7)
regS("Steel Ingot",8)
regS("Bauxite",8)
regS("Spiked Rebar",8)
#regS("Color Cartridge",10)
#regS("Flower Petals",10)
#regS("Mycelia",10)
regS("Sulfur",11)
regS("Polymer Resin",12)
#regS("Biomass",12)
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
#regS("Wood",30)
regS("Uranium",35)
regS("Caterium Ingot",42)
#regS("Solid Biofuel",48)
regS("Black Powder",50)
regS("Quartz Crystal",50)
regS("Empty Canister",60)
regS("Portable Miner",60)
regS("Rubber",60)
regS("Steel Beam",64)
#regS("Medicinal Inhaler",67)
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
#regS("Packaged Liquid Biofuel",370)
regS("Aluminum Casing",393)
regS("Modular Frame",408)
regS("Packaged Nitric Acid",412)
regS("Battery",465)
regS("Smart Plating",520)
regS("Packaged Turbofuel",570)
#regS("Parachute",608)
regS("Encased Industrial Beam",632)
regS("Rifle Cartridge",664)
regS("Circuit Board",696)
regS("Gas Filter",830)
#regS("Color Gun",860)
regS("AI Limiter",920)
regS("Nobelisk",980)
regS("Versatile Framework",1176)
regS("Automated Wiring",1440)
regS("Motor",1520)
#regS("Factory Cart",1552)
#regS("Xeno-Zapper",1880)
#regS("Rebar Gun",1968)
regS("Electromagnetic Control Rod",2560)
regS("Iodine Infused Filter",2718)
#regS("Chainsaw",2760)
regS("Heat Sink",2804)
regS("Crystal Oscillator",3072)
#regS("Object Scanner",3080)
regS("High-Speed Connector",3776)
#regS("Blade Runners",4988)
#regS("Zipline",5284)
regS("Modular Engine",9960)
regS("Heavy Modular Frame",11520)
regS("Cooling System",12006)
regS("Magnetic Field Generator",15650)
regS("Computer",17260)
#regS("Xeno-Basher",18800)
regS("Radio Control Unit",32908)
#regS("Jetpack",35580)
#regS("Nobelisk Detonator",39520)
regS("Uranium Fuel Rod",44092)
#regS("Hazmat Suit",54100)
#regS("Gas Mask",55000)
regS("Fused Modular Frame",62840)
regS("Adaptive Control Unit",86120)
#regS("Rifle",99160)
regS("Supercomputer",99576)
regS("Plutonium Fuel Rod",153184)
regS("Turbo Motor",242720)
regS("Pressure Conversion Cube",257312)
#regS("Hover Pack",413920)
regS("Nuclear Pasta",543424)
regS("Assembly Director System",543632)
regS("Thermal Propulsion Rocket",732956)

np.set_printoptions(precision=2, suppress=True)
solver_options = {'autoscale':True}
# ----- solving -----
def solve(target: str, penalty=0.0, outputMatrices=False, buildlimit=None):
    # goal
    c = np.zeros(len(Recipes))
    if target == "AWESOME points" or target in Items:
        for i in range(len(Recipes)):
            c[i] = Recipes[i].rate(target)
    elif target in RecipesByName:
        c[Recipes.index(RecipesByName[target])] = -1
    else:
        raise ValueError("Target not recognized.")
    c += penalty
    # inequalities: power and number of wells/nodes of each value of each resource
    A_ub = np.zeros(len(Recipes))
    for i in range(len(Recipes)):
        A_ub[i] = Recipes[i].power()
    b_ub = np.array(FreePower())
    for resource in ExtractBuildings:
        for building in ExtractBuildings[resource]:
            if building == "Resource Well Pressurizer":
                values = Wells[resource]
            else:
                values = Nodes[resource]
            for val in values:
                row = np.zeros(len(Recipes))
                for i in range(len(Recipes)):
                    if type(Recipes[i]) == ExtractRecipe:
                        rec = Recipes[i]
                        if rec.building == building and rec.resource == resource and rec.val == val:
                            row[i] = 1
                A_ub = np.vstack([A_ub, row])
                b_ub = np.append(b_ub, values[val])
    if buildlimit is not None:
        A_ub = np.vstack([A_ub, np.ones(len(Recipes))])
        b_ub = np.append(b_ub, buildlimit)
    # equalities: in=out for all registered items except target
    A_eq = np.zeros((len(Items),len(Recipes)))
    b_eq = np.zeros(len(Items))
    for i in range(len(Recipes)):
        rec = Recipes[i]
        for item in rec.inputs.keys() | rec.outputs.keys():
            if item not in (target, "AWESOME points"):
                A_eq[Items.index(item),i] = rec.rate(item)
    # idx = 0
    # while idx < A_eq.shape[0]:
    #     if A_eq[idx].sum() == 0:
    #         A_eq = np.delete(A_eq, idx, 0)
    #         b_eq = np.delete(b_eq, idx)
    #     idx += 1
    # solve
    for met in ('revised simplex', 'highs-ds', 'highs', 'simplex', 'highs-ipm', 'interior-point'):
        solver_method = met
        res = linprog(c, A_ub, b_ub, A_eq, b_eq, method=solver_method, options=solver_options)
        if res.success:
            print("solver method used 1st:",solver_method)
            break
    if res.status != 0:
        print("Couldn't solve for",target,", Status:",res.status)
        return [c, A_ub, b_ub, A_eq]
    assert res.status == 0
    if outputMatrices:
        return {"c":c, "A_ub":A_ub, "b_ub":b_ub, "A_eq":A_eq, "x":res.x}
    val = -res.fun
    val += penalty * np.sum(res.x)
    # undo the manual scaling of expensive milestone recipes
    if target == "ProjectAssembly4":
        val /= 1000.0
    stored_x = res.x
    A_eq = np.vstack([A_eq, c])
    b_eq= np.append(b_eq, res.fun)
    c = np.ones(len(Recipes))
    res = linprog(c, A_ub, b_ub, A_eq, b_eq, method=solver_method, options=solver_options)
    if not res.success:
        for met in ('revised simplex', 'highs-ds', 'highs', 'simplex', 'highs-ipm', 'interior-point'):
            solver_method = met
            res = linprog(c, A_ub, b_ub, A_eq, b_eq, method=solver_method, options=solver_options)
            if res.success:
                print("solver method used 2nd:",solver_method)
                break
    if res.status == 0:
        if not np.equal(stored_x, res.x).all():
            stored_x = res.x
    recps = dict()
    for i in range(len(Recipes)):
        if stored_x[i] > 10**(-9) and type(Recipes[i]) != MilestoneRecipe:
            recps[Recipes[i].name] = stored_x[i]
    recps = dict((x,recps[x]) for x in sorted(recps))
    return [recps, val]

def prettyprint(recpdict: dict):
    for r in recpdict:
        print(r,":",f"{recpdict[r]:.7g}")
    return None

def flow(item: str, rd: dict) -> list:
    sources = dict()
    sinks = dict()
    for rn in rd:
        r = RecipesByName[rn]
        ra = r.rate(item)
        if ra < 0.0:
            sources[rn] = -ra * rd[rn]
        elif ra > 0.0:
            sinks[rn] = ra * rd[rn]
    inflow = sum(sources[x] for x in sources)
    outflow = sum(sinks[x] for x in sinks)
    # if abs(inflow-outflow)>10**(-6):
    #     print("in- and outflow not matching!",inflow,"vs",outflow)
    sources = dict(sorted(sources.items(), key = lambda x: x[1], reverse=True))
    sinks = dict(sorted(sinks.items(), key = lambda x: x[1], reverse=True))
    return [inflow, sources, outflow, sinks]

def nlextract(resource: str, quota: float, minclock=0.0):
    if resource not in ExtractBuildings:
        raise KeyError("resource not recognized: "+resource)
    methods = list()
    # method: [building, val, num, base rate, base power, limit]
    if "Resource Well Pressurizer" in ExtractBuildings[resource]:
        for v in Wells[resource]:
            methods.append(["Resource Well Pressurizer", v, Wells[resource][v], v*30.0, 150.0, maxExtractClock(resource, "Resource Well Pressurizer", v)])
    if resource == "Crude Oil":
        for v in Nodes["Crude Oil"]:
            methods.append(["Oil Extractor", v, Nodes["Crude Oil"][v], v*60.0, 40.0, maxExtractClock("Crude Oil", "Oil Extractor", v)])
    if "Miner" in ExtractBuildings[resource]:
        for v in Nodes[resource]:
            methods.append(["Miner", v, Nodes[resource][v], v*MinerBaseSpeed[MinerMK-1,0], MinerBasePower[MinerMK], maxExtractClock(resource, "Miner", v)])
    if quota > sum(x[2]*x[3]*x[5] for x in methods):
        raise ValueError("demanded quota too high")
    elif quota < minclock*sum(x[2]*x[3] for x in methods):
        raise ValueError("quota too low")
    methods.sort(key = lambda x: x[4]/x[3])
    solutions = dict()
    for i in range(len(methods)+1):
        for j in range(i,len(methods)+1):
            q = quota - sum(x[2]*x[3]*x[5] for x in methods[:i]) - minclock * sum(x[2]*x[3] for x in methods[j:])
            if i == j:
                if q == 0.0:
                    sol = tuple(x[5] for x in methods[:i]) + tuple(minclock for _ in methods[j:])
                    solutions[sol] = sum(methods[k][2]*methods[k][4]*sol[k]**1.321928 for k in range(len(methods)))
            elif q >= 0.0:
                lam = q / sum(x[2] * x[3]**(1+1/(1.321928-1)) * x[4]**(-1/(1.321928-1)) for x in methods[i:j])
                sol = tuple(x[5] for x in methods[:i]) + tuple(lam * (methods[k][3]/methods[k][4])**(1/(1.321928-1)) for k in range(i,j)) + tuple(minclock for _ in methods[j:])
                assert len(sol) == len(methods)
                valid = True
                for k in range(len(methods)):
                    if sol[k] > methods[k][5] or sol[k] < minclock:
                        valid = False
                if valid:
                    solutions[sol] = sum(methods[k][2]*methods[k][4]*sol[k]**1.321928 for k in range(len(methods)))
    best = min(solutions, key= lambda x: solutions[x])
    outp = dict()
    for k in range(len(methods)):
        key = "extract_"
        if methods[k][0] == "Resource Well Pressurizer":
            key += "Well"
        else:
            key += "".join(methods[k][0].split())
        key += "-" + "".join(resource.split()) + "-"
        if methods[k][0] == "Resource Well Pressurizer":
            key += str(methods[k][1])
        else:
            if methods[k][1] == 1:
                key += "impure"
            elif methods[k][1] == 2:
                key += "normal"
            elif methods[k][1] == 4:
                key += "pure"
            else:
                raise ValueError("unrecognized node purity")
        key += "-@" + f"{best[k]*100:.7g}" + "%"
        global RecipesByName, Recipes
        if key not in RecipesByName:
            r = ExtractRecipe(methods[k][0], resource, methods[k][1], best[k])
            assert r.name == key
            RecipesByName[key] = r
            Recipes.append(r)
        outp[key] = methods[k][2]
    return [dict((x,outp[x]) for x in sorted(outp)), solutions[best]]

def shadowprices(target, **kwargs):
    sol = solve(target, outputMatrices=True, **kwargs)
    # n_vars = len(sol['x'])
    n_ineqs = len(sol['b_ub'])
    n_eqs = np.shape(sol['A_eq'])[0]
    b = (-1) * np.hstack([sol['b_ub'],np.zeros(n_eqs)])
    A = np.vstack([sol['A_ub'], sol['A_eq']]).T
    c = sol['c']
    # print("-b:")
    # print(b)
    # print("-A:")
    # print(A)
    # print("-c:")
    # print(c)
    bounds = [(None,0),]*n_ineqs + [(None, None),]*n_eqs
    res = linprog(b, A_ub=A, b_ub=c, bounds=bounds, method='interior-point')
    print("dual problem:")
    print(res)
    # assert res.success
    dualvars = list((-1)*res.x)
    v_power = dualvars[0]
    v_nodes = dualvars[1:n_ineqs]
    v_items = dualvars[n_ineqs:]
    names_nodes = list()
    for resource in ExtractBuildings:
        for building in ExtractBuildings[resource]:
            if building == "Resource Well Pressurizer":
                st = " Well "
                for val in Wells[resource]:
                    names_nodes.append(resource + st + str(val))
            else:
                st = " Node "
                for val in Nodes[resource]:
                    if val == 1:
                        purity = "impure"
                    elif val == 2:
                        purity = "normal"
                    elif val == 4:
                        purity = "pure"
                    else:
                        raise ValueError
                    names_nodes.append(resource + st + purity)
    assert len(names_nodes) == len(v_nodes)
    v_nodes = dict((names_nodes[i], v_nodes[i]) for i in range(len(v_nodes)))
    v_nodes = dict((y, v_nodes[y]) for y in sorted(v_nodes, key = lambda x:v_nodes[x], reverse=True))
    v_power = {"Power":v_power,}
    assert len(Items) == len(v_items)
    v_items = dict((Items[i], v_items[i]) for i in range(len(Items)))
    v_items = dict((y, v_items[y]) for y in sorted(v_items))
    return [v_power, v_nodes, v_items]

# ---- checking Zistack
bc = dict()
bc['pump_Water'] = 1535.03
bc['r_Cable'] = 83.64
bc ['r_Concrete'] = 88.73
bc['a_IronWire'] = 4693.93
bc['r_Screw'] = 5595.64
bc['r_SteelPipe'] = 1897.86
bc['a_SteelRod'] = 1478.03
bc['a_AdheredIronPlate'] = 42.82
bc['r_AILimiter'] = 618.08
bc['a_AlcladCasing'] = 86.93
bc['r_AssemblyDirectorSystem'] = 26.76
bc['r_AutomatedWiring'] = 120.43
bc['a_CheapSilica'] = 702.04
bc['r_CircuitBoard'] = 307.59
bc['a_CompactedCoal'] = 165.83
bc['a_CopperRotor'] = 760.56
bc['r_ElectromagneticControlRod'] = 711.97
bc['a_EncasedIndustrialPipe'] = 33.45
bc['a_FusedQuickwire'] = 736
bc['a_InsulatedCable'] = 43.92
bc['r_ModularFrame'] = 53.52
bc['r_Motor'] = 760.66
bc['r_Rotor'] = 713.39
bc['a_SiliconCircuitBoard'] = 30.94
bc['r_Stator'] = 2435.92
bc['a_SteelCoatedPlate'] = 15.95
bc['r_AdaptiveControlUnit'] = 40.14
bc['r_Beacon'] = 10.49
bc['r_Computer'] = 32.11
bc['a_HeavyEncasedFrame'] = 14.27
bc['a_InfusedUraniumCell'] = 34.99
bc['a_InsulatedCrystalOscillator'] = 107.93
bc['a_RadioControlSystem'] = 108.66
bc['a_SiliconHigh-SpeedConnector'] = 20.07
bc['r_Supercomputer'] = 10.7
bc['a_TurboElectricMotor'] = 579.55
bc['a_UraniumFuelUnit'] = 65.62
bc['a_Electrode-AluminumScrap'] = 65.2
bc['a_HeavyOilResidue'] = 390
bc['r_PetroleumCoke'] = 179.2
bc['a_PureCateriumIngot'] = 460
bc['a_PureCopperIngot'] = 1924
bc['a_PureIronIngot'] = 1302.28
bc['a_PureQuartzCrystal'] = 38.54
bc['a_RecycledPlastic'] = 272.93
bc['a_RecycledRubber'] = 168.71
bc['r_ResidualRubber'] = 292.5
bc['a_SloppyAlumina'] = 48.9
bc['a_SteamedCopperSheet'] = 1690.22
bc['r_SulfuricAcid'] = 14.7
bc['a_DilutedFuel'] = 139.72
bc['r_EncasedUraniumCell'] = 24.5
bc['a_TurboBlendFuel'] = 48.18
bc['r_AluminumIngot'] = 217.33
bc['a_CokeSteelIngot'] = 220.11
bc['a_CompactedSteelIngot'] = 368.51
bc['a_SolidSteelIngot'] = 649.35
bc['power_Turbofuel'] = 481.85
bc['power_UraniumFuelRod'] = 196.87
bc['sink_Limestone'] = 45.77
bc['sink_TurboMotor'] = 2.08
bc['sink_AssemblyDirectorSystem'] = 0.02

eu = dict()
eu['pump_Water'] = 1620.73
eu['r_AluminumCasing'] = 18.81
eu['r_Cable'] = 1928.62
eu['r_Concrete'] = 747.82
eu['r_CopperPowder'] = 186.85
eu['a_IronWire'] = 6970.97
eu['r_Quickwire'] = 294.11
eu['r_Screw'] = 721.81
eu['r_SteelBeam'] = 93.42
eu['r_SteelPipe'] = 1422.52
eu['a_SteelRod'] = 420.17
eu['a_AdheredIronPlate'] = 637.62
eu['r_AILimiter'] = 11.04
eu['r_AlcladAluminumSheet'] = 132.74
eu['a_AlcladCasing'] = 13.32
eu['r_AssemblyDirectorSystem'] = 249.13
eu['r_AutomatedWiring'] = 1121.10
eu['a_CateriumCircuitBoard'] = 598.05
eu['a_CheapSilica'] = 870.21
eu['a_CompactedCoal'] = 79.26
eu['a_ElectromagneticConnectionRod'] = 60.09
eu['a_EncasedIndustrialPipe'] = 400.82
eu['r_EncasedPlutoniumCell'] = 55.48
eu['a_FusedQuickwire'] = 265.41
eu['a_HeatExchanger'] = 59.65
eu['r_ModularFrame'] = 758.10
eu['r_Motor'] = 48.49
eu['a_OCSupercomputer'] = 17.57
eu['a_PlutoniumFuelUnit'] = 27.74
eu['r_PressureConversionCube'] = 60.58
eu['r_Rotor'] = 190.19
eu['a_SiliconCircuitBoard'] = 128.67
eu['r_Stator'] = 763.69
eu['a_SteelCoatedPlate'] = 171.09
eu['r_AdaptiveControlUnit'] = 373.70
eu['r_Beacon'] = 6.55
eu['a_CateriumComputer'] = 102.77
eu['a_ClassicBattery'] = 75.85
eu['r_Computer'] = 75.79
eu['a_FlexibleFramework'] = 62.28
eu['a_HeavyEncasedFrame'] = 171.02
eu['a_InsulatedCrystalOscillator'] = 29.45
eu['r_MagneticFieldGenerator'] = 186.85
eu['r_ModularEngine'] = 116.78
eu['a_PlasticSmartPlating'] = 46.71
eu['a_RadioControlSystem'] = 9.32
eu['a_RigourMotor'] = 13.34
eu['a_SiliconHigh-SpeedConnector'] = 80.12
eu['a_Super-StateComputer'] = 55.89
eu['r_ThermalPropulsionRocket'] = 46.71
eu['a_TurboElectricMotor'] = 16.60
eu['a_UraniumFuelUnit'] = 40.94
eu['a_Electrode-AluminumScrap'] = 65.2
eu['a_HeavyOilResidue'] = 390
eu['r_PetroleumCoke'] = 68.81
eu['a_PureCateriumIngot'] = 460
eu['a_PureCopperIngot'] = 1924
eu['a_PureIronIngot'] = 1773.47
eu['a_PureQuartzCrystal'] = 10.51
eu['a_RecycledPlastic'] = 458.5
eu['a_RecycledRubber'] = 362.23
eu['r_ResidualRubber'] = 292.5
eu['a_SloppyAlumina'] = 48.9
eu['a_SteamedCopperSheet'] = 169.54
eu['r_SulfuricAcid'] = 28.89
eu['a_WetConcrete'] = 24.09
eu['r_CoolingSystem'] = 49.71
eu['a_DilutedFuel'] = 256.95
eu['r_EncasedUraniumCell'] = 32.75
eu['a_FertileUranium'] = 18.49
eu['a_Heat-FusedFrame'] = 35.76
eu['r_NitricAcid'] = 37.85
eu['r_NuclearPasta'] = 93.42
eu['r_PlutoniumPellet'] = 18.49
eu['r_AluminumIngot'] = 217.33
eu['a_CokeSteelIngot'] = 57.93
eu['a_CompactedSteelIngot'] = 176.14
eu['a_SolidSteelIngot'] = 703.45
eu['power_PlutoniumFuelRod'] = 138.7
eu['power_UraniumFuelRod'] = 122.82