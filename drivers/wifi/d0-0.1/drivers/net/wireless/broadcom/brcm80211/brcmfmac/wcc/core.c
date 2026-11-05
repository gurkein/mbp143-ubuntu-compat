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
#include <linux/errno.h>
#include <linux/types.h>
#include <core.h>
#include <bus.h>
#include <fwvid.h>
#include <cfg80211.h>

#include "vops.h"

#define BRCMF_WCC_E_LAST		213

static int brcmf_wcc_set_sae_pwd(struct brcmf_if *ifp,
				 struct cfg80211_crypto_settings *crypto)
{
	return brcmf_set_wsec(ifp, crypto->sae_pwd, crypto->sae_pwd_len,
			      BRCMF_WSEC_PASSPHRASE);
}

static int brcmf_wcc_alloc_fweh_info(struct brcmf_pub *drvr)
{
	struct brcmf_fweh_info *fweh;

	fweh = kzalloc_flex(*fweh, evt_handler, BRCMF_WCC_E_LAST);
	if (!fweh)
		return -ENOMEM;

	fweh->num_event_codes = BRCMF_WCC_E_LAST;
	drvr->fweh = fweh;
	return 0;
}

const struct brcmf_fwvid_ops brcmf_wcc_ops = {
	.set_sae_password = brcmf_wcc_set_sae_pwd,
	.alloc_fweh_info = brcmf_wcc_alloc_fweh_info,
};
