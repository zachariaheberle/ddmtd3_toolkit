# Written by Thomas Vadnais and Zachariah Eberle
import board
import busio
import time

# REG_FILENAME = "./PLL_Conf/dcps_side/test120MHz.h"
REG_FILENAME="Si5394_REG.h"


def read_config(config_filename, si5344Instance):
    """
    reg_filename --> ouput of the Clock Builder C header file
    returns list of addresses and values including the preamble and the postamble
    """
    encd = "utf-8"  # encoding
    TOTAL_REG_NUM = 0  # total number of registers actions
    addresses_read = 0

    with open(config_filename, encoding=encd) as fp:
        for i, line in enumerate(fp):
            if "#define SI5394_REVA_REG_CONFIG_NUM_REGS" in line:
                TOTAL_REG_NUM = int(line.split()[-1])
            elif ("{" in line) & ("}" in line) & ("0x" in line):
                addr, val = line.split(" ")[1:3]
                address = addr.split(",")[0]
                value = val.split(",")[0]
                si5344Instance.transfer(address, value)
                addresses_read += 1
            elif "};" in line:
                break


    # print("Total Registers Detected: ", TOTAL_REG_NUM)
    # print("Total Registers Read    : ", addresses_read)
    assert TOTAL_REG_NUM == addresses_read


class si5344h_i2c:
    def __init__(self, i2cbus, i2caddress):
        self.i2c_device = i2cbus
        self.i2c_address = i2caddress
        self.PAGE_ADDR = 0x01  # Page Address

    def write_i2c(self, address, data):
        # The write_byte_data used in the original code is a SMbus
        # method used to write a byte of data to a specific address bus
        # For the circuitpython change we use the writeto method of the i2cdevice class
        self.i2c_device.writeto(self.i2c_address, bytes([address,data]))

    def read_i2c(self, register):
        result = bytearray(1)
        self.i2c_device.writeto_then_readfrom(self.i2c_address, bytes([register]), result)
        return result

    def set_page(self, page):
        self.i2c_device.writeto(self.i2c_address, bytes([0x01, page]))
        # Check if the page is correct...
        # readPage = self.read_i2c(self.PAGE_ADDR)
        # if int.from_bytes(readPage, "big") != page:
            # print("Unsuccessful Page Settings!", int.from_bytes(readPage, "big"), " ", page)

    def transfer(self, addr, val):
        page_byte = (int(addr, 16) >> 8) & 0xFF
        addr_byte = (int(addr, 16)) & 0xFF
        val_byte = int(val, 16) & 0xFF

        self.set_page(page_byte)
        self.write_i2c(addr_byte, val_byte)
        if page_byte == 0x05 and addr_byte == 0x40: # End of preamble, wait 300 ms
            time.sleep(0.3)

i2cbus = busio.I2C(board.SCL, board.SDA, frequency = 100000)
i2cbus.try_lock()
si5344h = si5344h_i2c(i2cbus, 0x68)
read_config(REG_FILENAME, si5344h) # Flash pll
i2cbus.unlock()

