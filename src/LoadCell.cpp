#include "LoadCell.h"
#include "pico/stdlib.h"
#include "hardware/i2c.h"

LoadCell::LoadCell(uint8_t sdaPin, uint8_t sclPin)
    : _sdaPin(sdaPin)
    , _sclPin(sclPin)
    , _calibrationFactor(LOADCELL_CALIBRATION)
    , _offset(LOADCELL_OFFSET)
    , _lastForce(0.0f)
    , _initialized(false)
{
}

bool LoadCell::begin() {
    // Initialize I2C
    i2c_init(NAU7802_I2C_PORT, NAU7802_I2C_FREQ);
    gpio_set_function(_sdaPin, GPIO_FUNC_I2C);
    gpio_set_function(_sclPin, GPIO_FUNC_I2C);
    gpio_pull_up(_sdaPin);
    gpio_pull_up(_sclPin);
    
    // Reset the NAU7802
    if (!reset()) {
        return false;
    }
    
    // Power up digital
    if (!setBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_PUD)) {
        return false;
    }
    
    // Wait for power up ready
    if (!waitForBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_PUR, 1000)) {
        return false;
    }
    
    // Power up analog
    if (!setBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_PUA)) {
        return false;
    }
    sleep_ms(10);
    
    // Set LDO to 3.0V (for 3.3V load cell excitation)
    uint8_t ctrl1 = readRegister(NAU7802_REG_CTRL1);
    ctrl1 &= 0xC7;  // Clear VLDO bits [5:3]
    ctrl1 |= ((uint8_t)NAU7802LDO::LDO_3V0 << 3);
    writeRegister(NAU7802_REG_CTRL1, ctrl1);
    
    // Enable internal LDO
    if (!setBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_AVDDS)) {
        return false;
    }
    
    // Set gain to 128 for maximum sensitivity
    setGain(NAU7802Gain::GAIN_128);
    
    // Set sample rate to 80 SPS
    setSampleRate(NAU7802SPS::SPS_80);
    
    // Turn off CLK_CHP (disable clock chopper)
    uint8_t adc = readRegister(NAU7802_REG_ADC);
    adc |= 0x30;  // Set REG_CHP bits
    writeRegister(NAU7802_REG_ADC, adc);
    
    // Enable PGA output bypass capacitor
    uint8_t pga = readRegister(NAU7802_REG_PGA);
    pga |= 0x80;  // Set LDOMODE bit for better stability
    writeRegister(NAU7802_REG_PGA, pga);
    
    // Perform internal calibration
    if (!calibrateAFE()) {
        return false;
    }
    
    // Start conversions
    if (!setBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_CS)) {
        return false;
    }
    
    // Wait for first conversion
    sleep_ms(100);
    
    // Perform initial tare
    tare(20);
    
    _initialized = true;
    return true;
}

float LoadCell::readForce() {
    if (!_initialized) {
        return 0.0f;
    }
    
    int32_t raw = readRaw();
    _lastForce = (float)(raw - _offset) / _calibrationFactor;
    return _lastForce;
}

int32_t LoadCell::readRaw() {
    // Wait for data ready
    if (!isReady()) {
        // Wait up to 50ms for data
        for (int i = 0; i < 50; i++) {
            sleep_ms(1);
            if (isReady()) break;
        }
    }
    
    // Read 24-bit ADC value
    uint8_t data[3];
    uint8_t reg = NAU7802_REG_ADCO_B2;
    
    i2c_write_blocking(NAU7802_I2C_PORT, NAU7802_I2C_ADDR, &reg, 1, true);
    i2c_read_blocking(NAU7802_I2C_PORT, NAU7802_I2C_ADDR, data, 3, false);
    
    // Combine bytes (MSB first)
    int32_t value = ((uint32_t)data[0] << 16) | ((uint32_t)data[1] << 8) | data[2];
    
    // Sign extend 24-bit to 32-bit
    if (value & 0x800000) {
        value |= 0xFF000000;
    }
    
    return value;
}

float LoadCell::readForceAverage(uint8_t samples) {
    if (samples == 0) samples = 1;
    
    float sum = 0.0f;
    uint8_t validSamples = 0;
    
    for (uint8_t i = 0; i < samples; i++) {
        // Wait for new data
        while (!isReady()) {
            sleep_ms(1);
        }
        sum += readForce();
        validSamples++;
    }
    
    if (validSamples == 0) {
        return _lastForce;
    }
    
    _lastForce = sum / validSamples;
    return _lastForce;
}

void LoadCell::tare(uint8_t samples) {
    if (samples == 0) samples = 1;
    
    int64_t sum = 0;
    uint8_t validSamples = 0;
    
    for (uint8_t i = 0; i < samples; i++) {
        while (!isReady()) {
            sleep_ms(1);
        }
        sum += readRaw();
        validSamples++;
    }
    
    if (validSamples > 0) {
        _offset = sum / validSamples;
    }
}

void LoadCell::setCalibrationFactor(float factor) {
    if (factor != 0.0f) {
        _calibrationFactor = factor;
    }
}

float LoadCell::getCalibrationFactor() const {
    return _calibrationFactor;
}

void LoadCell::setOffset(int32_t offset) {
    _offset = offset;
}

int32_t LoadCell::getOffset() const {
    return _offset;
}

bool LoadCell::isReady() {
    uint8_t status = readRegister(NAU7802_REG_PU_CTRL);
    return (status & NAU7802_PU_CTRL_CR) != 0;
}

bool LoadCell::isOverload() {
    float absForce = _lastForce > 0 ? _lastForce : -_lastForce;
    return absForce > FORCE_OVERLOAD_LIMIT;
}

float LoadCell::getLastForce() const {
    return _lastForce;
}

void LoadCell::setGain(NAU7802Gain gain) {
    uint8_t ctrl1 = readRegister(NAU7802_REG_CTRL1);
    ctrl1 &= 0xF8;  // Clear gain bits [2:0]
    ctrl1 |= (uint8_t)gain;
    writeRegister(NAU7802_REG_CTRL1, ctrl1);
}

void LoadCell::setSampleRate(NAU7802SPS sps) {
    uint8_t ctrl2 = readRegister(NAU7802_REG_CTRL2);
    ctrl2 &= 0x8F;  // Clear CRS bits [6:4]
    ctrl2 |= ((uint8_t)sps << 4);
    writeRegister(NAU7802_REG_CTRL2, ctrl2);
}

bool LoadCell::calibrateAFE() {
    // Start internal offset calibration
    uint8_t ctrl2 = readRegister(NAU7802_REG_CTRL2);
    ctrl2 |= 0x04;  // Set CALS bit
    writeRegister(NAU7802_REG_CTRL2, ctrl2);
    
    // Wait for calibration to complete (CAL_ERR bit should be 0)
    uint32_t startTime = to_ms_since_boot(get_absolute_time());
    while ((to_ms_since_boot(get_absolute_time()) - startTime) < 2000) {
        ctrl2 = readRegister(NAU7802_REG_CTRL2);
        if (!(ctrl2 & 0x04)) {  // CALS cleared = calibration done
            // Check for calibration error
            if (ctrl2 & 0x08) {  // CAL_ERR bit
                return false;
            }
            return true;
        }
        sleep_ms(10);
    }
    
    return false;  // Timeout
}

uint8_t LoadCell::getRevision() {
    return readRegister(NAU7802_REG_REVISION);
}

void LoadCell::powerDown() {
    clearBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_PUA);
    clearBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_PUD);
}

void LoadCell::powerUp() {
    setBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_PUD);
    waitForBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_PUR, 1000);
    setBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_PUA);
    sleep_ms(10);
    setBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_CS);
}

bool LoadCell::writeRegister(uint8_t reg, uint8_t value) {
    uint8_t data[2] = {reg, value};
    int result = i2c_write_blocking(NAU7802_I2C_PORT, NAU7802_I2C_ADDR, data, 2, false);
    return result == 2;
}

uint8_t LoadCell::readRegister(uint8_t reg) {
    uint8_t value;
    i2c_write_blocking(NAU7802_I2C_PORT, NAU7802_I2C_ADDR, &reg, 1, true);
    i2c_read_blocking(NAU7802_I2C_PORT, NAU7802_I2C_ADDR, &value, 1, false);
    return value;
}

bool LoadCell::setBit(uint8_t reg, uint8_t bit) {
    uint8_t value = readRegister(reg);
    value |= bit;
    return writeRegister(reg, value);
}

bool LoadCell::clearBit(uint8_t reg, uint8_t bit) {
    uint8_t value = readRegister(reg);
    value &= ~bit;
    return writeRegister(reg, value);
}

bool LoadCell::waitForBit(uint8_t reg, uint8_t bit, uint32_t timeout) {
    uint32_t startTime = to_ms_since_boot(get_absolute_time());
    
    while ((to_ms_since_boot(get_absolute_time()) - startTime) < timeout) {
        if (readRegister(reg) & bit) {
            return true;
        }
        sleep_ms(1);
    }
    
    return false;
}

bool LoadCell::reset() {
    // Set reset bit
    if (!setBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_RR)) {
        return false;
    }
    sleep_ms(1);
    
    // Clear reset bit
    if (!clearBit(NAU7802_REG_PU_CTRL, NAU7802_PU_CTRL_RR)) {
        return false;
    }
    sleep_ms(10);
    
    return true;
}
