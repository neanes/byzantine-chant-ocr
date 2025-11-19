# Deployment

## Model

To deploy a new version of the model, create a tag that starts with `model/v` and push it to the remote.

```bash
git tag model/v1.0.0
git push --tags
```

This will generate a draft release in Github. Go to the draft release and release it.

Next, update `dist/model/latest.json` and commit it to the `master` branch.

```bash
cd deploy
python generate_latest_model_file.py model/v1.0.0 > ../dist/model/latest.json
git commit -am "Bump latest model (v1.0.0)"
git push
```

## App

To deploy a new version of the app, update `version.py`, then create a tag that starts with `app/v` and push it to the remote.

```bash
git tag app/v1.0.0
git push --tags
```

This will generate a draft release in Github. Go to the draft release and release it.

## Fixing mistakes

Delete the bad tag.

```bash
git tag -d app/v1.0.0
git push origin :app/v1.0.0
```

Re-tag.
