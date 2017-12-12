# this file is created by TinyFish on 5th, May, 2017
# it is for toggle touchpad by a keyboard button

#!/bin/bash
#touchpad_id=$(xinput list | grep -i Synaptics | grep -iEo [0-9]{2})
touchpad_id=$(xinput list | grep -i Synaptics | grep -oP "(?<=id=)\d+")
touchpad_status=$(xinput list-props $touchpad_id | grep -i "Device Enabled" | grep -iEo "[0-9]+$")
echo $touchpad_status
#touchpad_status=$(synclient -l | grep -i TouchpadOff | grep -iEo [0-9])
if [ $touchpad_status -eq 0 ] ; then
    notify-send -i "gtk-yes" "Touchpad on" "AlpsPS/2 ALPS GlidePoint has been turned on"
#    synclient touchpadoff=1
    echo "enable touchpad" $touchpad_id
    xinput --enable $touchpad_id
else
    notify-send -i "gtk-no" "Touchpad off" "AlpsPS/2 ALPS GlidePoint has been turned off"
#    synclient touchpadoff=0
    echo "disable touchpad" $touchpad_id
    xinput --disable $touchpad_id
fi
