#!/bin/bash
# Preserve dynamically requested vendor modules in host-only images.
check() {
    [[ "$kernel" == "7.0.14-mbp14342p1" ]] || return 1
    [[ -f /lib/modules/7.0.14-mbp14342p1/updates/mbp143-wifi/brcmfmac.ko ]] || return 1
    return 0
}
installkernel() {
    hostonly='' instmods -c brcmfmac-wcc brcmfmac-cyw brcmfmac-bca
}
