# Installation

## prepare

you need the following software to build and run this project:

* git: https://git-scm.com/book/de/v2/Erste-Schritte-Git-installieren
* python3: https://www.python.org/downloads/ (allready installed on most systems)
* make: https://learn.microsoft.com/en-us/windows/package-manager/winget/ (allready installed on most systems)
* oss-cad-suite-build: https://github.com/YosysHQ/oss-cad-suite-build
* PlatformIO Core: https://platformio.org/install (optional for the Ethernet-Board)


## get the Sources
```
git clone https://github.com/multigcs/LinuxCNC-RIO
cd LinuxCNC-RIO
```

## generate the Project-Files

to generate/update all needed files in Output/TangNano9K/:
```
python3 buildtool.py configs/TangNano9K/config.json
```
or if you want to use the optional Ethernet-Board:
```
python3 buildtool.py configs/TangNano9K/config-udp.json
```
in this case, please first flash the ethernet-board, check the IP and edit the json-file


## build and load the FPGA-Bitstream

connect the TangNano9K board to your USB-Port and run:
```
cd Output/TangNano9K/Firmware
make all load
```
this will need some time

## compile and install the hal-component

please copy the folder Output/TangNano9K/LinuxCNC/Components to your target system where LinuxCNC is running,
then you can compile and install the component:

```
halcompile --install  Output/TangNano9K/LinuxCNC/Components/rio.c
```

## sample config for LinuxCNC

there are also a sample configuration in Output/TangNano9K/LinuxCNC/ConfigSamples/rio/

you can copy this folder to your LinuxCNC machine and start it:

```
linuxcnc Output/TangNano9K/LinuxCNC/ConfigSamples/rio/rio.ini
```


## connection to the Raspberry-PI

you can use a Raspberry-PI 4 with direct SPI connection to the FPGA-Board,
you can find the pinout in README.md (BOB-Adapter SPI-Pins)


## build and flash the optional Ethernet-Board

https://www.olimex.com/Products/IoT/ESP32/ESP32-POE-ISO/open-source-hardware

first you have to install the PlatformIO Core: https://platformio.org/install

then go into Folder: UDP2SPI-Bridge/ESP32-PoE-ISO and run the build process:

```
cd UDP2SPI-Bridge/ESP32-PoE-ISO
make build
```

then connect the Ethernet-Board to your USB and flash the Firmware:

```
make upload
```













