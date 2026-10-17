"""main2d.py: run this example with the pyIB2d solver (chapter 4c of Using IB Software).

Reads input2d through pyIB2d's own initializer and hands the parameters to its driver; this folder must sit under
pyIB2d/Examples/ of an IB2d clone (https://github.com/nickabattista/IB2d), where ../../IBM_Blackbox is the solver.
"""
import sys
sys.path.append('../../IBM_Blackbox')
import IBM_Driver as Driver
from please_Initialize_Simulation import please_Initialize_Simulation

if __name__ == "__main__":
    Fluid_Params, Grid_Params, Time_Params, Lag_Struct_Params, Output_Params, Lag_Name_Params = please_Initialize_Simulation()
    Driver.main(Fluid_Params, Grid_Params, Time_Params, Lag_Struct_Params, Output_Params, Lag_Name_Params)
