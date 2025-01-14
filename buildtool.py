#!/usr/bin/env python3
#
#

import argparse
import glob
import importlib
import json
import os
import sys

project = {}

parser = argparse.ArgumentParser()
parser.add_argument(
    "configfile", help="json config file", type=str, nargs="?", default=None
)
parser.add_argument(
    "outputdir", help="output directory", type=str, nargs="?", default=None
)
args = parser.parse_args()


project["config"] = args.configfile


data = open(project["config"], "r").read()
project["jdata"] = json.loads(data)


# loading plugins
project["plugins"] = {}
for path in glob.glob("plugins/*"):
    plugin = path.split("/")[1]
    if os.path.isfile(f"plugins/{plugin}/plugin.py"):
        vplugin = importlib.import_module(".plugin", f"plugins.{plugin}")
        project["plugins"][plugin] = vplugin.Plugin(project["jdata"])


generators = {}
for path in glob.glob("generators/*"):
    generator = path.split("/")[1]
    if os.path.isfile(f"generators/{generator}/{generator}.py"):
        generators[generator] = importlib.import_module(
            f".{generator}", f"generators.{generator}"
        )


project["verilog_files"] = []
project["pinlists"] = {}
project["expansions"] = {}
project["internal_clock"] = None

project["osc_clock"] = False
if project["jdata"].get("toolchain") == "icestorm":
    project["osc_clock"] = project["jdata"]["clock"].get("osc")
    project["internal_clock"] = project["jdata"]["clock"].get("internal")
    if project["internal_clock"]:
        pass
    elif project["osc_clock"]:
        project["pinlists"]["main"] = (
            ("sysclk_in", project["jdata"]["clock"]["pin"], "INPUT", True),
        )
    else:
        project["pinlists"]["main"] = (
            ("sysclk", project["jdata"]["clock"]["pin"], "INPUT", True),
        )

if "blink" in project["jdata"]:
    project["pinlists"]["blink"] = (
        ("BLINK_LED", project["jdata"]["blink"]["pin"], "OUTPUT"),
    )

if "error" in project["jdata"]:
    project["pinlists"]["error"] = (
        ("ERROR_OUT", project["jdata"]["error"]["pin"], "OUTPUT"),
    )

if "enable" in project['jdata']:
    project['pinlists']["enable"] = (("ENA", project['jdata']["enable"]["pin"], "OUTPUT"),)

for plugin in project["plugins"]:
    if hasattr(project["plugins"][plugin], "pinlist"):
        project["pinlists"][plugin] = project["plugins"][plugin].pinlist()
    if hasattr(project["plugins"][plugin], "expansions"):
        project["expansions"][plugin] = project["plugins"][plugin].expansions()


# check for double assigned pins
double_pins = False
uniq_pins = {}
for pinlist in project["pinlists"].values():
    for pinsetup in pinlist:
        pin_name = pinsetup[0]
        pin_id = pinsetup[1]
        if pin_id in uniq_pins:
            print()
            print(f"ERROR: pin {pin_id} allready in use")
            print(f"  old: {uniq_pins[pin_id]}")
            print(f"  new: {pinsetup}")
            double_pins = True
        else:
            uniq_pins[pin_id] = pinsetup
if double_pins:
    print("")
    exit(1)
    
project["vouts"] = 0
for plugin in project["plugins"]:
    if hasattr(project["plugins"][plugin], "vouts"):
        project["vouts"] += project["plugins"][plugin].vouts()

project["vins"] = 0
for plugin in project["plugins"]:
    if hasattr(project["plugins"][plugin], "vins"):
        project["vins"] += project["plugins"][plugin].vins()

project["dins"] = 0
project["dinnames"] = []
for plugin in project["plugins"]:
    if plugin.startswith("din_"):
        if hasattr(project["plugins"][plugin], "dins"):
            project["dins"] += project["plugins"][plugin].dins()
        if hasattr(project["plugins"][plugin], "dinnames"):
            project["dinnames"] += project["plugins"][plugin].dinnames()
for plugin in project["plugins"]:
    if not plugin.startswith("din_"):
        if hasattr(project["plugins"][plugin], "dins"):
            project["dins"] += project["plugins"][plugin].dins()
        if hasattr(project["plugins"][plugin], "dinnames"):
            project["dinnames"] += project["plugins"][plugin].dinnames()

project["douts"] = 0
project["doutnames"] = []
for plugin in project["plugins"]:
    if plugin.startswith("dout_"):
        if hasattr(project["plugins"][plugin], "douts"):
            project["douts"] += project["plugins"][plugin].douts()
        if hasattr(project["plugins"][plugin], "doutnames"):
            project["doutnames"] += project["plugins"][plugin].doutnames()
for plugin in project["plugins"]:
    if not plugin.startswith("dout_"):
        if hasattr(project["plugins"][plugin], "douts"):
            project["douts"] += project["plugins"][plugin].douts()
        if hasattr(project["plugins"][plugin], "doutnames"):
            project["doutnames"] += project["plugins"][plugin].doutnames()


project["jointtypes"] = []
for joint in project['jdata']['joints']:
    project["jointtypes"].append(joint['type'])

project["vins_data"] = []
for plugin in project["plugins"]:
    if hasattr(project["plugins"][plugin], "vdata"):
        project["vins_data"] += project["plugins"][plugin].vdata()

project["joints"] = 0
for plugin in project["plugins"]:
    if hasattr(project["plugins"][plugin], "joints"):
        project["joints"] += project["plugins"][plugin].joints()

project["jointcalcs"] = {}
for plugin in project["plugins"]:
    if hasattr(project["plugins"][plugin], "jointcalcs"):
        project["jointcalcs"].update(project["plugins"][plugin].jointcalcs())

project["joints_en_total"] = (project["joints"] + 7) // 8 * 8
project["douts_total"] = (project["douts"] + 7) // 8 * 8
project["dins_total"] = (project["dins"] + 7) // 8 * 8
project["douts_total"] = max(project["douts_total"], 8)
project["dins_total"] = max(project["dins_total"], 8)

project["tx_data_size"] = 32
project["tx_data_size"] += project["joints"] * 32
project["tx_data_size"] += project["vins"] * 32
project["tx_data_size"] += project["dins_total"]
project["rx_data_size"] = 32
project["rx_data_size"] += project["joints"] * 32
project["rx_data_size"] += project["vouts"] * 32
project["rx_data_size"] += project["joints_en_total"]
project["rx_data_size"] += project["douts_total"]
project["data_size"] = max(project["tx_data_size"], project["rx_data_size"])


# file structure
if args.outputdir:
    project["OUTPUT_PATH"] = args.outputdir
else:
    project[
        "OUTPUT_PATH"
    ] = f"Output/{project['jdata']['name'].replace(' ', '_').replace('/', '_')}"

project["FIRMWARE_PATH"] = f"{project['OUTPUT_PATH']}/Firmware"
project["SOURCE_PATH"] = f"{project['FIRMWARE_PATH']}"
project["PINS_PATH"] = f"{project['FIRMWARE_PATH']}"
project["LINUXCNC_PATH"] = f"{project['OUTPUT_PATH']}/LinuxCNC"
os.system(f"mkdir -p {project['OUTPUT_PATH']}")
os.system(f"mkdir -p {project['SOURCE_PATH']}")
os.system(f"mkdir -p {project['PINS_PATH']}")
os.system(f"mkdir -p {project['LINUXCNC_PATH']}")
os.system(f"mkdir -p {project['LINUXCNC_PATH']}/Components/")
os.system(f"mkdir -p {project['LINUXCNC_PATH']}/ConfigSamples/rio")
os.system(f"mkdir -p {project['LINUXCNC_PATH']}/ConfigSamples/rio/subroutines")
os.system(f"mkdir -p {project['LINUXCNC_PATH']}/ConfigSamples/rio/m_codes")
os.system(f"cp -a files/subroutines/* {project['LINUXCNC_PATH']}/ConfigSamples/rio/subroutines")


if project["jdata"].get("toolchain") == "diamond":
    project["SOURCE_PATH"] = f"{project['FIRMWARE_PATH']}/impl1/source"
    project["PINS_PATH"] = f"{project['FIRMWARE_PATH']}/impl1/source"
    os.system(f"mkdir -p {project['SOURCE_PATH']}")
    os.system(f"mkdir -p {project['PINS_PATH']}")


for plugin in project["plugins"]:
    if hasattr(project["plugins"][plugin], "ips"):
        for ipv in project["plugins"][plugin].ips():
            project["verilog_files"].append(ipv)
            # os.system(f"verilator --lint-only -Wall plugins/{plugin}/{ipv}")
            os.system(f"which verilator >/dev/null && verilator --lint-only plugins/{plugin}/{ipv}")
            os.system(f"cp -a plugins/{plugin}/{ipv} {project['SOURCE_PATH']}/{ipv}")

print(f"generating files in {project['OUTPUT_PATH']}")


for generator in generators.values():
    generator.generate(project)
