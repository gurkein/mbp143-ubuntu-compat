// SPDX-License-Identifier: ISC
/*
 * Distribution changes by mbp143-ubuntu-compat contributors, 2026-11-05:
 * added this notice to the selected source snapshot. Functional adaptations
 * are described in docs/source-provenance.md and the accompanying patches.
 * Original authorship and per-file license terms remain unchanged.
 */
/*
 * Copyright (c) 2012 Broadcom Corporation
 */

#include <linux/device.h>
#include <linux/module.h> /* bug in tracepoint.h, it should include this */

#ifndef __CHECKER__
#define CREATE_TRACE_POINTS
#include "bus.h"
#include "tracepoint.h"
#include "debug.h"

void __brcmf_err(struct brcmf_bus *bus, const char *func, const char *fmt, ...)
{
	struct va_format vaf = {
		.fmt = fmt,
	};
	va_list args;

	va_start(args, fmt);
	vaf.va = &args;
	if (bus)
		dev_err(bus->dev, "%s: %pV", func, &vaf);
	else
		pr_err("%s: %pV", func, &vaf);
	trace_brcmf_err(func, &vaf);
	va_end(args);
}

#endif
