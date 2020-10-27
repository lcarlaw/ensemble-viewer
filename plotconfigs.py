import pygrib
import matplotlib.pyplot as plt
import numpy as np

PLOT_DIR = "/Users/leecarlaw/Sites/images/"
DATA_DIR = '/Users/leecarlaw/model_data/GEFS/'
JSON_DIR = "/Users/leecarlaw/Sites/json"
perts = ['p'+str(i).zfill(2) for i in range(1,31)]
perts += ['c00']
MM2IN = 0.0393701
M2IN = 39.3701
MS2KTS = 1.94384

grb = pygrib.open('/Users/leecarlaw/scripts/gefs/gefs.grib2').select()[0]
lat, lon = grb.latlons()
lon = lon - 360.
n_perts = len(perts)
num_y, num_x = lon.shape

colors = plt.cm.PiYG(np.linspace(0, 1, n_perts))

styles = ['-', '-', ':', ':', '--', '--', '-', '-', ':', ':', '--', '--', '-', '-', ':']
styles += ['-', '-', ':', ':', '--', '--', '-', '-', ':', ':', '--', '--', '-', '-', ':']
styles += [':', ':']

qpf_cols = ['#bebebd','#a9a5a5','#838383','#6e6e6e','#b5fbab','#97f58d','#78f572',
            '#51f150','#1eb51e','#13a312','#1463d6','#2782ef','#50a5f5','#97d3fb',
            '#b5f0fb','#fffbab','#ffe978','#ffc13d','#ffa100','#ff6000','#ff3200',
            '#e11301','#c10100','#a50000','#860000','#643c32','#8c6459','#b78f85',
            '#c9a197','#f1ddd3','#cfc9df','#ada1c9','#9b89bd','#725ca3','#685293',
            '#760076','#8d018d','#b101b1','#c000c0','#db02db']
qpf_levs = [0.01,0.02,0.05,0.07,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.2,1.4,
            1.6,1.8,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,9,10,12,14,16,20]
#qpf_cols = ['#1d90ff','#000089','#018801','#228b22','#003800','#ffff00','#ffa500',
#            '#ff4500','#ff0000','#870a4d','#ff00ff','#da7046','#dda0dd']
#qpf_levs = [0.01,0.05,0.1,0.15,0.25,0.35,0.5,0.75,1,1.5,2,3,4,6]



snow_cols = ['#e1e1e1','#c8c8c8','#afafaf','#787878','#a5e0e0','#8bc1e1','#7daaf3',
             '#6488f5','#42529d','#36419b','#252e9d','#1e1ea1','#4b0082','#56098b',
             '#651294','#711c9d','#7c26a6','#8a2eaf','#9539b8','#a242c1','#ae4dca',
             '#ba55d3','#da70d6','#d662ca','#d454be','#d048b2','#cf39a5','#cc2c99',
             '#c91e8d','#c91b84','#ce3083','#d34281','#d85580','#dc697e','#e17c7c',
             '#e7907b','#eb9f83','#eead90','#f1ba9e','#f5c8ac','#f7d4ba','#fce3c7']
snow_levs = [0.1,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,11,12,13,
             14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30]
#snow_cols = snow_cols[::3]
#snow_levs = snow_levs[::3]

prob_cols = ['#989898','#656565','#4e4e4e','#3e4046','#2a3e83','#1c3dad','#023aff',
             '#0570fa','#0494f7','#02bcf4','#00e5f0','#70e78c','#b6ea4c','#ffe40b',
             '#fcbb07','#f66003','#f11704','#f87976','#f99d9b','#ffe6e5', '#ffffff']
prob_levs = np.arange(5,105,5)
