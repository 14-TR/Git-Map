"""Route blueprints for GitMap GUI."""
from flask import Blueprint

from . import branch, commit, config, diff, lsm, main, merge, portal, remote, repository, services

# Register all blueprints
blueprints = [
    main.bp,
    repository.bp,
    branch.bp,
    commit.bp,
    merge.bp,
    diff.bp,
    portal.bp,
    remote.bp,
    config.bp,
    lsm.bp,
    services.bp,
]


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    for bp in blueprints:
        app.register_blueprint(bp)
