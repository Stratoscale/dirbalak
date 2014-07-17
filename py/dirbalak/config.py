import os

DIRBALAK_DIR = os.path.join(os.environ['HOME'], ".dirbalak")
REPO_MIRRORS_BASEDIR = os.path.join(DIRBALAK_DIR, "repomirrors")
REPO_MIRRORS_LOCKFILE = os.path.join(REPO_MIRRORS_BASEDIR, "lock")

BUILD_CHROOT = os.path.join(DIRBALAK_DIR, "chroot")
BUILD_DIRECTORY = os.path.join(BUILD_CHROOT, "home", "dirbalak")

OFFICIAL_BUILD_ROOTFS = "solvent__rootfs-build__rootfs__b28426f0192d2d2a82f697672468320c9392a911__clean"
NO_DIRBALAK_MANIFEST_BUILD_ROOTFS = \
    "solvent__rootfs-build__rootfs__b28426f0192d2d2a82f697672468320c9392a911__clean"
