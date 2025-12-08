#ifndef LOADCELL_H
#define LOADCELL_H

#include <stdint.h>
#include "Config.h"

// NAU7802 Register Addresses
#define NAU7802_REG_PU_CTRL     0x00    // Power-up control
#define NAU7802_REG_CTRL1       0x01    // Control 1
#define NAU7802_REG_CTRL2       0x02    // Control 2
#define NAU7802_REG_OCAL1_B2    0x03    // Offset calibration
#define NAU7802_REG_OCAL1_B1    0x04
#define NAU7802_REG_OCAL1_B0    0x05
#define NAU7802_REG_GCAL1_B3    0x06    // Gain calibration
#define NAU7802_REG_GCAL1_B2    0x07
#define NAU7802_REG_GCAL1_B1    0x08
#define NAU7802_REG_GCAL1_B0    0x09
#define NAU7802_REG_I2C_CTRL    0x11    // I2C control
#define NAU7802_REG_ADCO_B2     0x12    // ADC output data
#define NAU7802_REG_ADCO_B1     0x13
#define NAU7802_REG_ADCO_B0     0x14
#define NAU7802_REG_ADC         0x15    // ADC control
#define NAU7802_REG_PGA         0x1B    // PGA control
#define NAU7802_REG_PWR_CTRL    0x1C    // Power control
#define NAU7802_REG_REVISION    0x1F    // Revision ID

// NAU7802 PU_CTRL Register Bits
#define NAU7802_PU_CTRL_RR      0x01    // Register reset
#define NAU7802_PU_CTRL_PUD     0x02    // Power up digital
#define NAU7802_PU_CTRL_PUA     0x04    // Power up analog
#define NAU7802_PU_CTRL_PUR     0x08    // Power up ready
#define NAU7802_PU_CTRL_CS      0x10    // Cycle start
#define NAU7802_PU_CTRL_CR      0x20    // Cycle ready
#define NAU7802_PU_CTRL_OSCS    0x40    // System clock source
#define NAU7802_PU_CTRL_AVDDS   0x80    // AVDD source select

// NAU7802 Gain Settings
enum class NAU7802Gain : uint8_t {
    GAIN_1   = 0,
    GAIN_2   = 1,
    GAIN_4   = 2,
    GAIN_8   = 3,
    GAIN_16  = 4,
    GAIN_32  = 5,
    GAIN_64  = 6,
    GAIN_128 = 7
};

// NAU7802 Sample Rate Settings
enum class NAU7802SPS : uint8_t {
    SPS_10  = 0,
    SPS_20  = 1,
    SPS_40  = 2,
    SPS_80  = 3,
    SPS_320 = 7
};

// NAU7802 LDO Voltage Settings
enum class NAU7802LDO : uint8_t {
    LDO_2V4 = 7,
    LDO_2V7 = 6,
    LDO_3V0 = 5,
    LDO_3V3 = 4,
    LDO_3V6 = 3,
    LDO_3V9 = 2,
    LDO_4V2 = 1,
    LDO_4V5 = 0
};

/**
 * @brief LoadCell class for NAU7802 24-bit ADC interface
 * 
 * Handles force measurement using Adafruit NAU7802 ADC with calibration,
 * taring, and overload protection for S-type load cells.
 */
class LoadCell {
public:
    /**
     * @brief Construct a new LoadCell object
     * @param sdaPin I2C SDA pin
     * @param sclPin I2C SCL pin
     */
    LoadCell(uint8_t sdaPin, uint8_t sclPin);

    /**
     * @brief Initialize the NAU7802 ADC
     * @return true if initialization successful
     */
    bool begin();

    /**
     * @brief Read current force value
     * @return Force in Newtons
     */
    float readForce();

    /**
     * @brief Read raw ADC value (24-bit signed)
     * @return Raw ADC value
     */
    int32_t readRaw();

    /**
     * @brief Read averaged force value
     * @param samples Number of samples to average
     * @return Averaged force in Newtons
     */
    float readForceAverage(uint8_t samples = LOADCELL_SAMPLES);

    /**
     * @brief Tare the load cell (set current reading as zero)
     * @param samples Number of samples for tare averaging
     */
    void tare(uint8_t samples = LOADCELL_SAMPLES);

    /**
     * @brief Set calibration factor
     * @param factor Calibration factor (raw units per Newton)
     */
    void setCalibrationFactor(float factor);

    /**
     * @brief Get current calibration factor
     * @return Current calibration factor
     */
    float getCalibrationFactor() const;

    /**
     * @brief Set zero offset
     * @param offset Zero offset value
     */
    void setOffset(int32_t offset);

    /**
     * @brief Get current zero offset
     * @return Current offset value
     */
    int32_t getOffset() const;

    /**
     * @brief Check if ADC conversion is ready
     * @return true if data ready
     */
    bool isReady();

    /**
     * @brief Check for force overload condition
     * @return true if force exceeds safety limit
     */
    bool isOverload();

    /**
     * @brief Get the last read force value (cached)
     * @return Last force value in Newtons
     */
    float getLastForce() const;

    /**
     * @brief Set PGA gain
     * @param gain Gain setting (1-128)
     */
    void setGain(NAU7802Gain gain);

    /**
     * @brief Set sample rate
     * @param sps Samples per second
     */
    void setSampleRate(NAU7802SPS sps);

    /**
     * @brief Perform internal calibration
     * @return true if calibration successful
     */
    bool calibrateAFE();

    /**
     * @brief Get revision ID of NAU7802
     * @return Revision ID
     */
    uint8_t getRevision();

    /**
     * @brief Power down the ADC
     */
    void powerDown();

    /**
     * @brief Power up the ADC
     */
    void powerUp();

private:
    uint8_t _sdaPin;
    uint8_t _sclPin;
    float _calibrationFactor;
    int32_t _offset;
    float _lastForce;
    bool _initialized;

    /**
     * @brief Write to NAU7802 register
     * @param reg Register address
     * @param value Value to write
     * @return true if successful
     */
    bool writeRegister(uint8_t reg, uint8_t value);

    /**
     * @brief Read from NAU7802 register
     * @param reg Register address
     * @return Register value
     */
    uint8_t readRegister(uint8_t reg);

    /**
     * @brief Set specific bit(s) in a register
     * @param reg Register address
     * @param bit Bit(s) to set
     * @return true if successful
     */
    bool setBit(uint8_t reg, uint8_t bit);

    /**
     * @brief Clear specific bit(s) in a register
     * @param reg Register address
     * @param bit Bit(s) to clear
     * @return true if successful
     */
    bool clearBit(uint8_t reg, uint8_t bit);

    /**
     * @brief Wait for specific bit to be set
     * @param reg Register address
     * @param bit Bit to wait for
     * @param timeout Timeout in milliseconds
     * @return true if bit set within timeout
     */
    bool waitForBit(uint8_t reg, uint8_t bit, uint32_t timeout = 1000);

    /**
     * @brief Reset the NAU7802
     * @return true if successful
     */
    bool reset();
};

#endif // LOADCELL_H
