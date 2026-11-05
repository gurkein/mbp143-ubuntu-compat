// SPDX-License-Identifier: ISC
/*
 * Distribution changes by mbp143-ubuntu-compat contributors, 2026-11-05:
 * added this notice to the selected source snapshot. Functional adaptations
 * are described in docs/source-provenance.md and the accompanying patches.
 * Original authorship and per-file license terms remain unchanged.
 */
/*
 * Copyright The Asahi Linux Contributors
 */

#include <linux/acpi.h>
#include "debug.h"
#include "core.h"
#include "common.h"

void brcmf_acpi_probe(struct device *dev, enum brcmf_bus_type bus_type,
		      struct brcmf_mp_device *settings)
{
	acpi_status status;
	const union acpi_object *o;
	struct acpi_buffer buf = {ACPI_ALLOCATE_BUFFER, NULL};
	struct acpi_device *adev = ACPI_COMPANION(dev);

	if (!adev)
		return;

	if (!ACPI_FAILURE(acpi_dev_get_property(adev, "module-instance",
						ACPI_TYPE_STRING, &o))) {
		brcmf_dbg(INFO, "ACPI module-instance=%s\n", o->string.pointer);
		settings->board_type = devm_kasprintf(dev, GFP_KERNEL,
						      "apple,%s",
						      o->string.pointer);
	} else {
		brcmf_dbg(INFO, "No ACPI module-instance\n");
		return;
	}

	status = acpi_evaluate_object(adev->handle, "RWCV", NULL, &buf);
	o = buf.pointer;
	if (!ACPI_FAILURE(status) && o && o->type == ACPI_TYPE_BUFFER &&
	    o->buffer.length >= 2) {
		char *antenna_sku = devm_kzalloc(dev, 3, GFP_KERNEL);

		if (antenna_sku) {
			memcpy(antenna_sku, o->buffer.pointer, 2);
			brcmf_dbg(INFO, "ACPI RWCV data=%*phN antenna-sku=%s\n",
				  (int)o->buffer.length, o->buffer.pointer,
				  antenna_sku);
			settings->antenna_sku = antenna_sku;
		}

		kfree(buf.pointer);
	} else {
		brcmf_dbg(INFO, "No ACPI antenna-sku\n");
	}
}
