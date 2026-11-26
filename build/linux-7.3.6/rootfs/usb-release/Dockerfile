FROM w600d-ubuntu-xfce:7.3.6
ARG APT_PROXY
RUN printf "#!/bin/sh\nexit 101\n" > /usr/sbin/policy-rc.d && \
    chmod 0755 /usr/sbin/policy-rc.d && \
    if [ -n "$APT_PROXY" ]; then \
        printf "Acquire::http::Proxy \"%s\";\nAcquire::https::Proxy \"%s\";\n" "$APT_PROXY" "$APT_PROXY" > /etc/apt/apt.conf.d/90-build-proxy; \
    fi && \
    apt-get -o APT::Update::Error-Mode=any -o Acquire::Languages=none update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        cloud-guest-utils fdisk wpasupplicant wireless-regdb bluez libinput-tools iw rfkill && \
    apt-get clean && \
    rm -f /usr/sbin/policy-rc.d /etc/apt/apt.conf.d/90-build-proxy /etc/ssh/ssh_host_* \
        /etc/systemd/system/serial-getty@ttyS2.service.d/bringup.conf && \
    rm -rf /var/lib/apt/lists/*
COPY rootfs/usb-release/grow-root /usr/local/sbin/w600d-grow-root
COPY rootfs/usb-release/w600d-grow-root.service /etc/systemd/system/
COPY rootfs/usb-release/FIRST-STEPS.txt /home/linux/Desktop/FIRST-STEPS.txt
RUN chmod 0755 /usr/local/sbin/w600d-grow-root && \
    chown linux:linux /home/linux/Desktop/FIRST-STEPS.txt && \
    systemctl enable w600d-grow-root.service && \
    test -x /usr/bin/growpart && test -x /usr/sbin/sfdisk && test -x /usr/sbin/resize2fs
