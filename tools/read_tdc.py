import board
import busio
from math import log
import digitalio
import time
import sys

REG_FILENAME="ZL30274_REG.mfg"

XO_CONFIG = 0x0026
XO_AMP_SEL = 0x0021

SYS_APLL_PRIMARY_DIV_INT = 0x002A # Only allows values from 16 - 67 (decimal)
SYS_APLL_PRIMARY_DIV_FRAC = 0x002B # 0x002B - 0x002F (32-bit)
SYS_APLL_SECONDARY_DIV = 0x0030 # 0x0030
MASTER_CLK_STATUS = 0x0032
MASTER_CLK_CFG_READY = 0x0033
CENTRAL_FREQ_OFFSET = 0x000B # 0x000B - 0x000E (signed 32-bit)

DPLL_MB_MASK = 0x0602 # 0x0602 - 0x0603 (16-bit)
DPLL_MB_SEM = 0x0604
DPLL_CONFIG = 0x0605

DPLL_FAST_LOCK_CTRL = 0x0609
DPLL_FAST_LOCK_PHASE_ERR = 0x0610 # 0x0610 - 0x0611 (16-bit)
DPLL_FAST_LOCK_FREQ_ERR = 0x0612

DPLL_BW_FIXED = 0x0620
DPLL_DURATION_GOOD = 0x0627
DPLL_PHASE_GOOD = 0x0628 # 0x0628 - 0x062B (32-bit)

DPLL_MEAS_IDX = 0x02D1
DPLL_MEAS_CTRL = 0x02D0
DPLL_MODE_REFSEL_0 = 0x0284
DPLL_MODE_REFSEL_1 = 0x0288
DPLL_MEAS_REF_EDGE_3_0 = 0x02D2

DPLL_PHASE_ERR_READ_MASK = 0x02D4
DPLL_PHASE_ERR_DATA_0 = 0x02D5 # 0x02D5 - 0x02DA (signed 48-bit)
DPLL_PHASE_ERR_DATA_1 = 0x02DB # 0x02DB - 0x02E0 (signed 48-bit)

DPLL_HO_DELAY = 0x0663

DPLL_REF_PRIO_0 = 0x0652
DPLL_REF_PRIO_1 = 0x0653
DPLL_REF_PRIO_2 = 0x0654
DPLL_REF_PRIO_3 = 0x0655

DPLL_STATE_REFSEL_STATUS_0 = 0x0130
DPLL_STATE_REFSEL_STATUS_1 = 0x0131
DPLL_MON_STATUS_0 = 0x0110
DPLL_MON_STATUS_1 = 0x0111

REF_MB_MASK = 0x0502 # 0x0502 - 0x0503 (16-bit)
REF_MB_SEM = 0x0504

REF_CONFIG = 0x050D
REF_SCM = 0x050F
REF_CFM = 0x0514

# REF_FREQ = REF_FREQ_BASE * REF_FREQ_MULT * REF_RATIO_M / REF_RATIO_N
REF_FREQ_BASE = 0x0505 # 0x0505 - 0x0506 (16-bit)
REF_FREQ_MULT = 0x0507 # 0x0507 - 0x0508 (16-bit)
REF_RATIO_M = 0x0509 # 0x0509 - 0x050A (16-bit)
REF_RATIO_N = 0x050B # 0x050B - 0x050C (16-bit)


SYNTH_MB_MASK = 0x0682 # 0x0682 - 0x0683 (16-bit)
SYNTH_MB_SEM = 0x0684

SYNTH_FREQ_BASE = 0x0686 # 0x0686 - 0x0687 (16-bit)
SYNTH_FREQ_MULT = 0x0688 # 0x0688 - 0x068B (32-bit)
SYNTH_RATIO_M = 0x068C # 0x068C - 0x068D (16-bit)
SYNTH_RATIO_N = 0x068E # 0x068E - 0x068F (16-bit)

SYNTH_CTRL_0 = 0x0480
SYNTH_CTRL_1 = 0x0481

REF_PHASE_ERR_READ_RQST = 0x020F
REF_FREQ_MEAS_CTRL = 0x021C

OUTPUT_MB_MASK = 0x0702 # 0x0702 - 0x0703 (16-bit)
OUTPUT_MB_SEM = 0x0704
OUTPUT_MODE = 0x0705
OUTPUT_DIV = 0x070C # 0x070C - 0x070F (32-bit)

OUTPUT_CTRL_5 = 0x04AD
OUTPUT_CTRL_6 = 0x04AE

REF_PHASE_0P = 0x0220 # 0x0220 - 0x0225 (48-bit)
REF_PHASE_0N = 0x0226 # 0x0226 - 0x022B (48-bit)

REF_PHASE_1P = 0x022C # 0x022C - 0x0231 (48-bit)
REF_PHASE_1N = 0x0232 # 0x0232 - 0x0237 (48-bit)

REF_PHASE_2P = 0x0238 # 0x0238 - 0x023D (48-bit)
REF_PHASE_2N = 0x0239 # 0x023E - 0x0243 (48-bit)

REF_PHASE_3P = 0x0244 # 0x0244 - 0x0249 (48-bit)
REF_PHASE_3N = 0x024A # 0x024A - 0x024F (48-bit)

REF_FREQ_0P = 0x0144 # 0x0144 - 0x0147 (32-bit)
REF_FREQ_0N = 0x0148 # 0x0148 - 0x014B (32-bit)

REF_FREQ_1P = 0x014C # 0x014C - 0x014F (32-bit)
REF_FREQ_1N = 0x0150 # 0x0150 - 0x0153 (32-bit)

REF_FREQ_2P = 0x0154 # 0x0154 - 0x0157 (32-bit)
REF_FREQ_2N = 0x0158 # 0x0158 - 0x015B (32-bit)

REF_FREQ_3P = 0x015C # 0x015C - 0x015F (32-bit)
REF_FREQ_3N = 0x0160 # 0x0160 - 0x0163 (32-bit)

def get_page_reg_from_addr(addr):
    page = addr // 128
    reg = addr % 128
    return bytes([page]), bytes([reg])

def get_dpll_statuses():

    state_dict = {
        0 : "FREERUN",
        1 : "HOLDOVER",
        2 : "FAST_LOCK",
        3 : "ACQUIRING",
        4 : "LOCK"
    }

    ref_dict = {
        0 : "REF0P",
        1 : "REF0N",
        2 : "REF1P",
        3 : "REF1N",
        4 : "REF2P",
        5 : "REF2N",
        6 : "REF3P",
        7 : "REF3N"
    }

    dpll0_buf = bytearray(1)
    dpll1_buf = bytearray(1)

    read_from_address(DPLL_STATE_REFSEL_STATUS_0, dpll0_buf)
    read_from_address(DPLL_STATE_REFSEL_STATUS_1, dpll1_buf)

    dpll0_buf = int.from_bytes(dpll0_buf, "big")
    dpll1_buf = int.from_bytes(dpll1_buf, "big")

    dpll0_state = state_dict[dpll0_buf >> 4 & 0b0111]
    dpll1_state = state_dict[dpll1_buf >> 4 & 0b0111]

    dpll0_ref = dpll0_buf & 0b1111
    dpll1_ref = dpll1_buf & 0b1111

    print(f"DPLL0 state: {dpll0_state}, REF: {ref_dict[dpll0_ref]}")
    print(f"DPLL1 state: {dpll1_state}, REF: {ref_dict[dpll1_ref]}")

    dpll0_buf = bytearray(1)
    dpll1_buf = bytearray(1)

    read_from_address(DPLL_MON_STATUS_0, dpll0_buf)
    read_from_address(DPLL_MON_STATUS_1, dpll1_buf)

    dpll0_buf = int.from_bytes(dpll0_buf, "big")
    dpll1_buf = int.from_bytes(dpll1_buf, "big")

    print(f"DPLL0 pslhit: {dpll0_buf >> 7}, flhit: {dpll0_buf >> 5 & 0b1}, ho_ready: {dpll0_buf >> 2 & 0b1}, ho: {dpll0_buf >> 1 & 0b1}, lock: {dpll0_buf & 0b1}")
    print(f"DPLL1 pslhit: {dpll1_buf >> 7}, flhit: {dpll1_buf >> 5 & 0b1}, ho_ready: {dpll1_buf >> 2 & 0b1}, ho: {dpll1_buf >> 1 & 0b1}, lock: {dpll1_buf & 0b1}")



def init_from_config_file(file: str, avg_factor=1):

    value = (avg_factor << 4 & 0xF0) + 1 # First 4 bits indicate avg_factor used for rolling average of phase diff measurements
    # Follows this equation: 
    # curr_avg = prev_avg * ((2^N – 1) / 2^N) + new_measurement * (1 / 2^N)
    # If avg_factor > 0, then N = (avg_factor-1)
    # If avg_factor == 0, N = 15
    # If avg_factor == 1, averaging is disabled

    d12 = digitalio.DigitalInOut(board.D12)
    d12.direction = digitalio.Direction.OUTPUT
    d12.value = False
    time.sleep(0.1)
    d12.value = True
    time.sleep(1)

    with open(file, "r") as fp:
        for line in fp:

            if line[0] == "X":
                cmd, addr, value = line[0:18].split(" , ")
                addr, value = int(addr, 16), int(value, 16) # Convert string to int
                # print(hex(addr), hex(value))
                write_to_device(addr, value)

            elif line[0] == "W":
                sleep_seconds = int(line.split(" , ")[1].strip())/1e6
                time.sleep(sleep_seconds)

                if sleep_seconds == 0.1:
                    clk_status_buf = bytearray(1)
                    read_from_address(MASTER_CLK_STATUS, clk_status_buf)
                    assert clk_status_buf == bytes([0x03]), "Bad clock config!" # Make sure APLL is locked and ready
        

def init_phase_meas(avg_factor=0):
    value = (avg_factor << 4 & 0xF0) + 1 # First 4 bits indicate avg_factor used for rolling average of phase diff measurements
    # Follows this equation: 
    # curr_avg = prev_avg * ((2^N – 1) / 2^N) + new_measurement * (1 / 2^N)
    # If avg_factor > 0, then N = (avg_factor-1)
    # If avg_factor == 0, N = 15
    # If avg_factor == 1, averaging is disabled

    d12 = digitalio.DigitalInOut(board.D12)
    d12.direction = digitalio.Direction.OUTPUT
    d12.value = False
    time.sleep(0.1)
    d12.value = True
    time.sleep(1)

    write_to_device(XO_CONFIG, 0b00000001)
    write_to_device(SYS_APLL_PRIMARY_DIV_INT, 50)
    write_to_device(SYS_APLL_SECONDARY_DIV, 5)
    write_to_device(CENTRAL_FREQ_OFFSET, 0x00000000, reg_width=4, signed=True)
    write_to_device(MASTER_CLK_CFG_READY, 0x01)

    time.sleep(0.1) # Wait at least 100ms before executing next writes

    clk_status_buf = bytearray(1)
    read_from_address(MASTER_CLK_STATUS, clk_status_buf)

    assert clk_status_buf == bytes([0x03]), "Bad clock config!" # Make sure APLL is locked and ready


    write_to_device(REF_MB_MASK, 0x00FF, reg_width=2)
    write_to_device(REF_MB_SEM, 0x02)
    time.sleep(0.02)

    write_to_device(REF_CONFIG, 0b01000101)
    # write_to_device(REF_SCM, 0x06)
    # write_to_device(REF_CFM, 0x06)

    write_to_device(REF_FREQ_BASE, 1_000, reg_width=2)
    write_to_device(REF_FREQ_MULT, 80, reg_width=2)
    write_to_device(REF_RATIO_M, 1_000, reg_width=2)
    write_to_device(REF_RATIO_N, 1, reg_width=2)
    write_to_device(REF_MB_SEM, 0x01)
    time.sleep(0.02)

    write_to_device(DPLL_MB_MASK, 0b11)
    write_to_device(DPLL_MB_SEM, 0x02)
    time.sleep(0.02)

    write_to_device(DPLL_CONFIG, 0x00)
    write_to_device(DPLL_BW_FIXED, 0b100)
    write_to_device(DPLL_FAST_LOCK_CTRL, 0x11)
    write_to_device(DPLL_FAST_LOCK_PHASE_ERR, 0x0000, reg_width=2)
    write_to_device(DPLL_FAST_LOCK_FREQ_ERR, 0x00)

    write_to_device(DPLL_DURATION_GOOD, 0x01)
    time.sleep(2)

    write_to_device(DPLL_MB_SEM, 0x01)
    time.sleep(0.02)

    write_to_device(DPLL_MODE_REFSEL_0, 0b01000010)
    write_to_device(DPLL_MODE_REFSEL_1, 0b01100010)
    time.sleep(0.1)

    write_to_device(SYNTH_MB_MASK, 0b0000_0000_0000_0011, reg_width=2)
    write_to_device(SYNTH_MB_SEM, 0x02)
    time.sleep(0.02)
    a = bytearray(4)
    write_to_device(SYNTH_FREQ_BASE, 1, reg_width=2)
    write_to_device(SYNTH_FREQ_MULT, 400_000_000, reg_width=4)
    write_to_device(SYNTH_RATIO_M, 1, reg_width=2)
    write_to_device(SYNTH_RATIO_N, 1, reg_width=2)

    write_to_device(SYNTH_MB_SEM, 0x01)
    time.sleep(0.02)

    write_to_device(OUTPUT_MB_MASK, 0b0000_0000_0110_0000, reg_width=2)
    write_to_device(OUTPUT_MB_SEM, 0x02)
    time.sleep(0.02)

    write_to_device(OUTPUT_MODE, 0x10)
    write_to_device(OUTPUT_DIV, 0x02, reg_width=4)

    write_to_device(OUTPUT_MB_SEM, 0x01)
    time.sleep(0.02)

    write_to_device(DPLL_MEAS_IDX, 0x00)
    write_to_device(DPLL_MEAS_REF_EDGE_3_0, 0x00)
    write_to_device(DPLL_MEAS_CTRL, value)
    write_to_device(DPLL_PHASE_ERR_READ_MASK, 0b11)

    write_to_device(SYNTH_CTRL_0, 0x01) # DPLL0
    write_to_device(SYNTH_CTRL_1, 0x11) # DPLL1

    write_to_device(OUTPUT_CTRL_5, 0b0000_0000) # Synth0
    write_to_device(OUTPUT_CTRL_6, 0b0000_0000) # Synth1

    # write_to_device(REF_PHASE_ERR_READ_RQST, 0x01)
    # time.sleep(0.1)

    # buf = bytearray(1)
    # read_from_address(REF_PHASE_ERR_READ_RQST, buf)

    # attempts = 1
    # while buf == bytes([0x01]) and attempts < 10:
    #     read_from_address(REF_PHASE_ERR_READ_RQST, buf)
    #     attempts += 1
    #     time.sleep(1)
    
    # if attempts == 10:
    #     raise TimeoutError("Unable to read ref phase data!")
    
    # while True:
    get_dpll_statuses()
    # time.sleep(5)



def write_to_device(addr: int, value: int, reg_width=1, signed=False):
    page_reg = bytes([0x7F]) # Page value register on each page
    page, reg = get_page_reg_from_addr(addr)

    i2c.writeto(0x70, page_reg + page) # Set page
    
    value = value.to_bytes(reg_width, "big", signed=signed)

    i2c.writeto(0x70, reg + value)


def read_from_address(addr: int, buffer_in: bytearray):
    page_reg = bytes([0x7F]) # Page value register on each page
    page, reg = get_page_reg_from_addr(addr)

    i2c.writeto(0x70, page_reg + page) # Set page
    i2c.writeto_then_readfrom(0x70, reg, buffer_in)
    # decimal_val = int.from_bytes(buffer_in, "big")
    # if decimal_val > 2**(len(buffer_in)*8-1) -1:
    #     decimal_val -= 2**(len(buffer_in)*8)
    # print(buffer_in, decimal_val)

# d12 = digitalio.DigitalInOut(board.D12)
# d12.direction = digitalio.Direction.OUTPUT
# d12.value = False
# time.sleep(0.1)
# d12.value = True
# time.sleep(0.5)

i2c = busio.I2C(board.SCL, board.SDA)
i2c.try_lock()

# buff = bytearray(1)

# i2c.writeto_then_readfrom(0x70, bytes([0x7f]), buff)

# print(buff)

print("Initializing ZL30274 PLL...")
init_from_config_file("./reg.mfg")
sys.stdout.write("\033[F")
print("Initializing ZL30274 PLL..." + " "*5 + "Done!\n\nRunning PLL Monitor...")


# print("Running init_phase_meas")
# init_phase_meas()
# print("Finished init_phase_meas")

ref0P_phase_buf = bytearray(6)
ref0N_phase_buf = bytearray(6)

ref1P_phase_buf = bytearray(6)
ref1N_phase_buf = bytearray(6)

ref2P_phase_buf = bytearray(6) # Read P and N phase values seperately
ref2N_phase_buf = bytearray(6) # IN0 -> Ref 2, IN1 -> Ref 3 on TDC board

ref3P_phase_buf = bytearray(6) # bytearrays read a signed 48-bit values, LSB == 0.01ps, big-endian order, value modded to [-0.5, +0.5] periods
ref3N_phase_buf = bytearray(6) # Updates at ~40Hz (~25ms) or ref clock frequency, whichever is lower

ref0P_freq_buf = bytearray(4)
ref0N_freq_buf = bytearray(4)

ref1P_freq_buf = bytearray(4)
ref1N_freq_buf = bytearray(4)

ref2P_freq_buf = bytearray(4)
ref2N_freq_buf = bytearray(4)

ref3P_freq_buf = bytearray(4)
ref3N_freq_buf = bytearray(4)

init = True

while True:
    # print("Holding program open...")
    buf = bytearray(1)
    write_to_device(REF_PHASE_ERR_READ_RQST, 0x01)
    write_to_device(REF_FREQ_MEAS_CTRL, 0b01)

    read_from_address(REF_FREQ_MEAS_CTRL, buf)
    time.sleep(0.1)
    while int.from_bytes(buf, "big") & 0b00000011 != 0:
        read_from_address(REF_FREQ_MEAS_CTRL, buf)
        time.sleep(0.1)
    
    def int_from_bytes(buffer):
        val = int.from_bytes(buffer, "big")
        if val > 2**(len(buffer)*8 - 1) - 1:
            val -= 2**(len(buffer)*8)
        return val

    read_from_address(REF_PHASE_0P, ref0P_phase_buf)
    # read_from_address(REF_PHASE_0N, ref0N_phase_buf)

    read_from_address(REF_PHASE_1P, ref1P_phase_buf)
    # read_from_address(REF_PHASE_1N, ref1N_phase_buf)

    read_from_address(REF_PHASE_2P, ref2P_phase_buf)
    # read_from_address(REF_PHASE_2N, ref2N_phase_buf)

    read_from_address(REF_PHASE_3P, ref3P_phase_buf)
    # read_from_address(REF_PHASE_3N, ref3N_phase_buf)

    # read_from_address(DPLL_PHASE_ERR_DATA_0, ref0N_phase_buf)
    # read_from_address(DPLL_PHASE_ERR_DATA_1, ref1N_phase_buf)

    read_from_address(REF_FREQ_0P, ref0P_freq_buf)
    # read_from_address(REF_FREQ_0N, ref0N_freq_buf)

    read_from_address(REF_FREQ_1P, ref1P_freq_buf)
    # read_from_address(REF_FREQ_1N, ref1N_freq_buf)

    read_from_address(REF_FREQ_2P, ref2P_freq_buf)
    # read_from_address(REF_FREQ_2N, ref2N_freq_buf)

    read_from_address(REF_FREQ_3P, ref3P_freq_buf)
    # read_from_address(REF_FREQ_3N, ref3N_freq_buf)

    if not init:
        for i in range(11):
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
    else:
        print("*"*50)
        print("-"*50)

    get_dpll_statuses()
    print(f"REF0/OUT5 Phase: {int_from_bytes(ref0P_phase_buf)*10:15} fs | Freq: {int_from_bytes(ref0P_freq_buf):8} Hz")
    print(f"REF1/OUT6 Phase: {int_from_bytes(ref1P_phase_buf)*10:15} fs | Freq: {int_from_bytes(ref1P_freq_buf):8} Hz")
    print(f"REF2/IN0  Phase: {int_from_bytes(ref2P_phase_buf)*10:15} fs | Freq: {int_from_bytes(ref2P_freq_buf):8} Hz")
    print(f"REF3/IN1  Phase: {int_from_bytes(ref3P_phase_buf)*10:15} fs | Freq: {int_from_bytes(ref3P_freq_buf):8} Hz")
    print(f"REF2/REF3 Phase Difference: {int_from_bytes(ref2P_phase_buf)/1000000000-int_from_bytes(ref3P_phase_buf)/100000000:.2f} us")
    print("-"*50)
    print("*"*50)
    

    time.sleep(1)
    init = False
i2c.unlock()