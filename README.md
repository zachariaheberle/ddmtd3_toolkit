# DDMTD3 Toolkit

This repo contains the tools used for testing the DDMTD3 setup, please check the schematics folder to see how everything is wired.

The setup current consists of three boards:
- CW_PLL (One of the purple boards)
- CW_DDMTD (The green board)
- CW_TDC (The other purple board)

The PLL board is responsible for generating both the measurement and offset clocks to the DDMTD board. On board, there is an Si5394 PLL to generate the clocks and an Itsybitsy M4 Express microcontroller on board that is used to program the PLL. The offset clock (on OUT0) is fed into the CLK input on the DDMTD board. the measurement clocks (on OUT1 and OUT2) are fed into D0/D1 (order doesn't matter) on the DDMTD board.

The DDMTD board is responsible for generating beat clocks based off the two measurement clocks coming in on D0 and D1 using the offset clock on the CLK input. More information about the functions of this board can be read here: https://arxiv.org/pdf/2210.05764.pdf
The outputs of the beat clock are output without any filtering on LPF0 and LPF1, and are output after passing through a second flipflop on the FF0 and FF1 outputs. (Although at the moment, FF1 is broken).

The TDC board is responsible for both cleaning up and measuring the relative phases of the the beat clocks coming from the DDMTD board. The inputs from the DDMTD board are fed into IN0 and IN1 on the board. These are then fed to the ZL30274 PLL chip on board on REF2 and REF3 of the chip. These clocks are then cleaned up and output on OUT5 and OUT6 of the chip an fed back into REF0 and REF1.You can read more about the functioning of the ZL30274 chip here: https://ww1.microchip.com/downloads/en/DeviceDoc/ZL30273-4-1-and-2-Channel-Jitter-Attenuators-with-up-to-20-Outputs-Product-Brief-20006636.pdf Additionally, check the schematics folder for more info on wiring.

## Required Python Packages
```text
numpy (whatever version you want)
```

## Setup

To set up the DDMTD3 for testing, please attach everything as shown below

(Insert picture here)

**IMPORTANT: Please ensure that you connect the microcontroller (Itsybitsy M4 Express) on the PLL board to your computer BEFORE the microcontroller on the TDC board. The PLL board's microcontroller is hard-coded to be at /dev/ttyACM0, and the TDC board's microcontroller is at /dev/ttyACM1, the order in which you connect these devices matters!**

Once every is connected, simply run the main.py script from within its directory and select which frequency plan you wish to use. From there, the device will automatically configure itself and begin running a PLL monitoring program that watches various registers on the ZL30274 chip. However, you may wish to create additional clock configurations than what has already been created, more on that in the next section.

## Clock Configuration
To generate a different frequency to test the clocks at, you will need to generate a new C header file for the Si5394 and a new .mfg file for the ZL30274.

### Clock Configuration - Si5394
To generate new clocks for the Si5394, you will want to use the ClockBuilder Pro Program from Skyworks. A link to download the program can be found here: https://www.skyworksinc.com/Application-Pages/Clockbuilder-Pro-Software

Start the program, select "Create New Project" and under "Jitter Attenuators" select the Si5394. You will only need to change a few settings.

#### Set the Reference Clocks
On step 3 of 17 on the page titled "Application & Reference", set the application as "Standard" and set the reference as an external XO Reference with a frequency of 48 MHz.

#### Enable Free Run Only Mode
On step 4 of 17 on the page titled "Free Run Only Mode", simply check the box to enable free run only mode.

#### Set the Output Clocks
On step 5 of 17 on the page titled "Output Clocks", OUT0 will be your offset clock, while OUT1 and OUT2 will be your measurement clocks. For OUT1 and OUT2, simply set their frequency to the desired measurement clock frequency. For OUT0, you will want to create an offset clock based on the chosen N value. Typically, we use 10k or 100k for this value, although the choice is arbitrary. Set the offset clock frequency as follows, 

$f\cdot\frac{N}{N+1}$.

Where $f$ is the desired clock frequency and $N$ is the chosen offset value. For example, for a 160 MHz clock with $N=100000$, we can simply type,
```text
160M*(100000/100001)
```
Into the program and it will use that to set the offset clock value.

#### Saving as a C Header File
Once you have set up the clock with the desired frequency plan, simply click the "Finish" button, then "Export", then save the file as a C header file. Don't forget to check the box to include pre- and post-write control registers writes before saving. Additionally, you will want to save the file with a specific naming scheme as follows:
```text
{frequency in megahertz}MHz_{N divided by 1000}k.h
```
For example, to save a file with a 160MHz measurement frequency and an N value of 100k, save it as,
```text
160MHz_100k.h
```
Then simply move the new file to ./pll_configs/si5394 and you're all set! (Don't forget to also set up the corresponding ZL30274 config file as well)

### Clock Configuration - ZL30274
To generate new clocks for the ZL30274, you will want to use the Microchip Azurite GUI. This software is not easily obtained, but can be obtained from Microchip with a request. Just download it from someone else who has access.

#### Loading the register file
To begin, first open the Azurite GUI and select the ZL30274 under the Azurite device family. From here, I highly recommend loading in a previously configured .mfg register file that has already been configured as use that file as a base. You can do this by selecting the ☰ symbol in the upper left corner of the GUI and selecting File > Load Registers. Then simply select one of the .mfg files in this repo as a base and choose "Reset then load".

#### Setting the Input Reference Clock Frequencies
We will need to change the frequencies on all of the input clock (REF0 - REF3) to the beat frequency of the desired frequency plan. You can calculate the beat frequency by the following equation,

$\frac{f}{N+1}$.

Where $f$ is the desired frequency and $N$ is the desired offset N value for the frequency plan. For $N>65535$, you will not always be able to get an exact frequency match since the denominator is limited by 16 bits. In such cases, simply type in the decimal frequency with as many digits as you can into the program. Repeat this step for all four inputs

#### Setting the Synth/Output Clock Frequencies
Setting the synth and output clock frequencies is a bit tricky, since the synths need to be running between 187 MHz - 748 MHz, which is well above our desired beat clock frequency. To get around this, there is a divisor on the outputs that can step the frequency back down to the same as the original beat clocks. You will have to manually adjust these two settings in tandem to ensure that the output clocks match the frequency of the beat clocks / input clocks. You should only use synths Synth0 and Synth1 and outputs OUT5 and OUT6. Both synths should have the same frequency and both outputs should have the same frequency.

#### Saving as an .mfg File
Once you have configured all of the clocks, you will want to save the configuration file by once again clicking on the ☰ symbol and selecting File > Save Modified Registers. Additionally, you will want to save the file with a similar naming scheme as the Si5394:
```text
{frequency in megahertz}MHz_{N divided by 1000}k.mfg
```
For example, to save a file with a 160MHz measurement frequency and an N value of 100k, save it as,
```text
160MHz_100k.mfg
```
Then simply move the new file to ./pll_configs/zl30274 and you're all set! (Don't forget to also set up the corresponding Si5394 config file as well)



