import os

DIRBALAK_DIR = os.path.join(os.environ['HOME'], ".dirbalak")
REPO_MIRRORS_BASEDIR = os.path.join(DIRBALAK_DIR, "repomirrors")
REPO_MIRRORS_LOCKFILE = os.path.join(REPO_MIRRORS_BASEDIR, "lock")

BUILD_CHROOT = os.path.join(DIRBALAK_DIR, "chroot")
BUILD_DIRECTORY = os.path.join(BUILD_CHROOT, "home", "dirbalak")

OFFICIAL_BUILD_ROOTFS = "rootfs-build__rootfs__7b80c2d6042097d3b154399e0bc60aa8bfdf7bea__bootstrap"
NO_DIRBALAK_MANIFEST_BUILD_ROOTFS = \
    "rootfs-build__rootfs__7b80c2d6042097d3b154399e0bc60aa8bfdf7bea__bootstrap"
