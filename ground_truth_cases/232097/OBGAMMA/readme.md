# NEURON Code for Implementing 2D Olfactory Bulb (OB) Model of Gamma Oscillations

**Author:**  
Guoshi Li  
Department of Psychiatry  
University of North Carolina at Chapel Hill  
Chapel Hill, NC 27599  

**Reference:**  
Li G and Cleland TA (2017). A coupled-oscillator model of olfactory bulb gamma oscillations. *PLoS computational biology*, 13(11), e1005760.

For questions, please email: [guoshi_li@med.unc.edu](mailto:guoshi_li@med.unc.edu)

---

## Overview

The OB model is implemented with **NEURON 7.3**, and simulations are run under both **CentOS Linux** and **Ubuntu Linux**.  

The default OB network model contains:  
- 25 mitral cells (MCs)  
- 25 periglomerular cells (PGs)  
- 100 granule cells (GCs)  

### Package Contents

The package contains the following folders:  
- **`celldata`**: Stores data from single-cell simulations  
- **`data0`**: Stores data from network simulations  
- **`connection`**: Stores connectivity information between MCs and GCs  
- **`Input`**: Stores odor input values  
- **`Readme`**: Contains model information  

### Running Simulations

- **Network simulation**: Run `mosinit.hoc`  
- **MC single-cell simulation**: Run `MC_Stim.hoc`  
- **GC single-cell simulation**: Run `GC_Stim.hoc`  
- **PG single-cell simulation**: Run `PG_Stim.hoc`  

### Major HOC Files

- **`Parameter.hoc`**: Specifies the parameters of the OB model  
- **`Connect.hoc`**: Specifies network connectivity  
- **`Background.hoc`**: Generates random background inputs to the network  
- **`Input.hoc`**: Generates odor inputs to the network  
- **`Figure.hoc`**: Generates graphic displays of network simulation results (optional)  
- **`SaveData.hoc`**: Saves all relevant data into files for later analysis  

---

## Simulation Details

- **Simulation step**: 0.002 ms  
- **Default simulation time**: 3000 ms (3 seconds)  

---

## Data Analysis

The data saved in the `data0` folder after simulation can be analyzed using the following custom MATLAB scripts.  
**Note**: The simulation time must be 3000 ms (3 seconds) for the MATLAB scripts to run properly.

- **`PlotV.m`**: Plots cell membrane voltages  
- **`Pro_Delay.m`**: Plots spike propagation delay of one representative MC  
- **`PlotG.m`**: Plots GABAa conductances  
- **`Rasterplot.m`**: Generates raster plots of spikes  
- **`LFP.m`**: Performs frequency analysis of the simulated local field potential (sLFP)  
- **`Load_data.m`**: Loads all relevant data into the workspace (to save the data into a `.mat` file for future analysis)  

---

## Changelog

- **2022-05**: Updated MOD files to compile with the latest NEURON releases where ion variables used as `STATE` cannot be declared as `GLOBAL`.  
- **2025-04-06**: Reformatted readme. Removed backup files and `__MACOSX` folder. Added full reference information (was previously listed as "in press")