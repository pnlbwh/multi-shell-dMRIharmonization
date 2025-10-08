#!/usr/bin/env bash

# download test data
test_data=multi-harm-test # change this value if test data name is changed
if [ ! -f ${test_data}.zip ]
then
    wget "https://www.dropbox.com/scl/fi/lx4d6vslyzs64rehbki45/multi-harm-test.zip?rlkey=0ox9pmg3gu04xs6hzl6jvctgt&st=o2qlfxn0" -O ${test_data}.zip
fi

unzip ${test_data}.zip

cd ${test_data}
CURRDIR=`pwd`

# append path to image list
sed -i "s+TESTDIR+$CURRDIR+g" *csv

### Run pipeline and obtain statistics when same number of matched reference and target images are used in
### tempalate creation and harmonization
# run test
./run.sh


