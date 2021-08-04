# Introduction

This are the exercises copied from the lecture Information Retrieval FS 2021 by Gislain Fourny. As all exercises are on a remote jupyter server I copied them here for my convenience. I take no responsibility for any bugs I may introduced.

# Installation  

I assume that you have Anaconda installed on your computer if not go to [anaconda.com](https://www.anaconda.com). Then after that follow these steps. If you are using pip instead the installation process should be similar.

1. Open your command window and set the current directory to the root folder containing all the files
2. use `conda env create -f environment.yml` to create a new environment
3. type `conda activate ir` 
4. then `jupyter notebook` to start your start your coding environment

Happy Coding!

# Notes

You may have to add

````python
import sys
sys.path.append("../../")
````

at the beginning of each notebook to import the stuff in the root.
