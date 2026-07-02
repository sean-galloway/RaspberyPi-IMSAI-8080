cmake_minimum_required(VERSION 3.13)

# Pull in the Pico SDK (set PICO_SDK_PATH in your environment, or drop
# pico_sdk_import.cmake next to this file). See firmware/README.md.
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(imspi8080 C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(imspi8080
    src/main.c
    src/crc8.c
    src/tlc5947.c
    src/hc165.c
    src/protocol.c
)

target_link_libraries(imspi8080
    pico_stdlib
    hardware_pwm
    hardware_gpio
)

# Panel link is native USB CDC; disable UART stdio.
pico_enable_stdio_usb(imspi8080 1)
pico_enable_stdio_uart(imspi8080 0)

pico_add_extra_outputs(imspi8080)   # produces imspi8080.uf2
