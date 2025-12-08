#ifndef STEPPER_H
#define STEPPER_H

#include <stdint.h>
#include "Config.h"

/**
 * @brief Movement direction enumeration
 */
enum class Direction : uint8_t {
    UP = 0,     // Tension direction (upward movement)
    DOWN = 1    // Release direction (downward movement)
};

/**
 * @brief Stepper motor controller class
 * 
 * Controls stepper motor via step/direction driver (e.g., A4988, DRV8825)
 * with acceleration, position tracking, and limit switch handling.
 */
class Stepper {
public:
    /**
     * @brief Construct a new Stepper object
     * @param stepPin Step pulse pin
     * @param dirPin Direction pin
     * @param enablePin Enable pin (active LOW)
     */
    Stepper(uint8_t stepPin, uint8_t dirPin, uint8_t enablePin);

    /**
     * @brief Initialize the stepper motor
     */
    void begin();

    /**
     * @brief Enable the stepper motor driver
     */
    void enable();

    /**
     * @brief Disable the stepper motor driver
     */
    void disable();

    /**
     * @brief Check if motor is enabled
     * @return true if enabled
     */
    bool isEnabled() const;

    /**
     * @brief Set maximum speed
     * @param speed Speed in steps per second
     */
    void setMaxSpeed(float speed);

    /**
     * @brief Set acceleration
     * @param acceleration Acceleration in steps per second squared
     */
    void setAcceleration(float acceleration);

    /**
     * @brief Set speed in mm/s
     * @param mmPerSec Speed in millimeters per second
     */
    void setSpeedMmPerSec(float mmPerSec);

    /**
     * @brief Move to absolute position (steps)
     * @param position Target position in steps
     */
    void moveTo(int32_t position);

    /**
     * @brief Move to absolute position (mm)
     * @param positionMm Target position in millimeters
     */
    void moveToMm(float positionMm);

    /**
     * @brief Move relative distance (steps)
     * @param steps Number of steps to move
     */
    void move(int32_t steps);

    /**
     * @brief Move relative distance (mm)
     * @param distanceMm Distance in millimeters
     */
    void moveMm(float distanceMm);

    /**
     * @brief Run the motor - call frequently for motion
     * @return true if motor is still moving
     */
    bool run();

    /**
     * @brief Run at constant speed (no acceleration)
     * @return true if step was taken
     */
    bool runSpeed();

    /**
     * @brief Stop motor immediately
     */
    void stop();

    /**
     * @brief Stop motor with deceleration
     */
    void stopSmooth();

    /**
     * @brief Check if motor is currently moving
     * @return true if moving
     */
    bool isMoving() const;

    /**
     * @brief Get current position in steps
     * @return Current position
     */
    int32_t getCurrentPosition() const;

    /**
     * @brief Get current position in millimeters
     * @return Current position in mm
     */
    float getCurrentPositionMm() const;

    /**
     * @brief Get target position in steps
     * @return Target position
     */
    int32_t getTargetPosition() const;

    /**
     * @brief Get distance to target
     * @return Distance remaining in steps
     */
    int32_t distanceToGo() const;

    /**
     * @brief Set current position (without moving)
     * @param position New current position
     */
    void setCurrentPosition(int32_t position);

    /**
     * @brief Reset position to zero
     */
    void resetPosition();

    /**
     * @brief Set movement direction for continuous movement
     * @param dir Movement direction
     */
    void setDirection(Direction dir);

    /**
     * @brief Get current movement direction
     * @return Current direction
     */
    Direction getDirection() const;

    /**
     * @brief Convert steps to millimeters
     * @param steps Steps to convert
     * @return Distance in millimeters
     */
    float stepsToMm(int32_t steps) const;

    /**
     * @brief Convert millimeters to steps
     * @param mm Distance to convert
     * @return Number of steps
     */
    int32_t mmToSteps(float mm) const;

    /**
     * @brief Configure limit switch pins
     * @param topPin Top limit switch pin
     * @param bottomPin Bottom limit switch pin
     */
    void setLimitSwitches(uint8_t topPin, uint8_t bottomPin);

    /**
     * @brief Check if top limit switch is triggered
     * @return true if triggered
     */
    bool isAtTopLimit() const;

    /**
     * @brief Check if bottom limit switch is triggered
     * @return true if triggered
     */
    bool isAtBottomLimit() const;

    /**
     * @brief Home the motor (move to limit switch)
     * @param dir Direction to home
     * @return true if homing successful
     */
    bool home(Direction dir = Direction::DOWN);

    /**
     * @brief Check if motor has been homed
     * @return true if homed
     */
    bool isHomed() const;

private:
    uint8_t _stepPin;
    uint8_t _dirPin;
    uint8_t _enablePin;
    uint8_t _topLimitPin;
    uint8_t _bottomLimitPin;
    
    int32_t _currentPos;
    int32_t _targetPos;
    float _speed;
    float _maxSpeed;
    float _acceleration;
    float _stepInterval;
    uint32_t _lastStepTime;
    
    bool _enabled;
    bool _homed;
    bool _hasLimitSwitches;
    Direction _direction;

    float _stepsPerMm;  // Calculated from config

    /**
     * @brief Perform a single step
     */
    void step();

    /**
     * @brief Compute new speed with acceleration
     */
    void computeNewSpeed();
};

#endif // STEPPER_H
