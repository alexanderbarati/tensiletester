cmake_minimum_required(VERSION 3.13)

# =============================================================================
# Raspberry Pi Pico SDK Configuration
# =============================================================================

# Initialize the Pico SDK
# Set PICO_SDK_PATH environment variable or set it here
# set(PICO_SDK_PATH "/path/to/pico-sdk")

# Include the Pico SDK
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# Project name and version
project(TensileTester
    VERSION 2.0.0
    DESCRIPTION "DIY Tensile Testing Machine Firmware - Raspberry Pi Pico"
    LANGUAGES C CXX ASM
)

# C/C++ Standards
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the Pico SDK (must be after project())
pico_sdk_init()

# =============================================================================
# Source Files
# =============================================================================

set(SOURCES
    src/main.cpp
    src/LoadCell.cpp
    src/Stepper.cpp
    src/Protocol.cpp
    src/StateMachine.cpp
)

set(HEADERS
    src/Config.h
    src/LoadCell.h
    src/Stepper.h
    src/Protocol.h
    src/StateMachine.h
)

# =============================================================================
# Executable
# =============================================================================

add_executable(${PROJECT_NAME}
    ${SOURCES}
    ${HEADERS}
)

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# =============================================================================
# Pico SDK Libraries
# =============================================================================

target_link_libraries(${PROJECT_NAME}
    pico_stdlib
    pico_stdio_usb
    hardware_i2c
    hardware_gpio
    hardware_timer
    hardware_watchdog
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 0)

# Create UF2 file for drag-and-drop programming
pico_add_extra_outputs(${PROJECT_NAME})

# =============================================================================
# Compiler Warnings
# =============================================================================

target_compile_options(${PROJECT_NAME} PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
)

# =============================================================================
# Build Information
# =============================================================================

message(STATUS "")
message(STATUS "==============================================")
message(STATUS "  Tensile Tester - Pico Firmware Build")
message(STATUS "==============================================")
message(STATUS "")
message(STATUS "Project: ${PROJECT_NAME} v${PROJECT_VERSION}")
message(STATUS "Target: Raspberry Pi Pico (RP2040)")
message(STATUS "")
message(STATUS "Build Instructions:")
message(STATUS "  1. Set PICO_SDK_PATH environment variable")
message(STATUS "  2. mkdir build && cd build")
message(STATUS "  3. cmake ..")
message(STATUS "  4. make -j4")
message(STATUS "  5. Copy ${PROJECT_NAME}.uf2 to Pico in BOOTSEL mode")
message(STATUS "")

# =============================================================================
# Hardware Pin Configuration (from Config.h)
# =============================================================================

message(STATUS "Hardware Configuration:")
message(STATUS "  Stepper: GP2 (STEP), GP3 (DIR), GP4 (EN)")
message(STATUS "  NAU7802: GP8 (SDA), GP9 (SCL)")
message(STATUS "  Limits:  GP10 (TOP), GP11 (BOTTOM)")
message(STATUS "  E-Stop:  GP12")
message(STATUS "  LEDs:    GP25 (onboard), GP15 (error)")
message(STATUS "")
