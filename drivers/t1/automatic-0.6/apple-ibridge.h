/* SPDX-License-Identifier: GPL-2.0 */
/*
 * Distribution changes by mbp143-ubuntu-compat contributors, 2026-11-05:
 * added this notice to the selected source snapshot. Functional adaptations
 * are described in docs/source-provenance.md and the accompanying patches.
 * Original authorship and per-file license terms remain unchanged.
 */
/*
 * Apple iBridge Driver
 *
 * Copyright (c) 2018 Ronald Tschalär
 */

#ifndef __LINUX_APPLE_IBRDIGE_H
#define __LINUX_APPLE_IBRDIGE_H

#define USB_VENDOR_ID_LINUX_FOUNDATION	0x1d6b
#define USB_DEVICE_ID_IBRIDGE_TB	0x0301
#define USB_DEVICE_ID_IBRIDGE_ALS	0x0302

/* Process context only. Never acquire this gate while holding a TB spinlock.
 * A successful begin must be paired with end, including when option is off.
 * Wake clients run inside the gate: they may invalidate/cache and queue work,
 * but must not acquire the gate, issue USB I/O, or wait for a worker.
 */
struct notifier_block;
int appleib_tb_io_begin(void);
void appleib_tb_io_end(void);
int appleib_tb_register_wake(struct notifier_block *nb);
int appleib_tb_unregister_wake(struct notifier_block *nb);
/* Called under the I/O gate after cache commit, outside TB spinlock. */
bool appleib_tb_report_result(bool refreshed, int result);

#endif
