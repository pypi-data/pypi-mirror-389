#!/usr/bin/env python
"""EIS as-run catalog search PyQt5 gui.

A python gui to search the EIS as-run catalog. The intention is to
be somewhat like the IDL routine eis_cat.pro, but with fewer
features, at least initially. Very much a work in progress.

(2017-Apr-12) First working version added to git.
(2020-Dec-16) Now tries to find SSW if the 'SSW' environment variable is missing
(2020-Dec-18) If no database is found, ask the user if they want to download it.
(2021-Oct-22) Major update adding in more search criteria and faster queries.
(2023-Jul-11) Added data mirrors for eis_cat.sqlite and HDF5 files
(2023-Sep-23) Added viewing context images from MSSL
(2024-May-07) Removed PyQt4 support, cleaned-up code and fixed a search bug
(2025-Oct-23) Added viewing thumbnail images from MSSL
(2025-Oct-24) Added viewing thumbnail images from OSLO
"""
__all__ = ['eis_catalog']

import sys
import time
import os
import copy
import pathlib
import argparse
import urllib
import ssl
import certifi
import sqlite3
from datetime import datetime, timedelta
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui, QtNetwork
from eispac.db.eisasrun import EISAsRun
from eispac.db.download_hdf5_data import download_hdf5_data
from eispac.db.download_db import download_db

import sunpy.map
from sunpy.coordinates import frames, get_earth
from sunpy.coordinates.utils import get_limb_coordinates


try:
    # Newer version of matplotlib (has support for Qt6)
    from matplotlib.backends.backend_qtagg import FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
except:
    # Fallback imports (should still work in newer version of matplotlib)
    from matplotlib.backends.backend_qt5agg import FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.backend_bases import MouseButton
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
# from matplotlib.ticker import FormatStrFormatter

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.visualization import ImageNormalize, AsinhStretch, LinearStretch
# from astropy.wcs.utils import wcs_to_celestial_frame

def get_remote_image_dir(filename, source='MSSL'):
    """Parse a Level-0 filename and get the remote image dir"""
    # Note: level-0 files have the form, eis_l0_YYYYMMDD_hhmmss.fits
    date_str = filename.split('_')[2]
    year_str = date_str[0:4]
    month_str = date_str[4:6]
    day_str = date_str[6:8]

    # Assemble and return the URL
    if source.upper() == 'MSSL':
        file_dir = year_str+'/'+month_str+'/'+day_str+'/'+filename+'/'
        base_url = 'https://solarb.mssl.ucl.ac.uk/SolarB/DEV/eis_gifs/'
    elif source.upper() == 'OSLO':
        # Note: OSLO assumes that the filename does NOT end in ".fits"
        shorter_name = filename.replace('.fits', '')
        file_dir = year_str+'/'+month_str+'/'+day_str+'/'+shorter_name+'/'
        base_url = 'https://sdc.uio.no/vol/icons/eis/level0/'
    
    return base_url + file_dir

def get_aia_synoptic_url(filename, wavelength=171):
    """Parse a Level-0 filename and get nearest matching AIA synoptic image"""
    # Note: level-0 files have the form, eis_l0_YYYYMMDD_hhmmss.fits
    # Note: the jsoc AIA files have the form AIA20250222_2222_0171.fits
    date_str = filename.split('_')[2]
    year_str = date_str[0:4]
    month_str = date_str[4:6]
    day_str = date_str[6:8]

    time_str = filename.split('_')[3]
    hour_str = time_str[0:2]
    min_str = time_str[2:4]

    # The AIA data has a 2 min cad, therefore we round DOWN to nearest even min
    lower_min = f"{2*int(int(min_str)/2):02}"

    # wavelength must be 94, 131, 171, 193, 211, 304, 335, 1600, or 4500
    wave_str = f"{wavelength:04}"

    filename = f"AIA{year_str}{month_str}{day_str}_{hour_str}{lower_min}_{wave_str}.fits"
    file_dir = f"{year_str}/{month_str}/{day_str}/H{hour_str}00/{filename}"
    base_url = 'https://jsoc1.stanford.edu/data/aia/synoptic/'
    
    return base_url + file_dir

def convert_ll_title_to_line_id(ll_title):
    """Convert an as-run window ID to a standardized line ID"""
    # e.g. FeXII 195.12 converts to  Fe_XII_195.120

    if ll_title is None or len(ll_title) < 2:
        # Return an empty string for empty or invalid IDs
        return "" 
    
    title_split = ll_title.split(None)
    ion = title_split[0]
    wave = title_split[-1]

    odd_list = ['FeVIIIXII', 'FeXIIX', 'FeXXIVetc', 'FeXXI',
                'FeXIVMgVI', 'CaXVIIOV', 'XVIXXIII', 'MgVIFe']
    odd_split_ind = [6, 4, 6, 3, 
                     5, 6, 3, 4]
    if ion in odd_list:
        # First, check for strange and malformed line IDs
        split_ind = odd_split_ind[odd_list.index(ion)]
        elem = ion[:split_ind]
        charge = ion[split_ind:]
    elif ion[1] in ['I', 'V', 'X']:
        # Single character element (e.g. "O" or "S")
        elem = ion[0]
        charge = ion[1:]
    elif ion[2] in ['I', 'V', 'X']:
        # Two character element (e.g. "Fe" or "Mg")
        elem = ion[:2]
        charge = ion[2:]
    elif ion.startswith('CCD') or ion.startswith('ccd'):
        # Full CCD window
        elem = ion[:-1]
        charge = '0'
    elif len(title_split) > 2:
        # title already had a space
        elem = ion
        charge = title_split[1]
    else:
        # Placeholder for anything that does not fit above
        elem = ion
        charge = 'M'

    return f"{elem}_{charge}_{float(wave):7.3f}"

class Top(QtWidgets.QWidget):

    def __init__(self, cat_filepath, parent=None):
        super(Top, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.file_list = None
        self.date_obs_list = None
        self.result_ind_list = None
        self.selected_file = None
        self.selected_date_obs = None
        self.selected_result = None
        self.selected_info = []
        self.default_filename = 'eis_filelist.txt'
        self.default_start_time = '2018-05-29 00:00' # '29-May-2018 00:00'
        self.default_end_time = '2018-05-29 23:59' # '29-May-2018 23:59'
        self.default_button_width = 150 #165 #130
        self.default_topdir = os.path.join(os.getcwd(), 'data_eis')
        self.dbfile = str(pathlib.Path(cat_filepath).resolve())
        self.db_loaded = False

        # Image settings
        self.context_eis_file = None
        self.context_imgNX = 768 #512
        self.context_imgNY = 768 #512
        self.thumb_eis_file = None
        self.num_thumb_cols = 5
        self.thumb_imgNX = 130
        self.thumb_imgNY = 130
        self.thumb_dialog = None
        self.thumb_dialog_iwin = None
        self.aia_eis_file = None
        self.aia_fits = str(pathlib.Path.home() / 'eis_catalog_temp_aia.fits')
        self.aia_click = None

        # Font settings
        self.default_font = QtGui.QFont()
        self.small_font = QtGui.QFont()
        self.info_detail_font = QtGui.QFont("Courier New", 9)
        self.default_font.setPointSize(11)
        self.small_font.setPointSize(9)

        # Dict of search criteria to include as options in the drop-down list
        # Note: the keys:value pairs give the mapping of gui_label:sqlite_col
        self.criteria = {'Date Only':'date_obs', 'Study ID':'study_id',
                         'Study Acronym':'stud_acr', 'HOP ID':'jop_id',
                         'Obs. Title':'obstitle',
                         'Raster ID':'rast_id', 'Raster Acr.':'rast_acr',
                         'Triggered Obs':None,
                         'Target':'target', 'Science Obj.':'sci_obj',
                         'Timeline ID':'tl_id'}
        # Filter drop-down lists. given as gui_label:filter_value pairs
        self.rast_types = {'Any':None, 'Scan (0)':0, 'Sit-and-Stare (1)':1}
        self.slit_slot = {'Any':None, 'Slit only (0 & 2)':[0,2],
                          '1" slit (0)':[0], '2" slit (2)':[2],
                          'Slot only (3 & 1)':[3,1],
                          '40" slot (3)':[3], '266" slot (1)':[1]}

        self.rtype_dict = {0:'0 (scan)', 1:'1 (sit-and-stare)'}
        self.sindex_dict = {0:'0 (1" slit)', 2:'2 (2" slit)',
                            3:'3 (40" slot)', 1:'1 (266" slot)'}
        
        # Load EIS as-run catalog (will also search other common dirs)
        if os.path.isfile(self.dbfile) or os.path.isdir(self.dbfile):
            self.d = EISAsRun(self.dbfile)
            if self.d.cat_filepath is not None:
                self.db_loaded = True
                self.dbfile = str(pathlib.Path(self.d.cat_filepath).resolve())
        
        if self.db_loaded == False:
            # Ask if the user wants to download a copy of the database
            ask_db = QtWidgets.QMessageBox.question(self, 'Missing eis_cat.sqlite',
                        'No EIS as-run catalog found.\n'
                        'Would you like to download a copy to your home directory?',
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if ask_db == QtWidgets.QMessageBox.Yes:
                # Default to downloading from NRL and, if that fails, try NASA
                # Will download to the user home dir
                try:
                    self.dbfile = download_db()
                except:
                    self.dbfile = download_db(source='NASA')
                if not str(self.dbfile).endswith('.part'):
                    self.d = EISAsRun(self.dbfile)
                    self.db_loaded = True
                    self.dbfile = str(pathlib.Path(self.d.cat_filepath).resolve())
                else:
                    print('Failed to download EIS database!')
            else:
                print('ERROR: No EIS as-run database found!')

        # Initialze the network manager for downloading images
        self.manager = QtNetwork.QNetworkAccessManager()
        self.manager.finished.connect(self.finished_context_download)

        self.thumb_manager = QtNetwork.QNetworkAccessManager()
        self.thumb_manager.finished.connect(self.finished_thumb_download)

        self.init_ui()

    def init_ui(self):
        """Manage everything."""
        self.grid = QtWidgets.QGridLayout(self)
        self.gui_row = 0
        # self.setStyleSheet("QLabel{font-size: 11pt;}")

        # Quit & Update DB buttons (with filename & timestamp)
        self.top_menu() # very top

        # Selecting search criteria
        self.select_dates() # top left
        self.select_primary() # top center

        # Filter values
        self.set_filters() # top center

        # Catalog info
        self.catalog_table() # middle left

        # Info for a single search result
        self.details() # right

        # Bottom stuff
        self.save_options() # bottom left

        # And away we go
        self.setLayout(self.grid)
        self.setGeometry(50, 100, 1800, 800) #(50, 100, 1800, 800)
        self.setWindowTitle('EIS As-Run Catalog Information')
        self.event_help()
        self.show()

    def event_quit(self):
        QtWidgets.QApplication.instance().quit()

    def top_menu(self):
        """Basic menu option."""
        self.quit = QtWidgets.QPushButton('Quit')
        self.quit.setFixedWidth(self.default_button_width)
        self.quit.setFont(self.default_font)
        self.quit.clicked.connect(self.event_quit)

        self.download_db = QtWidgets.QPushButton('Update Database', self)
        self.download_db.setFixedWidth(self.default_button_width)
        self.download_db.setFont(self.default_font)
        self.download_db.clicked.connect(self.event_download_db)

        self.db_source_box = QtWidgets.QComboBox()
        self.db_source_box.addItems(['NRL (source)', 'NASA (mirror)'])
        self.db_source_box.setFixedWidth(self.default_button_width) # or 150
        self.db_source_box.setFont(self.default_font)

        self.db_info = QtWidgets.QLabel(self)
        self.db_info.setFixedWidth(4*self.default_button_width)
        self.db_info.setFont(self.small_font)
        self.update_db_file_label()

        self.grid.addWidget(self.quit, self.gui_row, 0)
        self.grid.addWidget(self.download_db, self.gui_row, 1)
        self.grid.addWidget(self.db_source_box, self.gui_row, 2)
        self.grid.addWidget(self.db_info, self.gui_row, 3, 1, 4)

        self.gui_row += 1

    def update_db_file_label(self):
        if os.path.isfile(self.dbfile):
            t = 'DB file: '+os.path.abspath(self.dbfile)+'\nDownload date: '+ \
                    time.ctime(os.path.getmtime(self.dbfile)).lstrip().rstrip()
        else:
            t = 'Unable to locate DB: ' + self.dbfile
        self.db_info.setText(t)

    def event_download_db(self):
        self.tabs.setCurrentIndex(0) #switch to details tab
        self.info_detail.clear()
        self.table_m.clearContents()
        self.table_m.setRowCount(1)
        db_source = self.db_source_box.currentText()
        if db_source.lower().startswith('nrl'):
            db_remote_text = f'https://eis.nrl.navy.mil/level1/db/eis_cat.sqlite'
        else:
            db_remote_text = f'https://hesperia.gsfc.nasa.gov/ssw/hinode/eis' \
                            +f'/database/catalog/eis_cat.sqlite'
        info = (f'Downloading eis_cat.sqlite.\n'
                f'   Remote: {db_remote_text}\n'
                f'   Local: {os.path.abspath(self.dbfile)}\n\n'
                f'Please wait (see console for download progress)...')
        self.info_detail.append(info)
        QtWidgets.QApplication.processEvents() # update gui while user waits
        if self.db_loaded:
            self.d.cur.close()
            self.d.conn.close()
        self.d = 0
        self.dbfile = download_db(os.path.dirname(self.dbfile), source=db_source)
        if self.dbfile.endswith('.part'):
            self.info_detail.append('\nERROR: Database download failed! '
                                    +'Please check your internet connection '
                                    +' or try a different source.')
        else:
            self.d = EISAsRun(self.dbfile)
            self.update_db_file_label()
            self.info_detail.append('\nComplete')
            self.db_loaded = True

    def event_help(self):
        """Put help info in details window."""
        self.info_help.clear()
        help_text = """### Searching for Obervations

* If only the start date is provided, the end will be set for 24 hours later.
  WARNING: "Date Only" searches over the entire mission can take a VERY long 
  time, please be patient.

* Primary search criteria descriptions (with catalog column names):

  Study ID (study_id)
      ID number for specific observation plan (e.g. line list & rasters). 
      Studies may repeated throughout the mission.

  Study Acronym (stud_acr)
      Short text label for the study. You only need to input a few characters 
      (case is ignored).

  HOP ID (jop_id)
      Hinode Operation Plan ID. Assigned to observations that were coordinated 
      with other telescopes or spacecraft missions. 
      Also known as "JOP ID" (Joint Obs. Program ID)

  Obs. Title (obstitle)
      Observation title. Just a word or two is enough, results will be shown 
      for all titles containing the input text.

  Raster ID (rast_id) and Raster Acr. (rast_acr)
      ID number and short text label for the raster program used in the study. 
      Rasters may be shared by multiple studies.
      
  Triggered Obs
      Any raster run in response to an on-board trigger. There are three 
      triggers that can be run: XRT flare (tl_id=1), EIS flare (tl_id=3), 
      & EIS bright point (tl_id=4). 
      Selecting this the same as using Timeline ID = 1, 3, 4 

  Target (target)
      Main observation target (e.g., Active Region, Quiet Sun).

  Science Obj. (sci_obj)
      Target phenomena (e.g., AR, QS, BP, LMB)
  
  Timeline ID (tl_id)
      ID number for a unique set of contiguous observations. This
      could be a single raster or a set of multiple rasters run in
      sequence. Timeline IDs of 1, 3, & 4 are special (see above), 
      all other values should be unique over the life of EIS.

* Multiple ID numbers may be searched at the same time by separating
  the numbers with "," (e.g. "1, 3, 4"). Ranges of numbers can be 
  searched by separating the start & end values with "-" (e.g. "1-4")

* If "Target" and "Science Obj." are not defined by the EIS planner, 
  default values are assigned based on the orginal study use case.

### Downloading files

* If the "Use Date Tree" box is checked, files will be downloaded into 
  subdirectories organized by date (../YYYY/MM/DD/)
"""
        self.info_help.append(help_text)
        self.info_help.verticalScrollBar().setValue(
                                self.info_help.verticalScrollBar().minimum())

    def select_dates(self):
        """Set time range and make button for running the search"""
        title = QtWidgets.QLabel(self)
        title.setText('Date Range [start, end)')
        title.setFont(self.default_font)
        self.grid.addWidget(title, self.gui_row, 0, 1, 2)
        self.gui_row += 1

        start_t = QtWidgets.QLabel(self)
        start_t.setText('Start')
        start_t.setFont(self.default_font)
        self.start_time = QtWidgets.QLineEdit(self)
        self.start_time.setFixedWidth(self.default_button_width)
        self.start_time.setText(self.default_start_time)
        self.start_time.setFont(self.default_font)
        self.grid.addWidget(start_t, self.gui_row, 0)
        self.grid.addWidget(self.start_time, self.gui_row, 1)
        self.gui_row += 1

        end_t = QtWidgets.QLabel(self)
        end_t.setText('End (or # days)')
        end_t.setFont(self.default_font)
        self.end_time = QtWidgets.QLineEdit(self)
        self.end_time.setFixedWidth(self.default_button_width)
        self.end_time.setText(self.default_end_time)
        self.end_time.setFont(self.default_font)
        self.grid.addWidget(end_t, self.gui_row, 0)
        self.grid.addWidget(self.end_time, self.gui_row, 1)
        self.gui_row += 1

        time_recent = QtWidgets.QPushButton('Last 3 Weeks', self)
        time_recent.setFixedWidth(self.default_button_width)
        time_recent.setFont(self.default_font)
        self.grid.addWidget(time_recent, self.gui_row, 0, 1, 6)
        time_recent.clicked.connect(self.event_time_recent)

        time_mission = QtWidgets.QPushButton('Full Mission', self)
        time_mission.setFixedWidth(self.default_button_width)
        time_mission.setFont(self.default_font)
        self.grid.addWidget(time_mission, self.gui_row, 1, 1, 5)
        time_mission.clicked.connect(self.event_time_mission)
        self.gui_row += 1

        search_start = QtWidgets.QPushButton('Search', self)
        search_start.setFixedWidth(self.default_button_width)
        search_start.setFont(self.default_font)
        self.grid.addWidget(search_start, self.gui_row, 0, 1, 6)
        search_start.clicked.connect(self.event_search)

        self.gui_row -= 4

    def event_time_recent(self):
        end_time = datetime.now()
        start_time = end_time - timedelta(weeks=3)
        start_time_s = start_time.strftime('%Y-%m-%d 00:00')
        end_time_s = end_time.strftime('%Y-%m-%d 23:59')
        self.start_time.setText(start_time_s)
        self.end_time.setText(end_time_s)

    def event_time_mission(self):
        start_time_s = '2006-10-21 00:00'
        end_time_s = datetime.now().strftime('%Y-%m-%d 23:59')
        self.start_time.setText(start_time_s)
        self.end_time.setText(end_time_s)

    def select_primary(self):
        """Set primary search criterion"""
        title = QtWidgets.QLabel(self)
        title.setText('Primary Search Criteria')
        title.setAlignment(QtCore.Qt.AlignBottom)
        title.setFont(self.default_font)
        self.primary_box = QtWidgets.QComboBox()
        self.primary_box.addItems([item for item in self.criteria.keys()])
        self.primary_box.setFixedWidth(self.default_button_width) # or 150
        self.primary_box.setFont(self.default_font)
        self.primary_text = QtWidgets.QLineEdit(self)
        self.primary_text.setFont(self.default_font)

        self.grid.addWidget(title, self.gui_row, 2, 1, 2)
        self.gui_row += 1
        self.grid.addWidget(self.primary_box, self.gui_row, 2)
        self.grid.addWidget(self.primary_text, self.gui_row, 3, 1, 3)

        # Advance gui row as needed
        self.gui_row += 1

    def set_filters(self):
        """Set search result filters"""
        title = QtWidgets.QLabel(self)
        title.setText('Result Filters')
        title.setAlignment(QtCore.Qt.AlignBottom)
        title.setFont(self.default_font)

        rast_type_title = QtWidgets.QLabel(self)
        rast_type_title.setText('Raster Type (#)')
        rast_type_title.setFont(self.default_font)
        self.rast_type_box = QtWidgets.QComboBox()
        self.rast_type_box.addItems([item for item in self.rast_types.keys()])
        self.rast_type_box.setFixedWidth(self.default_button_width) # or 150
        self.rast_type_box.setFont(self.default_font)

        slit_slot_title = QtWidgets.QLabel(self)
        slit_slot_title.setText('Slit/Slot (slit_index)')
        slit_slot_title.setFont(self.default_font)
        self.slit_slot_box = QtWidgets.QComboBox()
        self.slit_slot_box.addItems([item for item in self.slit_slot.keys()])
        self.slit_slot_box.setFixedWidth(self.default_button_width) # or 150
        self.slit_slot_box.setFont(self.default_font)

        wave_title = QtWidgets.QLabel(self)
        wave_title.setText(u'Wavelength(s) [\u212B]')
        wave_title.setFont(self.default_font)
        self.wave_text = QtWidgets.QLineEdit(self)
        self.wave_text.setFixedWidth(self.default_button_width) # or 150
        self.wave_text.setFont(self.default_font)

        apply_filter = QtWidgets.QPushButton('Apply Filters', self)
        apply_filter.setFixedWidth(self.default_button_width)
        apply_filter.setFont(self.default_font)
        apply_filter.clicked.connect(self.event_apply_filter)

        clear_filter = QtWidgets.QPushButton('Clear Filters', self)
        clear_filter.setFixedWidth(self.default_button_width)
        clear_filter.setFont(self.default_font)
        clear_filter.clicked.connect(self.event_clear_filter)

        self.grid.addWidget(title, self.gui_row, 2, 1, 2)
        self.gui_row += 1
        self.grid.addWidget(clear_filter, self.gui_row, 2)
        self.grid.addWidget(rast_type_title, self.gui_row, 3)
        self.grid.addWidget(slit_slot_title, self.gui_row, 4)
        self.grid.addWidget(wave_title, self.gui_row, 5)
        self.gui_row += 1
        self.grid.addWidget(apply_filter, self.gui_row, 2)
        self.grid.addWidget(self.rast_type_box, self.gui_row, 3)
        self.grid.addWidget(self.slit_slot_box, self.gui_row, 4)
        self.grid.addWidget(self.wave_text, self.gui_row, 5)

        # Advance gui row as needed
        self.gui_row += 1

    def event_search(self):
        """Validate and process search request."""
        self.tabs.setCurrentIndex(0) #switch to details tab
        self.info_detail.clear()
        self.search_info.setText('Found ?? search results')
        self.filter_info.setText('Showing ?? filter matches')
        self.table_m.clearContents()
        self.table_m.setRowCount(1)
        if self.db_loaded == False:
            self.info_detail.setText('No EIS As-Run Catalog found!\n\n'
                                    +'Please use the "Update Database" '
                                    +'button above.')
            return
        else:
            self.info_detail.setText('Searching catalog. Please wait...')
        QtWidgets.QApplication.processEvents() # update gui while user waits

        # Get dates and user input text
        start_time = str(self.start_time.text())
        end_time = str(self.end_time.text())
        primary_key = str(self.primary_box.currentText())
        primary_value = str(self.primary_text.text())

        try:
            if self.criteria[primary_key] == 'date_obs':
                self.d.search(date=[start_time, end_time], noreturn=True)
            elif primary_key.lower().startswith('trigger'):
                # EIS triggered studies (1=XRT flare, 3=EIS flare, 4=EIS BP)
                search_kwargs = {'date':[start_time, end_time]}
                search_kwargs['tl_id'] = ['1', '3', '4']
                self.d.search(**search_kwargs, noreturn=True)
            else:
                search_kwargs = {'date':[start_time, end_time]}
                search_kwargs[self.criteria[primary_key]] = primary_value
                self.d.search(**search_kwargs, noreturn=True)
        except:
            self.file_list = []
            self.date_obs_list = []
            self.result_ind_list = []
            self.table_info = [(None, None, None, None, None, None,
                                None, None, None, None, None, None)]
            self.count_results = 0
            self.search_info.setText('Found ? search results')
            self.filter_info.setText('Showing ? filter matches')
            self.info_detail.append('\nERROR: invalid search paramaters and/or'
                                   +' malformed database entry.')
            self.info_detail.append('\nPlease check the inputs and try again')
            return

        # Clear / reset vars used to control the display
        self.selected_file = None
        self.selected_date_obs = None
        self.selected_result = None
        self.selected_result_ind = None
        self.context_eis_file = None
        self.thumb_eis_file = None
        self.thumb_pixmap = [None]*25
        self.thumb_line_ids = [None]*25
        self.thumb_dialog_iwin = None
        self.aia_eis_file = None
        if self.thumb_dialog is not None:
            self.thumb_dialog.clear_image()
        
        if len(self.d.eis_str) > 0:
            info = []
            i = 0
            for row in self.d.eis_str:
                info.append([row.date_obs, row.study_id, row.stud_acr,
                             row.obstitle, row.xcen, row.ycen,
                             row.filename, row.tl_id, row.rastertype,
                             row.slit_index, row.wavemin, row.wavemax])
            info.sort(key=lambda x: x[6]) # sort by filename
            self.count_results = len(info)
            self.search_info.setText('Found '+str(len(info))+' search results')
            self.info_detail.append('Search complete!')
            self.info_detail.append('\nSelect a search result to view observation'
                                   +' details')
            self.table_info = info
            self.mk_table(info)
        else:
            self.file_list = []
            self.date_obs_list = []
            self.result_ind_list = []
            self.table_info = [(None, None, None, None, None, None,
                                None, None, None, None, None, None)]
            self.count_results = 0
            self.search_info.setText('Found 0 search results')
            self.filter_info.setText('Showing 0 filter matches')
            self.info_detail.clear()
            self.info_detail.append('No entries found')

    def catalog_table(self):
        """Table with summary of search results"""
        self.search_info = QtWidgets.QLabel(self)
        self.search_info.setText('Found ?? search results')
        self.search_info.setFont(self.default_font)
        self.grid.addWidget(self.search_info, self.gui_row, 0, 1, 2)

        self.filter_info = QtWidgets.QLabel(self)
        self.filter_info.setText('Showing ?? filter matches')
        self.filter_info.setFont(self.default_font)
        self.grid.addWidget(self.filter_info, self.gui_row, 2, 1, 2)
        self.gui_row += 1

        headers = ['Date Observed', 'Study ID', 'Study Acronym',
                   'Obs. Title', 'Xcen', 'Ycen']
        widths = [160, 60, 160, 300, 60, 60] #[180, 80, 180, 350, 80, 80]

        self.table_m = QtWidgets.QTableWidget(self)
        self.table_m.verticalHeader().setVisible(False)
        self.table_m.setRowCount(1)
        self.table_m.setColumnCount(len(headers))
        self.table_m.setItem(0, 0, QtWidgets.QTableWidgetItem(' '))
        self.table_m.setHorizontalHeaderLabels(headers)
        for i in range(len(headers)):
            self.table_m.setColumnWidth(i, widths[i])
        self.table_m.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.grid.addWidget(self.table_m, self.gui_row, 0, 1, 6)
        self.grid.setRowStretch(self.gui_row, 1)
        self.gui_row += 1

    def mk_table(self, info):
        """Add entries to the results table."""
        len_info = len(info)
        self.file_list = []
        self.date_obs_list = []
        self.result_ind_list = []
        self.table_m.clearContents()
        self.table_m.setRowCount(1)
        r_type = self.rast_types[self.rast_type_box.currentText()]
        s_index = self.slit_slot[self.slit_slot_box.currentText()]
        wave_list = list(str(self.wave_text.text()).strip().split(','))
        self.count_filtered = 0
        for row in range(len_info):
            # Apply result filters (raster type, slit index, wavelengths)
            if r_type is not None and int(info[row][8]) != r_type:
                continue
            elif s_index is not None and int(info[row][9]) not in s_index:
                continue
            elif any(wave_list):
                missing_wave = False
                for w in range(len(wave_list)):
                    try:
                        wvl = float(wave_list[w])
                        # Note: row[10] == wavemin array, row[11] == wavemax array
                        wave_check = (wvl - info[row][10])*(info[row][11] - wvl)
                        if wave_check.max() < 0:
                            missing_wave = True
                            break
                    except:
                        # Might be good to print a warning about invalid inputs
                        pass
                if missing_wave:
                    continue

            # If row passes all filters, extend the table and append data
            new_row_ind = self.count_filtered
            self.count_filtered += 1
            self.table_m.setRowCount(self.count_filtered)

            # Date and start time
            item = QtWidgets.QTableWidgetItem(info[row][0])
            self.table_m.setItem(new_row_ind, 0, item)
            # Study ID
            item = QtWidgets.QTableWidgetItem(str(info[row][1]))
            self.table_m.setItem(new_row_ind, 1, item)
            # Study acronym
            item = QtWidgets.QTableWidgetItem(info[row][2])
            self.table_m.setItem(new_row_ind, 2, item)
            # Description
            item = QtWidgets.QTableWidgetItem(info[row][3])
            self.table_m.setItem(new_row_ind, 3, item)
            # Xcen and Ycen
            fstring = '{:0.1f}'.format(info[row][4])
            item = QtWidgets.QTableWidgetItem(fstring)
            self.table_m.setItem(new_row_ind, 4, item)
            fstring = '{:0.1f}'.format(info[row][5])
            item = QtWidgets.QTableWidgetItem(fstring)
            self.table_m.setItem(new_row_ind, 5, item)
            if info[row][9] in [3, 1]:
                # Color slot rows a slightly darker gray
                for col_j in range(6):
                    self.table_m.item(new_row_ind, col_j).setBackground(QtGui.QColor(222,222,222))
            self.file_list.append(info[row][6])
            self.date_obs_list.append(info[row][0])
            self.result_ind_list.append(row)

        # Update filter count label
        if r_type is None and s_index is None and not any(wave_list):
            self.filter_info.setText('Showing all results (no filter applied)')
        else:
            self.filter_info.setText('Showing '+str(self.count_filtered)
                                    +' filter matches')

        # Any cells highlighted?
        self.table_m.currentCellChanged.connect(self.get_details)
        self.tabs.currentChanged.connect(self.event_update_image_tabs)

    def get_details(self, row, column):
        """Provide details on selected cell."""
        self.info_detail.clear()
        # Checking for a valid filename prevents crashes when a new search is
        # made and the results list is empty
        try:
            row_filename = str(self.file_list[row])
        except:
            row_filename = None
        if row_filename:
            self.selected_file = row_filename
            self.selected_date_obs = str(self.date_obs_list[row])
            self.selected_result_ind = int(self.result_ind_list[row])
            self.selected_result = self.d.eis_str[self.selected_result_ind]
            info = self.fill_info(row_filename)
            for line in info:
                self.info_detail.append(line)
            self.info_detail.verticalScrollBar().\
                setValue(self.info_detail.verticalScrollBar().minimum())

            # Update the context image
            self.event_update_image_tabs(0)

    def fill_info(self, file):
        """Retrieve useful info for a selected file."""
        info = []
        if len(self.d.eis_str) != 0:
            row, = [x for x in self.d.eis_str if x.filename == str(file)]
            info.append(f"{'filename':<20} {row.filename}")
            info.append(f"{'date_obs':<20} {row.date_obs}")
            info.append(f"{'date_end':<20} {row.date_end}")
            info.append(f"{'xcen, ycen':<20} {row.xcen:0.2f}, {row.ycen:0.2f}")
            info.append(f"{'fovx, fovy':<20} {row.fovx:0.2f}, {row.fovy:0.2f}")
            info.append(f"{'tl_id':<20} {row.tl_id}")
            info.append(f"{'study_id, stud_acr':<20} {row.study_id}, {row.stud_acr}")
            info.append(f"{'rast_id, rast_acr':<20} {row.rast_id}, {row.rast_acr}")
            info.append(f"{'jop_id':<20} {row.jop_id}")
            info.append(f"{'obstitle':<20} {row.obstitle}")
            info.append(f"{'obs_dec':<20} {row.obs_dec}")
            info.append(f"{'sci_obj':<20} {row.sci_obj}")
            info.append(f"{'target':<20} {row.target}")
            # Note: SAA and HLZ do not match the actual time periods
            # info.append(f"{'saa, hlz':<20} {row.saa}, {row.hlz}")
            # Note: tr_mode seems to be filled with "0" in the as-run DB (Fits files are fine?)
            # info.append(f"{'tr_mode':<20} {row.tr_mode}")
            info.append(f"{'rastertype':<20} {self.rtype_dict[int(row.rastertype)]}")
            info.append(f"{'slit_index':<20} {self.sindex_dict[int(row.slit_index)]}")
            info.append(f"{'scan_fm_nsteps':<20} {row.scan_fm_nsteps}")
            info.append(f"{'scan_fm_stepsize':<20} {row.scan_fm_stepsize}")
            info.append(f"{'nexp':<20} {row.nexp}")
            info.append(f"{'exptime':<20} {row.exptime[0:row.nexp]}")

            line_list_title = f"----- Line List (ll_id: {row.ll_id},  ll_acr: {row.ll_acr}) -----"
            info.append(f"\n\n{line_list_title:<55}")
            info.append(f"{'window':<8} {'title':<20} "
                       +f"{'wavemin':<9} {'wavemax':<9} {'width':<5}")
            for i in range(0, row.n_windows):
                info.append(f"{i:<8} {row.ll_title[i]:<20} "
                           +f"{row.wavemin[i]:<9.2f} {row.wavemax[i]:<9.2f} "
                           +f"{row.width[i]:<5}")
            info.append("\n")

            # Generate info for display in context tab
            self.selected_info = []
            self.selected_info.append(f"{'filename':<20} {row.filename}")
            self.selected_info.append(f"{'date_obs, date_end':<20} {row.date_obs}   to   {row.date_end}")
            self.selected_info.append(f"{'xcen, ycen':<20} {row.xcen:0.2f}, {row.ycen:0.2f}")
            self.selected_info.append(f"{'fovx, fovy':<20} {row.fovx:0.2f}, {row.fovy:0.2f}")
            self.selected_info.append(f"{'study_id, stud_acr':<20} {row.study_id}, {row.stud_acr}")
            self.selected_info.append(f"{'obstitle':<20} {row.obstitle}")
        return info

    @QtCore.pyqtSlot(int)
    def get_context_image(self):
        url = self.context_url
        self.start_context_request(url)

    def start_context_request(self, url):
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        self.manager.get(request)

    @QtCore.pyqtSlot(QtNetwork.QNetworkReply)
    def finished_context_download(self, reply):
        target = reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)
        if reply.error():
            print("error: {}".format(reply.errorString()))
            if 'jsoc' in str(reply.url()):
                self.event_plot_aia_context(plot_wireframe=True)
            else:
                self.event_clear_context_image(info_text="Context image is unavailable."
                                                        +" Please try again later")
            return
        elif target:
            newUrl = reply.url().resolved(target)
            self.start_context_request(newUrl)
            return
        
        if 'jsoc' in str(reply.url()):
            # Save to disk, then plot the low-res AIA "synoptic" image (~1.5 MB)
            if os.path.isfile(self.aia_fits):
                os.remove(self.aia_fits)
            f = QtCore.QFile(self.aia_fits)
            f.open(QtCore.QIODevice.ReadWrite)
            f.write(reply.readAll())
            f.close()
            self.event_plot_aia_context(load_aia=True)
        else:
            # Display the MSSL context image (~50 kB file)
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(reply.readAll())
            pixmap = pixmap.scaled(self.context_imgNX, self.context_imgNY)
            self.context_img.setPixmap(pixmap)

    @QtCore.pyqtSlot(int)
    def get_thumb_image(self):
        url = self.thumb_url
        self.start_thumb_request(url)

    def start_thumb_request(self, url):
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        self.thumb_manager.get(request)

    @QtCore.pyqtSlot(QtNetwork.QNetworkReply)
    def finished_thumb_download(self, reply):
        target = reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)
        if self.thumb_last_source.upper() == 'MSSL':
            url_split = str(reply.url()).split('line_')
            iwin = int(url_split[1][:2])
        elif self.thumb_last_source.upper() == 'OSLO':
            url_split = str(reply.url()).split('_')
            iwin = int(url_split[-1].split('.')[0])
       
        if reply.error():
            print("error: {}".format(reply.errorString()))
            self.event_clear_thumb_image(iwin, label_text='ERROR!')
            return
        elif target:
            newUrl = reply.url().resolved(target)
            self.start_thumb_request(newUrl)
            return
       
        self.thumb_pixmap[iwin] = QtGui.QPixmap()
        self.thumb_pixmap[iwin].loadFromData(reply.readAll())
        if self.thumb_last_source.upper() == 'MSSL':
            # All MSSL thumbnails are square
            this_imgNX = self.thumb_imgNX
        elif self.thumb_last_source.upper() == 'OSLO':
            # OSLO thumbnails have fixed heights, but variable widths
            x_scale = self.thumb_imgNY / self.thumb_pixmap[iwin].height()
            this_imgNX = int(x_scale*self.thumb_pixmap[iwin].width())

        scaled_pixmap = self.thumb_pixmap[iwin].scaled(this_imgNX, self.thumb_imgNY)
        
        self.thumb_img_list[iwin].setPixmap(scaled_pixmap)
        self.thumb_label_list[iwin].setText(self.thumb_line_ids[iwin])

        if self.thumb_dialog is not None and self.thumb_dialog_iwin == iwin:
            self.thumb_dialog.update_image(parent=self, iwin=iwin)

    def event_update_image_tabs(self, tab_index):
        """Download context image into memory and update the image tab"""

        if self.selected_file is not None:
            clean_filename = self.selected_file.replace('.gz','')

        if (self.selected_file is not None and self.tabs.currentIndex() != 2
        and self.thumb_dialog is not None and self.thumb_dialog.isVisible()):
            # If not on the Thumb tab, update the thumbnail dialog box
            t_iwin = self.thumb_dialog_iwin
            remote_dir = get_remote_image_dir(clean_filename, source=self.thumb_last_source)
            max_thumbs = self.selected_result['n_windows']
            if t_iwin < max_thumbs:
                thumb_filename = self.get_remote_thumb_filename(clean_filename, iwin=t_iwin)
                self.thumb_url = remote_dir+thumb_filename
                self.thumb_label_list[t_iwin].setText('UPDATING...')
                self.get_thumb_image()
            else:
                self.event_clear_thumb_image(iwin=t_iwin)

        if (self.tabs.currentIndex() == 1 and self.selected_file is not None
        and self.selected_file != self.context_eis_file):
            # Display a context AIA or EIT image along with some key details
            self.context_eis_file = self.selected_file
            try:
                remote_dir = get_remote_image_dir(clean_filename)
                context_img_name = 'XRT_'+clean_filename+'.gif'
                self.context_url = remote_dir+context_img_name
                self.get_context_image()
            except:
                print('   ERROR: context images or server are unavailable.')

            self.info_context.clear()
            for line in self.selected_info:
                self.info_context.append(line)
        elif (self.tabs.currentIndex() == 2 and self.selected_file is not None
        and self.selected_file != self.thumb_eis_file):
            # Display a grid of thumbnail images
            self.thumb_eis_file = self.selected_file
            self.thumb_last_source = self.thumb_source_box.currentText()
            self.thumb_title.setText(f"{self.thumb_eis_file} Intensities"
                                    +f" (click to view larger)")
            remote_dir = get_remote_image_dir(clean_filename, source=self.thumb_last_source)
            self.thumb_line_ids = ['']*25 # Clear & reset the list
            max_thumbs = self.selected_result['n_windows'] # row['n_windows'][0]
            for iwin in range(25):
                if iwin < max_thumbs:
                    try:
                        thumb_filename = self.get_remote_thumb_filename(clean_filename, iwin=iwin)
                        self.thumb_url = remote_dir+thumb_filename
                        self.thumb_label_list[iwin].setText('UPDATING...')
                        self.get_thumb_image()
                    except:
                        print('   ERROR: thumbnail images or server are unavailable.')
                else:
                    self.event_clear_thumb_image(iwin)
        elif (self.tabs.currentIndex() == 3 and self.selected_file is not None
        and self.selected_file != self.aia_eis_file):
            # Download & plot a "live" aia context image with the selected EIS FoV
            self.aia_eis_file = self.selected_file
            aia_wave = int(self.aia_wave_box.currentText())
            self.aia_title.setText(f"{self.aia_eis_file} FoV"
                                    +f" (middle click to toggle pan/zoom)")
            try:
                jsoc_url = get_aia_synoptic_url(self.selected_file, wavelength=aia_wave)
                self.context_url = jsoc_url
                self.get_context_image()
            except:
                print('   ERROR: AIA context image or server are unavailable.')
                self.event_plot_aia_context(plot_wireframe=True)
        else:
            # When no result is selected, clear the various image tabs
            if self.context_eis_file is None:
                self.event_clear_context_image()
                self.info_context.setText('Select a search result to view the context image')
            
            if self.thumb_eis_file is None:
                self.thumb_title.setText(f"Select a search result to view thumbnails")
                for iwin in range(25):
                    self.event_clear_thumb_image(iwin)
                if self.thumb_dialog is not None:
                    self.thumb_dialog.clear_image()

            if self.aia_eis_file is None:
                self.aia_title.setText(f"Select a search result to view AIA context")
                self.event_plot_aia_context(clear=True)

    def get_remote_thumb_filename(self, eis_filename, iwin=0):
        clean_filename = eis_filename

        self.thumb_line_ids[iwin] = convert_ll_title_to_line_id(self.selected_result['ll_title'][iwin])

        if self.thumb_last_source.upper() == 'MSSL':
            thumb_filename = f"{clean_filename}_line_{iwin:02}" \
                            +f"_{self.thumb_line_ids[iwin]}.int.gif"
        elif self.thumb_last_source.upper() == 'OSLO':
            clean_filename = clean_filename.replace('.fits','')
            thumb_filename = f"{clean_filename}_{iwin}.jpg"

        return thumb_filename

    def event_clear_context_image(self, info_text=''):
        self.info_context.clear()
        self.info_context.append(info_text)
        buff = np.zeros((self.context_imgNX, self.context_imgNX, 3), dtype=np.int16)
        image = QtGui.QImage(buff, self.context_imgNX, self.context_imgNY,
                             QtGui.QImage.Format_ARGB32)
        self.context_img.setPixmap(QtGui.QPixmap(image))

    def event_clear_thumb_image(self, iwin, label_text=''):
        image = QtGui.QImage(self.blank_thumb, self.thumb_imgNX, self.thumb_imgNY, 
                             QtGui.QImage.Format_ARGB32)
        self.thumb_img_list[iwin].setPixmap(QtGui.QPixmap(image))
        self.thumb_label_list[iwin].setText(label_text)
        self.thumb_pixmap[iwin] = None

        if self.thumb_dialog is not None and self.thumb_dialog_iwin == iwin:
            self.thumb_dialog.clear_image()

    def event_redraw_thumbs(self):
        self.thumb_eis_file = None
        self.event_update_image_tabs(2)

    def event_plot_aia_context(self, load_aia=True, plot_wireframe=False, clear=False):
        if self.aia_ax is not None:
            self.aia_ax.cla()
        self.aia_fig.clf() # Clear the entire figure

        if clear:
            load_aia = False
            plot_wireframe = False 

        if plot_wireframe and self.selected_date_obs is not None:
            # Generate a wireframe placeholder map
            limb_coords = get_limb_coordinates(get_earth(self.selected_date_obs))
            limb_coords = limb_coords.transform_to(frames.Helioprojective)
            max_arcsec = float(limb_coords.Tx.arcsec.max()*1.3) #scale to 2.6 Rs FoV
            empty_scale = [max_arcsec/500, max_arcsec/500]*u.arcsec/u.pix
            empty_data = np.zeros([1000,1000])
            cen_coords = SkyCoord(0.0*u.arcsec, 0.0*u.arcsec, 
                                  frame=frames.Helioprojective, observer='Earth', 
                                  obstime=self.selected_date_obs)
            empty_header = sunpy.map.make_fitswcs_header(empty_data, cen_coords, 
                                                        scale=empty_scale)

            aia_map = sunpy.map.Map(empty_data, empty_header)
        elif load_aia:
            # Load the AIA data and ensure the colormap is scaled correctly
            aia_map = sunpy.map.Map(self.aia_fits)
            aia_map.plot_settings['norm'] = ImageNormalize(vmin=0.0, 
                                                stretch=AsinhStretch(0.01))
        else:
            # Skip plotting
            if self.aia_ax is not None:
                self.aia_ax.figure.canvas.draw_idle() # Update the plot!
            return None

        # Make the plot
        self.aia_ax = self.aia_fig.add_subplot(projection=aia_map)
        aia_map.plot(axes=self.aia_ax)
        if plot_wireframe:
            aia_map.draw_limb(axes=self.aia_ax, color='white')
            aia_map.draw_grid(axes=self.aia_ax, color='white')

        # Calculate the EIS FoV box corners
        row = self.d.eis_str[np.where(self.d.eis_str['filename'] == self.selected_file)]
        bl_coords = [row['xcen'][0] - 0.5*row['fovx'][0], row['ycen'][0] - 0.5*row['fovy'][0]]
        tr_coords = [row['xcen'][0] + 0.5*row['fovx'][0], row['ycen'][0] + 0.5*row['fovy'][0]]

        bottom_left = SkyCoord(bl_coords[0]*u.arcsec, bl_coords[1]*u.arcsec,
                                frame=aia_map.coordinate_frame)
        top_right = SkyCoord(tr_coords[0]*u.arcsec, tr_coords[1]*u.arcsec, 
                                frame=aia_map.coordinate_frame)

        aia_map.draw_quadrangle(bottom_left=bottom_left, top_right=top_right, axes=self.aia_ax, linewidth=2, edgecolor='white')
        self.aia_fig.subplots_adjust(left=0.10, right=1.0, bottom=0.06, top=0.95)
        self.aia_ax.figure.canvas.draw_idle() # Update the plot!
        self.aia_click = self.aia_fig.canvas.mpl_connect('button_press_event', self.event_aia_click)

    def event_redraw_aia_context(self):
        self.aia_eis_file = None
        self.event_update_image_tabs(3)

    def event_aia_click(self, event):
        """Event for clicks on the AIA context image"""
        if event.button is MouseButton.MIDDLE:
            # Toggle pan/zoom on middle click
            self.aia_nav.pan()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.event_thumb_dialog(int(source.objectName().split('_')[-1]))
        return super(Top, self).eventFilter(source, event)

    def event_thumb_dialog(self, iwin=0):
        """Event for opening the dialog box for viewing a larger thumbnail"""
        self.thumb_dialog_iwin = iwin
        old_geometry = None
        if self.thumb_dialog is not None:
            dialog_is_vis = self.thumb_dialog.isVisible()
            if dialog_is_vis:
                old_geometry = self.thumb_dialog.geometry()
            self.thumb_dialog.close()
        self.thumb_dialog = ThumbDialog(self, iwin=iwin, 
                                        old_geometry=old_geometry)
        self.thumb_dialog.show()

    def details(self):
        """Display detailed cat info."""
        # Initialize tab panel and add main tabs
        self.tabs = QtWidgets.QTabWidget()
        self.detail_tab = QtWidgets.QWidget()
        self.image_tab = QtWidgets.QWidget()
        self.thumb_tab = QtWidgets.QScrollArea()
        self.thumb_tab.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.thumb_tab.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.aia_tab = QtWidgets.QWidget()
        self.help_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.detail_tab,"Details")
        self.tabs.addTab(self.image_tab,"Context Image (MSSL)")
        self.tabs.addTab(self.thumb_tab,"Intensity Maps")
        self.tabs.addTab(self.aia_tab,"AIA Context")
        self.tabs.addTab(self.help_tab,"Help")

        # Create details tab
        self.detail_tab.grid = QtWidgets.QGridLayout()
        self.info_detail = QtWidgets.QTextEdit()
        self.info_detail.setFont(self.info_detail_font)
        self.info_detail.setReadOnly(True)
        self.detail_tab.grid.addWidget(self.info_detail)
        self.detail_tab.setLayout(self.detail_tab.grid)

        # Create context image tab and initialize SSL context for downloading
        self.image_tab.grid = QtWidgets.QGridLayout()
        self.info_context = QtWidgets.QTextEdit()
        self.info_context.setFont(self.info_detail_font)
        self.info_context.setReadOnly(True)
        self.image_tab.grid.addWidget(self.info_context, 0, 0)
        self.context_img = QtWidgets.QLabel()
        self.image_tab.grid.addWidget(self.context_img, 1, 0, 4, 1)
        self.image_tab.setLayout(self.image_tab.grid)
        self.event_clear_context_image()
        self.info_context.setText('Select a search result to view the context image')

        # self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        # self.ssl_context.load_verify_locations(certifi.where())

        # Create thumbnail images tab
        self.thumb_gallery = QtWidgets.QWidget()
        self.thumb_gallery.grid = QtWidgets.QGridLayout()
        self.thumb_source_box = QtWidgets.QComboBox()
        self.thumb_source_box.addItems(['MSSL', 'OSLO'])
        self.thumb_source_box.setFixedWidth(self.thumb_imgNX)
        self.thumb_source_box.setFont(self.default_font)
        self.thumb_source_box.currentIndexChanged.connect(self.event_redraw_thumbs)
        self.thumb_gallery.grid.addWidget(self.thumb_source_box, 0, 0)
        self.thumb_title = QtWidgets.QLabel(self)
        self.thumb_title.setFont(self.default_font)
        self.thumb_title.setAlignment(QtCore.Qt.AlignLeft)
        self.thumb_title.setText('Select a search result to view thumbnails')
        self.thumb_gallery.grid.addWidget(self.thumb_title, 0, 1, 1, (self.num_thumb_cols-1))
        self.blank_thumb = np.zeros((self.thumb_imgNX, self.thumb_imgNX, 3), dtype=np.int16)
        self.thumb_pixmap = [None]*25
        self.thumb_img_list = [None]*25
        self.thumb_line_ids = [None]*25
        self.thumb_label_list = [None]*25
        for iwin in range(25):
            t_row = int(iwin / self.num_thumb_cols)
            t_col = int(iwin % self.num_thumb_cols)
            self.thumb_img_list[iwin] = QtWidgets.QLabel()
            self.thumb_img_list[iwin].setObjectName(f'thumb_{iwin}')
            image = QtGui.QImage(self.blank_thumb, self.thumb_imgNX, self.thumb_imgNY,
                                 QtGui.QImage.Format_ARGB32)
            self.thumb_img_list[iwin].setPixmap(QtGui.QPixmap(image))
            self.thumb_img_list[iwin].installEventFilter(self)
            self.thumb_gallery.grid.addWidget(self.thumb_img_list[iwin], 2*t_row+1, t_col)

            self.thumb_label_list[iwin] = QtWidgets.QLabel(self)
            self.thumb_label_list[iwin].setFixedWidth(self.thumb_imgNX)
            self.thumb_label_list[iwin].setFont(self.small_font)
            self.thumb_label_list[iwin].setAlignment(QtCore.Qt.AlignCenter)
            self.thumb_label_list[iwin].setStyleSheet('''
                padding-top: 0px;
                padding-bottom: 8px;
                QLabel { qproperty-indent: 0; }''')
            self.thumb_label_list[iwin].setText('')
            self.thumb_gallery.grid.addWidget(self.thumb_label_list[iwin], 2*t_row+2, t_col)

        self.thumb_gallery.setLayout(self.thumb_gallery.grid)
        self.thumb_tab.setWidget(self.thumb_gallery)

        # Create AIA context tab
        self.aia_ax = None
        self.aia_tab.grid = QtWidgets.QGridLayout()
        self.aia_wave_label = QtWidgets.QLabel(self)
        self.aia_wave_label.setFont(self.default_font)
        self.aia_wave_label.setText(u'AIA Channel [\u212B]')
        self.aia_wave_label.setFixedWidth(140)
        self.aia_wave_box = QtWidgets.QComboBox()
        self.aia_wave_box.addItems(['94', '131', '171', '193', 
                                    '211', '304', '335', '1600'])
        self.aia_wave_box.setFixedWidth(66)
        self.aia_wave_box.setFont(self.default_font)
        self.aia_wave_box.setCurrentIndex(3) #default to 193
        self.aia_wave_box.currentIndexChanged.connect(self.event_redraw_aia_context)
        self.aia_title = QtWidgets.QLabel(self)
        self.aia_title.setFont(self.default_font)
        self.aia_title.setText('Select a search result to view AIA context')
        self.aia_fig = Figure(figsize=(5, 5))
        self.aia_canvas = FigureCanvas(self.aia_fig)
        self.aia_nav = NavigationToolbar(self.aia_canvas, self)
        self.aia_tab.grid.addWidget(self.aia_wave_label, 0, 0)
        self.aia_tab.grid.addWidget(self.aia_wave_box, 0, 1)
        self.aia_tab.grid.addWidget(self.aia_title, 0, 2)
        self.aia_tab.grid.addWidget(self.aia_nav, 1, 0, 1, 3)
        self.aia_tab.grid.addWidget(self.aia_canvas, 2, 0, 1, 3)
        self.aia_tab.setLayout(self.aia_tab.grid)

        # Create help tab
        self.help_tab.grid = QtWidgets.QGridLayout()
        self.info_help = QtWidgets.QTextEdit()
        self.info_help.setFont(self.info_detail_font)
        self.info_help.setReadOnly(True)
        self.help_tab.grid.addWidget(self.info_help)
        self.help_tab.setLayout(self.help_tab.grid)

        # Add tabs to main window
        self.tabs.setStyleSheet('QTabBar{font-size: 11pt; font-family: Courier New;}')
        # self.grid.addWidget(self.tabs, 1, 6, self.gui_row + 1, 3)
        self.grid.addWidget(self.tabs, 0, 6, self.gui_row + 2, 3)
        self.tabs.setCurrentIndex(4) # switch to help tab

    def event_apply_filter(self):
        if self.count_results > 0:
            self.mk_table(self.table_info)

    def event_clear_filter(self):
        self.rast_type_box.setCurrentIndex(0)
        self.slit_slot_box.setCurrentIndex(0)
        self.wave_text.clear()
        if self.count_results > 0:
            self.mk_table(self.table_info)

    def save_options(self):
        """Controls for saving files."""

        data_source_title = QtWidgets.QLabel(self)
        data_source_title.setText('Data Source')
        data_source_title.setFont(self.default_font)
        self.grid.addWidget(data_source_title, self.gui_row, 0)

        set_save_dir = QtWidgets.QPushButton('Change Save Dir', self)
        set_save_dir.setFixedWidth(self.default_button_width)
        set_save_dir.setFont(self.default_font)
        self.grid.addWidget(set_save_dir, self.gui_row, 1)
        set_save_dir.clicked.connect(self.event_set_save_dir)

        self.topdir_box = QtWidgets.QLineEdit(self)
        self.topdir_box.resize(4*self.default_button_width, self.frameGeometry().height())
        self.topdir_box.setText(self.default_topdir)
        self.topdir_box.setFont(self.default_font)
        self.grid.addWidget(self.topdir_box, self.gui_row, 2, 1, 4)

        self.gui_row += 1

        self.data_source_box = QtWidgets.QComboBox()
        self.data_source_box.addItems(['NRL (main)', 'NASA (mirror)', 'MSSL (mirror)'])
        self.data_source_box.setFixedWidth(self.default_button_width) # or 150
        self.data_source_box.setFont(self.default_font)
        self.grid.addWidget(self.data_source_box, self.gui_row, 0)

        download_selected = QtWidgets.QPushButton('Download Selected', self)
        download_selected.setFixedWidth(self.default_button_width)
        download_selected.setFont(self.default_font)
        self.grid.addWidget(download_selected, self.gui_row, 1)
        download_selected.clicked.connect(self.event_download_selected)

        download_list = QtWidgets.QPushButton('Download All', self)
        download_list.setFixedWidth(self.default_button_width)
        download_list.setFont(self.default_font)
        self.grid.addWidget(download_list, self.gui_row, 2)
        download_list.clicked.connect(self.event_download_file_list)

        self.radio = QtWidgets.QRadioButton("Use Date Tree")
        self.radio.setFixedWidth(self.default_button_width)
        self.radio.setFont(self.default_font)
        self.grid.addWidget(self.radio, self.gui_row, 3)

        self.save_list = QtWidgets.QPushButton('Save File List', self)
        self.save_list.setFixedWidth(self.default_button_width)
        self.save_list.setFont(self.default_font)
        self.grid.addWidget(self.save_list, self.gui_row, 4)
        self.save_list.clicked.connect(self.event_save_file_list)

        self.filename_box = QtWidgets.QLineEdit(self)
        self.filename_box.setFixedWidth(self.default_button_width)
        self.filename_box.setText(self.default_filename)
        self.filename_box.setFont(self.default_font)
        self.grid.addWidget(self.filename_box, self.gui_row, 5)

    def event_set_save_dir(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        options |= QtWidgets.QFileDialog.ShowDirsOnly
        new_savedir = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                'Select a directory',
                                                options=options)
        if os.path.isdir(new_savedir):
            self.topdir_box.setText(new_savedir)

    def event_download_selected(self):
        if self.selected_file is not None:
            self.tabs.setCurrentIndex(0) #switch to details tab
            data_source = self.data_source_box.currentText()
            datetree = self.radio.isChecked()
            topdir = self.topdir_box.text()
            self.info_detail.clear()
            info = (f'Downloading {self.selected_file}\n'
                    f'   Data Source: {data_source}\n'
                    f'   Save dir: {topdir}\n\n'
                    f'Please wait...')
            self.info_detail.append(info)
            QtWidgets.QApplication.processEvents() # update gui while user waits
            o = download_hdf5_data(filename=self.selected_file, datetree=datetree,
                                   source=data_source, local_top=topdir, overwrite=True)
            self.info_detail.append('\nComplete')

    def event_download_file_list(self):
        if self.file_list is not None:
            self.tabs.setCurrentIndex(0) #switch to details tab
            data_source = self.data_source_box.currentText()
            datetree = self.radio.isChecked()
            topdir = self.topdir_box.text()
#            sys.stdout = OutLog(self.info_detail, sys.stdout)
#            sys.stderr = OutLog(self.info_detail, sys.stderr)
            self.info_detail.clear()
            info = (f'Downloading all files listed above\n'
                    f'   Data Source: {data_source}\n'
                    f'   Save dir: {topdir}\n\n'
                    f'Please wait (see console for download progress)...')
            self.info_detail.append(info)
            QtWidgets.QApplication.processEvents() # update gui while user waits
            o = download_hdf5_data(filename=self.file_list, datetree=datetree,
                                   source=data_source, local_top=topdir, overwrite=True)
            self.info_detail.append('\nComplete')

    def event_save_file_list(self):
        """Save a list of the displayed files, one per line."""
        if self.file_list is not None:
            topdir = self.topdir_box.text()
            filename = self.filename_box.text()
            if filename != '':
                with open(os.path.join(topdir, filename), 'w') as fp:
                    for item in self.file_list:
                        fp.write("{}\n".format(item))
                        print(item)
                print(f' + wrote {filename}')

    def event_quit(self):
        """Close all figures, clean-up GUI objects, and quit the app"""
        if self.thumb_dialog is not None:
            self.thumb_dialog.close()

        if self.aia_click is not None:
            self.aia_fig.canvas.mpl_disconnect(self.aia_click)
        self.aia_nav.close()
        self.aia_canvas.close()
        if os.path.isfile(self.aia_fits):
            os.remove(self.aia_fits)
        QtWidgets.QApplication.instance().quit()
        self.close()

    def closeEvent(self, event):
        """Override the close event when the "X" button on the window is clicked"""
        self.event_quit()

class ThumbDialog(QtWidgets.QDialog):
    """Make a cutom dialog box for viewing a larger thumbnail"""
    def __init__(self, parent=None, iwin=0, old_geometry=None):
        super().__init__(parent)

        self.iwin = iwin
        self.thumb_gallery = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout()
    
        # Placeholder image
        self.thumb_imgNX = 768
        self.thumb_imgNY = 768
        self.blank_thumb = np.zeros((self.thumb_imgNX, self.thumb_imgNX, 3), 
                                    dtype=np.int16)
        image = QtGui.QImage(self.blank_thumb, self.thumb_imgNX, self.thumb_imgNY, 
                             QtGui.QImage.Format_ARGB32)
        pixmap = QtGui.QPixmap(image)

        self.thumb_img = QtWidgets.QLabel(self)
        self.thumb_img.setPixmap(pixmap)
        self.grid.addWidget(self.thumb_img, 0, 0)

        self.thumb_label = QtWidgets.QLabel(self)
        self.thumb_label.setFont(parent.default_font)
        self.thumb_label.setAlignment(QtCore.Qt.AlignCenter)
        self.thumb_label.setText("")
        self.grid.addWidget(self.thumb_label, 1, 0)
        self.setLayout(self.grid)

        self.update_image(parent=parent, iwin=iwin)
        if old_geometry is not None:
            self.setGeometry(old_geometry) # Keep previous on-screen location

    def update_image(self, parent=None, iwin=0):
        """Update the thumbnail image"""
        self.setWindowTitle(f"EIS Intensity Thumbnail from {parent.thumb_last_source}")
        label_str = f"{parent.selected_file}   |   Window {iwin}" \
                   +f"   |   {parent.thumb_line_ids[iwin]}"
    
        pixmap = parent.thumb_pixmap[iwin]
        if pixmap is not None:
            self.thumb_imgNX = pixmap.width()
            self.thumb_imgNY = pixmap.height()
        else:
            self.thumb_imgNX = 768
            self.thumb_imgNY = 768
            self.blank_thumb = np.zeros((self.thumb_imgNX, self.thumb_imgNX, 3), 
                                        dtype=np.int16)
            image = QtGui.QImage(self.blank_thumb, self.thumb_imgNX, self.thumb_imgNY, 
                                 QtGui.QImage.Format_ARGB32)
            pixmap = QtGui.QPixmap(image)

        self.thumb_img.setPixmap(pixmap)
        self.thumb_label.setText(label_str)
        self.setFixedSize(self.grid.sizeHint())

    def clear_image(self, label_text=''):
        """Clear the thumnail image"""
        self.blank_thumb = np.zeros((self.thumb_imgNX, self.thumb_imgNX, 3), dtype=np.int16)
        image = QtGui.QImage(self.blank_thumb, self.thumb_imgNX, self.thumb_imgNY, 
                             QtGui.QImage.Format_ARGB32)
        self.thumb_img.setPixmap(QtGui.QPixmap(image))
        self.thumb_label.setText(label_text)

# [NOT IMPLEMENTED YET] This class will handles the redirection of stdout
class OutLog:
    def __init__(self, edit, out=None):
        self.edit = edit
        self.out = None

    def write(self, m):
        self.edit.moveCursor(QtGui.QTextCursor.End)
        self.edit.insertPlainText(m)

        if self.out:
            self.out.write(m)

#-#-#-#-# MAIN #-#-#-#-#
def eis_catalog():
    parser = argparse.ArgumentParser()
    parser.add_argument('cat_filepath', nargs='?', default='.',
                        help='[optional] Dir or file containing "eis_cat.sqlite".'
                            +'\nIf not given, will automatically search for the catalog')

    args = parser.parse_args()
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    
    topthing = Top(args.cat_filepath)

    sys.exit(app.exec_())

if __name__ == '__main__':
    eis_catalog()
