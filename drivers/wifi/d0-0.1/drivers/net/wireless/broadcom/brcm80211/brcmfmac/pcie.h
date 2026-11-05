// SPDX-License-Identifier: ISC
/*
 * Distribution changes by mbp143-ubuntu-compat contributors, 2026-11-05:
 * added this notice to the selected source snapshot. Functional adaptations
 * are described in docs/source-provenance.md and the accompanying patches.
 * Original authorship and per-file license terms remain unchanged.
 */
/*
 * Copyright (c) 2014 Broadcom Corporation
 */
#ifndef BRCMFMAC_PCIE_H
#define BRCMFMAC_PCIE_H


struct brcmf_pciedev {
	struct brcmf_bus *bus;
	struct brcmf_pciedev_info *devinfo;
};

#endif /* BRCMFMAC_PCIE_H */
