#include "StateMachine.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include <cmath>

StateMachine::StateMachine(LoadCell& loadCell, Stepper& stepper, Protocol& protocol)
    : _loadCell(loadCell)
    , _stepper(stepper)
    , _protocol(protocol)
    , _state(State::IDLE)
    , _previousState(State::IDLE)
    , _lastSampleTime(0)
    , _testStartTime(0)
    , _lastStatusTime(0)
    , _stateEntryTime(0)
    , _peakForce(0)
    , _extensionAtPeak(0)
    , _startPosition(0)
    , _jogActive(false)
    , _jogDirection(Direction::UP)
    , _emergencyStopActive(false)
    , _emergencyStopPin(EMERGENCY_STOP_PIN)
{
    // Initialize default test parameters
    _params.speed = DEFAULT_SPEED_MM_S;
    _params.maxForce = DEFAULT_MAX_FORCE;
    _params.maxExtension = DEFAULT_MAX_EXTENSION;
    _params.sampleRate = SAMPLE_RATE_MS;
    _params.stopOnBreak = true;
    _params.breakThreshold = 0.5f;  // 50% drop
    
    resetTestResult();
}

void StateMachine::begin() {
    // Setup emergency stop pin
    gpio_init(_emergencyStopPin);
    gpio_set_dir(_emergencyStopPin, GPIO_IN);
    gpio_pull_up(_emergencyStopPin);
    
    // Setup indicator LEDs
    gpio_init(LED_STATUS_PIN);
    gpio_init(LED_ERROR_PIN);
    gpio_set_dir(LED_STATUS_PIN, GPIO_OUT);
    gpio_set_dir(LED_ERROR_PIN, GPIO_OUT);
    
    gpio_put(LED_STATUS_PIN, false);
    gpio_put(LED_ERROR_PIN, false);
    
    setState(State::IDLE);
}

void StateMachine::update() {
    // Always check emergency stop first
    if (checkEmergencyStop() && _state != State::EMERGENCY) {
        emergencyStop();
        return;
    }
    
    // Read current sensor values
    _loadCell.readForce();
    
    // Run stepper if needed
    if (_stepper.isEnabled()) {
        _stepper.run();
    }
    
    // Update based on current state
    switch (_state) {
        case State::IDLE:
            updateIdle();
            break;
        case State::HOMING:
            updateHoming();
            break;
        case State::READY:
            updateReady();
            break;
        case State::RUNNING:
            updateRunning();
            break;
        case State::PAUSED:
            updatePaused();
            break;
        case State::STOPPED:
            updateStopped();
            break;
        case State::ERROR:
            updateError();
            break;
        case State::EMERGENCY:
            updateEmergency();
            break;
    }
    
    // Periodic status update
    uint32_t now = to_ms_since_boot(get_absolute_time());
    if ((now - _lastStatusTime) >= STATUS_UPDATE_MS) {
        _lastStatusTime = now;
        // Status LED blink based on state
        static bool ledState = false;
        ledState = !ledState;
        
        switch (_state) {
            case State::IDLE:
            case State::STOPPED:
                gpio_put(LED_STATUS_PIN, false);
                break;
            case State::READY:
                gpio_put(LED_STATUS_PIN, true);
                break;
            case State::RUNNING:
                gpio_put(LED_STATUS_PIN, ledState);
                break;
            case State::PAUSED:
                gpio_put(LED_STATUS_PIN, ledState && (now % 1000 < 500));
                break;
            case State::ERROR:
            case State::EMERGENCY:
                gpio_put(LED_ERROR_PIN, ledState);
                break;
            default:
                break;
        }
    }
}

void StateMachine::handleCommand(Command cmd) {
    float param = _protocol.getParameter();
    
    switch (cmd) {
        case Command::START_TEST:
            if (startTest()) {
                _protocol.sendOK("Test started");
            } else {
                _protocol.sendError(ResponseStatus::ERROR_NOT_READY);
            }
            break;
            
        case Command::STOP_TEST:
            stopTest();
            _protocol.sendOK("Test stopped");
            break;
            
        case Command::PAUSE_TEST:
            pauseTest();
            _protocol.sendOK("Test paused");
            break;
            
        case Command::RESUME_TEST:
            resumeTest();
            _protocol.sendOK("Test resumed");
            break;
            
        case Command::EMERGENCY_STOP:
            emergencyStop();
            _protocol.sendOK("Emergency stop");
            break;
            
        case Command::MOVE_UP:
            jog(Direction::UP, _protocol.hasParameter() ? param : 0);
            _protocol.sendOK();
            break;
            
        case Command::MOVE_DOWN:
            jog(Direction::DOWN, _protocol.hasParameter() ? param : 0);
            _protocol.sendOK();
            break;
            
        case Command::MOVE_TO:
            if (_protocol.hasParameter()) {
                _stepper.moveToMm(param);
                _protocol.sendOK();
            } else {
                _protocol.sendError(ResponseStatus::ERROR_INVALID_PARAM);
            }
            break;
            
        case Command::STOP_MOVEMENT:
            stopJog();
            _protocol.sendOK();
            break;
            
        case Command::HOME:
            if (startHoming()) {
                _protocol.sendOK("Homing started");
            } else {
                _protocol.sendError(ResponseStatus::ERROR_BUSY);
            }
            break;
            
        case Command::SET_SPEED:
            if (_protocol.hasParameter()) {
                setTestSpeed(param);
                _protocol.sendOK();
            } else {
                _protocol.sendError(ResponseStatus::ERROR_INVALID_PARAM);
            }
            break;
            
        case Command::SET_MAX_FORCE:
            if (_protocol.hasParameter()) {
                setMaxForce(param);
                _protocol.sendOK();
            } else {
                _protocol.sendError(ResponseStatus::ERROR_INVALID_PARAM);
            }
            break;
            
        case Command::SET_MAX_EXTENSION:
            if (_protocol.hasParameter()) {
                setMaxExtension(param);
                _protocol.sendOK();
            } else {
                _protocol.sendError(ResponseStatus::ERROR_INVALID_PARAM);
            }
            break;
            
        case Command::SET_SAMPLE_RATE:
            if (_protocol.hasParameter()) {
                setSampleRate((uint32_t)param);
                _protocol.sendOK();
            } else {
                _protocol.sendError(ResponseStatus::ERROR_INVALID_PARAM);
            }
            break;
            
        case Command::TARE:
            tare();
            _protocol.sendOK("Tared");
            break;
            
        case Command::CALIBRATE:
            // TODO: Implement calibration mode
            _protocol.sendError(ResponseStatus::ERROR_NOT_READY, "Not implemented");
            break;
            
        case Command::SET_CAL_FACTOR:
            if (_protocol.hasParameter()) {
                _loadCell.setCalibrationFactor(param);
                _protocol.sendOK();
            } else {
                _protocol.sendError(ResponseStatus::ERROR_INVALID_PARAM);
            }
            break;
            
        case Command::GET_STATUS:
            _protocol.sendStatus(
                getStateName(),
                getCurrentForce(),
                getCurrentPosition(),
                isTestActive()
            );
            break;
            
        case Command::GET_FORCE:
            _protocol.sendForce(getCurrentForce());
            break;
            
        case Command::GET_POSITION:
            _protocol.sendPosition(getCurrentPosition());
            break;
            
        case Command::GET_CONFIG:
            _protocol.sendConfig(
                _params.speed,
                _params.maxForce,
                _params.maxExtension,
                _params.sampleRate
            );
            break;
            
        case Command::RESET:
            clearEmergency();
            setState(State::IDLE);
            _protocol.sendOK("Reset");
            break;
            
        case Command::IDENTIFY:
            _protocol.sendIdentity();
            break;
            
        case Command::UNKNOWN:
        default:
            _protocol.sendError(ResponseStatus::ERROR_UNKNOWN_CMD);
            break;
    }
}

State StateMachine::getState() const {
    return _state;
}

const char* StateMachine::getStateName() const {
    switch (_state) {
        case State::IDLE:      return "IDLE";
        case State::HOMING:    return "HOMING";
        case State::READY:     return "READY";
        case State::RUNNING:   return "RUNNING";
        case State::PAUSED:    return "PAUSED";
        case State::STOPPED:   return "STOPPED";
        case State::ERROR:     return "ERROR";
        case State::EMERGENCY: return "EMERGENCY";
        default:               return "UNKNOWN";
    }
}

float StateMachine::getCurrentForce() const {
    return _loadCell.getLastForce();
}

float StateMachine::getCurrentPosition() const {
    return _stepper.getCurrentPositionMm();
}

const TestParameters& StateMachine::getTestParameters() const {
    return _params;
}

const TestResult& StateMachine::getTestResult() const {
    return _result;
}

void StateMachine::setTestSpeed(float speed) {
    if (speed > 0 && speed <= 100.0f) {
        _params.speed = speed;
        _stepper.setSpeedMmPerSec(speed);
    }
}

void StateMachine::setMaxForce(float force) {
    if (force > 0 && force <= LOADCELL_MAX_FORCE) {
        _params.maxForce = force;
    }
}

void StateMachine::setMaxExtension(float extension) {
    if (extension > 0 && extension <= EXTENSION_MAX_LIMIT) {
        _params.maxExtension = extension;
    }
}

void StateMachine::setSampleRate(uint32_t rateMs) {
    if (rateMs >= 10 && rateMs <= 10000) {
        _params.sampleRate = rateMs;
    }
}

bool StateMachine::startTest() {
    if (_state != State::READY) {
        return false;
    }
    
    // Initialize test
    resetTestResult();
    _testStartTime = to_ms_since_boot(get_absolute_time());
    _startPosition = getCurrentPosition();
    _peakForce = 0;
    _extensionAtPeak = 0;
    
    // Configure stepper for test
    _stepper.setSpeedMmPerSec(_params.speed);
    _stepper.enable();
    
    // Start movement (tensile = upward)
    _stepper.moveToMm(_params.maxExtension);
    
    // Enable data streaming
    _protocol.setDataStreaming(true);
    
    setState(State::RUNNING);
    return true;
}

void StateMachine::stopTest() {
    if (_state == State::RUNNING || _state == State::PAUSED) {
        _stepper.stop();
        finalizeTest();
        _protocol.setDataStreaming(false);
        setState(State::STOPPED);
    }
}

void StateMachine::pauseTest() {
    if (_state == State::RUNNING) {
        _stepper.stopSmooth();
        setState(State::PAUSED);
    }
}

void StateMachine::resumeTest() {
    if (_state == State::PAUSED) {
        _stepper.moveToMm(_params.maxExtension);
        setState(State::RUNNING);
    }
}

void StateMachine::emergencyStop() {
    _emergencyStopActive = true;
    _stepper.stop();
    _stepper.disable();
    
    gpio_put(LED_ERROR_PIN, true);
    gpio_put(LED_STATUS_PIN, false);
    
    if (_state == State::RUNNING) {
        finalizeTest();
        _protocol.setDataStreaming(false);
    }
    
    setState(State::EMERGENCY);
}

void StateMachine::clearEmergency() {
    if (_state == State::EMERGENCY && !checkEmergencyStop()) {
        _emergencyStopActive = false;
        gpio_put(LED_ERROR_PIN, false);
        setState(State::IDLE);
    }
}

bool StateMachine::startHoming() {
    if (_state != State::IDLE && _state != State::READY && _state != State::STOPPED) {
        return false;
    }
    
    _stepper.enable();
    setState(State::HOMING);
    return true;
}

void StateMachine::tare() {
    _loadCell.tare();
}

void StateMachine::jog(Direction dir, float distance) {
    if (_state == State::RUNNING || _state == State::EMERGENCY) {
        return;
    }
    
    if (!_stepper.isEnabled()) {
        _stepper.enable();
    }
    
    _jogActive = true;
    _jogDirection = dir;
    
    if (distance > 0) {
        // Move specific distance
        if (dir == Direction::UP) {
            _stepper.moveMm(distance);
        } else {
            _stepper.moveMm(-distance);
        }
    } else {
        // Continuous movement
        _stepper.setDirection(dir);
        if (dir == Direction::UP) {
            _stepper.moveTo(INT32_MAX / 2);
        } else {
            _stepper.moveTo(INT32_MIN / 2);
        }
    }
}

void StateMachine::stopJog() {
    if (_jogActive) {
        _stepper.stopSmooth();
        _jogActive = false;
    }
}

bool StateMachine::isSafe() const {
    return _state != State::EMERGENCY && 
           _state != State::ERROR &&
           !_emergencyStopActive;
}

bool StateMachine::isTestActive() const {
    return _state == State::RUNNING || _state == State::PAUSED;
}

void StateMachine::setState(State newState) {
    _previousState = _state;
    _state = newState;
    _stateEntryTime = to_ms_since_boot(get_absolute_time());
}

void StateMachine::updateIdle() {
    // Handle any jog movements
    if (_jogActive && !_stepper.isMoving()) {
        _jogActive = false;
    }
}

void StateMachine::updateHoming() {
    static bool homingStarted = false;
    
    if (!homingStarted) {
        if (_stepper.home(Direction::DOWN)) {
            homingStarted = false;
            setState(State::READY);
        } else {
            homingStarted = false;
            setState(State::ERROR);
        }
    }
}

void StateMachine::updateReady() {
    // Handle jog movements
    if (_jogActive && !_stepper.isMoving()) {
        _jogActive = false;
    }
    
    // Check safety
    if (!checkSafety()) {
        setState(State::ERROR);
    }
}

void StateMachine::updateRunning() {
    // Check safety limits
    if (!checkSafety()) {
        stopTest();
        setState(State::ERROR);
        return;
    }
    
    // Check force overload
    float force = getCurrentForce();
    if (force >= _params.maxForce || _loadCell.isOverload()) {
        stopTest();
        _protocol.sendError(ResponseStatus::ERROR_OVERLOAD, "Force limit exceeded");
        return;
    }
    
    // Check extension limit
    float extension = getCurrentPosition() - _startPosition;
    if (extension >= _params.maxExtension) {
        stopTest();
        _protocol.sendOK("Extension limit reached");
        return;
    }
    
    // Track peak force
    if (force > _peakForce) {
        _peakForce = force;
        _extensionAtPeak = extension;
    }
    
    // Check for specimen break
    if (_params.stopOnBreak && detectBreak()) {
        _result.specimenBroke = true;
        _result.breakForce = force;
        _result.breakExtension = extension;
        stopTest();
        _protocol.sendOK("Specimen break detected");
        return;
    }
    
    // Check if movement complete
    if (!_stepper.isMoving()) {
        _result.completed = true;
        stopTest();
        _protocol.sendOK("Test completed");
        return;
    }
    
    // === HYBRID SAMPLING: Time-based + Event-based ===
    uint32_t now = to_ms_since_boot(get_absolute_time());
    uint32_t timeSinceLast = now - _lastSampleTime;
    
    // Event detection
    static float lastSampledForce = 0;
    static float lastSlope = 0;
    static float maxForceSeen = 0;
    
    // Calculate force rate (slope)
    float dt = timeSinceLast / 1000.0f;
    float currentSlope = (dt > 0) ? (force - lastSampledForce) / dt : 0;
    
    // Event flags
    bool timeBasedSample = (timeSinceLast >= _params.sampleRate);
    bool forceChangeEvent = (fabsf(force - lastSampledForce) > 5.0f);  // 5N threshold
    bool slopeChangeEvent = (fabsf(lastSlope) > 1.0f && 
                            fabsf(currentSlope - lastSlope) / fabsf(lastSlope) > 0.3f);
    bool peakEvent = (force > maxForceSeen && force > maxForceSeen * 0.99f);
    bool forceDropEvent = (maxForceSeen > 50.0f && force < maxForceSeen * 0.9f);
    
    bool eventBasedSample = (timeSinceLast >= 20) &&  // Min 20ms between samples
                           (forceChangeEvent || slopeChangeEvent || peakEvent || forceDropEvent);
    
    if (timeBasedSample || eventBasedSample) {
        recordDataPoint();
        _lastSampleTime = now;
        lastSampledForce = force;
        lastSlope = currentSlope;
        if (force > maxForceSeen) {
            maxForceSeen = force;
        }
    }
}

void StateMachine::updatePaused() {
    // Just maintain position, wait for resume or stop
}

void StateMachine::updateStopped() {
    // Allow review of results, wait for reset
}

void StateMachine::updateError() {
    // Wait for reset command
    gpio_put(LED_ERROR_PIN, true);
}

void StateMachine::updateEmergency() {
    // Keep everything stopped
    // Check if emergency stop button released
    if (!checkEmergencyStop()) {
        // Allow clearing via command
    }
}

bool StateMachine::checkSafety() {
    // Check limit switches
    if (_stepper.isAtTopLimit() && _stepper.getDirection() == Direction::UP) {
        _stepper.stop();
        return false;
    }
    if (_stepper.isAtBottomLimit() && _stepper.getDirection() == Direction::DOWN) {
        _stepper.stop();
        return false;
    }
    
    return true;
}

bool StateMachine::checkEmergencyStop() {
    return gpio_get(_emergencyStopPin) == false;  // Active LOW
}

bool StateMachine::detectBreak() {
    if (_peakForce < 10.0f) return false;  // Minimum force before break detection
    
    float currentForce = getCurrentForce();
    float dropRatio = 1.0f - (currentForce / _peakForce);
    
    return dropRatio > _params.breakThreshold;
}

void StateMachine::recordDataPoint() {
    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    DataPacket packet;
    packet.timestamp = now - _testStartTime;
    packet.force = getCurrentForce();
    packet.extension = getCurrentPosition() - _startPosition;
    packet.stress = 0;  // Would need specimen dimensions
    packet.strain = 0;  // Would need gauge length
    
    _result.dataPoints++;
    
    if (_protocol.isDataStreaming()) {
        _protocol.sendData(packet);
    }
}

void StateMachine::resetTestResult() {
    _result.maxForce = 0;
    _result.maxExtension = 0;
    _result.breakForce = 0;
    _result.breakExtension = 0;
    _result.duration = 0;
    _result.dataPoints = 0;
    _result.completed = false;
    _result.specimenBroke = false;
}

void StateMachine::finalizeTest() {
    _result.maxForce = _peakForce;
    _result.maxExtension = _extensionAtPeak;
    _result.duration = to_ms_since_boot(get_absolute_time()) - _testStartTime;
}
