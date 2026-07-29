# CLSI Widgets
## Description
`clsi-widgets` is a collection of reusable interactive widgets developed for CLSI scientific workflows.

The first workflow included in this package is the **Synaptic Events Fitting** widget. It supports fitting synaptic events using experimental data and computational models.

Additional CLSI widgets and workflows will be added to this repository in future releases.

## Installation
To install `clsi-widgets` from a local clone of the repository in development mode, run:

```
pip install -e ".[test]"
```

To install the optional dependency required for local best-fit analysis with NEURON, run:

```
pip install -e .[neuron]
```
Please note that installation of `neuron` from PyPI may not work on all operating systems.
For Windows, NEURON should be installed separately using the official Windows installer.

### JupyterLab

To use the widgets in JupyterLab, make sure JupyterLab is installed in the same Python environment:
```
pip install jupyterlab
```
Then start JupyterLab:
```
jupyter lab
```
The maintained Synaptic Events Fitting notebook is: `notebooks/SynapticEventsFitting.ipynb`

### EBRAINS authentication

Some features require authentication with EBRAINS services.
If you are running locally, set the CLB_AUTH environment variable before launching JupyterLab:
```
export CLB_AUTH="{Your TokenString copied from EBRAINS Collab}"
```

To retrieve the token string, run the following command in the EBRAINS JupyterLab environment (https://lab.ebrains.eu/):
```
clb_oauth.get_token()
```


## Contributors 
- Carmen Alina Lupascu, carmen.lupascu@ibf.cnr.it
- Roberto Smiriglia, roberto.smiriglia@ibf.cnr.it
- Luca Leonardo Bologna, lucaleonardo.bologna@cnr.it
- Dario Curreri, dario.curreri@ibf.cnr.it
