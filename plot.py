import matplotlib.pyplot as plt
import matplotlib as mpl
import pylab
from datetime import datetime, timedelta

import cartopy.feature as cfeature
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader

from plotconfigs import *

class Plot():
    def __init__(self, **kwargs):
        self.dummy = ''

    def make_figure(self, **kwargs):
        """Create the plotting figure and axes

        Optional Parameters
        -------------------
        dpi : int
            Dots per inch. Default = 75
        fig_width : int
            Desired figured width (pixels). Default = 900
        fig_aspect : float
            Width : Height figure aspect. Default = 1.65
        """

        dpi = kwargs.get('dpi', 75)
        fig_width = kwargs.get('fig_width', 900)
        self.fig_aspect = kwargs.get('fig_aspect', 1.65)

        fig_height = fig_width / self.fig_aspect
        self.fig = pylab.figure(figsize=(fig_width/dpi, fig_height/dpi), dpi=dpi)

        axes_left = 0.01
        axes_bot = 0.01
        axes_hght = 0.99
        axes_wid = axes_hght / self.fig_aspect
        self.ax = pylab.axes([axes_left, axes_bot, 0.99, axes_hght])
        self.ax.get_xaxis().set_ticks([])
        self.ax.get_yaxis().set_ticks([])

    def make_map(self, bounds, fig=None, **kwargs):
        """Create the Cartopy plotting object.

        Parameters
        ----------
        bounds : list
            Bounding box for the plot. Of the form [min_lon, max_lon, min_lat, max_lat]
            Specified in plotconfigs.py

        Optional Parameters
        -------------------
        fig : figure object
            Figure plotting object. If None (default), creates one.
        counties : bool
            Whether or not to plot counties. Default = False.
        """

        if not fig: self.make_figure()

        central_longitude = kwargs.get('central_longitude', 265)
        #self.proj = ccrs.LambertConformal(central_longitude=central_longitude)
        self.proj = ccrs.PlateCarree(central_longitude=central_longitude)
        self.ax = self.fig.add_axes([0., 0., 1, 1], projection=self.proj)

        # Add geographic information
        if kwargs.get('counties', False):
            reader = shpreader.Reader('/Users/leecarlaw/scripts/gefs/shapefiles/countyl010g.shp')
            counties = list(reader.geometries())
            COUNTIES = cfeature.ShapelyFeature(counties, ccrs.PlateCarree())
            self.ax.add_feature(COUNTIES, facecolor='none', edgecolor='darkgrey',
                                linewidth=0.5)
        self.ax.coastlines('50m')
        self.ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=1)

        # Resize the plotting domain to ensure specific aspect ratio
        self.bounds = self.set_map_extents(min_lon=bounds[0], max_lon=bounds[1],
                                           min_lat=bounds[2], max_lat=bounds[3])
        self.ax.set_extent(self.bounds, crs=ccrs.PlateCarree())

    def set_map_extents(self, min_lon, max_lon, min_lat, max_lat):
        """Alter the requested boundaries to fit a particular aspect ratio. This function
        inherits self.fig_aspect from make_plot().

        Parameters
        ----------
        min_lon : float
            Minimum longitude.
        max_lon : float
            Maximum longitude.
        min_lat : float
            Minimum latitude.
        max_lat : float
            Maximum latitude.

        Returns
        -------
        list
            List containing the altered west, east, north, and south map bounds.
        """
        #Get lat/lon bounds
        bound_w = min_lon+0.0
        bound_e = max_lon+0.0
        bound_s = min_lat+0.0
        bound_n = max_lat+0.0

        #If only one coordinate point, artificially induce a spread
        if bound_w == bound_e:
            bound_w = bound_w - 0.6
            bound_e = bound_e + 0.6
        if bound_s == bound_n:
            bound_n = bound_n + 0.6
            bound_s = bound_s - 0.6

        #Function for fixing map ratio
        def fix_map_ratio(bound_w, bound_e, bound_n, bound_s, nthres=1.65):
            xrng = abs(bound_w-bound_e)
            yrng = abs(bound_n-bound_s)
            diff = float(xrng) / float(yrng)
            if diff < nthres: #plot too tall, need to make it wider
                goal_diff = nthres * (yrng)
                factor = abs(xrng - goal_diff) / 2.0
                bound_w = bound_w - factor
                bound_e = bound_e + factor
            elif diff > nthres: #plot too wide, need to make it taller
                goal_diff = xrng / nthres
                factor = abs(yrng - goal_diff) / 2.0
                bound_s = bound_s - factor
                bound_n = bound_n + factor
            return bound_w,bound_e,bound_n,bound_s

        #First round of fixing ratio
        bound_w,bound_e,bound_n,bound_s = fix_map_ratio(bound_w, bound_e, bound_n,
                                                        bound_s, self.fig_aspect)
        return bound_w,bound_e,bound_s,bound_n


class PlanView(Plot):
    def __init__(self):
        self.dummy = ''

    def plot_spag(self, data, time, thresh, run_date, plot_info, prop={}, map_prop={},
                  save_name=None):
        """Creates spaghetti plots.

        Parameters
        ----------
        data : np.array

        Optional Parameters
        -------------------

        Returns
        -------
        """
        n_perts = data[:].shape[0]
        contours = []
        for i in range(n_perts):
            plot_data = np.where(data[i][time] < thresh, 0, data[i][time])
            c = plt.contour(lon, lat, plot_data, [thresh], linestyles=styles[i],
                             linewidths=1.75, zorder=99, transform=ccrs.PlateCarree(),
                             colors=mpl.colors.to_hex(colors[i]))
            contours.append(c)

        valid_time = run_date + timedelta(hours=int(time*3))
        img_time = "%s GEFS [~27 km] | F%s Valid: %s"%(run_date.strftime("%HZ"),
                                                 str(int(time*3)).zfill(2),
                                                 valid_time.strftime("%HZ %a %b %d %Y"))
        t1 = pylab.text(1., 1.007, img_time, transform=pylab.gca().transAxes, ha='right',
                        fontsize=12)
        t2 = pylab.text(0., 1.007, plot_info, transform=pylab.gca().transAxes, ha='left',
                        fontsize=12)
        pylab.savefig(save_name, bbox_inches='tight', dpi=100)
        self.clean_objects(None, contours, t1, t2, None)

    def plot_lpmm(self, data, run_date, plot_info, time_str, save_name, prop={},
                  map_prop={}, **kwargs):
        """Creates spaghetti plots.

        Parameters
        ----------
        data : np.array

        Optional Parameters
        -------------------

        Returns
        -------
        """

        plot_levs = kwargs.get('plot_levs', qpf_levs)
        plot_cols = kwargs.get('plot_cols', qpf_cols)
        cf = plt.contourf(lon, lat, data, plot_levs, transform=ccrs.PlateCarree(),
                          colors=plot_cols)
        valid_time = run_date + timedelta(hours=int(time_str))
        img_time = "%s GEFS [~27 km] | F%s Valid: %s"%(run_date.strftime("%HZ"),
                                                 time_str.zfill(2),
                                                 valid_time.strftime("%HZ %a %b %d %Y"))
        t1 = pylab.text(1., 1.007, img_time, transform=pylab.gca().transAxes, ha='right',
                        fontsize=12)
        t2 = pylab.text(0., 1.007, plot_info, transform=pylab.gca().transAxes, ha='left',
                        fontsize=12)

        cax = plt.axes([0., 0., 1, 0.018])
        cb = plt.colorbar(cf, cax=cax, orientation='horizontal')
        pylab.savefig(save_name, bbox_inches='tight', dpi=100)
        self.clean_objects(cf, None, t1, t2, cb)

    def clean_objects(self, cf, c1, t1, t2, cb):
        """
        """
        if cb: cb.remove()
        if cf:
            for member in cf.collections: member.remove()
        if c1:
            for c in c1:
                for member in c.collections: member.remove()
        t1.remove()
        t2.remove()
