# Satisfactory Production Optimizer
For the video game Satisfactory. A program to calculate an optimal production plan with regard to a custom optimization objective. Updated to game version 1.0.

## Modeling Assumptions
- Assumes access to all resources in the game world and all recipes and alt recipes unlocked
- Production plan is required to be sustainable with regard to any resource or item except the objective
- Unlimited buildings' clock speeds for the sake of power consumption assumed to be 100% (WIP)
- Fractional multiples of recipe executions allowed. This is to be interpreted as using clock speed adjustments to match quota.
- Somersloops for production amplification allowed for all applicable recipes and any number of sloops per building
- Clock speeds of buildings with any sloops in them set to 250%

## Usage
In any case: requires Python 3 with Numpy and Scipy.optimize. Run optimizerSomer.py in interactive mode and use as desired.
### Production Optimization
1. Use solve(target) with the optimization target. Can use specific items, "AWESOME points", "ProjectAssemblyN", N up to 5. This will try out all possible numbers of power augmenters.
   - If you've already decided on a number of power augmenters and want to save on execution time, use solve_sub(target, unfueled_APAs, fueled_APAs) instead.
2. It's convenient to store the output in a variable. The first output item is a dictionary containing all recipes' positive execution multiplicity, the second is the achieved goal value.
3. Use prettyprint(dict) for a pretty representation of the raw output dictionary.
4. Use flow(item, dict) to get all producers and consumers of a specific item with their respective throughput in the given production plan dictionary.
### Shadow Prices
1. Use shadowprice() to calculate the shadow price of a specific item towards the stated optimization target.
2. Use shadowprices() for the shadow prices of all items. This may take a while.
3. Output is the subderivative of the target quantity with respect to the selected item quantity.
   - this is a measure for the marginal value of the selected item for the given optimization target. E.g., towards maximizing points, the value is how many points 1 item of the type is worth (at the margin).
   - if this is a pair, the first value is in the direction lowering the item's available quantity and the second value in the direction increasing the item's available quantity.

## Future Work
- Integerize Somersloop recipe usage
- A more flexible approach to building count vs energy efficiency trade-off than fixing at 100%
- Handle resource extraction clocking outside of the Linear Program explicitly by matching shadow prices
- Decompose the Linear Program into power-dependent and -independent components
- Solve these components exactly, using fractions rather than floats
