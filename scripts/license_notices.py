#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Publication annotation shared by source-replay and archive verification."""
NOTICE = '/*\n * Distribution changes by mbp143-ubuntu-compat contributors, 2026-11-05:\n * added this notice to the selected source snapshot. Functional adaptations\n * are described in docs/source-provenance.md and the accompanying patches.\n * Original authorship and per-file license terms remain unchanged.\n */\n'

def without_notice(data):
    """Remove only our exact dated comment; retain every upstream byte."""
    notice = NOTICE.encode()
    if notice in data[:600]:
        return data.replace(notice, b'', 1)
    return data
