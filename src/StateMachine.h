#ifndef STATEMACHINE_H
#define STATEMACHINE_H

#include <stdint.h>
#include "Config.h"
#include "LoadCell.h"
#include "Stepper.h"
#include "Protocol.h"

/**
 * @brief Machine states enumeration
 */
enum class State : uint8_t {
    IDLE,           // Machine idle, ready for commands
    HOMING,         // Homing sequence in progress
    READY,          // Homed and ready for test
    RUNNING,        // Test in progress
    PAUSED,         // Test paused
    STOPPED,        // Test stopped (can review data)
    ERROR,          // Error state
    EMERGENCY       // Emergency stop activated
};

/**
 * @brief Test result structure
 */
struct TestResult {
    float maxForce;         // Maximum force recorded (N)
    float maxExtension;     // Extension at max force (mm)
    float breakForce;       // Force at break (N)
    float breakExtension;   // Extension at break (mm)
    uint32_t duration;      // Test duration (ms)
    uint32_t dataPoints;    // Number of data points recorded
    bool completed;         // Test completed normally
    bool specimenBroke;     // Specimen failure detected
};

/**
 * @brief Test parameters structure
 */
struct TestParameters {
    float speed;            // Test speed (mm/s)
    float maxForce;         // Maximum force limit (N)
    float maxExtension;     // Maximum extension limit (mm)
    uint32_t sampleRate;    // Sample rate (ms)
    bool stopOnBreak;       // Stop test if specimen breaks
    float breakThreshold;   // Force drop % to detect break
};

/**
 * @brief State machine for tensile tester control
 * 
 * Manages machine states, test execution, safety monitoring,
 * and coordinates all subsystems.
 */
class StateMachine {
public:
    /**
     * @brief Construct a new StateMachine object
     * @param loadCell Reference to LoadCell instance
     * @param stepper Reference to Stepper instance
     * @param protocol Reference to Protocol instance
     */
    StateMachine(LoadCell& loadCell, Stepper& stepper, Protocol& protocol);

    /**
     * @brief Initialize the state machine
     */
    void begin();

    /**
     * @brief Update state machine - call frequently in main loop
     */
    void update();

    /**
     * @brief Process a command from protocol
     * @param cmd Command to process
     */
    void handleCommand(Command cmd);

    /**
     * @brief Get current state
     * @return Current state
     */
    State getState() const;

    /**
     * @brief Get state name as string
     * @return State name string
     */
    const char* getStateName() const;

    /**
     * @brief Get current force reading
     * @return Force in Newtons
     */
    float getCurrentForce() const;

    /**
     * @brief Get current position/extension
     * @return Position in mm
     */
    float getCurrentPosition() const;

    /**
     * @brief Get test parameters
     * @return Current test parameters
     */
    const TestParameters& getTestParameters() const;

    /**
     * @brief Get test result
     * @return Test result structure
     */
    const TestResult& getTestResult() const;

    /**
     * @brief Set test speed
     * @param speed Speed in mm/s
     */
    void setTestSpeed(float speed);

    /**
     * @brief Set maximum force limit
     * @param force Force in Newtons
     */
    void setMaxForce(float force);

    /**
     * @brief Set maximum extension limit
     * @param extension Extension in mm
     */
    void setMaxExtension(float extension);

    /**
     * @brief Set sample rate
     * @param rateMs Sample rate in milliseconds
     */
    void setSampleRate(uint32_t rateMs);

    /**
     * @brief Start tensile test
     * @return true if test started successfully
     */
    bool startTest();

    /**
     * @brief Stop current test
     */
    void stopTest();

    /**
     * @brief Pause current test
     */
    void pauseTest();

    /**
     * @brief Resume paused test
     */
    void resumeTest();

    /**
     * @brief Trigger emergency stop
     */
    void emergencyStop();

    /**
     * @brief Clear emergency stop and reset
     */
    void clearEmergency();

    /**
     * @brief Start homing sequence
     * @return true if homing started
     */
    bool startHoming();

    /**
     * @brief Tare the load cell
     */
    void tare();

    /**
     * @brief Manual jog movement
     * @param dir Direction to move
     * @param distance Distance in mm (0 for continuous)
     */
    void jog(Direction dir, float distance = 0);

    /**
     * @brief Stop manual jog movement
     */
    void stopJog();

    /**
     * @brief Check if machine is in safe state for operations
     * @return true if safe
     */
    bool isSafe() const;

    /**
     * @brief Check if test is active (running or paused)
     * @return true if test active
     */
    bool isTestActive() const;

private:
    LoadCell& _loadCell;
    Stepper& _stepper;
    Protocol& _protocol;
    
    State _state;
    State _previousState;
    
    TestParameters _params;
    TestResult _result;
    
    // Timing
    uint32_t _lastSampleTime;
    uint32_t _testStartTime;
    uint32_t _lastStatusTime;
    uint32_t _stateEntryTime;
    
    // Test data tracking
    float _peakForce;
    float _extensionAtPeak;
    float _startPosition;
    bool _jogActive;
    Direction _jogDirection;
    
    // Safety
    bool _emergencyStopActive;
    uint8_t _emergencyStopPin;

    /**
     * @brief Transition to new state
     * @param newState State to transition to
     */
    void setState(State newState);

    /**
     * @brief Update IDLE state
     */
    void updateIdle();

    /**
     * @brief Update HOMING state
     */
    void updateHoming();

    /**
     * @brief Update READY state
     */
    void updateReady();

    /**
     * @brief Update RUNNING state
     */
    void updateRunning();

    /**
     * @brief Update PAUSED state
     */
    void updatePaused();

    /**
     * @brief Update STOPPED state
     */
    void updateStopped();

    /**
     * @brief Update ERROR state
     */
    void updateError();

    /**
     * @brief Update EMERGENCY state
     */
    void updateEmergency();

    /**
     * @brief Check safety conditions
     * @return true if all safe
     */
    bool checkSafety();

    /**
     * @brief Check for emergency stop button
     * @return true if emergency stop pressed
     */
    bool checkEmergencyStop();

    /**
     * @brief Check for specimen break
     * @return true if break detected
     */
    bool detectBreak();

    /**
     * @brief Record data point during test
     */
    void recordDataPoint();

    /**
     * @brief Reset test result structure
     */
    void resetTestResult();

    /**
     * @brief Finalize test results
     */
    void finalizeTest();
};

#endif // STATEMACHINE_H
