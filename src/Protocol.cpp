#include "Protocol.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

// Device identification
static const char* DEVICE_NAME = "TensileTester";
static const char* DEVICE_VERSION = "2.0.0";
static const char* DEVICE_MANUFACTURER = "DIY-Pico";

Protocol::Protocol()
    : _bufferIndex(0)
    , _parameter(0.0f)
    , _hasParameter(false)
    , _dataStreaming(false)
{
    memset(_buffer, 0, COMMAND_BUFFER_SIZE);
}

void Protocol::begin(uint32_t baudRate) {
    // USB CDC is initialized by stdio_init_all() in main
    (void)baudRate;  // Baud rate not relevant for USB CDC
    clearBuffer();
}

Command Protocol::processInput() {
    int c;
    while ((c = getchar_timeout_us(0)) != PICO_ERROR_TIMEOUT) {
        // Handle line endings
        if (c == '\n' || c == '\r') {
            if (_bufferIndex > 0) {
                _buffer[_bufferIndex] = '\0';
                
                // Parse command
                char* space = strchr(_buffer, ' ');
                if (space) {
                    *space = '\0';
                    parseParameter(space + 1);
                } else {
                    _hasParameter = false;
                }
                
                Command cmd = parseCommand(_buffer);
                clearBuffer();
                return cmd;
            }
        }
        // Add character to buffer
        else if (_bufferIndex < COMMAND_BUFFER_SIZE - 1) {
            _buffer[_bufferIndex++] = (char)c;
        }
    }
    
    return Command::NONE;
}

float Protocol::getParameter() const {
    return _parameter;
}

int32_t Protocol::getIntParameter() const {
    return (int32_t)_parameter;
}

bool Protocol::hasParameter() const {
    return _hasParameter;
}

void Protocol::sendOK(const char* message) {
    printf("OK");
    if (message && strlen(message) > 0) {
        printf(" %s", message);
    }
    printf("\n");
}

void Protocol::sendError(ResponseStatus status, const char* message) {
    printf("ERROR %d ", (int)status);
    
    // Print error description
    switch (status) {
        case ResponseStatus::ERROR_UNKNOWN_CMD:
            printf("Unknown command");
            break;
        case ResponseStatus::ERROR_INVALID_PARAM:
            printf("Invalid parameter");
            break;
        case ResponseStatus::ERROR_NOT_READY:
            printf("Not ready");
            break;
        case ResponseStatus::ERROR_BUSY:
            printf("Busy");
            break;
        case ResponseStatus::ERROR_OVERLOAD:
            printf("Force overload");
            break;
        case ResponseStatus::ERROR_LIMIT_REACHED:
            printf("Limit reached");
            break;
        case ResponseStatus::ERROR_NOT_HOMED:
            printf("Not homed");
            break;
        case ResponseStatus::ERROR_EMERGENCY:
            printf("Emergency stop");
            break;
        default:
            printf("Unknown error");
            break;
    }
    
    if (message && strlen(message) > 0) {
        printf(": %s", message);
    }
    printf("\n");
}

void Protocol::sendStatus(const char* state, float force, float position, bool isRunning) {
    printf("STATUS %s F:%.2f P:%.3f R:%d\n", state, force, position, isRunning ? 1 : 0);
}

void Protocol::sendForce(float force) {
    printf("FORCE %.3f\n", force);
}

void Protocol::sendPosition(float position) {
    printf("POS %.3f\n", position);
}

void Protocol::sendConfig(float speed, float maxForce, float maxExtension, uint32_t sampleRate) {
    printf("CONFIG SPD:%.2f MAXF:%.1f MAXE:%.1f SR:%lu\n", speed, maxForce, maxExtension, sampleRate);
}

void Protocol::sendData(const DataPacket& packet) {
    printf("DATA %lu,%.3f,%.4f,%.3f,%.6f\n", 
           packet.timestamp, packet.force, packet.extension, packet.stress, packet.strain);
}

void Protocol::sendIdentity() {
    printf("ID %s V%s %s\n", DEVICE_NAME, DEVICE_VERSION, DEVICE_MANUFACTURER);
}

void Protocol::setDataStreaming(bool enable) {
    _dataStreaming = enable;
}

bool Protocol::isDataStreaming() const {
    return _dataStreaming;
}

void Protocol::clearBuffer() {
    memset(_buffer, 0, COMMAND_BUFFER_SIZE);
    _bufferIndex = 0;
    _hasParameter = false;
}

Command Protocol::parseCommand(const char* cmd) {
    // Convert to uppercase for case-insensitive comparison
    char upper[32];
    size_t len = strlen(cmd);
    if (len >= sizeof(upper)) len = sizeof(upper) - 1;
    
    for (size_t i = 0; i < len; i++) {
        upper[i] = toupper(cmd[i]);
    }
    upper[len] = '\0';
    
    // Test Control
    if (strcmp(upper, "START") == 0) return Command::START_TEST;
    if (strcmp(upper, "STOP") == 0) return Command::STOP_TEST;
    if (strcmp(upper, "PAUSE") == 0) return Command::PAUSE_TEST;
    if (strcmp(upper, "RESUME") == 0) return Command::RESUME_TEST;
    if (strcmp(upper, "ESTOP") == 0) return Command::EMERGENCY_STOP;
    
    // Movement
    if (strcmp(upper, "UP") == 0) return Command::MOVE_UP;
    if (strcmp(upper, "DOWN") == 0) return Command::MOVE_DOWN;
    if (strcmp(upper, "GOTO") == 0) return Command::MOVE_TO;
    if (strcmp(upper, "HALT") == 0) return Command::STOP_MOVEMENT;
    if (strcmp(upper, "HOME") == 0) return Command::HOME;
    
    // Configuration
    if (strcmp(upper, "SPEED") == 0) return Command::SET_SPEED;
    if (strcmp(upper, "MAXFORCE") == 0) return Command::SET_MAX_FORCE;
    if (strcmp(upper, "MAXEXT") == 0) return Command::SET_MAX_EXTENSION;
    if (strcmp(upper, "SRATE") == 0) return Command::SET_SAMPLE_RATE;
    
    // Calibration
    if (strcmp(upper, "TARE") == 0) return Command::TARE;
    if (strcmp(upper, "CAL") == 0) return Command::CALIBRATE;
    if (strcmp(upper, "CALFACTOR") == 0) return Command::SET_CAL_FACTOR;
    
    // Query
    if (strcmp(upper, "STATUS") == 0) return Command::GET_STATUS;
    if (strcmp(upper, "FORCE") == 0) return Command::GET_FORCE;
    if (strcmp(upper, "POS") == 0) return Command::GET_POSITION;
    if (strcmp(upper, "CONFIG") == 0) return Command::GET_CONFIG;
    if (strcmp(upper, "DATA") == 0) return Command::GET_DATA;
    
    // System
    if (strcmp(upper, "RESET") == 0) return Command::RESET;
    if (strcmp(upper, "ID") == 0) return Command::IDENTIFY;
    if (strcmp(upper, "?") == 0) return Command::IDENTIFY;
    
    return Command::UNKNOWN;
}

void Protocol::parseParameter(const char* str) {
    if (str == nullptr || strlen(str) == 0) {
        _hasParameter = false;
        _parameter = 0.0f;
        return;
    }
    
    // Skip leading whitespace
    while (*str == ' ' || *str == '\t') str++;
    
    if (*str == '\0') {
        _hasParameter = false;
        _parameter = 0.0f;
        return;
    }
    
    _parameter = atof(str);
    _hasParameter = true;
}
