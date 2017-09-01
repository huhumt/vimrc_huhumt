#!/usr/bin/env bash

echo ""

# delete old tags and cscope files
if [ -e "tags" ]
then
    rm tags
fi

cscope_item=( ./cscope.out ./cscope.in.out ./cscope.po.out )
for item in $cscope_item[@]
do
    if [ -f $item ]
    then
        rm $item
    fi
done

echo "Update code tags"

# generate ctags
ctags -Rn
# check whether tags file generated
find ./ -name "tags" > /dev/null
if [ $? -eq 0 ]
then
    echo "...ctags built"
else
    echo "Fail to build ctags"
fi

# generate cscope
cscope -Rbkq
# check how many cscope file generated
cs_num=$(find ./ -name "cscope*" | wc -l)
if [ $cs_num -eq 3 ]
then
    echo "...cscope built"
else
    echo "Fail to build cscope"
fi

echo "Finish update code tags, let's roll"
