# Introduction

These are the exercises from the lecture Information Retrieval FS 2021 by Ghislain Fourny. Since all the exercises are on a remote Jupyter server, I copied them here for convenience, that I can access them even after the lecture. I take no responsibility for any errors I may have introduced.

All credit goes to the TA team and Mr. Fourny for providing not only this code, but also a fantastic lecture. [link](https://systems.ethz.ch/education/courses/2021-spring/information-retrieval.html)

# Installation  

I assume that you have Anaconda installed on your computer if not go to [anaconda.com](https://www.anaconda.com). Then after that follow these steps. If you are using pip instead the installation process should be similar.

1. Open your command window and set the current directory to the root folder containing all the files
2. use `conda env create -f environment.yml` to create a new environment
3. type `conda activate ir` 
4. then `jupyter notebook` to start your jupyter coding environment

Happy Coding!

# Notes

You may have to add

````python
import sys
sys.path.append("../../")
````

at the beginning of a notebook to import the stuff in the root.
