
# Boostrsa

This library is based on rsatoolbox(https://github.com/rsagroup/rsatoolbox).

The purpose of library is made to boost calcuation speed for searchlight RSA(Representational Similarity Analysis). However, It is still in development, so this library only includes tools for boosting crossnobis distance calculation for constructing RDM(Representational Dissimilartiy Matrix) on the whole brain. 

## How it works?

Basically, this library uses a Nvidia's GPU instead of CPU for parallel processing. In the searchlight analysis, the data targeted for constructing the RDM in volvxes a voxel and its neighboring voxels. That is well-suited for parallel processing since the calculations for each target are independent of one another. This library utilizes GPU-compatible libraries such as Numba and Cupy to facilitate this process.

## Dependencies

To use this library, you need to have a Nvidia's GPU and CUDA. Additionally, this library heavily relies on Cupy and Numba. It is essential to install the appropriate versions of these libraries.

### cupy

Cupy is designed to work with specific versions of CUDA. See cupy's guide and install appropriate version in correspond to your system (https://github.com/cupy/cupy).

Please check your cuda version to install cupy.
- versions
    - cupy-cuda10x (for cuda 10)
    - cupy-cuda11x (for cuda 11)
    - cupy-cuda12x (for cuda 12)
    

If you installed the cuda10 in your computer, then install cupy-cuda10x. install cupy-cuda10x. ex) pip install cupy-cuda10x

### numba

The numba library is a powerful tool that enbales python functions to be compiled to machine code at runtime using the LLVM. One of its key features is the ability to generate native code for different architectures, including CPUs and GPUs, which greatly accelerates the execution of data-heavy and computationally intense python code.

Please see installation guideline of numba (https://numba.pydata.org/numba-doc/latest/user/installing.html).

Pip installation). 

- pip install numba

### rsatoolbox

The rsatoolbox is a Python library specifically designed for Representational Similarity Analysis (RSA). 

Please see installation guideline of rsatoolbox (https://github.com/rsagroup/rsatoolbox)

- pip install rsatoolbox

# Installation

pip install boostrsa

# Checked version

These are the latest checked environment.

- OS
    - Linux, ubuntu - 21.10
- numba
    - 0.57.0 ~ 0.59.1 is fine to use
- cupy
    - cupy-cuda11x
    - cupy-cuda12x

# Future works

- Add calculation sources to get neighbors and centers (boost)
- Add RSA sources (boost)
- Support other calculation methods except crossnobis distance
