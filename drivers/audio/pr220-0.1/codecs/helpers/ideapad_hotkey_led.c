// SPDX-License-Identifier: GPL-2.0
/*
 * Distribution changes by mbp143-ubuntu-compat contributors, 2026-11-05:
 * added this notice to the selected source snapshot. Functional adaptations
 * are described in docs/source-provenance.md and the accompanying patches.
 * Original authorship and per-file license terms remain unchanged.
 */
/*
 * Ideapad helper functions for Lenovo Ideapad LED control,
 * It should be included from codec driver.
 */

#if IS_ENABLED(CONFIG_IDEAPAD_LAPTOP)

#include <linux/acpi.h>
#include <linux/leds.h>

static bool is_ideapad(struct hda_codec *codec)
{
	return (codec->core.subsystem_id >> 16 == 0x17aa) &&
	       (acpi_dev_found("LHK2019") || acpi_dev_found("VPC2004"));
}

static void hda_fixup_ideapad_acpi(struct hda_codec *codec,
				   const struct hda_fixup *fix, int action)
{
	if (action == HDA_FIXUP_ACT_PRE_PROBE) {
		if (!is_ideapad(codec))
			return;
		snd_hda_gen_add_mute_led_cdev(codec, NULL);
		snd_hda_gen_add_micmute_led_cdev(codec, NULL);
	}
}

#else /* CONFIG_IDEAPAD_LAPTOP */

static void hda_fixup_ideapad_acpi(struct hda_codec *codec,
				   const struct hda_fixup *fix, int action)
{
}

#endif /* CONFIG_IDEAPAD_LAPTOP */
