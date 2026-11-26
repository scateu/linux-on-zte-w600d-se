if load usb 0:1 0x00800000 /native-uboot/u-boot-w600d-native.bin; then
    if load usb 0:1 0x10000000 /native-uboot/w600d-native-chain.bin; then
        usb stop
        go 0x10000000
    fi
fi
echo Native-display chainload failed; factory shell remains active
