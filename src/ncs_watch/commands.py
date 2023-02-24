import argparse
import logging
import re
from typing import List, Iterable, Sequence
from pathlib import Path
from shutil import rmtree
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED
from itertools import chain
from datetime import datetime
from paramiko.ssh_exception import SSHException
from netmiko import ConnectHandler, NetmikoBaseException
from .loader import load_yaml, LoaderException, ConfigModel


logger = logging.getLogger('ncs_watch.commands')


#
# Command implementation
#

def apply_cmd(cli_args: argparse.Namespace) -> None:
    """
    Execute command collection
    :param cli_args: Parsed CLI args
    :return: None
    """
    try:
        run_spec = load_yaml(ConfigModel, 'config', cli_args.file)
    except LoaderException as ex:
        logger.critical(f"Failed loading spec file: {ex}")
        return

    for prompt_arg in cli_args.prompt_arguments:
        if getattr(cli_args, prompt_arg.argument) is None:
            setattr(cli_args, prompt_arg.argument, prompt_arg())

    # Temporary directory
    base_path = Path(str(uuid4()))
    base_path.mkdir(parents=True)

    output_filename = f"Hourly-script-log-{datetime.now():%Y-%m-%d-%H%M%S}.txt"

    for node_name, node_info in run_spec.devices.items():
        output_buffer: List[str] = []
        logger.info(f"[{node_name}] Starting session to {node_info.address}")
        session_args = {
            'device_type': node_info.device_type,
            'host':  str(node_info.address),
            'username': cli_args.user,
            'password': cli_args.password,
            'ssh_config_file': cli_args.ssh_config_file
        }
        try:
            with ConnectHandler(**session_args) as session:
                intf_data = re.findall(
                    r'HundredGigE(\d+/(\d+)/\d+/\d+)',
                    session.send_command("show ip int brief | i Hun", read_timeout=run_spec.globals.timeout_std),
                    re.MULTILINE
                )
                intf_list = [intf for intf, _ in intf_data]
                slot_list = sorted({slot for _, slot in intf_data})
                logger.info(f"[{node_name}] Slots: {len(slot_list)}, Interfaces: {len(intf_list)}")

                logger.info(f"[{node_name}] Starting line-card section")
                for slot in slot_list:
                    session.send_command(f"attach location 0/{slot}/CPU0", read_timeout=run_spec.globals.timeout_std,
                                         expect_string=r'[#\$]')
                    session.find_prompt()

                    for command in [
                        f"epm_show_ltrace -T 0x1 | grep dispatch_link_notify",
                        f"ofa_show_ltrace | grep dispatch_link_notify | grep linkstatus"
                    ]:
                        logger.info(f"[{node_name}][slot {slot}] Sending '{command}'")
                        output_buffer.append(f"### {node_name} slot {slot} - {command} ###")
                        output_buffer.append(session.send_command_timing(command,
                                                                         read_timeout=run_spec.globals.timeout_ext,
                                                                         cmd_verify=False))

                    session.send_command("exit", read_timeout=run_spec.globals.timeout_std, expect_string=r'[#\$]')
                    session.find_prompt()

                logger.info(f"[{node_name}] Finished line-card section")

                intf_command_iter = expand(
                    ["show controllers optics {item}",
                     "show interface HundredGigE{item}",
                     "show controllers HundredGigE{item} phy"], intf_list
                )
                slot_command_iter = expand(
                    ["show controllers fia diagshell 0 \"counter pbm=all\" location 0/{item}/CPU0",
                     "show controllers fia diagshell 0 \"show counters full\" location 0/{item}/CPU0"],
                    slot_list
                )
                for command in chain(intf_command_iter, slot_command_iter):
                    logger.info(f"[{node_name}] Sending '{command}'")
                    output_buffer.append(f"### {node_name} - {command} ###")
                    output_buffer.append(session.send_command_timing(command,
                                                                     read_timeout=run_spec.globals.timeout_ext))

        except (NetmikoBaseException, SSHException) as ex:
            logger.critical(f"[{node_name}] Connection error: {ex}")
        except ValueError as ex:
            logger.critical(f"[{node_name}] Parsing error: {ex}")

        device_path = Path(base_path, node_name)
        device_path.mkdir(parents=True, exist_ok=True)
        with open(Path(device_path, output_filename), 'w') as f:
            f.write('\n\n'.join(output_buffer))

        logger.info(f"[{node_name}] Closed session")

    archive_create(cli_args.save, base_path)
    if not cli_args.keep_tmp:
        rmtree(base_path, ignore_errors=True)

    logger.info(f"Saved output to '{cli_args.save}'")


def schema_cmd(cli_args: argparse.Namespace) -> None:
    """
    Generate JSON schema for spec file
    :param cli_args: Parsed CLI args
    :return: None
    """
    with open(cli_args.save, 'w') as schema_file:
        schema_file.write(ConfigModel.schema_json(indent=2))

    logger.info(f"Saved spec file schema as '{cli_args.save}'")


#
# Utility functions
#

def archive_create(archive_filename: str, src_dir: Path) -> None:
    """
    Create a zip archive with the contents of src_dir
    @param archive_filename: zip archive filename
    @param src_dir: directory to be archived, as Path object
    """
    with ZipFile(archive_filename, mode='w', compression=ZIP_DEFLATED) as archive_file:
        for member_path in src_dir.rglob("*"):
            archive_file.write(member_path, arcname=member_path.relative_to(src_dir))

    return


def expand(templates: Sequence[str], items: Iterable[str]) -> Iterable[str]:
    return (template.format(item=item) for template in templates for item in items)
