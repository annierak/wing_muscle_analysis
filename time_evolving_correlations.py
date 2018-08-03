from matplotlib import pyplot as plt
import numpy as np
import scipy
import flylib as flb
from flylib import util
import pandas as pd
import itertools
import time
import matplotlib.cm


fly_num = 1542

try:
    fly = flb.NetFly(fly_num,rootpath='/home/annie/imager/media/imager/FlyDataD/FlyDB/')
except(OSError):
    fly = flb.NetFly(fly_num)


# fly = flb.NetFly(1538,rootpath='/home/annie/work/programming/fly_muscle_data/')

flydf = fly.construct_dataframe()
# flydf = flydf[0:5000]
# print(flydf.columns.values)
muscle_cols = \
['iii1_left', 'iii3_left',
 'i1_left',  'i2_left',
 'hg1_left', 'hg2_left', 'hg3_left', 'hg4_left',
 'b1_left', 'b2_left', 'b3_left',
 'iii1_right', 'iii3_right',
 'i1_right', 'i2_right',
 'hg1_right', 'hg2_right', 'hg3_right', 'hg4_right',
 'b1_right', 'b2_right', 'b3_right' ]


groups_of_interest = ['hg','i']
filtered_muscle_cols = [
[muscle for muscle in muscle_cols if (
(group in muscle[0:len(group)]) and (muscle[len(group)+1]!='i'))]
for group in groups_of_interest]
group_lengths_list = [len(group_list) for group_list in filtered_muscle_cols]
num_groups = len(groups_of_interest)

filtered_muscle_cols = list(itertools.chain(*filtered_muscle_cols))
muscle_count = len(filtered_muscle_cols)



frames_per_step = 5
dt = frames_per_step*(flydf['t'][1]-flydf['t'][0])
window_size = 3
window_size = np.floor(window_size/dt)*dt
time.sleep(1)
t_stop = 10*60

# plt.figure(2)
# plt.plot(flydf['t'])
# plt.show()
# time.sleep(5)
# plt.show()
t = 0
counter = 0

time_window_inds = (flydf['t']>t)&(flydf['t']<=t+window_size)
muscle_matrix = np.array(flydf.loc[time_window_inds,filtered_muscle_cols]).T
print(np.shape(muscle_matrix))
steps_per_window = int(window_size/dt)

muscle_pair_array = util.prod_list(filtered_muscle_cols,square=True)

muscle_pair_list = util.symm_matrix_half(muscle_pair_array)
group_index_list = [length*[index] for index,length in enumerate(group_lengths_list) ]

colormap1= matplotlib.cm.get_cmap('RdYlBu_r')
# colormap2 = matplotlib.cm.get_cmap('Dark2')
colormap2 = ['blue', 'orange', 'green', 'red',
 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
num_colors = (num_groups*(num_groups+1)/2)
color_list = np.zeros(np.shape(muscle_pair_list)[0]).astype(int)

group_pair_list = util.prod_list(groups_of_interest)
print(group_pair_list)

for ind,pair in enumerate(muscle_pair_list):
    chopped_pair = tuple(util.muscle_group(pair))
    try:
        color = group_pair_list.index(chopped_pair)
    except(ValueError):
        color = group_pair_list.index((chopped_pair[1],chopped_pair[0]))
    color_list[ind] = int(color)


#Test the muscle pair colors
# for i,color in enumerate(color_list):
#     if color==3:
#         print(muscle_pair_list[i])


plt.ion()
ax1 = plt.subplot(1,2,1)
# fig.canvas.flush_events()
title_text =plt.title(' ')

corr_values_by_t = np.zeros((muscle_count*(muscle_count+1)/2-muscle_count,steps_per_window))
lines = plt.plot(corr_values_by_t.T)
for ind,line in enumerate(lines):
    line.set_color(colormap2[color_list[ind]])
plt.ylim([-160,180])
ax2 = plt.subplot(1,2,2)
image = plt.imshow(np.zeros((22,22)),vmin=-150,vmax=150,interpolation='none',
cmap=colormap1)
# ax3 = plt.subplot(3,1,3)
# n,bins,_ = plt.hist(np.zeros(22*22))
# raw_input('--')

while t<t_stop:
    # print(t)
    time_window_inds = (flydf['t']>t)&(flydf['t']<=t+window_size)
    state_mtrx = np.array(flydf.loc[time_window_inds,filtered_muscle_cols]).T
    text = flydf.iloc[counter]['stimulus']
    ax1.set_title(text)
    # time.sleep(5)

    #Watch out for muscles that have no activity
    off_muscle_inds = (np.sum(state_mtrx,axis=1)==0.)
    # Set them to a very small amt of activity so nan's are not created
    state_mtrx[off_muscle_inds] = 1e-8
    # print(state_mtrx[4,1:50])
    centered_mtrx = state_mtrx - np.mean(state_mtrx,axis = 1)[:,None]
    # print(np.std(centered_mtrx,axis = 1))
    std_mtrx = centered_mtrx/np.std(centered_mtrx,axis = 1)[:,None]
    # print(std_mtrx[np.isnan(std_mtrx)])
    cor_mtrx = np.dot(std_mtrx,std_mtrx.T)

    image.set_data(cor_mtrx)
    # ax3.cla()
    # print(np.unique((cor_mtrx.flatten())))
    # plt.hist((cor_mtrx.flatten()))

    corr_values = util.symm_matrix_half(cor_mtrx)

    if counter<steps_per_window:
        corr_values_by_t[:,counter] = corr_values
    else:
        # print('past starting phase')
        corr_values_by_t[:,:-1] = corr_values_by_t[:,1:]
        corr_values_by_t[:,-1] = corr_values
        x_values = np.linspace(t,t+window_size,steps_per_window)
        ax1.set_xlim((t,t+window_size))
        for row,line in enumerate(lines):
            line.set_ydata(corr_values_by_t[row,:])
            line.set_xdata(x_values)
            line.set_color(colormap2[color_list[row]])
    plt.draw()
    plt.pause(0.001)
    t+=dt
    counter+=1
