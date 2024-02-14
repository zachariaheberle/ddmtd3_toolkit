import subprocess
from glob import glob
import os
import sys
import shutil
import numpy as np

def get_verified_input(input_message, allowed_values, error_message):
    user_input = input(input_message)
    while user_input not in allowed_values:
        print(error_message, end="\n\n")
        user_input = input(input_message)
    return user_input

if __name__ == "__main__":

    si5394_config_files = glob("./pll_configs/si5394/*MHz_*k.h")
    zl30274_config_files = glob("./pll_configs/zl30274/*MHz_*k.mfg")

    allowed_frequencies = [os.path.split(file)[1].split("MHz")[0] for file in si5394_config_files 
                           if os.path.split(file)[1][:-2] in " ".join(zl30274_config_files)]

    print(f"Available Frequencies: {', '.join(np.unique([freq + 'MHz' for freq in allowed_frequencies]))}")
    FREQ = get_verified_input("Choose an input frequency (MHz): ", allowed_frequencies, "No config with that frequency was found!")

    allowed_N = [os.path.split(file)[1].split("MHz_")[1][:-2] for file in si5394_config_files 
                 if os.path.split(file)[1][:-2] in " ".join(zl30274_config_files) and FREQ in file]
    

    print(f"\nAvailable N values: {', '.join(np.unique(allowed_N))}")
    allowed_N = allowed_N + [str(int(n[:-1])*1000) for n in allowed_N]
    N = get_verified_input("Choose an N value: ", allowed_N, "No config with that N value was found!")

    si5394_config = f"./pll_configs/si5394/{FREQ}MHz_{N}.h"
    zl30274_config = f"./pll_configs/zl30274/{FREQ}MHz_{N}.h"

    print(f"\nUsing Si5394 PLL config: \n\t{si5394_config}")
    print(f"\nUsing ZL30274 PLL config: \n\t{zl30274_config}\n")

    print("Flashing Si5394 PLL...")
    sys.stdout.write("\033[F")

    shutil.copyfile(si5394_config, f"/media/{os.environ['USER']}/CIRCUITPY/Si5394_REG.h") # ORDER MATTERS IN WHICH THESE DEVICES ARE PLUGGED IN
    shutil.copyfile(zl30274_config, f"/media/{os.environ['USER']}/CIRCUITPY1/ZL30274_REG.mfg")
    subprocess.run(["mpremote", "connect", "/dev/ttyACM0", "run", "./tools/flash_pll.py"])
    # subprocess.run(["./tools/start_pll.sh", si5394_config])

    print("Flashing Si5394 PLL..." + " "*10 + "Done!")

    try:
        subprocess.run(["mpremote", "connect", "/dev/ttyACM1", "run", "./tools/read_tdc.py"])
    except KeyboardInterrupt:
        print("\nClosing monitor...")