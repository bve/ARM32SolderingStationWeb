# Solder Web — firmware releases

Public firmware packages for the **web-generation** soldering station.

[Download the latest release](https://github.com/bve/ARM32SolderingStationWeb/releases/latest).

## Compatibility

These packages require the new station bootloader with its application at
**0x8000**. They are **not compatible** with legacy stations using the old
`0x10000` application layout and on-station firmware download menu.

Legacy stations continue using
[ARM32SolderingStation](https://github.com/bve/ARM32SolderingStation/releases).
That repository is not modified by this release channel.

## Updating

1. Stop heating and keep the station attended.
2. Download the station `.ota` matching your board revision (V1, V2 or V3).
   Select the actual board, not the highest revision number.
3. Upload and install it through **Updates → Station** in the web interface.
4. Update the web interface separately with the `.espota` under
   **Updates → Web interface**. Do not disconnect power during installation.

Existing web interfaces checking the old repository need one manual `.espota`
upload from this repository before their update checks can find this channel.
Companions with a single application slot need a USB partition migration first.
Legacy stations require a separate service migration of the bootloader and
companion; these packages alone do not perform that migration.

Factory provisioning is not part of a normal update. No factory bundles,
authentication IDs, bootloader keys, device backups or private source code are
published here.

## Files and integrity

- `ARM32SolderingStationWeb-board_v1-v<version>.ota`
- `ARM32SolderingStationWeb-board_v2-v<version>.ota`
- `ARM32SolderingStationWeb-board_v3-v<version>.ota`
- `ARM32SolderingStationWeb-esp32c3-v<version>.espota`
- `SHA256SUMS.txt`

Verify downloaded files with `sha256sum -c SHA256SUMS.txt`.
Station packages are encrypted and authenticated by the station bootloader.
The web package has integrity checks but is not digitally signed: download only
from this repository and update on a trusted local network.

Tags trigger a workflow that validates the exact file set, versions, package
headers and checksums before publishing. The workflow can also be run manually
for an existing, unpublished tag. Firmware is built in the private source project;
this repository contains only release packages, notes and publication tooling.
