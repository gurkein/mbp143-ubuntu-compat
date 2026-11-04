#!/bin/bash
# brcmfmac requests vendor modules dynamically; they are not hard dependencies.
check() {
    [[ "$kernel" == "7.0.14-mbp14342p1" ]] || return 1
    [[ -f /lib/modules/7.0.14-mbp14342p1/updates/mbp143-wifi-d0/brcmfmac.ko ]] || return 1
    return 0
}

installkernel() {
    # A failed probe leaves helpers unloaded; host-only filtering must not omit them.
    hostonly='' instmods -c brcmfmac-wcc brcmfmac-cyw brcmfmac-bca
}
