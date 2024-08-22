#%%
import glob as glob
import os as os
from AstroDART.utils import data_organiser, get_directory, image_combination
from AstroDART.first_stage import *
from AstroDART.second_stage import *
from AstroDART.third_stage_photometry import *
#%%


uncal_dir = '/uncal_data/'
reduction_dir = '/reduced_data/'
uncal_data_dir = '/uncal_data/XXXXX/'

change_keys = {'INSFILTE': 'FILTER'}
append_keys = {'BUNIT': 'adu', 'GAIN' : 4.23, 'RON' : 6.5, 'SCALE': 0.322}
update_keys = {'OBJECT': 'ASAS'}


uncal_files = glob.glob(uncal_data_dir + '*.fits')

#header_tools(files=uncal_files,header_dict=change_keys).change_header_key_name()

#header_tools(files=uncal_files,header_dict=update_keys).update_header_values()

#header_tools(files=uncal_files,header_dict=append_keys).append_header_key()


organiser = data_organiser(uncal_dir = uncal_dir, reduction_dir = reduction_dir,date='XXXXX',target='XXXX',overwrite='yes')
organiser.run()

data_dir = organiser.get_directory()


bias_dir, bias_files = get_directory(data_dir).bias()
flat_dir, flat_files, flat_filters = get_directory(data_dir).flatfield()
object_dir, object_files, object_filters = get_directory(data_dir).science()




#%%

region = '[1000:3040,1000:3040]'

step = trimmer(wdir = bias_dir, files = bias_files,region=region, overwrite='yes')

results_trim = step.run()

step = deviation_calculation(wdir = bias_dir, files = results_trim, overwrite='yes')

results_dc = step.run()

step = gain_correction(wdir = bias_dir, files = results_dc,overwrite='yes')

results_gc = step.run()



masterbias = image_combination(wdir=bias_dir,files=results_gc,output_name='Masterbias.fits',combining_method='median',clipping_method='sigclip',minclip=2,maxclip=5).run()


for ii in range(len(flat_dir)):

    step = trimmer(wdir = flat_dir[ii], files = flat_files[ii], region=region, overwrite='yes')

    results_trim = step.run()

    step = deviation_calculation(wdir = flat_dir[ii], files = results_trim, overwrite='yes')

    results_dc = step.run()

    step = gain_correction(wdir = flat_dir[ii], files = results_dc,overwrite='yes')

    results_gc = step.run()

    results_bias_subtraction = subtract_bias(wdir=flat_dir[ii],files=results_gc,masterbias_file=masterbias,overwrite='yes').run()

    globals()['masterflat_' + flat_filters[ii]] = image_combination(wdir=flat_dir[ii],files=results_bias_subtraction,output_name=f'Masterflat_{flat_filters[ii]}.fits',combining_method='median',clipping_method='sigclip',minclip=2,maxclip=5).run()





for ii in range(len(object_dir)):

    step = trimmer(wdir = object_dir[ii], files = object_files[ii], region=region, overwrite='yes')

    results_trim = step.run()

    step = deviation_calculation(wdir = object_dir[ii], files = results_trim, overwrite='yes')

    results_dc = step.run()

    step = gain_correction(wdir = object_dir[ii], files = results_dc,overwrite='yes')

    results_gc = step.run()

    step = cosmic_ray_laplacian_correction(wdir = object_dir[ii], files = results_gc, overwrite='yes')

    results_crlc = step.run()

    results_bias_subtraction = subtract_bias(wdir=object_dir[ii],files=results_crlc,masterbias_file=masterbias,overwrite='yes').run()

    results_flat_correction = correct_flatfield(wdir=object_dir[ii], files=results_bias_subtraction, masterflatfield_file = globals()['masterflat_' + flat_filters[ii]], overwrite='yes').run()


directories, files = finalize_stage1(data_dir=data_dir,object_dir=object_dir,bias_dir=bias_dir,flatfield_dir=flat_dir).run()
#%%




api_key = ''
fwhms_out = []
for ii in range(len(directories)):
    globals()[f'failed_astrometry_files_filter_{object_filters[ii]}'] = []
    fwhms = get_fwhm(files[ii]).estimate_fwhm()
    fwhms_out.append(fwhms)
    print(fwhms)
    globals()[f'failed_astrometry_files_filter_{object_filters[ii]}'].append(astrometry(directory=directories[ii],files=files[ii],api_key=api_key,fwhm=fwhms).run())



#%%
directories, files, filters = get_directory(data_dir = '/XXXX/XXXX/').science_final()


target, comparison = coordinates(files=files[0],reference_frame=0).from_image()

target_in_px = []
comparison_in_px = []

for ii in range(len(files)):

    target_in_px_filter = coordinates(files=files[ii],world_coordinates=target).world_to_px()
    target_in_px.append(target_in_px_filter) 

for ii in range(len(comparison)):
    comparison_in_px_filters = []
    for jj in range(len(files)):
        comparison_in_px_filter = coordinates(files=files[jj],world_coordinates=comparison[ii]).world_to_px()
        comparison_in_px_filters.append(comparison_in_px_filter) 
    
    comparison_in_px.append(comparison_in_px_filters)



step = photometry(phot_method='sky',aperture_type='fwhm',files=files,filters=filters,obs_location='OT',target_coord = target, comparison_coord=comparison,save_results=True,save_data_dir='/XXXX/XXX/')

#step = photometry(phot_method='pixel',aperture_type='custom',radius_phot=15,radius_annulus=20,radius_dannulus=25,files=files,filters=filters,obs_location='OT',single_coord=target_in_px, multi_coord=comparison_in_px, save_results=True,save_data_dir='/XXXX/XXX/')

photometry_results = step.run_multi_coord()
