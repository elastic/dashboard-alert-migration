# Workshop patches applied to vendored mig-to-kbn after `./scripts/update_mig_to_kbn.sh`

Pending upstream merge (track [observability-migration-platform](https://github.com/elastic/observability-migration-platform/issues)):

| Patch | Purpose |
| --- | --- |
| `ensure_data_view-id-title.patch` | Recreate Fleet-created data views when `id != title` so dashboard upload references resolve (Instruqt Lab 2) |

Remove a patch file once the same fix lands on upstream `main`, then run `./scripts/update_mig_to_kbn.sh`.
