# Workaround for the Cartopy / PROJ issue
# For scitools default environments 
import os
os.environ['PROJ_NETWORK']='OFF'