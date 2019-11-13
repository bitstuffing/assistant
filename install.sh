#!/bin/bash

git clone https://github.com/Kitt-AI/snowboy
cd snowboy/swig/Python3
make -j4
cp snowboydetect.py ../../../
cp _snowboydetect.so ../../../
cp snowboydecoder.py ../../../

#raspbyan
#sudo apt-get install libatlas-base-dev sox libpcre3 libcre3-dev
#wget http://downloads.sourceforge.net/swig/swig-3.0.10.tar.gz
#archlinux
#sudo pacman -S swig python-snowboy julia openblas
#yaourt -S openblas-lapack
#replace"     LDLIBS := -lm -ldl -lf77blas -lcblas -llapack -latlas" by "    LDLIBS := -lm -ldl -lcblas -llapack"
