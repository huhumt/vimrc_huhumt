#!/usr/bin/env bash

# get current working directory
cur_dir=$(pwd)
backup_dir=${cur_dir##*/}

# get year-month-day informathon
year=$(date +%Y)
month=$(date +%m)
day=$(date +%d)
cur_date=$year
cur_date+=$month
cur_date+=$day

# get hour:minute:second informathon
hour=$(date +%H)
minute=$(date +%M)
second=$(date +%S)
cur_time=$hour
cur_time+=$minute
cur_time+=$second

# use date and time informathon as backup file appendix
appendix="_backup_"
appendix+=$cur_date
appendix+="_"
appendix+=$cur_time

# generate backup filename
backup_filename=$backup_dir
backup_filename+=$appendix
backup_filename+=".tar.gz"

ori_dir=$backup_dir

# get current user's home directory
usr_home=$(eval echo ~${SUDO_USER})
dest_dir=$usr_home
dest_dir+="/backup/"
# check whether exist backup directory
if [ ! -d $dest_dir ]
then
    mkdir $dest_dir
fi

# get final destination
dest_dir+=$backup_filename

cd ../
tar -zcf $dest_dir $ori_dir

if [ $? -eq 0 ]
then
    printf "\n************************************************************************************\n"
    printf "Time: $year-$month-$day, $hour:$minute:$second\n"
    printf "Orig: $ori_dir\n"
    printf "Dest: $dest_dir\n"
    printf "************************************************************************************\n"
else
    printf "Fail to backup directory\n"
fi
