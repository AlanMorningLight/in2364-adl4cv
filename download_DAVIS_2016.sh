# Get DAVIS 2016

INITIAL_DIR=$(pwd)

cd DAVIS_2016
wget https://graphics.ethz.ch/Downloads/Data/Davis/DAVIS-data.zip
unzip DAVIS-data.zip
rm DAVIS-data.zip

cd $INITIAL_DIR