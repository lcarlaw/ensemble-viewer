import os
import argparse
import time
import matplotlib.pyplot as plt
import pygrib
import numpy as np
from subprocess import Popen
import subprocess
from datetime import datetime, timedelta
from plotconfigs import *
from plot import *
from mapinfo import *
import tools
import geojsoncontour
import json
import geopandas
import pandas as pd
import shapely
import io
import geobuf

def timestamp(str1, str2):
    """Print out some simple date and time information for log files
    """

    print("%s  %s : %s" % (str1, datetime.strftime(datetime.now(), "%c"), str2))

def get_filesize(fname):
    """Test filesize on the local system. If the file DNE, return a filsize of 0 bytes.

    Parameters
    ----------
    fname : str
        Location on the local file system to grab filesize for

    Returns
    -------
    fsize : int
        Filsize (bytes)
    """

    try:
        fsize = os.stat(fname).st_size
    except:
        fsize = 0
    return fsize

def check_for_file(fname):
    """Check for file existence on the local system, as well as filesize.

    Parameters
    ----------
    fname : str
        Full path to file
    """

    fsize = get_filesize(fname)
    file_exists = os.path.exists(fname)
    num_attempts = 0
    while not file_exists and fsize < 50000 and num_attempts < 90:
        timestamp("[INFO]", "waiting for %s" % (fname))
        file_exists = os.path.exists(fname)
        fsize = get_filesize(fname)
        num_attempts += 1
        time.sleep(60)

ap = argparse.ArgumentParser()
ap.add_argument('-r', '--realtime', dest="realtime", help="Number of hours in the past")
ap.add_argument('-t', '--time-str', dest="time_str", help="YYYY-MM-DD/HH")
args = ap.parse_args()

if args.time_str is not None and not args.realtime:
    date_string = args.time_str
elif args.realtime:
    target_dt = datetime.utcnow() - timedelta(hours=int(args.realtime))
    date_string = target_dt.strftime('%Y-%m-%d/%H')

JSON_DIR = "%s/%s" % (JSON_DIR, date_string)
if not os.path.exists(JSON_DIR): os.makedirs(JSON_DIR)
#plot_obj = Plot()
#plot_obj.make_map(bounds=domains['MW'], counties=True)
#plot_obj.make_map(bounds=domains['MW'], counties=False)
#p = PlanView()
#proj = ccrs.PlateCarree()

fig = plt.figure()
ax = fig.add_subplot(111)

times = np.arange(0, 120+3, 3)
n_times = times.shape[0]

dir_= "%s/%s" % (DATA_DIR, date_string)
accum = {}
accum['3'] = np.zeros((n_perts, n_times, num_y, num_x))
accum['6'] = np.zeros((n_perts, n_times, num_y, num_x))
accum['12'] = np.zeros((n_perts, n_times, num_y, num_x))
accum['24'] = np.zeros((n_perts, n_times, num_y, num_x))
accum['48'] = np.zeros((n_perts, n_times, num_y, num_x))

snod = {}
snod['3'] = np.zeros((n_perts, n_times, num_y, num_x))
snod['total'] = np.zeros((n_perts, n_times, num_y, num_x))

winds = {}
winds['wspd10m'] = np.zeros((n_perts, n_times, num_y, num_x))
winds['wgust10m'] = np.zeros((n_perts, n_times, num_y, num_x))

for t in range(0, n_times):
    c1_objects = []
    p_knt = 0
    for pert in perts:
        fname = "%s/ge%s.t%sz.pgrb2s.0p25.f%s-reduced.grib2" % (dir_, pert,
                                                                date_string[-2:],
                                                                str(times[t]).zfill(3))
        check_for_file(fname)
        timestamp("[INFO]", fname)
        data = pygrib.open(fname)

        snow_depth = data.select(name="Snow depth")[-1]
        #u10 = data.select(name="10 metre U wind component")[-1]
        #v10 = data.select(name="10 metre V wind component")[-1]
        #wspd10 = np.sqrt(u10.values**2 + v10.values**2)
        wgust10 = data.select(name="Wind speed (gust)")[-1].values
        run_date = snow_depth.analDate

        # Derive 3-hourly precipitation at 6-hourly intervals (6, 12, 18, etc.)
        if t > 0:
            apcp = data.select(name="Total Precipitation")[-1]
            idx_start = str(apcp).index('fcst time') + 10
            idx_end = str(apcp).index('hrs') - 1
            delta_string = str(apcp)[idx_start:idx_end]
            idx = delta_string.index('-')
            delta = int(delta_string[idx+1:]) - int(delta_string[0:idx])

            if delta % 6 == 0:
                accum['3'][p_knt][t] = (apcp.values * MM2IN) - accum['3'][p_knt][t-1]
            else:
                accum['3'][p_knt][t] = apcp.values * MM2IN
            if t >= 1:
                accum['6'][p_knt][t] = np.sum(accum['3'][p_knt][t-1:t+1], axis=0)
            if t >= 2: accum['12'][p_knt][t] = np.sum(accum['3'][p_knt][t-2:t+1], axis=0)
            if t >= 4: accum['24'][p_knt][t] = np.sum(accum['3'][p_knt][t-4:t+1], axis=0)
            if t >= 8: accum['48'][p_knt][t] = np.sum(accum['3'][p_knt][t-8:t+1], axis=0)

        # Snow information
        snod['total'][p_knt][t] = snow_depth.values * M2IN

        # Kinematics
        #winds['wspd10m'][p_knt][t] = wspd10 * MS2KTS
        winds['wgust10m'][p_knt][t] = wgust10 * MS2KTS
        p_knt += 1
    time_str = str(int(times[t]))


    '''
    data = np.array(winds['wspd10m'])
    thresholds = [20, 25, 30, 35]
    for thresh in thresholds:
        sums = 0
        for pert in range(len(perts)):
            sums = np.where(data[pert,t]>=thresh, sums+1, sums)
        probs = (sums / float(len(perts))) * 100.
        save_name = "%s/wind_ge_%s.f%s.geojson" % (JSON_DIR, thresh, time_str)
        contourf = ax.contourf(lon, lat, probs, prob_levs)
        geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2,
                                           geojson_filepath=save_name)

        df = pd.DataFrame(columns=['problev', 'color'])
        with open(save_name) as f: geojson = json.load(f)
        knt = 0
        for feature in geojson['features']:
            geojson['features'][knt]['properties'] = {'problev': float(prob_levs[knt])}
            tmp = feature['properties']['problev']
            df.loc[knt] = [tmp, float(prob_levs[knt])]
            knt += 1
        df.to_csv(save_name + '.csv')
        with open(save_name, 'w') as f: json.dump(geojson, f)

    data = np.array(winds['wgust10m'])
    thresholds = [10, 30, 35, 39, 50]
    for thresh in thresholds:
        sums = 0
        for pert in range(len(perts)):
            sums = np.where(data[pert,t]>=thresh, sums+1, sums)
        probs = (sums / float(len(perts))) * 100.
        save_name = "%s/windgust_ge_%s.f%s.geojson" % (JSON_DIR, thresh, time_str)
        contourf = ax.contourf(lon, lat, probs, prob_levs)
        geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2,
                                           geojson_filepath=save_name)

        df = pd.DataFrame(columns=['problev', 'color'])
        with open(save_name) as f: geojson = json.load(f)
        knt = 0
        for feature in geojson['features']:
            geojson['features'][knt]['properties'] = {'problev': float(prob_levs[knt])}
            tmp = feature['properties']['problev']
            df.loc[knt] = [tmp, float(prob_levs[knt])]
            knt += 1
        df.to_csv(save_name + '.csv')
        with open(save_name, 'w') as f: json.dump(geojson, f)


    data = np.array(snod['total'])
    lpmm = tools.calc_LPMM(data[:,t], delta=5)
    plot_info = 'Snow Depth (in) localized (r=125 km) probability-matched mean'
    save_name = "%s/snod_total_lpmm.f%s.png" % (PLOT_DIR, time_str)
    p.plot_lpmm(lpmm, run_date, plot_info, time_str, save_name, plot_cols=snow_cols,
                 plot_levs=snow_levs)

    data = np.array(accum['3'])
    lpmm = tools.calc_LPMM(data[:,t])
    plot_info = '3-hour QPF (in) localized (r=125 km) probability-matched mean'
    save_name = "%s/qpf_03h_lpmm.f%s.png" % (PLOT_DIR, time_str)
    p.plot_lpmm(lpmm, run_date, plot_info, time_str, save_name)


    if t >= 1:
        data = np.array(accum['3'])
        lpmm = tools.calc_LPMM(data[:,t])
    else:
        lpmm = np.zeros((num_y, num_x))
    save_name = "%s/qpf_03h_lpmm.f%s" % (JSON_DIR, time_str)
    contourf = ax.contourf(lon, lat, lpmm, qpf_levs, colors=qpf_cols)
    tmp = geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2)
    geojson = json.loads(tmp)
    #for feature in range(len(geojson['features'])):
    #    geojson['features'][feature]['properties'] = {'member': 0, 'pert': 'c00'}
    with open(save_name, 'w') as f: json.dump(geojson, f)


    if t >= 2:
        data = np.array(accum['12'])
        lpmm = tools.calc_LPMM(data[:,t])
    else:
        lpmm = np.zeros((num_y, num_x))
    plot_info = '12-hour QPF (in) localized (r=125 km) probability-matched mean'
    save_name = "%s/qpf_12h_lpmm.f%s.geojson" % (JSON_DIR, time_str)
    contourf = ax.contourf(lon, lat, lpmm, qpf_levs)
    geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2,
                                       geojson_filepath=save_name)
    df = pd.DataFrame(columns=['problev', 'color'])
    with open(save_name) as f: geojson = json.load(f)
    knt = 0
    for feature in geojson['features']:
        geojson['features'][knt]['properties'] = {'problev': qpf_levs[knt]}
        tmp = feature['properties']['problev']
        df.loc[knt] = [tmp, qpf_levs[knt]]
        knt += 1
    df.to_csv(save_name + '.csv')
    with open(save_name, 'w') as f: json.dump(geojson, f)


    #for thresh in [0.01, 0.05, 0.10, 0.25, 0.5, 1., 2.]:
    for thresh in [0.01, 0.10, 0.25, 0.5, 1.]:
        save_name = "%s/qpf_06h_sp_%s.f%s" % (JSON_DIR, str(thresh), time_str)
        for i in range(n_perts):
            plot_data = accum['6'][i][t]
            contour = ax.contour(lon, lat, plot_data, [thresh])
            tmp = geojsoncontour.contour_to_geojson(contour=contour, ndigits=2)
            geojson = json.loads(tmp)
            for feature in range(len(geojson['features'])):
                geojson['features'][feature]['properties'] = {'member': i, 'pert': perts[i]}
            with open('%s-%s' % (save_name, i), 'w') as f: json.dump(geojson, f)
    '''


    # 3-hr precipitation
    if t >= 1:
        data = np.array(accum['3'])
        lpmm = tools.calc_LPMM(data[:,t])
    else:
        lpmm = np.zeros((num_y, num_x))
    save_name = "%s/qpf_03h_lpmm.f%s" % (JSON_DIR, time_str)
    contourf = ax.contourf(lon, lat, lpmm, qpf_levs, colors=qpf_cols)
    geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2, geojson_filepath=save_name)

    data = np.array(accum['3'])
    contourf = ax.contourf(lon, lat, np.max(data[:,t], axis=0), qpf_levs, colors=qpf_cols)
    save_name = "%s/qpf_03h_max.f%s" % (JSON_DIR, time_str)
    geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2, geojson_filepath=save_name)

    # 6-hr precipitatiom
    if t >= 1:
        data = np.array(accum['6'])
        lpmm = tools.calc_LPMM(data[:,t])
    else:
        lpmm = np.zeros((num_y, num_x))
    save_name = "%s/qpf_06h_lpmm.f%s" % (JSON_DIR, time_str)
    contourf = ax.contourf(lon, lat, lpmm, qpf_levs, colors=qpf_cols)
    geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2, geojson_filepath=save_name)

    data = np.array(accum['6'])
    contourf = ax.contourf(lon, lat, np.max(data[:,t], axis=0), qpf_levs, colors=qpf_cols)
    save_name = "%s/qpf_06h_max.f%s" % (JSON_DIR, time_str)
    geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2, geojson_filepath=save_name)

    # 12-hr precipitatiom
    if t >= 1:
        data = np.array(accum['12'])
        lpmm = tools.calc_LPMM(data[:,t])
    else:
        lpmm = np.zeros((num_y, num_x))
    save_name = "%s/qpf_12h_lpmm.f%s" % (JSON_DIR, time_str)
    contourf = ax.contourf(lon, lat, lpmm, qpf_levs, colors=qpf_cols)
    geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2, geojson_filepath=save_name)

    data = np.array(accum['12'])
    contourf = ax.contourf(lon, lat, np.max(data[:,t], axis=0), qpf_levs, colors=qpf_cols)
    save_name = "%s/qpf_12h_max.f%s" % (JSON_DIR, time_str)
    geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2, geojson_filepath=save_name)


    # Total snow depth
    data = np.array(snod['total'])
    lpmm = tools.calc_LPMM(data[:,t], delta=5)
    save_name = "%s/snod_total_lpmm.f%s" % (JSON_DIR, time_str)
    lpmm = np.where(lpmm >= 0.05, lpmm, np.nan)
    contourf = ax.contourf(lon, lat, lpmm, snow_levs, colors=snow_cols)
    geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2,
                                             geojson_filepath=save_name)
    #df = geopandas.read_file(save_name)
    #df_out = df.copy()
    #geojson = json.loads(tmp)
    #knt = 0
    #for feature in geojson['features']:
    #    feature['id'] = feature['properties']['title']
    #    feature['properties'] = {}
    #    feature['properties']['value'] = snow_levs[knt]
    #    knt += 1
    #geojson = json.loads(tmp)
    #for feature in geojson['features']:
    #for feature in range(len(json['features'])):
    #    feature['id'] = feature['properties']['title']
        #json['features'][feature]['id'] = json['features'][feature]['properties']['title']
        #geojson['features'][feature]['properties'] = {'member': 0, 'pert': 'c00'}
    #df_out['geometry'] = df.geometry.simplify(tolerance=0.1, preserve_topology=True)
    #with open(save_name, 'w') as f: json.dump(geojson, f)
    #if len(df_out) > 0: df_out.to_file(save_name, driver='GeoJSON')

    '''
    for thresh in [0.05, 0.10]:
        files_to_remove = []
        #save_name = "%s/qpf_03h_sp_%s.f%s" % (JSON_DIR, str(thresh), time_str)
        #df = []
        for i in range(n_perts):
            save_name = "%s/qpf_03h_sp_%s.f%s-%s" % (JSON_DIR, str(thresh), time_str, i)
            plot_data = accum['3'][i][t]
            contourf = ax.contourf(lon, lat, plot_data, [thresh,999999])
            geojsoncontour.contourf_to_geojson(contourf=contourf, ndigits=2, geojson_filepath=save_name)
            #arg = 'geobuf encode < %s > %s.pbf' % (save_name, save_name)
            #print(arg)
            #subprocess.call(arg, shell=True)
            #df['geometry'] = df.geometry.simplify(tolerance=0.1, preserve_topology=False)
            #df_out = df.copy()
            #df_out['geometry'] = df.geometry.simplify(tolerance=0.01, preserve_topology=False)
            #geojson = json.loads(tmp)
            #for feature in range(len(geojson['features'])):
            #    geojson['features'][feature]['properties'] = {'member': i, 'pert': perts[i]}
            #jsonfile = '%s-%s' % (save_name, i)
            #files_to_remove.append(save_name)
            #with open(jsonfile, 'w') as f: json.dump(geojson, f)
            #df = geopandas.read_file(jsonfile).append(df, ignore_index=True)
        #if len(pbf) > 0: pbf.to_file(save_name, driver='GeoJSON')
        #for f in files_to_remove: os.remove(f)

    for thresh in [0.01, 0.05, 0.10, 0.25, 0.5, 1., 3.]:
        plot_info = 'Total 6-hour precipitation >= %s"' % (thresh)
        save_name = "%s/qpf_06h_sp_%s.f%s.png" % (PLOT_DIR, str(thresh), time_str)
        p.plot_spag(accum['6'][:], t, thresh, run_date, plot_info,
                             save_name=save_name)
    '''
