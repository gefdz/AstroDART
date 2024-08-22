Astrophotography guide
====================

First stage: Image reduction 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: 

    The first two stages are mostly the same as in the photometry case shown in :ref:`photometry` , with the exception of cosmic ray correction.


This pipeline is intended for two main uses, astrophotography data reduction (including image combination and alignment) and photometry. This notebook in particular is a demo of the former. This pipeline is basically a wrapper of astropy functions and in particular those of `ccdproc <https://ccdproc.readthedocs.io/en/latest/>`_. We being by importing the necessary packages


.. code-block:: python

    import glob as glob
    import os as os
    from AstroDART.utils import  data_organiser, get_directory, image_combination
    from AstroDART.first_stage import *
    from AstroDART.second_stage import *
    from AstroDART.third_stage_astrophotography import *


Let's define where the data are stored. I recommend using the empty directories you can find when you did the git clone of the repository but any uncal and reduced data directories will work. However it is important that the uncal_data_dir has the dates of observation as YYMMDD inside. 230313_crab will work if you observed the Crab Nebula that day, but it could generate conflict further down the line, the code allows for multiple targets to be observed in one night so there is no need to do that.

.. code-block:: python

    uncal_dir = '/uncal_data/'
    reduction_dir = '/reduced_data/'
    uncal_data_dir = '/uncal_data/XXXXX/'

The first functionality is related to fits headers. Although there are standards in place different telescopes use different keys for the same field in the fits header. For instance IAC80 uses INSFILTE for the filter key. However in the hopes of making the code more general we would like to use the word FILTER instead. We can change this key using the header tools class. This class also allows to append new keys and update the value of already existing ones.


.. code-block:: python

    change_keys = {'INSFILTE': 'FILTER'}
    append_keys = {'BUNIT': 'adu', 'GAIN' : 4.23, 'RON' : 6.5, 'SCALE': 0.322}
    update_keys = {'OBJECT': 'ASAS'}


    uncal_files = glob.glob(uncal_data_dir + '*.fits')


    header_tools(files=uncal_files,header_dict=change_keys).change_header_key_name()

    header_tools(files=uncal_files,header_dict=update_keys).update_header_values()

    header_tools(files=uncal_files,header_dict=append_keys).append_header_key()


Now let us organize the data in the necessary folders. This will make things more easy to follow. The following code will copy the data to the directory where the reduction is to be done. This will only copy those files that have the target field in *data_ organiser* equal to the name in the *OBJECT* field in the header. This allows you to reduce targets observed in the same night independently. All commands expect lists of strings (the paths of the files), not the hdul data itself.

.. code-block:: python

    organiser = data_organiser(uncal_dir = uncal_dir, reduction_dir = reduction_dir,date='XXXXX',target='XXXX',overwrite='yes')
    organiser.run()

    data_dir = organiser.get_directory()


    bias_dir, bias_files = get_directory(data_dir).bias()
    flat_dir, flat_files, flat_filters = get_directory(data_dir).flatfield()
    object_dir, object_files, object_filters = get_directory(data_dir).science()


Now that we have the data where we want it let's start the reduction. First thing to do is correct the image of overscan and trim the image. I will skip overscan as it is not as common you may look into the source code but the idea is the same as the rest of commands. Assuming the image has some vignneting (or that we want to crop it) lets define a region and run the trimmer class. After that we will calculate the deviation (the uncertainties basically, these are not strictly necessary but you can still do some science with these images) and we will correct of gain. If this filed is not in the header you should run it using header tools as described above. We will start with the bias files.

.. code-block:: python

    region = '[1000:3040,1000:3040]'

    step = trimmer(wdir = bias_dir, files = bias_files,region=region, overwrite='yes')

    results_trim = step.run()

    step = deviation_calculation(wdir = bias_dir, files = results_trim, overwrite='yes')

    results_dc = step.run()

    step = gain_correction(wdir = bias_dir, files = results_dc,overwrite='yes')

    results_gc = step.run()


The masterbias can be calculated with the *image_combination* class. The methods for combining images are median, average, sum, scaled and weighted (please refer to `the ccdproc image combination guide <https://ccdproc.readthedocs.io/en/latest/image_combination.html>`_ for more information). The methods for clipping method are sigclip, extrema_clipping and minmax. You may also specify the maximum amount of memory used, the deafult is 1 GB of RAM.



.. code-block:: python

    masterbias = image_combination(wdir=bias_dir,files=results_gc,output_name='Masterbias.fits',
                               combining_method='median',clipping_method='sigclip',minclip=2,maxclip=5).run()


Let's repeat the same steps but for flats, in this case we will subtract the masterbias file and combine the images into their respective masterflatfield.

.. code-block:: python

    for ii in range(len(flat_dir)):

        step = trimmer(wdir = flat_dir[ii], files = flat_files[ii], region=region, overwrite='yes')

        results_trim = step.run()

        step = deviation_calculation(wdir = flat_dir[ii], files = results_trim, overwrite='yes')

        results_dc = step.run()

        step = gain_correction(wdir = flat_dir[ii], files = results_dc,overwrite='yes')

        results_gc = step.run()

        results_bias_subtraction = subtract_bias(wdir=flat_dir[ii],files=results_gc,masterbias_file=masterbias,overwrite='yes').run()

        globals()['masterflat_' + flat_filters[ii]] = image_combination(wdir=flat_dir[ii],
                                                                        files=results_bias_subtraction,
                                                                        output_name=f'Masterflat_{flat_filters[ii]}.fits',
                                                                        combining_method='median',clipping_method='sigclip',
                                                                        minclip=2,maxclip=5).run()


Now let's do the same for the object files, we will divide by the master flatfield, there is no need to normalize as the function takes care of that by itself. Unlike in the photometry case we are interested in eliminating the cosmic rays, there are two methods, cosmic_ray_laplacian_correction and cosmic_ray_median_correction, the latter is similar to the one available in IRAF.


.. code-block:: python

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

        results_flat_correction = correct_flatfield(wdir=object_dir[ii], files=results_bias_subtraction, 
                                                    masterflatfield_file = globals()['masterflat_' + flat_filters[ii]], overwrite='yes').run()



Done! The design philosophy behind this pipeline is that you can either run it entirely with minimal user input (only at the beginning) or step by step. This generates a lot of intermediate files, and these may not be necessary at the end. So let's just delete them and finalize stage 1. The finalize_stage1 class returns the directories and files that have been reduced and rearranges the files so that you have date/target/filters/data.

.. code-block:: python

    directories, files = finalize_stage1(data_dir=data_dir,object_dir=object_dir,bias_dir=bias_dir,flatfield_dir=flat_dir).run()



Second stage: Astrometry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The final objective is doing astrophotography, so, aligning images is a must. This program makes use of `Astrometry.net <https://nova.astrometry.net/>`_ to astromtrize images, they will later be projected in the same wcs. You should register and the obtain your API key. It will be used to astrometrize the images.

.. code-block:: python

    api_key = ''
    fwhms_out = []
    for ii in range(len(directories)):
        globals()[f'failed_astrometry_files_filter_{object_filters[ii]}'] = []
        fwhms = get_fwhm(files[ii]).estimate_fwhm()
        fwhms_out.append(fwhms)
        print(fwhms)
        globals()[f'failed_astrometry_files_filter_{object_filters[ii]}'].append(astrometry(directory=directories[ii],
                                                                                            files=files[ii],api_key=api_key,fwhm=fwhms).run())

If you decided to stop here (it can take up to 2 hours in the worst case scenario depending on the astrometry) and continue another day but stll decided to continue with this code you would find that the lists of files etc are not stored in memory. Because doing it yourself is quite annoying the code has got you covered. Just run the following. Data dir should be where the data are, so /reduced_data/YYMMDD/target/

.. code-block:: python

    directories, files, filters = get_directory(data_dir = '/XXXX/XXXX/').science_final()

Third stage: Image combination
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We are ready to align and combine the images to create our beautiful color images. First let's align all images with respect to one reference frame.

.. code-block:: python

    aligned_images = align(files_to_align=files,directories=directories,reference_frame=files[0][0]).run()

Let's combine those images which are in the same filter. 

.. code-block:: python

    combined_images = []
    for ii in range(len(filters)):
        combined_images.append(image_combination(wdir=directories[ii],files=aligned_images[ii],
                                                output_name=f'Combined_image_{filters[ii]}.fits',
                                                combining_method='median',clipping_method='sigclip',
                                                minclip=2,maxclip=5,remove_files='yes').run())

Done!! This is the end of stage 3 and the astrophotography guide. You can now create beautiful images, good luck!! 
