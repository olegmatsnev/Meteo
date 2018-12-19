# this code is based on https://gist.github.com/phobson/41b41bdd157a2bcf6e14
# another source of inspiration: http://youarealegend.blogspot.com/2008/09/windrose.html

import pandas
import matplotlib.pyplot as plt
import numpy as np
import seaborn
seaborn.set_style("ticks")

filename = input('Enter path to the file: ')
data = pandas.read_csv(filename).filter(['Avg. wind speed', 'Wind direction'])
data.dropna(inplace=True)

calm_count = data[data['Avg. wind speed'] == 0].shape[0]
total_count = data.shape[0]

dir_labels = ['N1', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N2']


def speed_labels(bins, units):
    labels = []
    for left, right in zip(bins[:-1], bins[1:]):
        if left == bins[0]:
            labels.append('calm'.format(right))
        elif np.isinf(right):
            labels.append('>{} {}'.format(left, units))
        else:
            labels.append('{} - {} {}'.format(left, right, units))

    return list(labels)


spd_bins = [-1, 0, 1, 2, 3, 4, np.inf]  # if winds get stronger, additional values can be added to the list
spd_labels = speed_labels(spd_bins, units='m/s')

seg_lim = np.arange(-11.25, 372, 22.5)  # define limits of segments for each of 16 compass points

rose_data = (
    data.assign(Wind_speed_bins = lambda df: pandas.cut(df['Avg. wind speed'],  bins=spd_bins, labels=spd_labels, right=True)
                )
    .assign(Compass_points=lambda df: pandas.cut(df['Wind direction'], bins=seg_lim, labels=dir_labels, right=False)
            )
    .replace({'Compass_points': {'N1': 'N', 'N2': 'N'}})
    .groupby(by=['Compass_points', 'Wind_speed_bins'])
    .size()
    .unstack(level='Wind_speed_bins')
    .fillna(0)
    .assign(calm=lambda df: calm_count / df.shape[0])
    .sort_index(axis=1)
    .applymap(lambda x: x / total_count * 100)
)

barDir = np.arange(0, 360, 22.5) * np.pi/180. - np.pi/np.arange(0, 360, 22.5).shape[0] #central angle of each sector in radians
barWidth = 2 * np.pi / np.arange(0, 360, 22.5).shape[0]  # width of each sector in radians


# function that draws the wind rose:
def wind_rose(rosedata, bd, bw, palette=None):
    if palette is None:
        palette = seaborn.color_palette('binary', n_colors=rosedata.shape[1])

    fig, ax = plt.subplots(figsize=(20, 20), subplot_kw=dict(polar=True))
    ax.set_theta_direction('clockwise')
    ax.set_theta_zero_location('N')
    ax.set_axisbelow(False)  # puts grid and y-labels on top of the plot
    ax.yaxis.grid(color='black', linewidth=0.1)
    ax.xaxis.grid(alpha=0)  # makes the x-axis transparent since it's useless in this plot

    ax.bar(0, 0, width=0,  # dummy plot needed to add an explainer to the legend
           label='Radial coordinates represent % of time\nwhen wind blew from a given direction\nwithin a given speed range',
           color='None')

    for n, (c1, c2) in enumerate(zip(rosedata.columns[:-1], rosedata.columns[1:])):
        if n == 0:
            # first column only
            ax.bar(bd, rosedata[c1].values,
                   width=bw,
                   align='edge',  # each sector is centered on a corresponding compass point
                   color=palette[0],
                   edgecolor='none',
                   label=c1,
                   linewidth=0,
                   alpha=1)  # sets transparency level

        # all other columns
        ax.bar(bd, rosedata[c2].values,
               width=bw,
               bottom=rosedata.cumsum(axis=1)[c1].values,  # each segment is added on top of the previous one
               align='edge',
               color=palette[n + 1],
               edgecolor='none',
               label=c2,
               linewidth=0,
               alpha=1)

    ax.set_ylim(0, 13)
    ax.set_rgrids((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12))
    ax.set_rlabel_position(90)  # set radial ticks to a given angle in degrees
    ax.set_xticks(np.pi / 180 * np.arange(0, 360, 22.5))  # in radians
    ax.legend(loc=(0.05, 0.45), ncol=1)
    ax.set_xticklabels(
        ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'])

    return fig


fig = wind_rose(rose_data, barDir, barWidth)
fig.savefig(filename.split('\\')[::-1][0].split('.csv')[0] + '_wind_rose.png')

