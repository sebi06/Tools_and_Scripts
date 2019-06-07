#@UIService uiService
# @LogService log

import sys
import os
import json
import time
import shutil

#scriptdir = '/Fiji.app/scripts'
#sys.path.append(scriptdir)
#log.info('Script Directory: ' + scriptdir)
from java.lang.System import getProperty
sys.path.append(getProperty('fiji.dir') + '/scripts')

from fijipytools import ExportTools, FilterTools, ImageTools, ImportTools
from fijipytools import AnalyzeTools, RoiTools, MiscTools, ThresholdTools
from fijipytools import JSONTools
from ij.measure import ResultsTable
from ij.gui import Roi, Overlay
from ij.io import FileSaver
from ij.plugin.frame import RoiManager
from ij.plugin.filter import ParticleAnalyzer as PA
from ij.plugin.filter import GaussianBlur, RankFilters, BackgroundSubtracter, Binary
from ij.plugin import Thresholder, Duplicator
from ij.process import ImageProcessor, ImageConverter, LUT, ColorProcessor
from ij import IJ, ImagePlus, ImageStack, Prefs
from java.lang import Double, Integer
from ij.plugin import ChannelSplitter
from ij.plugin.filter import EDM

# MorphoLibJ imports
from inra.ijpb.binary import BinaryImages, ChamferWeights3D#, ChamferWeights2D
from inra.ijpb.morphology import MinimaAndMaxima3D, Morphology, Strel3D
from inra.ijpb.watershed import Watershed
from inra.ijpb.label import LabelImages
from inra.ijpb.plugins import ParticleAnalysis3DPlugin, BoundingBox3DPlugin, ExtendBordersPlugin
from inra.ijpb.data.border import BorderManager3D, ReplicatedBorder3D
from inra.ijpb.util.ColorMaps import CommonLabelMaps
from inra.ijpb.util import CommonColors
from inra.ijpb.plugins import DistanceTransformWatershed3D, FillHolesPlugin
from inra.ijpb.data.image import Images3D
from inra.ijpb.watershed import ExtendedMinimaWatershed
from inra.ijpb.morphology import Reconstruction
from inra.ijpb.morphology import Reconstruction3D

############################################################################


def run(imagefile, outputpath_orig, convert_orig2copy=False,
        sft='ome.tiff',
        verbose=False):

    # Opening the image
    log.info('Opening Image: ' + imagefile)

    # stitch togehter tiles
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

   

    if EXTRACT_CHANNEL:
	    imp = MiscTools.splitchannel(imp, CHINDEX)



    # optional filtering
    if FILTERTYPE != 'NONE':

        log.info('Apply Filter      : ' + FILTERTYPE)
        imp = FilterTools.apply_filter(imp,
                                       radius=FILTER_RADIUS,
                                       filtertype=FILTERTYPE)
    """   
    # apply threshold
    log.info('Apply Threshold ...')
    imp = ThresholdTools.apply_threshold(imp,
                                         method=THRESHOLD_METHOD,
                                         background_threshold=THRESHOLD_BGRD,
                                         stackopt=THRESHOLD_STACKOPTION)

    """

    ip = imp.getProcessor()
    ip.threshold(500)
    imp.setProcessor(ip)
    #IJ.run(imp, "8-bit", "")



    
    return imp
    

##########################################################

# clear the console automatically when not in headless mode
uiService.getDefaultUI().getConsolePane().clear()

showdir = False
stackopt = True
method = 'Otsu'
background_threshold = 'dark'
imagefile = r"c:\Temp\input\Osteosarcoma_01.ome.tiff"
#imagefile = r"c:\Temp\input\nuclei3d-holes.ome.tiff"
corrf = 1.0

SUFFIX_RT = '_RESULTS'
SAVEFORMAT_RT = 'txt'
RESULTSAVE = False

MINSIZE = 0
MAXSIZE = 1000000
MINCIRC = 0.0
MAXCIRC = 1.0
ROIS = False

# Parse Inputs of Module
#INPUT_JSON = json.loads(os.environ['WFE_INPUT_JSON'])
#IMAGEPATH = INPUT_JSON['IMAGEPATH']
IMAGEPATH = imagefile
# IMAGESERIES = 0

EXTRACT_CHANNEL = True
CHINDEX = 3
# parameters for Rolling Ball
CREATEBACKGROUND = False
CORRECTCORNERS = True
USEPARABOLOID = True
DOPRESMOOTH = True
#CORRECT_BACKGROUND = INPUT_JSON['CORRECT_BACKGROUND']
CORRECT_BACKGROUND = False
#RB_RADIUS = int(INPUT_JSON['RB_RADIUS'])
RB_RADIUS = 5
LIGHTBACKGROUND = False

# parameters for filter
#FILTERTYPE = INPUT_JSON['FILTERTYPE']
#FILTER_RADIUS = INPUT_JSON['FILTER_RADIUS']
FILTERTYPE = 'MEDIAN'
FILTER_RADIUS = 5

# parameters for threshold
#THRESHOLD_METHOD = INPUT_JSON['THRESHOLD_METHOD']
#THRESHOLD_STACKOPTION = INPUT_JSON['STACKOPTION']
#THRESHOLD_BGRD = 'dark'
#THRESHOLD_CORR = INPUT_JSON['THRESHOLD_CORR']
THRESHOLD_METHOD = 'Otsu'
THRESHOLD_STACKOPTION = stackopt
THRESHOLD_BGRD = 'dark'
THRESHOLD_CORR = 1.0

# parameters for saving the binary output
SAVEFORMAT_DEFAULT = 'ome.tiff'
SUFFIX_TH = '_TH'
# SAVEFORMAT = INPUT_JSON['SAVEFORMAT']
SAVEFORMAT = 'ome.tiff'
CONVERT_ORIGINAL = False

# check if SAVEFORMAT is an empty string
if SAVEFORMAT == '':
    SAVEFORMAT = SAVEFORMAT_DEFAULT
    log.info('Save Format Used : ' + SAVEFORMAT)

# for testing
if showdir:
    showfiles(r'/input/')

# check if file exits
files_exists = os.path.exists(IMAGEPATH)
if not files_exists:
    log.info('File: ' + IMAGEPATH + ' was not found. Exiting.')
    #os._exit()


log.info('Starting ...')
log.info('Filename               : ' + IMAGEPATH)
log.info('File exists            : ' + str(files_exists))
log.info('Channel to Analyse     : ' + str(CHINDEX))
log.info('-----------------------------------------')
log.info('Correct Background     : ' + str(CORRECT_BACKGROUND))
log.info('Rolling Ball Radius    : ' + str(RB_RADIUS))
log.info('Light Background       : ' + str(LIGHTBACKGROUND))
log.info('Use paraboloid         : ' + str(USEPARABOLOID))
log.info('Doing PreSmooth        : ' + str(DOPRESMOOTH))
log.info('Correct Corners        : ' + str(CORRECTCORNERS))
log.info('-----------------------------------------')
log.info('Filter Type            : ' + FILTERTYPE)
log.info('Filter Radius          : ' + str(FILTER_RADIUS))
log.info('-----------------------------------------')
log.info('Threshold Method       : ' + THRESHOLD_METHOD)
log.info('Threshold Histo Calc   : ' + str(THRESHOLD_STACKOPTION))
log.info('Threshold Corr-Factor  : ' + str(THRESHOLD_CORR))
log.info('-----------------------------------------')
log.info('Save Format used       : ' + SAVEFORMAT)
log.info('Convert Original Image : ' + str(CONVERT_ORIGINAL))
log.info('------------  START IMAGE ANALYSIS ------------')

#############################################################

# define path stuff
outputimagepath = 'C:/Temp/output/' + os.path.basename(IMAGEPATH)
# create output imagepath
outputpath_orig = outputimagepath

basename = os.path.splitext(outputimagepath)[0]
# remove the extra .ome before reassembling the filename
if basename[-4:] == '.ome':
    basename = basename[:-4]
    log.info('New basename :' + basename)

# Save processed image
outputimagepath = basename + SUFFIX_TH + '.' + SAVEFORMAT
outputpath_orig = basename + '.' + SAVEFORMAT


# run the actual image analysis pipeline
th_image = run(IMAGEPATH, outputpath_orig,
               convert_orig2copy=CONVERT_ORIGINAL,
               sft=SAVEFORMAT,
               verbose=False)

"""
# run the actual image analysis pipeline
th_image, pa_stack, results = run(IMAGEPATH, outputpath_orig,
                                  convert_orig2copy=CONVERT_ORIGINAL,
                                  sft=SAVEFORMAT,
                                  verbose=False)
"""

log.info('Output Path Threshold :' + outputimagepath)
savepath_th_image = ExportTools.savedata(th_image,
                                         outputimagepath,
                                         extension=SAVEFORMAT,
                                         replace=True)

log.info('Saving threshold image ...')


if RESULTSAVE:
    # save the result table as file
    rtsavelocation = AnalyzeTools.create_resultfilename(outputimagepath,
                                                        suffix=SUFFIX_RT,
                                                        extension=SAVEFORMAT_RT)
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

# finish and exit the script
#os._exit()

#ip = th_image.getProcessor()
#ip = ip.convertToByte(True)
#th_image.setProcessor(ip)



th_image.show()
