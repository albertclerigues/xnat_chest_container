FROM ubuntu:18.04
MAINTAINER Sergi Valverde <svalverde@eia.udg.edu>

# ------------------------------------------------------------------------------
# Install basic libraries + miniconda
# ------------------------------------------------------------------------------

RUN apt-get update
RUN apt-get --assume-yes install wget git curl bzip2 zip unzip imagemagick dcmtk
RUN apt-get -qq update && apt-get -qq -y install curl bzip2 \
    && curl -sSL https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -bfp /usr/local \
    && rm -rf /tmp/miniconda.sh \
    && conda install -y python=3 \
    && conda update -y conda \
    && apt-get -qq -y remove curl bzip2 \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
    && conda clean --all --yes
ENV PATH /opt/conda/bin:$PATH
RUN pip install --upgrade pip

# ------------------------------------------------------------------------------
# enable neurodebian packages
# install mricron, dcm2niix, minimal fsl and fsl MNI152 templates
# ------------------------------------------------------------------------------

#RUN wget -O- http://neuro.debian.net/lists/xenial.us-tn.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
#RUN apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9
#RUN apt-get update
#RUN apt-get --assume-yes install mricron fsl fsl-mni152-templates dcm2niix dcmtk imagemagick
RUN apt update && apt install -y libsm6 libxext6

# ------------------------------------------------------------------------------
# xnat libraries
# ------------------------------------------------------------------------------
RUN pip install pyxnat nibabel pydicom requests opencv-python
RUN conda install gdcm -c conda-forge

# install fastai
RUN conda install -c pytorch -c fastai fastai


# ------------------------------------------------------------------------------
# container standard dirs
# ------------------------------------------------------------------------------

RUN mkdir /input  # xnat inputs mount
RUN mkdir /output # xnat outputs mount
RUN mkdir /data # user intermediate data
RUN mkdir /src
RUN mkdir /src/tmp
RUN touch /src/__init__.py
ENV PATH=/src:${PATH}

# ------------------------------------------------------------------------------
# Add all source files inside image
# ------------------------------------------------------------------------------
ADD run_container.py /src/
ADD lib /src/lib
ADD models /src/models

# EXPOSE ports for email sending
EXPOSE 25
