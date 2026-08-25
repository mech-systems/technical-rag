# BorgBackup

## Overview

BorgBackup, usually called Borg, is a deduplicating backup program. It optionally supports compression and authenticated encryption. Borg splits files into content-defined chunks and stores only chunks that are not already present in the repository.

A repository stores one or more archives. Each archive represents a backup snapshot. Repositories can be local directories or remote repositories accessed through SSH.

## Initialize a repository

Create a local encrypted repository:

```bash
borg init --encryption=repokey /path/to/repo
```

The encryption mode is chosen when the repository is created and cannot be changed later for that repository. Use a strong, unique passphrase and protect the repository key.

## Create a backup

Create an archive from selected directories:

```bash
borg create /path/to/repo::Monday ~/src ~/Documents
```

Create another archive and show statistics:

```bash
borg create --stats /path/to/repo::Tuesday ~/src ~/Documents
```

Because Borg deduplicates chunks, unchanged data already present in the repository is not stored again.

## List archives and files

List all archives in a repository:

```bash
borg list /path/to/repo
```

List the contents of one archive:

```bash
borg list /path/to/repo::Monday
```

## Restore data

Extract a complete archive into the current working directory:

```bash
borg extract /path/to/repo::Monday
```

Extract only a selected path:

```bash
borg extract /path/to/repo::Monday path/to/extract
```

Test extraction without writing files:

```bash
borg extract --dry-run /path/to/repo::Monday
```

`borg extract` writes into the current working directory. Change to the intended restore directory before running it.

## Check repository and archive integrity

Check a repository or archive for consistency:

```bash
borg check /path/to/repo
```

Perform cryptographic archive data verification:

```bash
borg check --verify-data /path/to/repo
```

`--verify-data` reads and verifies archive data and therefore requires more time than a regular check.

## Retention with prune

`borg prune` removes archives according to retention rules. It is potentially destructive. Always inspect the result with `--dry-run` first:

```bash
borg prune --list --dry-run \
  --keep-daily=7 \
  --keep-weekly=4 \
  /path/to/repo
```

After verifying the output, remove `--dry-run` to apply the retention policy.

When a repository contains archives from multiple machines, restrict pruning with an archive pattern:

```bash
borg prune --list --dry-run \
  --glob-archives='{hostname}-*' \
  --keep-daily=7 \
  --keep-weekly=4 \
  /path/to/repo
```

## Reclaim repository space

Deleting or pruning archives does not immediately reclaim repository disk space. Run compaction separately:

```bash
borg compact /path/to/repo
```

## Important operational notes

- Test restore procedures, not only backup creation.
- Use `--dry-run` before destructive archive-selection operations.
- Keep sufficient free space on the repository filesystem and in the Borg cache location.
- Files changing during backup can lead to an inconsistent backup state.
- Databases and running virtual machines require application-consistent or snapshot-based backup methods.
- Protect the passphrase and key of encrypted repositories. Losing required key material or the passphrase can make backups inaccessible.

## Source

Based on the official stable BorgBackup documentation:
[Official BorgBackup documentation](https://borgbackup.readthedocs.io/_/downloads/en/stable/pdf/)
