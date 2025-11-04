from loguru import logger

from primitive.network.redfish import RedfishClient
from primitive.utils.ssh import test_ssh_connection, run_command


def pxe_boot_via_redfish(target_hardware_secret: dict):
    bmc_host = target_hardware_secret.get("bmcHostname", None)
    bmc_username = target_hardware_secret.get("bmcUsername", None)
    bmc_password = target_hardware_secret.get("bmcPassword", "")

    if bmc_host is None:
        logger.error(
            "No BMC host found in target hardware secret for out-of-band power cycle"
        )
        return True
    if bmc_username is None:
        logger.error(
            "No BMC username found in target hardware secret for out-of-band power cycle"
        )
        return True

    redfish = RedfishClient(host=bmc_host, username=bmc_username, password=bmc_password)
    redfish.update_boot_options(
        system_id="1",
        boot_source_override_target="Pxe",
        boot_source_override_enabled="Once",
        boot_source_override_mode="UEFI",
    )
    redfish.compute_system_reset(system_id="1", reset_type="ForceRestart")


def pxe_boot_via_efibootmgr(target_hardware_secret: dict):
    run_command(
        hostname=target_hardware_secret.get("hostname"),
        username=target_hardware_secret.get("username"),
        password=target_hardware_secret.get("password"),
        command="sudo efibootmgr -n $(efibootmgr | awk '/PXE IPV4/ {print substr($1,5,4)}' | head -n1 || efibootmgr | awk '/ubuntu/ {print substr($1,5,4)}' | head -n1) && sudo reboot",
        port=22,
    )


def pxe_boot(target_hardware_secret: dict) -> bool:
    redfish_available = False
    ssh_available = False

    if target_hardware_secret.get("bmcHostname", None):
        redfish_available = True
    else:
        logger.info(
            "No BMC credentials found, skipping Redfish PXE boot method. Checking efiboot method."
        )

    ssh_available = test_ssh_connection(
        hostname=target_hardware_secret.get("hostname"),
        username=target_hardware_secret.get("username"),
        password=target_hardware_secret.get("password"),
        port=22,
    )

    if redfish_available:
        pxe_boot_via_redfish(target_hardware_secret=target_hardware_secret)
        return True
    elif ssh_available:
        pxe_boot_via_efibootmgr(target_hardware_secret=target_hardware_secret)
        return True
    else:
        logger.error(
            "No available method to PXE boot target hardware. Missing BMC credentials and SSH is not available."
        )
    return False
