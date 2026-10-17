"""Reflected-boundary Richardson–Lucy with recorded measured/estimated PSFs."""
import numpy as np
from scipy.signal import fftconvolve
from pydantic import BaseModel,Field,ConfigDict
from organelle_scope.image_io import ImageError

class DeconvolutionOptions(BaseModel):
    model_config=ConfigDict(extra='forbid')
    image_id:str
    psf_image_id:str|None=None
    psf_background:float=Field(default=0,ge=0,le=65535,allow_inf_nan=False)
    sigma_xy_um:float|None=Field(default=None,gt=0,le=100,allow_inf_nan=False)
    sigma_z_um:float|None=Field(default=None,gt=0,le=100,allow_inf_nan=False)
    iterations:int=Field(default=10,ge=1,le=100)
    acknowledge_psf_model:bool=False

def gaussian_psf(sigmas):
    if min(sigmas)<=0 or max(sigmas)>16:raise ImageError('Estimated PSF sigma must be positive and at most 16 source voxels on each axis.')
    axes=[np.arange(-int(np.ceil(4*s)),int(np.ceil(4*s))+1,dtype=float) for s in sigmas]
    grids=np.meshgrid(*axes,indexing='ij');kernel=np.exp(-sum((g/s)**2/2 for g,s in zip(grids,sigmas)));return (kernel/kernel.sum()).astype(np.float32)

def richardson_lucy_reflect(image,psf,iterations,checkpoint=lambda:None,progress=lambda i:None):
    # Poisson-model multiplicative update. No intensity normalization or [-1,1] clipping.
    if not np.isfinite(psf).all() or np.any(psf<0) or psf.sum()<=0 or any(n%2==0 for n in psf.shape):raise ImageError('PSF must be finite, nonnegative, odd-sized and have positive mass.')
    psf=(psf/psf.sum(dtype=np.float64)).astype(np.float32);pad=tuple((n//2,n//2) for n in psf.shape)
    data=np.pad(image.astype(np.float32),pad,mode='reflect');estimate=np.full_like(data,.5);reverse=psf[tuple(slice(None,None,-1) for _ in psf.shape)]
    for i in range(iterations):
        checkpoint();blur=fftconvolve(estimate,psf,mode='same');ratio=data/(blur+1e-12)
        estimate*=np.maximum(fftconvolve(ratio,reverse,mode='same'),0);progress(i+1)
    slices=tuple(slice(a,a+n) for (a,_),n in zip(pad,image.shape));result=estimate[slices].copy()
    if not np.isfinite(result).all():raise ImageError('Deconvolution produced non-finite intensities.')
    return result
