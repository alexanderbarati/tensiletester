
# This file must be in your project root for CMake to find the Pico SDK
# It will import the Pico SDK from the path set in PICO_SDK_PATH
if(NOT DEFINED PICO_SDK_PATH)
	if(DEFINED ENV{PICO_SDK_PATH})
		set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})
	else()
		message(FATAL_ERROR "PICO_SDK_PATH is not set. Please set it to your pico-sdk directory.")
	endif()
endif()
include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)
