#!/bin/sh
if [ ! -r /proc/cmdline ]; then
    mount -t proc proc /proc
fi
if [ ! -d /sys/class/graphics ]; then
    mount -t sysfs sysfs /sys
fi
if [ -c /dev/fb0 ] &&
   [ "$(cat /sys/class/graphics/fb0/virtual_size)" = '1920,1080' ] &&
   [ "$(cat /sys/class/graphics/fb0/stride)" = 7680 ] &&
   [ "$(cat /sys/class/graphics/fb0/bits_per_pixel)" = 32 ]; then
    printf 'Writing 8294400 white bytes to fb0; this is not a text console.\n'
    if dd if=/dev/zero bs=7680 count=1080 2>/dev/null |
       tr '\000' '\377' |
       dd of=/dev/fb0 bs=7680 count=1080 iflag=fullblock conv=notrunc; then
        printf '0,0\n' > /sys/class/graphics/fb0/pan
    else
        printf 'Framebuffer write failed; no pan requested.\n'
    fi
else
    printf 'Expected framebuffer geometry not found; no framebuffer write.\n'
fi
