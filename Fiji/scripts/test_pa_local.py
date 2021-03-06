#@UIService uiService
#@LogService log

import sys
import os
import json
import time
import shutil

from java.lang.System import getProperty
sys.path.append(getProperty('fiji.dir') + '/scripts')

from fijipytools import ExportTools, FilterTools, ImageTools, ImportTools
from fijipytools import AnalyzeTools, RoiTools, MiscTools, ThresholdTools
from fijipytools import WaterShedTools
from fijipytools import JSONTools
from ij.measure import ResultsTable
from ij.gui import Roi, Overlay
from ij.io import FileSaver
from ij.plugin.frame import RoiManager
from ij.plugin.filter import ParticleAnalyzer as PA
from ij.plugin.filter import GaussianBlur, RankFilters
from ij.plugin.filter import BackgroundSubtracter, Binary
from ij.plugin import Thresholder, Duplicator
from ij.process import ImageProcessor, ImageConverter, LUT, ColorProcessor
from ij import IJ, ImagePlus, ImageStack, Prefs
from java.lang import Double, Integer


############################################################################

# clear the console automatically when not in headless mode
uiService.getDefaultUI().getConsolePane().clear()

# imagefile = r"/datadisk1/tuxedo/Github/Tools_and_Scripts/Fiji/scripts/3d_nuclei_image_holes_T.ome.tiff"
# imagefile = r"/datadisk1/tuxedo/Github/Tools_and_Scripts/Fiji/scripts/3d_nuclei_image_holes.ome.tiff"
imagefile = r"/datadisk1/tuxedo/temp/input/Osteosarcoma_01.ome.tiff"

# define output directory
outputdir = r"/datadisk1/tuxedo/temp/output/"

# extract channel
extract_channel = True
channelindex = 3

# parameters for Rolling Ball
correct_background = True
create_background = False
correct_corners = True
useparaboloid = True
dopresmooth = True
rb_radius = 20
lightbackground = False

# parameters for filter
filtertype = 'MEDIAN'
filter_radius = 5

# parameters for threshold
threshold_method = 'Otsu'
threshold_stackoption = True
threshold_background = 'dark'
threshold_corr = 1.0

# parameters for watershed
watershed = True
watershed_connectivity = 6

# parameters for particle analysis
minsize = 10
maxsize = 100000
mincirc = 0.3
maxcirc = 1.0
suffix_pa = '_PA'
suffix_rt = '_RESULTS'
saveformat_rt = 'TXT'
resultsave = True
rois = False

# parameters for saving the binary output
saveformat = 'ome.tiff'

# summarize parameters
log.info('Starting ...')
log.info('Filename               : ' + imagefile)
log.info('-----------------------------------------')
log.info('Extract Channel        : ' + str(extract_channel))
log.info('Channel Index          : ' + str(channelindex))
log.info('-----------------------------------------')
log.info('Correct Background     : ' + str(correct_background))
log.info('Rolling Ball Radius    : ' + str(rb_radius))
log.info('Light Background       : ' + str(lightbackground))
log.info('-----------------------------------------')
log.info('Filter Type            : ' + filtertype)
log.info('Filter Radius          : ' + str(filter_radius))
log.info('-----------------------------------------')
log.info('Threshold Method       : ' + threshold_method)
log.info('Threshold Histo Calc   : ' + str(threshold_stackoption))
log.info('Threshold Corr-Factor  : ' + str(threshold_corr))
log.info('-----------------------------------------')
log.info('Watershed Separation   : ' + str(watershed))
log.info('Watershed Conectivity  : ' + str(watershed_connectivity))
log.info('-----------------------------------------')
log.info('Minimum Size [pixel]   : ' + str(minsize))
log.info('Maximum Size [pixel]   : ' + str(maxsize))
log.info('Minimum Circularity    : ' + str(mincirc))
log.info('Maximum Circularity    : ' + str(maxcirc))
log.info('Result Table Format    : ' + saveformat_rt)
log.info('------------  START IMAGE ANALYSIS ------------')

#############################################################

# define path stuff
outputimagepath = os.path.join(outputdir, os.path.basename(imagefile))

# create output imagepath
outputpath_orig = outputimagepath

basename = os.path.splitext(outputimagepath)[0]
# remove the extra .ome before reassembling the filename
if basename[-4:] == '.ome':
    basename = basename[:-4]
    log.info('New basename :' + basename)

# define save locations for processed data
outputimagepath = basename + suffix_pa + '.' + saveformat
outputpath_orig = basename + '.' + saveformat

##############  PIPELINE START ##################

# open the image
log.info('Opening Image: ' + imagefile)

# stitch togehter image tiles
stitchtiles = True
# when set to True the number of pyramid levels can be read
setflatres = True
# select the desired pyramid level - level=0 for full resolution
readpylevel = 0
setconcat = True
openallseries = True
showomexml = False
attach = False
autoscale = True
verbose = True

# read the image
imp, MetaInfo = ImportTools.openfile(imagefile,
                                     stitchtiles=stitchtiles,
                                     setflatres=setflatres,
                                     readpylevel=readpylevel,
                                     setconcat=setconcat,
                                     openallseries=openallseries,
                                     showomexml=showomexml,
                                     attach=attach,
                                     autoscale=autoscale)

if verbose:
    for k, v in MetaInfo.items():
        log.info(str(k) + ' : ' + str(v))


# do the processing
log.info('Start Processing ...')

if extract_channel:
    imp = MiscTools.splitchannel(imp, channelindex)

# correct background
if correct_background:

    log.info('Removing Background using Rolling Ball ...')
    imp = FilterTools.apply_rollingball(imp,
                                        radius=rb_radius,
                                        createBackground=create_background,
                                        lightBackground=lightbackground,
                                        useParaboloid=useparaboloid,
                                        doPresmooth=dopresmooth,
                                        correctCorners=correct_corners)

# filter image
if filtertype != 'NONE':

    log.info('Apply Filter      : ' + filtertype)
    imp = FilterTools.apply_filter(imp,
                                   radius=filter_radius,
                                   filtertype=filtertype)

# apply threshold
log.info('Apply Threshold ...')
imp = ThresholdTools.apply_threshold(imp,
                                     method=threshold_method,
                                     background_threshold=threshold_background,
                                     stackopt=threshold_stackoption,
                                     corrf=threshold_corr)

if watershed:
    imp = WaterShedTools.run_watershed(imp,
                                       mj_normalize=True,
                                       mj_dynamic=1,
                                       mj_connectivity=watershed_connectivity)

pastack, results = AnalyzeTools.analyzeParticles(imp,
                                                 minsize,
                                                 maxsize,
                                                 mincirc,
                                                 maxcirc,
                                                 filename=imagefile,
                                                 addROIManager=rois)

# apply suitable LUT to visualize particles
pastack = ImagePlus('Particles', pastack)
IJ.run(pastack, 'glasbey_inverted', '')
IJ.run(pastack, 'Enhance Contrast', 'saturated=0.35')

################ PIPELINE END ###################

log.info('Output Path Particle Stack :' + outputimagepath)
savepath_pastack = ExportTools.savedata(pastack,
                                        outputimagepath,
                                        extension=saveformat,
                                        replace=True)

if resultsave:
    # save the result table as file
    rtsavelocation = AnalyzeTools.create_resultfilename(outputimagepath,
                                                        suffix=suffix_rt,
                                                        extension=saveformat_rt)
    # save the results
    results.saveAs(rtsavelocation)

    # check if the saving did actually work
    filesaveOK = os.path.exists(rtsavelocation)
    log.info('FileCheck Result : ' + str(filesaveOK))
    if filesaveOK:
        log.info('Saved Results to : ' + rtsavelocation)
    if not filesaveOK:
        log.info('Saving did not work for : ' + rtsavelocation)

# finish
log.info('Done.')

# show particle stack
pastack.show()
