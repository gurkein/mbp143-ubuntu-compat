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
#ifdef CONFIG_OF
int brcmf_of_probe(struct device *dev, enum brcmf_bus_type bus_type,
		   struct brcmf_mp_device *settings);
#else
static int brcmf_of_probe(struct device *dev, enum brcmf_bus_type bus_type,
			  struct brcmf_mp_device *settings)
{
	return 0;
}
#endif /* CONFIG_OF */
