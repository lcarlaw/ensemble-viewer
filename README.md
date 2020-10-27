# ensemble-viewer

Purpose: Make interacting with Numerical Weather Prediction ensemble model output easier for the operational forecaster to aid in the of deliver of Decision Support Services to end-users and Deep Core Partners.

The temporary website to access the application can be found here: https://f82808d9705f.ngrok.io

![](https://raw.githubusercontent.com/lcarlaw/ensemble-viewer/main/examples/qpf_03hr_lpmm.png)
<p align="center">
  <em>Web application view for 3-hour QPF Localized Probability Matched Mean output
  </em>
</p>

![](https://github.com/lcarlaw/ensemble-viewer/blob/main/examples/qpf_03hr_sp.png?raw=true)
<p align="center">
  <em>Web application view for 3-hour QPF Spaghetti plots for 0.25" exceedance values.
  </em>
</p>

## Setup Notes

This code was developed using Anaconda and Python 3.7. It is highly unlikely this will work with Python 2.xx.

```
conda create --name ensemble-viewer python=3.7
conda install dash pygrib numba
pip install geojsoncontour dash-leaflet
```

The actual web application is driven by [Plotly Dash](https://dash.plotly.com/) and the associated javascript bindings in [dash-leaflet](https://dash-leaflet.herokuapp.com/).

The ```numba``` module––which is a "Just-in-Time" (JIT) compiler that translates Python into fast machine code using LLVM––is leveraged for the computationally-expensive post-processing calculations such as the creation of Localized Probability Matched Mean output. ```numba``` helps us achieve C++ or Fortran-like speeds after code compilation at runtime.

## Usage and code hierarchy

The code hierarchy and data structure is described below:

```
ensemble/
app.py
create_geojson.py
tools.py
assets/
    |————func.js
    |————style.css
Sites/
json/
    |————2020-10-27/
            |————00
            |————06
            |————12
            |————18
    |————2020-10-26/
            |————...
```

The web application is driven entirely by the ```app.py``` script.

Once ensemble data is downloaded to the system from NOMADS, ```create_geojson.py``` produces GEOJSON output files for various parameters, such as 3-,6-,12-hour QPF, total snow depth, etc. Localized probability matched mean values are computed for each dataset, as are maximum values and thresholded probabilities and spaghetti contours. This is accomplished via the ```geojsoncontour``` module.

Further documentation will be added...
