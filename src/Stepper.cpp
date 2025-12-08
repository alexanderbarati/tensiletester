#include "Stepper.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/timer.h"

Stepper::Stepper(uint8_t stepPin, uint8_t dirPin, uint8_t enablePin)
    : _stepPin(stepPin)
    , _dirPin(dirPin)
    , _enablePin(enablePin)
    , _topLimitPin(0)
    , _bottomLimitPin(0)
    , _currentPos(0)
    , _targetPos(0)
    , _speed(0.0f)
    , _maxSpeed(STEPPER_MAX_SPEED)
    , _acceleration(STEPPER_ACCELERATION)
    , _stepInterval(0)
    , _lastStepTime(0)
    , _enabled(false)
    , _homed(false)
    , _hasLimitSwitches(false)
    , _direction(Direction::UP)
{
    // Calculate steps per mm based on config
    float stepsPerRev = STEPPER_STEPS_PER_REV * STEPPER_MICROSTEPPING;
    _stepsPerMm = stepsPerRev / STEPPER_MM_PER_REV;
}

void Stepper::begin() {
    gpio_init(_stepPin);
    gpio_init(_dirPin);
    gpio_init(_enablePin);
    
    gpio_set_dir(_stepPin, GPIO_OUT);
    gpio_set_dir(_dirPin, GPIO_OUT);
    gpio_set_dir(_enablePin, GPIO_OUT);
    
    gpio_put(_stepPin, false);
    gpio_put(_dirPin, false);
    gpio_put(_enablePin, true);  // Disabled by default (active LOW for DM542T)
    
    _enabled = false;
    _currentPos = 0;
    _targetPos = 0;
}

void Stepper::enable() {
    gpio_put(_enablePin, false);  // DM542T: LOW = enabled
    _enabled = true;
    sleep_ms(10);  // Allow driver to wake up
}

void Stepper::disable() {
    gpio_put(_enablePin, true);   // DM542T: HIGH = disabled
    _enabled = false;
}

bool Stepper::isEnabled() const {
    return _enabled;
}

void Stepper::setMaxSpeed(float speed) {
    if (speed < 0.0f) speed = -speed;
    if (speed != _maxSpeed) {
        _maxSpeed = speed;
        if (_speed > _maxSpeed) {
            _speed = _maxSpeed;
        }
    }
}

void Stepper::setAcceleration(float acceleration) {
    if (acceleration < 0.0f) acceleration = -acceleration;
    _acceleration = acceleration;
}

void Stepper::setSpeedMmPerSec(float mmPerSec) {
    setMaxSpeed(mmPerSec * _stepsPerMm);
}

void Stepper::moveTo(int32_t position) {
    _targetPos = position;
}

void Stepper::moveToMm(float positionMm) {
    moveTo(mmToSteps(positionMm));
}

void Stepper::move(int32_t steps) {
    moveTo(_currentPos + steps);
}

void Stepper::moveMm(float distanceMm) {
    move(mmToSteps(distanceMm));
}

bool Stepper::run() {
    if (!_enabled) return false;
    
    int32_t distance = distanceToGo();
    if (distance == 0) return false;
    
    // Check limit switches
    if (_hasLimitSwitches) {
        if (distance > 0 && isAtTopLimit()) {
            _targetPos = _currentPos;
            return false;
        }
        if (distance < 0 && isAtBottomLimit()) {
            _targetPos = _currentPos;
            return false;
        }
    }
    
    computeNewSpeed();
    
    if (_stepInterval <= 0) return true;
    
    uint64_t now = time_us_64();
    if ((now - _lastStepTime) >= (uint64_t)_stepInterval) {
        step();
        _lastStepTime = now;
    }
    
    return true;
}

bool Stepper::runSpeed() {
    if (!_enabled) return false;
    if (_speed == 0.0f) return false;
    
    // Check limit switches
    if (_hasLimitSwitches) {
        if (_direction == Direction::UP && isAtTopLimit()) return false;
        if (_direction == Direction::DOWN && isAtBottomLimit()) return false;
    }
    
    uint64_t now = time_us_64();
    float absSpeed = _speed > 0 ? _speed : -_speed;
    uint64_t interval = (uint64_t)(1000000.0f / absSpeed);
    
    if ((now - _lastStepTime) >= interval) {
        step();
        _lastStepTime = now;
        return true;
    }
    
    return false;
}

void Stepper::stop() {
    _targetPos = _currentPos;
    _speed = 0;
}

void Stepper::stopSmooth() {
    // Set target so we decelerate to stop
    int32_t stepsToStop = (int32_t)((_speed * _speed) / (2.0f * _acceleration));
    if (_speed > 0) {
        _targetPos = _currentPos + stepsToStop;
    } else {
        _targetPos = _currentPos - stepsToStop;
    }
}

bool Stepper::isMoving() const {
    return _currentPos != _targetPos;
}

int32_t Stepper::getCurrentPosition() const {
    return _currentPos;
}

float Stepper::getCurrentPositionMm() const {
    return stepsToMm(_currentPos);
}

int32_t Stepper::getTargetPosition() const {
    return _targetPos;
}

int32_t Stepper::distanceToGo() const {
    return _targetPos - _currentPos;
}

void Stepper::setCurrentPosition(int32_t position) {
    _currentPos = position;
    _targetPos = position;
    _speed = 0;
}

void Stepper::resetPosition() {
    setCurrentPosition(0);
}

void Stepper::setDirection(Direction dir) {
    _direction = dir;
    gpio_put(_dirPin, (dir == Direction::UP) ? true : false);
    // DM542T requires 5µs direction setup time
    sleep_us(DIR_SETUP_TIME_US);
}

Direction Stepper::getDirection() const {
    return _direction;
}

float Stepper::stepsToMm(int32_t steps) const {
    return (float)steps / _stepsPerMm;
}

int32_t Stepper::mmToSteps(float mm) const {
    return (int32_t)(mm * _stepsPerMm);
}

void Stepper::setLimitSwitches(uint8_t topPin, uint8_t bottomPin) {
    _topLimitPin = topPin;
    _bottomLimitPin = bottomPin;
    
    gpio_init(_topLimitPin);
    gpio_init(_bottomLimitPin);
    gpio_set_dir(_topLimitPin, GPIO_IN);
    gpio_set_dir(_bottomLimitPin, GPIO_IN);
    gpio_pull_up(_topLimitPin);
    gpio_pull_up(_bottomLimitPin);
    
    _hasLimitSwitches = true;
}

bool Stepper::isAtTopLimit() const {
    if (!_hasLimitSwitches) return false;
    return gpio_get(_topLimitPin) == false;  // Active LOW
}

bool Stepper::isAtBottomLimit() const {
    if (!_hasLimitSwitches) return false;
    return gpio_get(_bottomLimitPin) == false;  // Active LOW
}

bool Stepper::home(Direction dir) {
    if (!_hasLimitSwitches) return false;
    if (!_enabled) enable();
    
    setDirection(dir);
    _speed = _maxSpeed * 0.5f;  // Home at half speed
    
    uint32_t timeout = 60000;  // 60 second timeout
    uint32_t startTime = to_ms_since_boot(get_absolute_time());
    
    // Move until limit switch hit
    while ((to_ms_since_boot(get_absolute_time()) - startTime) < timeout) {
        if (dir == Direction::DOWN && isAtBottomLimit()) break;
        if (dir == Direction::UP && isAtTopLimit()) break;
        
        runSpeed();
        tight_loop_contents();
    }
    
    if ((to_ms_since_boot(get_absolute_time()) - startTime) >= timeout) {
        return false;  // Timeout
    }
    
    // Back off slightly
    setDirection((dir == Direction::DOWN) ? Direction::UP : Direction::DOWN);
    _speed = _maxSpeed * 0.1f;  // Slow speed
    
    int32_t backoffSteps = mmToSteps(2.0f);  // 2mm backoff
    for (int32_t i = 0; i < backoffSteps; i++) {
        runSpeed();
        uint64_t interval = (uint64_t)(1000000.0f / _speed);
        sleep_us(interval);
    }
    
    // Set position
    resetPosition();
    _homed = true;
    
    return true;
}

bool Stepper::isHomed() const {
    return _homed;
}

void Stepper::step() {
    int32_t distance = distanceToGo();
    
    if (distance > 0) {
        setDirection(Direction::UP);
        _currentPos++;
    } else if (distance < 0) {
        setDirection(Direction::DOWN);
        _currentPos--;
    }
    
    // Generate step pulse - DM542T requires minimum 2.5µs pulse width
    gpio_put(_stepPin, true);
    sleep_us(STEP_PULSE_WIDTH_US);
    gpio_put(_stepPin, false);
}

void Stepper::computeNewSpeed() {
    int32_t distance = distanceToGo();
    
    if (distance == 0) {
        _speed = 0;
        _stepInterval = 0;
        return;
    }
    
    // Calculate required speed based on distance and acceleration
    float targetSpeed = (distance > 0) ? _maxSpeed : -_maxSpeed;
    
    // Calculate deceleration distance
    float stepsToStop = (_speed * _speed) / (2.0f * _acceleration);
    
    int32_t absDistance = distance > 0 ? distance : -distance;
    
    // Need to decelerate?
    if ((float)absDistance <= stepsToStop) {
        // Decelerate
        if (_speed > 0) {
            _speed -= _acceleration * (_stepInterval / 1000000.0f);
            if (_speed < 100) _speed = 100;  // Minimum speed
        } else {
            _speed += _acceleration * (_stepInterval / 1000000.0f);
            if (_speed > -100) _speed = -100;
        }
    } else {
        // Accelerate towards max speed
        if (_speed < targetSpeed) {
            _speed += _acceleration * (_stepInterval / 1000000.0f);
            if (_speed > targetSpeed) _speed = targetSpeed;
        } else if (_speed > targetSpeed) {
            _speed -= _acceleration * (_stepInterval / 1000000.0f);
            if (_speed < targetSpeed) _speed = targetSpeed;
        }
    }
    
    // Calculate step interval in microseconds
    float absSpeed = _speed > 0 ? _speed : -_speed;
    if (absSpeed > 0) {
        _stepInterval = 1000000.0f / absSpeed;
    } else {
        _stepInterval = 0;
    }
}
