# Kodi repository ZIP layout

Place release ZIP artifacts in these folders:

- `repo/zips/repository.kodiseerr/repository.kodiseerr-<version>.zip`
- `repo/zips/plugin.video.kodiseerr/plugin.video.kodiseerr-<version>.zip`

Kodi uses `repo/addons.xml` and `repo/addons.xml.md5` to discover available add-ons and versions.
Update those files whenever a new ZIP is published:

```bash
python3 scripts/build_repo_index.py
```
