# aosproot

aosproot is a simple way to apply the Magisk boot image patch as part of the AOSP build. This allows building a rooted custom firmware, while preserving AVB (Android Verified Boot).

For patching existing/prebuilt firmware, see [avbroot](https://github.com/chenxiaolong/avbroot). However, building open source Android firmware with aosproot included is preferable to using avbroot.

**NOTE**: This is currently a proof of concept implementation and has not yet been tested on a real device. It should, in theory, be functional. When applied to the GrapheneOS source, a Pixel 7 Pro (`cheetah`) build produces a rooted and signed `init_boot.img`.

### Warnings and Caveats

* **Do not ever disable the `OEM unlocking` checkbox when using a locked bootloader with root.** This is critically important. With root access, it is possible to corrupt the running system, for example by zeroing out the boot partition. In this scenario, if the checkbox is turned off, both the OS and recovery mode will be made unbootable and `fastboot flashing unlock` will not be allowed. This effectively renders the device **_hard bricked_**.

* Any operation that causes an unsigned or differently-signed boot image to be flashed will result in the device being unbootable and unrecoverable without unlocking the bootloader again (and thus, triggering a data wipe). This includes:

    * The `Direct install` method for updating Magisk. Magisk updates must be done by building a new firmware image and flashing the corresponding OTA.

* Only the latest version of AOSP is supported (13 at this time). There is no plan to support older AOSP versions.

### Usage

1. Place [`aosproot.xml`](./aosproot.xml) in `.repo/local_manifests/` at the root of the AOSP source code.

    ```bash
    mkdir -p .repo/local_manifests
    curl -L -o .repo/local_manifests/aosproot.xml \
        https://github.com/chenxiaolong/aosproot/raw/master/aosproot.xml
    ```

2. Sync the repo.

    ```bash
    repo sync vendor/aosproot
    ```

3. Source the `build/envsetup.sh` as usual for AOSP builds.

    ```bash
    source build/envsetup.sh
    ```

4. Copy the Magisk APK into `vendor/aosproot/magisk.apk`. A symlink also works, though it makes the AOSP build less reproducible.

    ```bash
    cp /path/to/magisk.apk vendor/aosproot/magisk.apk
    ```

5. Build `aosproot`.

    ```bash
    m aosproot
    ```

6. Apply code patches to other repos to allow aosproot to be injected into the AOSP build process. The set of patches can be found in the [`patches/`](./patches) directory. **NOTE**: This need to be rerun every time `repo sync` is run.

    ```bash
    aosproot patch_code
    ```

7. Build AOSP as normal. The `init_boot` or `boot` image will be patched with Magisk automatically during the build process, prior to signing.

### License

aosproot is licensed under GPLv3. Please see [`LICENSE`](./LICENSE) for the full license text.
