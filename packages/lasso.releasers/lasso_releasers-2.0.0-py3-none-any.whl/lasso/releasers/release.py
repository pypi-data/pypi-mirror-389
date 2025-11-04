# encoding: utf-8
"""Release automation."""
import argparse
import logging
import os
import sys

import github3

from . import VERSION

_logger = logging.getLogger(__name__)


def add_expected_arguments(parser: argparse.ArgumentParser):
    """Add normally expected command-line arguments to the given ``parser``."""
    # The "version" option
    parser.add_argument("--version", action="version", version=VERSION)

    # Logging options
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const=logging.DEBUG,
        default=logging.INFO,
        dest="loglevel",
        help="Log copious debugging messages suitable for developers",
    )
    group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=logging.WARNING,
        dest="loglevel",
        help="Don't log anything except warnings and critically-important messages",
    )


def create_release(repo, repo_name, branch_name, tag_name, tagger, upload_assets):
    """Create a tag, if needed, and release.

    Push the assets created in target directory.
    """
    _logger.info("🧐 create new release, repo_name: %s, branch_name: %s, tag_name: %s", repo_name, branch_name, tag_name)

    try:
        our_branch = repo.branch(branch_name)
        _logger.info(
            '🏷️ Attempting to create tag %s for branch %s with commmit %s',
            tag_name, branch_name, our_branch.commit.sha
        )
        repo.create_tag(tag_name, "release", our_branch.commit.sha, "commit", tagger)
    except github3.GitHubError:
        _logger.info('🏷️ GitHubError: tag %s probably already exists, probably created by Roundup, so continuing', tag_name)

    try:
        # create the release
        _logger.info("𝌚 Creating release %s from tag %s", tag_name, tag_name)
        release = repo.create_release(
            tag_name,
            name=repo_name + " " + tag_name,
            prerelease=False,
        )
        _logger.info("⬆️ Uploading assets")
        upload_assets(repo_name, tag_name, release)
    except github3.GitHubError as error:
        _logger.error('‼️ Error creating release or uploading assets: %s', error)
        _logger.error('🔍 Errors: %r', error.errors)
        raise


def delete_snapshot_releases(_repo, suffix):
    """Delete all pre-existing snapshot releases."""
    _logger.info("delete previous releases")
    for release in _repo.releases():
        if release.tag_name.endswith(suffix):
            release.delete()


def create_snapshot_release(repo, repo_name, branch_name, tag_name, tagger, upload_assets):
    """Create a tag and new release from the latest commit on branch_name.

    Push the assets created in target directory.
    """
    _logger.info("create new snapshot release")

    try:
        our_branch = repo.branch(branch_name)
        _logger.info('🏷️ Attempting to create tag %s for branch %s with commmit %s', tag_name, branch_name, our_branch.commit.sha)
        repo.create_tag(tag_name, "SNAPSHOT release", our_branch.commit.sha, "commit", tagger)
    except github3.GitHubError:
        _logger.info('🏷️ GitHubError: tag %s probably already exists, probably created by Roundup, so continuing', tag_name)

    try:
        _logger.info('📀 Attempting to create snapshot release %s for branch %s', tag_name, branch_name)
        # create the release
        release = repo.create_release(
            tag_name,
            target_commitish=branch_name,
            name=repo_name + " " + tag_name,
            prerelease=True,
        )

        _logger.info("⬆️ Uploading snapshot assets")
        upload_assets(repo_name, tag_name, release)

    except github3.exceptions.GitHubError as error:  # 💢
        _logger.error('‼️ Error creating snapshot release: %s', error)
        _logger.error('🔍 Errors: %r', error.errors)
        raise


def release_publication(suffix, get_version, upload_assets, prefix="v"):
    """Script made to work in the context of a github action."""
    parser = argparse.ArgumentParser(description="Create new release")
    add_expected_arguments(parser)
    parser.add_argument("--token", dest="token", help="github personal access token")
    parser.add_argument("--repo_name", help="full name of github repo (e.g. user/repo)")
    parser.add_argument(
        "--workspace",
        help="path of workspace. defaults to current working directory if this or GITHUB_WORKSPACE not specified",
    )
    parser.add_argument("--snapshot", action="store_true", help="Mark release as a SNAPSHOT release.")
    args, unknown = parser.parse_known_args()
    print(
        f"🪵 Setting log level to {args.loglevel}, debug happens to be {logging.DEBUG}",
        file=sys.stderr,
    )
    logging.basicConfig(level=args.loglevel, format="%(levelname)s %(message)s")

    # read organization and repository name
    repo_full_name = args.repo_name or os.environ.get("GITHUB_REPOSITORY")
    if not repo_full_name:
        _logger.error("Github repository must be provided or set as environment variable (GITHUB_REPOSITORY).")
        sys.exit(1)

    workspace = args.workspace or os.environ.get("GITHUB_WORKSPACE")
    if not workspace:
        workspace = os.getcwd()
        os.environ["GITHUB_WORKSPACE"] = workspace

    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        _logger.error("Github token must be provided or set as environment variable (GITHUB_TOKEN).")

    repo_full_name_array = repo_full_name.split("/")
    org = repo_full_name_array[0]
    repo_name = repo_full_name_array[1]

    tag_name = prefix + get_version(workspace)
    print(f"YO YO YO USING tag_name of «{tag_name}»", file=sys.stdout)
    tagger = {"name": "PDSEN CI Bot", "email": "pdsen-ci@jpl.nasa.gov"}

    gh = github3.login(token=token)
    repo = gh.repository(org, repo_name)
    delete_snapshot_releases(repo, suffix)
    if tag_name.endswith(suffix) or args.snapshot:
        if not tag_name.endswith(suffix):
            tag_name = tag_name + suffix
        create_snapshot_release(repo, repo_name, "main", tag_name, tagger, upload_assets)
    else:
        create_release(repo, repo_name, "main", tag_name, tagger, upload_assets)
