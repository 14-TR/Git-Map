# CLI Reference

Git-Map provides a Git-inspired CLI for managing web map versions.

## Command Summary

| Command | Description |
|---------|-------------|
| [`init`](init.md) | Initialize a new repository |
| [`clone`](clone.md) | Clone a map from Portal into a new repo |
| [`status`](status.md) | Show working tree status |
| [`commit`](commit.md) | Record staged changes as a commit |
| [`branch`](branch.md) | List, create, or delete branches |
| [`checkout`](checkout.md) | Switch branches or restore commits |
| [`diff`](diff.md) | Show changes between commits or index |
| [`log`](log.md) | Show commit history |
| [`show`](show.md) | Show details of a specific commit |
| [`merge`](merge.md) | Merge a branch into the current branch |
| [`push`](push.md) | Push the current branch to Portal |
| [`pull`](pull.md) | Pull the latest map from Portal |
| [`revert`](revert.md) | Revert to a previous commit |
| [`stash`](stash.md) | Stash uncommitted changes temporarily |
| [`tag`](tag.md) | Create or list version tags |

## Global Options

```
gitmap [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show version and exit.
  --help     Show help and exit.
```

## Getting Help

Every command has a `--help` flag:

```bash
gitmap commit --help
gitmap push --help
```
