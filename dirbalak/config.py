import os

DIRBALAK_DIR = os.path.join(os.environ['HOME'], ".dirbalak")
REPO_MIRRORS_BASEDIR = os.path.join(DIRBALAK_DIR, "repomirrors")
REPO_MIRRORS_LOCKFILE = os.path.join(REPO_MIRRORS_BASEDIR, "lock")

DEFAULT_BUILD_ROOTFS_LABEL = 'solvent__rootfs-build-nostrato__rootfs__f3144655d4b75b21eaaa22676c142d7be5481006__dirty'
BUILD_CHROOT = os.path.join(DIRBALAK_DIR, "chroot")
BUILD_DIRECTORY = os.path.join(BUILD_CHROOT, "home", "dirbalak")
