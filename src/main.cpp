/**
 * @file main.cpp
 * @brief Tensile Tester Main Application - Raspberry Pi Pico
 * 
 * Main entry point for the DIY tensile testing machine firmware.
 * Runs on Raspberry Pi Pico and communicates with Raspberry Pi 4 via USB.
 * 
 * Hardware:
 * - Raspberry Pi Pico (RP2040)
 * - Adafruit NAU7802 24-bit ADC (I2C)
 * - FBFTGMRMTA S-type Load Cell (500N)
 * - DM542T Digital Stepper Driver
 * - Waveshare 7" Display (connected to Pi 4)
 * 
 * Serial Commands:
 * - START     : Start tensile test
 * - STOP      : Stop current test
 * - PAUSE     : Pause test
 * - RESUME    : Resume paused test
 * - ESTOP     : Emergency stop
 * - HOME      : Home the machine
 * - UP [mm]   : Jog up (optional distance)
 * - DOWN [mm] : Jog down (optional distance)
 * - HALT      : Stop movement
 * - SPEED x   : Set test speed (mm/s)
 * - MAXFORCE x: Set max force limit (N)
 * - MAXEXT x  : Set max extension limit (mm)
 * - TARE      : Tare load cell
 * - STATUS    : Get current status
 * - FORCE     : Get current force
 * - POS       : Get current position
 * - CONFIG    : Get configuration
 * - ID        : Get device identification
 * - RESET     : Reset system
 */

#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/i2c.h"
#include "hardware/watchdog.h"
#include <stdio.h>

#include "Config.h"
#include "LoadCell.h"
#include "Stepper.h"
#include "Protocol.h"
#include "StateMachine.h"

// ============================================================================
// Global Objects
// ============================================================================

// Hardware interfaces
LoadCell loadCell(NAU7802_SDA_PIN, NAU7802_SCL_PIN);
Stepper stepper(STEPPER_STEP_PIN, STEPPER_DIR_PIN, STEPPER_ENABLE_PIN);
Protocol protocol;

// State machine
StateMachine stateMachine(loadCell, stepper, protocol);

// ============================================================================
// Setup
// ============================================================================

void setup() {
    // Initialize Pico stdio (USB CDC)
    stdio_init_all();
    
    // Wait for USB connection (with timeout)
    for (int i = 0; i < 30 && !stdio_usb_connected(); i++) {
        sleep_ms(100);
    }
    
    sleep_ms(500);  // Additional delay for terminal to connect
    
    // Startup message
    printf("\n");
    printf("========================================\n");
    printf("  DIY Tensile Tester - Pico Firmware\n");
    printf("  Version 2.0.0\n");
    printf("========================================\n");
    printf("\n");
    
    // Initialize load cell (NAU7802)
    printf("Initializing NAU7802 ADC... ");
    if (loadCell.begin()) {
        printf("OK (Rev: 0x%02X)\n", loadCell.getRevision());
    } else {
        printf("FAILED!\n");
        printf("Check I2C wiring: SDA=GP%d, SCL=GP%d\n", NAU7802_SDA_PIN, NAU7802_SCL_PIN);
    }
    
    // Initialize stepper motor
    printf("Initializing stepper driver (DM542T)... ");
    stepper.begin();
    stepper.setLimitSwitches(LIMIT_SWITCH_TOP_PIN, LIMIT_SWITCH_BOTTOM_PIN);
    stepper.setMaxSpeed(STEPPER_MAX_SPEED);
    stepper.setAcceleration(STEPPER_ACCELERATION);
    printf("OK\n");
    
    // Initialize state machine
    printf("Initializing state machine... ");
    stateMachine.begin();
    printf("OK\n");
    
    // Print configuration
    printf("\n");
    printf("Configuration:\n");
    printf("  Load Cell: 500N S-type (NAU7802)\n");
    printf("  Stepper: %d steps/rev, 1/%d microstepping\n", 
           STEPPER_STEPS_PER_REV, STEPPER_MICROSTEPPING);
    printf("  Lead Screw: %.1f mm/rev\n", STEPPER_MM_PER_REV);
    printf("  Max Force: %.0f N\n", LOADCELL_MAX_FORCE);
    printf("  Sample Rate: %d ms\n", SAMPLE_RATE_MS);
    
    // Check limit switches
    printf("\n");
    printf("Limit switches: TOP=%s BOTTOM=%s\n",
           stepper.isAtTopLimit() ? "ACTIVE" : "open",
           stepper.isAtBottomLimit() ? "ACTIVE" : "open");
    
    // Ready message
    printf("\n");
    printf("System ready. Type 'ID' for identification.\n");
    printf("Type 'HOME' to home the machine before testing.\n");
    printf("\n");
    
    // Initialize protocol (after USB is ready)
    protocol.begin(SERIAL_BAUD_RATE);
    
    // Enable watchdog
    // watchdog_enable(WATCHDOG_TIMEOUT_MS, true);
}

// ============================================================================
// Main Loop
// ============================================================================

void loop() {
    // Process serial commands
    Command cmd = protocol.processInput();
    if (cmd != Command::NONE) {
        stateMachine.handleCommand(cmd);
    }
    
    // Update state machine
    stateMachine.update();
    
    // Feed watchdog
    // watchdog_update();
}

// ============================================================================
// Main Entry Point
// ============================================================================

int main() {
    setup();
    
    while (true) {
        loop();
    }
    
    return 0;
}
