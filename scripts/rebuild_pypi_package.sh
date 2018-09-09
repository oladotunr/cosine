#!/bin/bash
source venv/bin/activate

set -e

function increment_version {
    v=$1
    if [ -z $2 ]
    then
        rgx='^((?:[0-9]+\.)*)([0-9]+)($)'
    else

        rgx='^((?:[0-9]+\.){'$(($2-1))'})([0-9]+)(\.|$)'
        for (( p=`grep -o "\."<<<".$v" | wc -l`; p<$2; p++)); do
            v+=.0;
        done;
    fi
    val=`echo -e "$v" | perl -pe 's/^.*'$rgx'.*$/$2/'`
    echo "$v" | perl -pe s/$rgx.*$'/${1}'`printf %0${#val}s $(($val+1))`/
}

# roll the version number

# extract the version number from the setup.py file
VER=$(sed -n '/version=\"/p' ./setup.py | sed 's/[[:alpha:]([:space:]\"=,]//g' | awk -F- '{print $1}')
echo "Extracted version is: Last: ${VER}"
LAST_VER=${VER}

# increment the version number
VER=$( increment_version ${VER} )
echo "Version is: Last: ${LAST_VER}, Next: ${VER}"

# update the version number in the setup.py file
sed "s/${LAST_VER}/${VER}/g" < ./setup.py > ./setup.py.tmp
mv ./setup.py.tmp ./setup.py

# clean up the build files...
rm -r ./build
rm ./dist/*

# build the latest package...
python3 setup.py sdist bdist_wheel