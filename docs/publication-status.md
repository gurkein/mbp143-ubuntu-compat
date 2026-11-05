# Publication status

Source publication reviewed on 2026-11-05 for
`gurkein/mbp143-ubuntu-compat`. Git contains selected source trees, seven kernel
patches, the exact config, package templates, build-only tools, offline tests,
source/artifact manifests, compatibility and rollback documentation.

The seven DEBs and two complete source archives are prepared locally in ignored
`dist/`. They are not included in a Git clone. No binary Release has been
published; the DEBs and both source archives must be uploaded together when
creating one. See [source distribution](source-distribution.md).

The owner chose MIT for independent tools and CC BY 4.0 for new documentation;
imported source notices remain in force. Historical recipes are text references.
No private signing key, personalized firmware/NVRAM or raw network log is included.

The graphics/EFI addition includes the original local GPU-selector C source,
a portable build-only Makefile, Boot Camp/rollback documentation and the original
installer as text. Only a build-command dry run was performed; no EFI binary
was compiled, installed or executed, and no firmware/GRUB setting changed.

The selected DEBs use documentation-only numeric packaging revisions. Original and
revised hashes and unchanged executable payloads are recorded in the licensing
manifest. Sources and notices are described in [source distribution](source-distribution.md). Some generated
headers and binary/module metadata contain the original local build path;
the per-package counts are documented in the payload audit. Those path strings
were not rewritten or presented as fully anonymized binary metadata.

Checks performed and their limits are recorded in `manifests/validation.json`
and `manifests/payload-audit.json`. Successful offline/source/build checks do not
add hardware coverage. A complete new kernel build and on-device installation
from this public candidate were not performed.

Before publishing a binary Release: select a prerelease tag, upload all
manifest-listed DEBs and both source archives, verify downloaded checksums,
and publish the scoped experimental release notes.

T1 0.6 replaces 0.5 in the selected source/package set. It removes once/repeat
activation modes while preserving the ordered transaction path and error checks.
Earlier five-cycle evidence describes 0.5; 0.6 source/ABI and system-readiness/
boot-conversion checks are described in the release notes.


Publication prose and historical text references omit private peripheral/AP
models, nearby-machine details, local usernames/paths and the site-specific
regulatory example. The old unpublished Git history was excluded from this project; its temporary
private backup was subsequently deleted at the owner's request. Original kernel/headers binaries can retain
build-path metadata; they are not claimed to be fully anonymized binaries.

The maintainer accepted retaining existing build-path metadata in the selected
binary artifacts; no rebuild for path redaction is requested.
