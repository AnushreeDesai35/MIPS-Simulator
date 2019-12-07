#! /bin/sh

if [ "$1" = "clean" ]; then
	rm -f ./*.pyc
    file="result.txt"
    if [ -f $file ] ; then
        rm $file
    fi
