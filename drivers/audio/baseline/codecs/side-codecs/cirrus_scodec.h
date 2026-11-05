/* SPDX-License-Identifier: GPL-2.0
/*
 * Distribution changes by mbp143-ubuntu-compat contributors, 2026-11-05:
 * added this notice to the selected source snapshot. Functional adaptations
 * are described in docs/source-provenance.md and the accompanying patches.
 * Original authorship and per-file license terms remain unchanged.
 */
 *
 * Copyright (C) 2023 Cirrus Logic, Inc. and
 *                    Cirrus Logic International Semiconductor Ltd.
 */

#ifndef CIRRUS_SCODEC_H
#define CIRRUS_SCODEC_H

int cirrus_scodec_get_speaker_id(struct device *dev, int amp_index,
				 int num_amps, int fixed_gpio_id);

#endif /* CIRRUS_SCODEC_H */
