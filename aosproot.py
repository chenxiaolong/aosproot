#!/usr/bin/env python3

import argparse
import contextlib
import os
import shutil
import subprocess
import tempfile
import zipfile


@contextlib.contextmanager
def open_output_file(path, atomic):
    '''
    If atomic writes are requested, create a temporary file in the same
    directory as the specified path and atomically replace it if the function
    succeeds.
    '''

    if atomic:
        directory = os.path.dirname(path)

        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as f:
            try:
                yield f
                os.rename(f.name, path)
            except:
                os.unlink(f.name)
                raise
    else:
        yield open(path, 'wb')


MAGISK_FILES = {
    'assets/boot_patch.sh': 'boot_patch.sh',
    'assets/util_functions.sh': 'util_functions.sh',
    'lib/arm64-v8a/libmagisk64.so': 'magisk64',
    'lib/arm64-v8a/libmagiskinit.so': 'magiskinit',
    'lib/armeabi-v7a/libmagisk32.so': 'magisk32',
    'lib/x86/libmagiskboot.so': 'magiskboot',
}


def patch_image(input, output, magisk, atomic):
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(magisk, 'r') as zip:
            for source, target in MAGISK_FILES.items():
                info = zip.getinfo(source)
                info.filename = target
                zip.extract(info, path=temp_dir)

        subprocess.check_call(
            ['sh', './boot_patch.sh', os.path.abspath(input)],
            cwd=temp_dir,
            env={
                'BOOTMODE': 'true',
                'KEEPVERITY': 'true',
                'KEEPFORCEENCRYPT': 'true',
            },
        )

        with open_output_file(output, atomic) as f_out:
            with open(os.path.join(temp_dir, 'new-boot.img'), 'rb') as f_in:
                shutil.copyfileobj(f_in, f_out)


def patch_code():
    top_dir = os.getenv('ANDROID_BUILD_TOP')
    if top_dir is None:
        raise Exception('ANDROID_BUILD_TOP is not set. '
                        'Has build/envsetup.sh been sourced?')

    patches_dir = os.path.join(top_dir, 'vendor', 'aosproot', 'patches')

    for root, _, files in os.walk(patches_dir):
        for f in files:
            if f.endswith('.patch'):
                repo_rel_path = os.path.relpath(root, patches_dir)
                repo_path = os.path.join(top_dir, repo_rel_path)
                patch_path = os.path.join(root, f)

                print(f'Applying {patch_path} in {repo_path}')

                subprocess.check_call([
                    'git',
                    '-C', repo_path,
                    'am', patch_path,
                ])


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand', required=True,
                                       help='Subcommands')

    patch_image = subparsers.add_parser('patch_image', help='Patch boot image')

    patch_image.add_argument('-i', '--input', required=True,
                             help='Path to original boot image')
    patch_image.add_argument('-o', '--output',
                             help='Path to new boot image')
    patch_image.add_argument('--non-atomic', action='store_true',
                             help='Write to output file non-atomically')
    patch_image.add_argument('-m', '--magisk', required=True,
                             help='Path to Magisk API')

    subparsers.add_parser('patch_code', help='Patch AOSP repos')

    args = parser.parse_args()

    if args.subcommand == 'patch_image' and args.output is None:
        args.output = args.input + '.patched'

    return args


def main():
    args = parse_args()

    if args.subcommand == 'patch_image':
        patch_image(args.input, args.output, args.magisk, not args.non_atomic)
    elif args.subcommand == 'patch_code':
        patch_code()
    else:
        raise NotImplementedError()


if __name__ == '__main__':
    main()
