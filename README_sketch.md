Idea sketch:

Introduction:

In computational neuroscience, the normative methodology while developing model of specific neuronal circuit is to first
explore already exisiting models which try to capture similar / in a similar fashion some qualitative phenomenon e.g. 
oscillogenesis.

A more or less systematic exploration of exisiting models is to go to modeldb.science, query structure/cell/phenomenon
of interest and go over each code repository. What makes it very time consuming is that modeldb doesn't impose any
standardized way to provide parameters/ results etc. Moreover, there are three major programming languagues in which 
these models are written. It's basically a wild west.

Once we find an interesting model on which we can begin to explore the system (as long as we are not creating one from
scratch), it's a common procedure to validate what kind of properties modeled circuit exhibits and whether it does so
with parametrization that is at least partially biologically plausible. For example, it is a good habit to check whether
net capacitance of a single cell model is similar to in-vivo cell. There exists a database called NeuroElectro, which 
acts as a repository of in-vivo registered electrophysiological properties of many cell types. It is curated and has some
API. NeuroElectro is a reliable database to validate whether parametrization in the model is biologically sound.

Example problem:

Imagine I wish to explore oscillogenesis of gamma band in the olfactory bulb, basing on some existing computational model.
So I query modeldb.science with https://modeldb.science/search?q=Olfactory+bulb#models.

First one is a model from (Li & Cleland, 2017): https://modeldb.science/232097, and I wish to explore its functionality.

I can simply download the model, and given that it's written using primarly NEURON language, I just need to
execute mosinit.hoc file, which is normative to use as the main executable file. This will produce data that the authors
shared in the article describing this model.

I am satisified with how the model works so far, but I wish validate to which extent parametrization of model components
e.g. cells or synapses have been kept with accordance to experimental data. Here is where it gets, messy. Parameters are
scattered very often in many different files of the project, and their description is very often limited.
From the perspective of the modeller, he needs to go over many different files, search where the parameters are assigned,
make sure that the units are correct and then compare them with NeuroElectro database.

Suppose I want to check what the capacitance of template Mitral cell is:
https://modeldb.science/232097?tab=2 > https://modeldb.science/232097?tab=2&file=OBGAMMA/MC_def.hoc
Only then, in the 137 line, I can see that:
      cm = 1.2    // uF/cm^2; Shen et al. JNP, 1999

If I wanted to check synapse conductance, I have to navigate and explore completely different file.

For one model, this does not sound too bad. It gets bad when we need to explore more models, to choose the best one.

Proposed solution:

Minimum: A data scrapper that will go over all files of the model, present me with the importing order of the files
(hierarchy), and extract all the parameters that were used assigned in the model and in which file.

Additional:
    - Deducing the units of each parameter.
    - Describing/explaining the parameter interpretation.
    - Properly identyfing the name of parameterized component e.g. instead of MC_def.hoc > Olfactory bulb Mitral cell
    - Classifying, whether the parameter has direct physical interpretation or whether it's and abstract interpretation e.g. in Izikhevich models.
    - Fetching the data concerning specific component from NeuroElectro.
    - Creating a comparison report between params. in the model and NeuroElectro database.
    
