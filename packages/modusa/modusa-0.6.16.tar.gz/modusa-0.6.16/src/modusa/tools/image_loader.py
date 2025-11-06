#!/usr/bin/env python3

#---------------------------------
# Author: Ankit Anand
# Date: 06/11/25
# Email: ankit0.anand0@gmail.com
#---------------------------------

import imageio.v3 as iio

def load_image(path):
	"""
	Loads an images using imageio.

	Parameters
	----------
	path: str | PathLike
		Image file path.
	
	Returns
	-------
	ndarray
		Image array (2D/3D with RGB channel)
	"""
	img = iio.imread(path)
	
	return img