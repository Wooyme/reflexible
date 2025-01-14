#!/usr/bin/env python
# -*- coding: utf-8 -*-
# John F Burkhart - 2010
# Licence : this code is released under the matplotlib license
""" Matplotlib Basemap Tool Suite """

from __future__ import print_function

import sys
import os
import os.path
import re

import yaml
import numpy as np
from PIL import Image

import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits import basemap

from reflexible import Structure

# mpl.use("Agg")
# mp.interactive(False)
# mpl.use('Agg')

__author__ = "John F Burkhart <jfburkhart@gmail.com>"
__version__ = "0.03"

from reflexible.wrapping import MyBaseMap


def map_regions(map_region='default', map_par=None, fig_par=None):
    """Given a `map_region`, return the associated parameters in mapping DB.

    USAGE::
        map_par, fig_par = map_regions(map_region="polarcat")

    The list of regions know by reflexible by default is located in the
    package file named 'mapping_db.yml'.  If you want to create a new region,
    or override an existing one in reflexible itself, you can create it in
    your own YAML file.  For example, suppose that you have the next
    'myregions.yml' file::

      northern_hemisphere:
        descr: Northern Hemisphere
        alias: my_own_nh
        map_par:
            projection: cyl
            llcrnrlat: 0.5
            urcrnrlat: 90
            llcrnrlon: -180.7
            urcrnrlon: 180
            resolution: c
            # anchor: W
        fig_par:
            figsize: [8, 3]  # w,h tuple
            axlocs: [0.1, 0.1, .7, .8]

    For informing reflexible on where your mapping file is located, you just
    create the REFLEXIBLE_MAPDB environment variable with its path::

      $ export REFLEXIBLE_MAPDB = $HOME/my_analysis/myregions.yml

    Since this moment on, the definitions in your file will be used (with
    highest priority) for finding the regions specified in `map_region`.

    Returns
      Two dictionaries, first a map_par dictionary with keywords that are the
      same as what is need to create a basemap instance of matplotlib:

      ============      ==========================
      keys              description
      ============      ==========================
      llcrnrlat         lower left latitude
      llcrnrlon         lower left longitude
      urcrnrlat         upper right latitude
      urcrnrlon         upper right longitude
      area_thresh       area threshold
      resolution        resolution
      projection        projection
      lat_1             lat_1
      lon_0             lon_0
      rsphere           (6378137.00,6356752.3142)
      m                 you can pass an m object
                        which is needed for some
                        regions
      ============      ==========================

      Second, a fig_par dictionary that contains options that may be passed to
      the :mod:`matplotlib.pyplot` :func:`figure` function:

      ============      ==========================
      keys              description
      ============      ==========================
      figsize           size of the figure
      axlocs            locations of the axes
      ============      ==========================

      .. note::
          You can override the returned map_par and fig_par dicts by passing
          dicts through the optional `map_par` and `fig_par` parameters.
    """
    # Set some default values
    map_par_ = Structure(anchor='C')
    fig_par_ = Structure(
        figsize=[8, 7],                 # w,h tuple
        axlocs = [0.05, 0.01, .8, .9],  # rect = l,b,w,h
    )

    # Get the database out of the system YAML file
    mapdb_file = os.path.join(os.path.dirname(__file__), 'mapping_db.yml')
    with open(mapdb_file) as mapdb:
        mapping_db = yaml.safe_load(mapdb)

    # and merge it with a possible one pointed by REFLEXIBLE_MAPDB env var
    if 'REFLEXIBLE_MAPDB' in os.environ:
        user_mapdb_file = os.environ['REFLEXIBLE_MAPDB']
        with open(user_mapdb_file) as mapdb:
            mapping_db.update(yaml.safe_load(mapdb))

    # Lookup the region and its aliases
    try:
        region = mapping_db[map_region]
    except KeyError:
        # Lookup aliases
        for key in mapping_db:
            if 'alias' in mapping_db[key]:
                alias = mapping_db[key]['alias']
                if map_region in re.split(r',\s*', alias):
                    region = mapping_db[key]
                    break
        else:
            raise KeyError("region {} not found".format(map_region))

    # Get the params
    map_par_.update(region['map_par'])         # map_par should be always there
    fig_par_.update(region.get('fig_par', {})) # fig_par not always present

    # Override params if `map_par` or `fig_par` are passed
    map_par_.update(map_par or {})
    fig_par_.update(fig_par or {})

    # Just in case
    map_par_.pop('m', None)

    return map_par_, fig_par_


def draw_grid(m, xdiv=10., ydiv=5., location=[1, 0, 0, 1],
              linewidth=0.5, color='k'):
    """
    draw parallels and meridians on a map.

    Currently draws labels on left, right and bottom of map.

    Keyword arguments:

        =========       ===========================
        keyword         description
        =========       ===========================
        xdiv            The division between lon
        ydiv            The division between lat
        location        Where to draw labels
        linewidth       Width of the grid lines.
        color           color of the grid lines
        =========       ===========================


    """
    # Label properties
    p_leg = mpl.font_manager.FontProperties(size='8')

    pd_options = [0.0001, 0.001, 0.01, 0.1, 0.2, 0.5, 1, 2.5, 5, 10, 20]
    md_options = [0.0001, 0.001, 0.01, 0.1, 0.2, 0.5, 1, 2.5, 5, 10, 20]

    xdiff = np.abs(m.urcrnrlon - m.llcrnrlon)
    ydiff = np.abs(m.urcrnrlat - m.llcrnrlat)

    if m.projection in ['npstere', 'spstere']:
        ydiff = 90. - np.abs(m.urcrnrlat)
        maxlat = 90.
    else:
        maxlat = None

    # setup map to have meridians:
    if xdiff > xdiv:
        md = np.round((xdiff / xdiv))
    else:
        md = np.round((xdiff / xdiv), 1)

    md = md_options[(np.abs(np.array(md_options) - md)).argmin()]
    # print(md)
    if m.projection in ['npstere', 'spstere']:
        meridians = np.arange(-180, 181, 20)
    else:
        meridians = np.arange(m.llcrnrlon, m.urcrnrlon, md)
    m_m = m.drawmeridians(meridians, labels=location,
                          linewidth=linewidth, color=color,
                          fontproperties=p_leg)

    # setup map to have parallels.
    if ydiff > ydiv:
        pd = np.round((ydiff / ydiv))
    else:
        pd = np.round((ydiff / ydiv), 2)
    if not maxlat:
        maxlat = m.urcrnrlat

    pd = pd_options[(np.abs(np.array(pd_options) - pd)).argmin()]
    if m.projection in ['npstere', 'spstere']:
        parallels = np.arange(30, 91, 10)
    else:
        if pd > 0.01:
            parallels = np.arange(np.round(m.llcrnrlat), maxlat, pd)
        else:
            parallels = np.arange(m.llcrnrlat, maxlat, pd)

    print(parallels, m.llcrnrlat, maxlat, pd)
    m_p = m.drawparallels(parallels, labels=location,
                          linewidth=linewidth, color=color,
                          fontproperties=p_leg)
    return m_p, m_m


def get_base_image(map_region='default', map_par=None, fig_par=None,
                   image=None, figname=None, fig=None, drawlsmask=False):
    """
    Primarily an internally used function, creates a basemap for plotting.
    Returns a fig object and a basemap instance.

    Examples::

      > fig, m = get_base_image(map_region="region_name")
      > fig, m = get_base_image(map_region="myregion", image=image)
    """

    # Use map_regions function to define input parameters for Basemap
    map_par, fig_par = map_regions(map_region, map_par, fig_par)

    # create the figure
    if fig is None:
        axlocs = fig_par.pop('axlocs')
        fig = plt.figure(**fig_par)
        ax = fig.add_axes(axlocs)
    else:
        ax = fig.gca()

    plt.axes(ax)  # make the original axes current again

    #m = basemap.Basemap(**map_par)
    m = MyBaseMap(**map_par)

    if image is None:
        # draw coastlines and political boundaries.
        m.drawcoastlines(linewidth=0.8)
        m.drawcountries(linewidth=0.2)
        m.drawstates(linewidth=0.2)
        if drawlsmask:
            m.drawlsmask(ocean_color='#008EBA', zorder=0)
        # draw parallels and meridians
        # use draw_grid function
        draw_grid(m)
    else:

        m.imshow(image)
        # draw coastlines.
        m.drawcoastlines(linewidth=0.5, color='0.5')
        if drawlsmask:
            m.drawlsmask(ocean_color='#008EBA', zorder=0)
        # draw parallels and meridians.
        draw_grid(m, linewidth=0.5, color='0.5')

    if figname is not None:
        plt.savefig(figname)
    return fig, m


if __name__ == '__main__':
    # Some tests for reading the mapping YAML database
    # map_regions(map_region='northern_hemisphere')
    get_base_image(map_region="world",drawlsmask=True)
    plt.show()
