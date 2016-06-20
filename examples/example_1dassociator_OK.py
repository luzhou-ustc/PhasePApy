""" example_1dassociator_OK.py
This example shows an example using the 1D associator.  The traveltime lookup table for 
this example is included in the data directory.  Third party programs are required to build
the traveltime lookup table.

The associator also uses sqlalchemy to store phase picks and associated events in a database.
This example uses sqlite which should be included in python. 

"""
from phasepapy.phasepicker import fbpicker
from phasepapy.associator import tables1D, assoc1D, plot1D
from obspy.core import time
from sqlalchemy.orm import *
from sqlalchemy import create_engine
from datetime import datetime
import glob
import os

# If the associator database exists delete it first, start fresh for this example
if os.path.exists('1dassociator_ok.db'):
  os.remove('1dassociator_ok.db')

# Our SQLite databases are:
db_assoc='sqlite://1dassociator_ok.db'
tt_assoc='sqlite://data_20130616153750/tt_stations_1D.db'


# Connect to our databases
engine_assoc=create_engine(db_assoc, echo=False)
# Create the tables required to run the 1D associator
tables1D.Base.metadata.create_all(engine_assoc)
Session=sessionmaker(bind=engine_assoc)
session=Session()

# Find all waveform data in the data directory
file_list=glob.glob('data_20130616153750/*.msd')

# Define our picker instance
picker = fbpicker.FBPicker(t_long = 5, freqmin = 1, mode = 'rms', t_ma = 20, nsigma = 6, \
    t_up = 0.78, nr_len = 2, nr_coeff = 2, pol_len = 10, pol_coeff = 10, uncert_coeff = 3)
 
# Pick the waveforms     
for wf_file in file_list:
  st=read(wf_file)
  st.merge()
  for tr in st:
    tr.detrend('linear')
    scnl,picks,polarity,snr,uncert=picker.picks(tr)
    t_create=datetime.utcnow() # Record the time we made the picks
    # Add each picks to the database
    for i in range(len(picks)):
      new_pick=tables1d.Pick(scnl,picks[i].datetime,polarity[i],snr[i],uncert[i],t_create)
      session.add(new_pick) # Add pick i to the database
    session.commit() # Commit the pick to the database
    
# Define the associator
assocOK=assoc1D.LocalAssociator(db_assoc, db_tt,
  max_km = 350, 
  aggregation = 1, 
  aggr_norm = 'L2', 
  cutoff_outlier = 10, 
  assoc_ot_uncert = 7, 
  nsta_declare = 4, 
  loc_uncert_thresh = 0.2)
  
# Identify candidate events (Pick Aggregation)
assoc_ok.id_candidate_events()

# Associate events
assoc_ok.associate_candidates()

# Add singles stations to events
assoc_ok.single_phase()

# Plot example event
plt=plot1D.Plot(db_assoc,db_tt)
plt.cluster_plot(assoc_ot_uncert=3)
plt.event_plot(1)
plt.section_plot(1,file_list)