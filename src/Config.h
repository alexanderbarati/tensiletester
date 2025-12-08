#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// Tensile Tester Configuration
// Hardware: Raspberry Pi Pico + NAU7802 + DM542T Driver
// ============================================================================

// --- Platform ---
#define PLATFORM_PICO           1       // Raspberry Pi Pico (RP2040)

// --- Hardware Pin Definitions (Raspberry Pi Pico GPIO) ---

// Stepper Motor Pins (DM542T Digital Driver)
// DM542T: PUL+/PUL-, DIR+/DIR-, ENA+/ENA-
// Connect PUL-, DIR-, ENA- to GND; PUL+, DIR+, ENA+ to Pico GPIO via 270-1k resistor
#define STEPPER_STEP_PIN        2       // GP2 -> DM542T PUL+
#define STEPPER_DIR_PIN         3       // GP3 -> DM542T DIR+
#define STEPPER_ENABLE_PIN      4       // GP4 -> DM542T ENA+ (LOW=enabled)

// NAU7802 24-bit ADC (I2C Interface)
#define NAU7802_I2C_PORT        i2c0    // I2C port
#define NAU7802_SDA_PIN         8       // GP8 -> NAU7802 SDA
#define NAU7802_SCL_PIN         9       // GP9 -> NAU7802 SCL
#define NAU7802_I2C_ADDR        0x2A    // NAU7802 I2C address (fixed)
#define NAU7802_I2C_FREQ        400000  // 400kHz I2C clock

// Limit Switch Pins (Active LOW with internal pull-up)
#define LIMIT_SWITCH_TOP_PIN    10      // GP10 -> Top limit switch
#define LIMIT_SWITCH_BOTTOM_PIN 11      // GP11 -> Bottom limit switch

// Emergency Stop Pin (Active LOW with internal pull-up)
#define EMERGENCY_STOP_PIN      12      // GP12 -> E-Stop button (NC contact)

// LED Indicator Pins
#define LED_STATUS_PIN          25      // GP25 -> Onboard LED (Pico)
#define LED_ERROR_PIN           15      // GP15 -> External error LED

// --- DM542T Stepper Driver Configuration ---
// DIP Switch Settings for microstepping (set on driver):
// SW5 SW6 SW7 SW8 = Microstep resolution
// OFF OFF OFF OFF = 400  (1/2 step)
// ON  OFF OFF OFF = 800  (1/4 step)
// OFF ON  OFF OFF = 1600 (1/8 step)
// ON  ON  OFF OFF = 3200 (1/16 step) <- Recommended
// OFF OFF ON  OFF = 6400 (1/32 step)

#define STEPPER_STEPS_PER_REV   200     // Motor steps per revolution (1.8° motor)
#define STEPPER_MICROSTEPPING   16      // Microstepping factor (set on DM542T)
#define STEPPER_MAX_SPEED       4000    // Maximum speed (steps/sec)
#define STEPPER_ACCELERATION    2000    // Acceleration (steps/sec²)
#define STEPPER_MM_PER_REV      8.0f    // Lead screw pitch (mm per revolution)

// DM542T Timing Requirements
#define STEP_PULSE_WIDTH_US     3       // Minimum pulse width (2.5µs min for DM542T)
#define STEP_PULSE_INTERVAL_US  3       // Minimum pulse interval
#define DIR_SETUP_TIME_US       5       // Direction setup time (5µs min for DM542T)

// --- NAU7802 Load Cell Configuration ---
// FBFTGMRMTA S-type Load Cell: 500N capacity
#define LOADCELL_CAPACITY       500.0f  // Maximum rated capacity (N)
#define LOADCELL_SENSITIVITY    2.0f    // Sensitivity (mV/V) - check datasheet
#define LOADCELL_EXCITATION     3.3f    // Excitation voltage (V)

// Calibration (adjust after calibration procedure)
#define LOADCELL_CALIBRATION    420000.0f // Raw counts per Newton (calibrate!)
#define LOADCELL_OFFSET         0       // Zero offset (set during tare)
#define LOADCELL_SAMPLES        10      // Number of samples for averaging
#define LOADCELL_MAX_FORCE      500.0f  // Maximum force for this load cell (N)

// NAU7802 Settings
#define NAU7802_GAIN            128     // PGA gain (1, 2, 4, 8, 16, 32, 64, 128)
#define NAU7802_SPS             80      // Samples per second (10, 20, 40, 80, 320)
#define NAU7802_LDO_VOLTAGE     3.0f    // Internal LDO voltage (2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.2, 4.5)

// --- Test Parameters ---
#define DEFAULT_SPEED_MM_S      1.0f    // Default test speed (mm/s)
#define DEFAULT_MAX_EXTENSION   100.0f  // Default max extension (mm)
#define DEFAULT_MAX_FORCE       450.0f  // Default max force (N) - below capacity
#define SAMPLE_RATE_MS          50      // Data sampling rate (ms) - 20Hz

// --- Serial Communication (USB CDC to Raspberry Pi 4) ---
#define SERIAL_BAUD_RATE        115200  // USB Serial baud rate
#define COMMAND_BUFFER_SIZE     128     // Command buffer size

// --- Safety Limits ---
#define FORCE_OVERLOAD_LIMIT    480.0f  // Force overload protection (N)
#define FORCE_OVERLOAD_PERCENT  0.96f   // 96% of load cell capacity
#define EXTENSION_MAX_LIMIT     150.0f  // Maximum extension limit (mm)
#define EXTENSION_MIN_LIMIT     0.0f    // Minimum extension limit (mm)

// --- Timing ---
#define DEBOUNCE_DELAY_MS       50      // Button debounce delay
#define EMERGENCY_CHECK_MS      10      // Emergency stop check interval
#define STATUS_UPDATE_MS        200     // Status update interval (faster for GUI)
#define WATCHDOG_TIMEOUT_MS     8000    // Watchdog timeout

// --- Display Info (Waveshare 7" - handled by Pi 4) ---
#define DISPLAY_WIDTH           1024
#define DISPLAY_HEIGHT          600

#endif // CONFIG_H
