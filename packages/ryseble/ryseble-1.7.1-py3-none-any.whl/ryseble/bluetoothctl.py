import asyncio
import subprocess
import logging
import re

_LOGGER = logging.getLogger(__name__)


def close_process(process):
    process.stdin.close()
    process.stdout.close()
    process.stderr.close()
    process.wait()


async def run_command(command):
    """Run a bluetoothctl command and return the output."""
    proc = await asyncio.create_subprocess_exec(
        "bluetoothctl",
        *command.split(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
        return {"stdout": stdout, "stderr": stderr, "returncode": proc.returncode}
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"bluetoothctl command timed out: {command}")
    except Exception as e:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"Command failed: {command} - {str(e)}")


def start_bluetoothctl():
    """Start bluetoothctl as an interactive process."""
    return subprocess.Popen(
        ["bluetoothctl"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1024,
    )


async def send_command_in_process(process, command, delay=2):
    """Send a command to the bluetoothctl process and wait for a response."""
    process.stdin.write(f"{command}\n")
    process.stdin.flush()
    await asyncio.sleep(delay)


async def is_device_connected(address):
    """Check if a Bluetooth device is connected by its MAC address."""
    cmdout = await run_command("devices Connected")
    target_address = address.lower().encode()

    for line in cmdout["stdout"].splitlines():
        # Check if line starts with "Device" followed by MAC address
        if line.lower().startswith(b"device " + target_address):
            return True
    return False


async def is_device_bonded(address):
    """Check if a Bluetooth device is bonded by its MAC address."""
    cmdout = await run_command("devices Bonded")
    target_address = address.lower().encode()

    for line in cmdout["stdout"].splitlines():
        # Check if line starts with "Device" followed by MAC address
        if line.lower().startswith(b"device " + target_address):
            return True
    return False


async def is_device_paired(address):
    """Check if a Bluetooth device is paired by its MAC address."""
    cmdout = await run_command("devices Paired")
    target_address = address.lower().encode()

    for line in cmdout["stdout"].splitlines():
        # Check if line starts with "Device" followed by MAC address
        if line.lower().startswith(b"device " + target_address):
            return True
    return False


async def get_first_manufacturer_data_byte(mac_address: str) -> int:
    """
    Returns the first byte of ManufacturerData.Value for a BLE device using bluetoothctl.
    Returns None if not found.
    """
    # Run bluetoothctl info and capture output
    cmd = ["bluetoothctl", "info", mac_address]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Wait for completion (timeout: 10 sec)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        _LOGGER.error("bluetoothctl command timed out")
        return None

    # Parse output
    lines = stdout.decode().splitlines()

    for i, line in enumerate(lines):
        if "ManufacturerData.Value" in line:
            # The next line contains the hex bytes (e.g., "cc 64 62 64")
            if (i + 1) < len(lines):
                hex_str = re.search(r"([0-9a-fA-F]{2})", lines[i + 1].strip())
                if hex_str:
                    return int(hex_str.group(1), 16)
    return None


async def pair_with_ble_device(device_name: str, device_address: str) -> bool:
    """Attempt to pair with a BLE device using bluetoothctl with retries."""

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Start bluetoothctl in interactive mode
            process = start_bluetoothctl()
            await send_command_in_process(process, f"trust {device_address}", delay=1)
            await send_command_in_process(process, f"connect {device_address}", delay=2)
            await send_command_in_process(process, "yes", delay=7)

            idc = await is_device_connected(device_address)
            idp = await is_device_paired(device_address)

            if idc and not idp:
                await send_command_in_process(
                    process,
                    f"pair {device_address}",
                    delay=7,
                )

            await send_command_in_process(process, "exit", delay=1)
            close_process(process)

            # Verify connection/bond status
            idc = await is_device_connected(device_address)
            idb = await is_device_bonded(device_address)
            idp = await is_device_paired(device_address)

            if idc and idb and idp:
                _LOGGER.debug(
                    "Connected, Paired and Bonded to %s",
                    device_address,
                )
                return True
            else:
                _LOGGER.error(
                    "Failed to connect and bond(attempt %d)",
                    retry_count + 1,
                )
                _LOGGER.error(
                    "Connected? %s \t Paired? %s \t Bonded? %s",
                    idc,
                    idp,
                    idb,
                )

        except Exception as e:
            _LOGGER.error(
                "Connection error (attempt %d): %s",
                retry_count + 1,
                e,
            )

        retry_count += 1
        await asyncio.sleep(3)  # Wait before retrying

    return False


async def filter_ryse_devices_pairing(devices, existing_addresses: set[str]) -> dict[str, str]:
    """Filter BLE RYSE devices and return only those in pairing mode."""
    device_options = {}

    for device in devices:
        if not device.name:
            continue  # Ignore unnamed devices
        if device.address in existing_addresses:
            _LOGGER.debug(
                "Skipping already configured device: %s (%s)",
                device.name,
                device.address,
            )
            continue  # Skip already configured devices

        manufacturer_data = getattr(device, "manufacturer_data", None)
        raw_data = manufacturer_data.get(0x0409) if manufacturer_data else None
        if raw_data is None:
            continue

        btctlMfgdata0 = await get_first_manufacturer_data_byte(device.address)
        if (
            len(raw_data) > 0
            and btctlMfgdata0 is not None
            and (btctlMfgdata0 & 0x40)
        ):
            device_options[device.address] = f"{device.name} ({device.address})"
            _LOGGER.debug(
                "Found RYSE in pairing mode: %s (%s) btctlMfgdata0=%02X",
                device.name,
                device.address,
                btctlMfgdata0,
            )

    return device_options
