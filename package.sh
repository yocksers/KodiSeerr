#!/bin/bash

rm -rf plugin.video.kodiseerr.zip
mkdir plugin.video.kodiseerr
for item in ./*;do
    if [[ "$item" != "./plugin.video.kodiseerr" ]] \
    && [[ "$item" != "./README.md" ]] \
    && [[ "$item" != "./package.sh" ]];then
        cp -r "$item" plugin.video.kodiseerr/
    fi
done
zip -r plugin.video.kodiseerr.zip ./plugin.video.kodiseerr
rm -rf plugin.video.kodiseerr
