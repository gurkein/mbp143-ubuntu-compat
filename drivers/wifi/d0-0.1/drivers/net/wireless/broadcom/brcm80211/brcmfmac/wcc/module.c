// SPDX-License-Identifier: ISC
/*
 * Distribution changes by mbp143-ubuntu-compat contributors, 2026-11-05:
 * added this notice to the selected source snapshot. Functional adaptations
 * are described in docs/source-provenance.md and the accompanying patches.
 * Original authorship and per-file license terms remain unchanged.
 */
/*
 * Copyright (c) 2022 Broadcom Corporation
 */
#include <linux/module.h>
#include <bus.h>
#include <core.h>
#include <fwvid.h>

#include "vops.h"

static int __init brcmf_wcc_init(void)
{
	return brcmf_fwvid_register_vendor(BRCMF_FWVENDOR_WCC, THIS_MODULE,
					   &brcmf_wcc_ops);
}

static void __exit brcmf_wcc_exit(void)
{
	brcmf_fwvid_unregister_vendor(BRCMF_FWVENDOR_WCC, THIS_MODULE);
}

MODULE_DESCRIPTION("Broadcom FullMAC WLAN driver plugin for Broadcom mobility chipsets");
MODULE_LICENSE("Dual BSD/GPL");
MODULE_IMPORT_NS("BRCMFMAC");

module_init(brcmf_wcc_init);
module_exit(brcmf_wcc_exit);
