# Synaptic_Events_Fitting
## Description
Fitting synaptic events using data and model in NeuroInformatics Platform

## Installation
To install `synaptic-events-fitting` from a local clone of the repository, run:

```
pip install -e .
```

If you want to use the full functionality, including the local best-fit analysis based on NEURON, install optional
dependency with:

```
pip install -e .[neuron]
```
Please note that installation of `neuron` from PyPI may not work on all operating systems.
For Windows, NEURON should be installed separately using the official Windows installer.

If you want to use the widgets in JupyterLab, make sure JupyterLab is installed in the same environment:
```
pip install jupyterlab
```
Then start JupyterLab with:
```
jupyter lab
```

Some features require authentication with EBRAINS services.
If you are running locally, set the CLB_AUTH environment variable before launching JupyterLab.
```
export CLB_AUTH="{Your TokenString copied from EBRAINS Collab}"
```

To retrieve the token string, execute in https://lab.ebrains.eu/:
```
clb_oauth.get_token()
```


## Contributors 
- Carmen Alina Lupascu, carmen.lupascu@ibf.cnr.it
- Roberto Smiriglia, roberto.smiriglia@ibf.cnr.it
- Luca Leonardo Bologna, lucaleonardo.bologna@cnr.it
- Dario Curreri, dario.curreri@ibf.cnr.it
