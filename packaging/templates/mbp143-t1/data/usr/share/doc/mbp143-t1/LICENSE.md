# Licensing

The owner selected the following licensing on 2026-11-04:

- Independent project tools, independent tests, original local maintenance
  recipes and CI configuration: [MIT](LICENSES/MIT-project.txt).
- New project documentation, including README, CHANGELOG, `docs/` and authored
  evidence summaries: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/legalcode.en).
  Attribution: mbp143-ubuntu-compat contributors; indicate changes when adapting.
- Imported driver sources, kernel files, patches and package scripts retain
  their own notices and per-file licenses. Neither of the above grants replaces
  them. Local modifications to those components remain under their applicable
  original licenses.

Source-generating recipes containing kernel/driver C and the combined actual-C
offline tests are distributed as GPL-2.0-only works; their paths are listed in
`manifests/licensing.json`. Existing MIT grants for independently authored parts
remain available; the MIT grant does not replace the GPL on imported fragments
or the assembled test programs. GPL driver changes are distributed under the
applicable original GPL terms. Independent build/export/verification tools and
policy tests remain MIT.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the original headers.
`LICENSES/kernel/` preserves the source kernel's complete license-text directory.
The T1 wrapper's MIT license and the GPL driver license are separate notices.
There is no blanket claim that this repository is entirely MIT or CC BY.
