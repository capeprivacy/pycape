Releasing PyCape and Serdio
=========

PyCape and Serdio are versioned and released in lock-step. The procedure is almost entirely automated via a combination of the project Makefile and its Github Actions workflows.

PyCape follows [SemVer](https://semver.org/), so the released versions follow the pattern `MAJOR.MINOR.PATCH`. All commits between released versions are considered release candidates and follow the pattern `MAJOR.MINOR.PATCH-rc`. Only released versions are guaranteed to respect semantic versioning.

Serdio is lock-stepped with a corresponding PyCape version, so while its versions may seem to respect SemVer, there is no guarantee that they will.

## 0. Pre-requisites
You will need to be an admin of the repo in order to follow this release process. If you're not, request admin permissions or ask an admin to do it for you.

You will also need to have GPG-signing configured locally and linked to a verified Github email address. This is necessary for Github to consider the release commits signed by a verified GPG key.

IMPORTANT. Make sure that you are currently on the `main` branch of the repo. Following the release process on another branch will fail to trigger the correct Github Action workflows.

IMPORTANT. Make sure your local `main` branch is up-to-date with the latest commits from the `origin` remote. Forgetting to include recent commits will prevent you from pushing the released commits to Github later.

NEVER PUBLISH A RELEASE FROM A COMMIT THAT HAS FAILED ANY OF ITS STATUS CHECKS.

## 1. Decide on a version bump level
The SemVer requirements for deciding the bump level are reproduced below:
- A `major` bump signifies an incompatible or breaking change.
- A `minor` bump signifies new functionality that is backwards-compatible.
- A `patch` bump signifies backwards-compatible bugfixes

Note that these only apply to the _public_ PyCape API. For example, breaking changes to downstream Cape projects might introduce backwards-incompatible changes that are purely internal to PyCape. These types of internal changes do not constitute a breaking change for PyCape.

## 2. Bump the version
From the project root, run the corresponding cmake target for the version bump. The options are listed below:
- `make bump-patch`
- `make bump-minor`
- `make bump-major`

This will actually trigger two separate release bumps: one from the current release candidate to tagged release, and then another from tagged release to the next release candidate. Using `make bump-minor` as an example,

1. Commit #1 bumps `1.0.0-rc` to `1.1.0`. The commit ref is tagged with the version number, i.e. `git tag 1.1.0`.
2. Commit #2 bumps `1.1.0` to `1.1.1-rc`. This commit starts the next release candidate, so it won't be tagged.

NOTE that if you have to start over at any point after this step, you will have to delete the tag that was created here with something like `git tag -d 1.1.0`.

## 3. Examine the commits
The above changes are automatically committed, so you'll want to be sure that the commits happened the way you expected them to. You can do this by checking the version numbers in the `pyproject.toml` of both Serdio and PyCape, as well as checking your `git log` to make sure the right commit has been tagged. The `git log` should look something like this:

```console
commit <OMITTED> (HEAD -> main)
Author: <OMITTED> <<OMITTED>@capeprivacy.com>
Date:   <OMITTED>

    bump version 1.1.0 -> 1.1.1-rc

commit <OMITTED> (tag: 1.1.0)
Author: <OMITTED> <<OMITTED>@capeprivacy.com>
Date:   <OMITTED>

    bump version 1.0.0-rc -> 1.1.0
```

You can verify that the commits have been propely signed with `git log --show-signature`.

If you don't have automatic GPG-signing set up, you should use your GPG key to sign these commits retroactively with:
```console
git rebase origin/main -x 'git commit -n -S --no-edit --amend'
```

BEFORE you follow the next step, it's worth fetching from `origin` and checking your `git log` to make sure that your current HEAD is only two commits ahead of the latest commit on main. If more commits have been added, you will have to hard reset your local version of `main` to the origin's and start over.

## 4. Push the release commits to `origin`
Finally, push the last two commits to main with:
```console
git push origin main
```
Now, WAIT for the latest commit on main to pass its CI workflow. If for some reason the CI status check fails, you will need to investigate why and resolve it. If resolution requires any new commits, you will have to wait for the relevant PRs to be merged into `main`, and then restart this release process from the newer version of `main`.

## 5. Push the new tag to `origin`
Finally, once you've verified that CI is passing for the release commits, you will push the git tag to Github.

Seriously, this is your last chance to avoid disaster. NEVER PUSH A TAG IF ITS COMMITS HAVEN'T PASSED THE CI WORKFLOWS IN GITHUB ACTIONS.

```console
$ git push origin 1.1.0
```

This will trigger the PyCape and Serdio release workflows in the repo's Github Actions. These workflows will build wheels for PyCape and Serdio, test the wheels, upload them to the latest draft Github Release, and finally push them to PyPI for public consumption.

## 6. Wait for the release workflows to pass
If something went wrong, you will have to diagnose and fix it here. This might require you to start over. Sorry.

NEVER PUBLISH A GITHUB RELEASE FROM A TAG THAT HAS FAILED ITS RELEASE WORKFLOWS

## 7. Update pydocs by merging tag into `staging/docs`
Our Netlify pydocs site (https://pydocs.capeprivacy.com) is set to publish from the `staging/docs` branch on Github. Since we want this site to host documentation for the latest released version of PyCape, you will need to merge the latest tag into this branch. You can do so with the following:
```console
$ git checkout staging/docs
$ git merge --ff 1.1.0
$ git push origin staging/docs
```
Once the Netlify deploy succeeds, you can check https://pydocs.capeprivacy.com to ensure it has the latest release changes.


## 8. Publish the Github Release
Finally, navigate to the `Releases` section of the repo (you can find it on the right sidebar of the repo's homepage). The latest one should be a "draft" release. Open the draft release, and update it to match the version bump you just went through. This includes:
1. Make sure the tag (drop-down menu in top-left) is set to `1.1.0`.
2. Modify the release title to match your semantic version bump. By default it's the next patch version, so you'll probably only have to change it if you are doing a minor or major bump.
3. If you'd like, you have a chance to clean up the version history in the Release body before publishing. You can also add comments here to emphasize or describe higher-level changes to the library. This could include pointing out or explaining breaking changes that required a major version bump.
4. Finally, press "Publish".

## 8. Relax.
Congratulations, you have successfully cut and published a release of PyCape and Serdio.
