#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include "Config.h"

/**
 * @brief Command types for serial protocol
 */
enum class Command : uint8_t {
    NONE = 0,
    
    // Test Control Commands
    START_TEST,         // Start tensile test
    STOP_TEST,          // Stop current test
    PAUSE_TEST,         // Pause current test
    RESUME_TEST,        // Resume paused test
    EMERGENCY_STOP,     // Emergency stop
    
    // Movement Commands
    MOVE_UP,            // Move crosshead up
    MOVE_DOWN,          // Move crosshead down
    MOVE_TO,            // Move to position
    STOP_MOVEMENT,      // Stop movement
    HOME,               // Home the machine
    
    // Configuration Commands
    SET_SPEED,          // Set test speed (mm/s)
    SET_MAX_FORCE,      // Set maximum force limit
    SET_MAX_EXTENSION,  // Set maximum extension limit
    SET_SAMPLE_RATE,    // Set data sample rate
    
    // Calibration Commands
    TARE,               // Tare the load cell
    CALIBRATE,          // Start calibration mode
    SET_CAL_FACTOR,     // Set calibration factor
    
    // Query Commands
    GET_STATUS,         // Get current status
    GET_FORCE,          // Get current force reading
    GET_POSITION,       // Get current position
    GET_CONFIG,         // Get current configuration
    GET_DATA,           // Get test data point
    
    // System Commands
    RESET,              // Reset system
    IDENTIFY,           // Get device identification
    
    UNKNOWN = 0xFF
};

/**
 * @brief Response status codes
 */
enum class ResponseStatus : uint8_t {
    OK = 0,
    ERROR_UNKNOWN_CMD,
    ERROR_INVALID_PARAM,
    ERROR_NOT_READY,
    ERROR_BUSY,
    ERROR_OVERLOAD,
    ERROR_LIMIT_REACHED,
    ERROR_NOT_HOMED,
    ERROR_EMERGENCY
};

/**
 * @brief Data packet structure for test data
 */
struct DataPacket {
    uint32_t timestamp;     // Time in milliseconds
    float force;            // Force in Newtons
    float extension;        // Extension in mm
    float stress;           // Calculated stress (if applicable)
    float strain;           // Calculated strain (if applicable)
};

/**
 * @brief Serial protocol handler for PC communication
 * 
 * Handles command parsing, response formatting, and data streaming
 * over serial connection.
 */
class Protocol {
public:
    /**
     * @brief Construct a new Protocol object
     */
    Protocol();

    /**
     * @brief Initialize serial communication
     * @param baudRate Baud rate for serial
     */
    void begin(uint32_t baudRate = SERIAL_BAUD_RATE);

    /**
     * @brief Process incoming serial data
     * @return Parsed command (NONE if no complete command)
     */
    Command processInput();

    /**
     * @brief Get parameter value from last command
     * @return Parameter value as float
     */
    float getParameter() const;

    /**
     * @brief Get integer parameter from last command
     * @return Parameter value as integer
     */
    int32_t getIntParameter() const;

    /**
     * @brief Check if a parameter was provided
     * @return true if parameter exists
     */
    bool hasParameter() const;

    /**
     * @brief Send OK response
     * @param message Optional message
     */
    void sendOK(const char* message = nullptr);

    /**
     * @brief Send error response
     * @param status Error status code
     * @param message Optional error message
     */
    void sendError(ResponseStatus status, const char* message = nullptr);

    /**
     * @brief Send status response
     * @param state Current state name
     * @param force Current force
     * @param position Current position
     * @param isRunning Is test running
     */
    void sendStatus(const char* state, float force, float position, bool isRunning);

    /**
     * @brief Send force reading
     * @param force Force in Newtons
     */
    void sendForce(float force);

    /**
     * @brief Send position reading
     * @param position Position in mm
     */
    void sendPosition(float position);

    /**
     * @brief Send configuration values
     * @param speed Test speed
     * @param maxForce Maximum force limit
     * @param maxExtension Maximum extension limit
     * @param sampleRate Sample rate in ms
     */
    void sendConfig(float speed, float maxForce, float maxExtension, uint32_t sampleRate);

    /**
     * @brief Send test data point
     * @param packet Data packet to send
     */
    void sendData(const DataPacket& packet);

    /**
     * @brief Send device identification
     */
    void sendIdentity();

    /**
     * @brief Enable/disable data streaming
     * @param enable Enable streaming
     */
    void setDataStreaming(bool enable);

    /**
     * @brief Check if data streaming is enabled
     * @return true if streaming
     */
    bool isDataStreaming() const;

    /**
     * @brief Clear input buffer
     */
    void clearBuffer();

private:
    char _buffer[COMMAND_BUFFER_SIZE];
    uint8_t _bufferIndex;
    float _parameter;
    bool _hasParameter;
    bool _dataStreaming;

    /**
     * @brief Parse command string to Command enum
     * @param cmd Command string
     * @return Parsed command
     */
    Command parseCommand(const char* cmd);

    /**
     * @brief Parse parameter from command string
     * @param str String containing parameter
     */
    void parseParameter(const char* str);
};

#endif // PROTOCOL_H
