-- Add PSGC-based rider address fields and a normalized service areas table

-- 1) Extend `riders` to store the official PSGC selection used at registration
ALTER TABLE riders
    ADD COLUMN address_region_code VARCHAR(20) NULL AFTER service_area,
    ADD COLUMN address_region_name VARCHAR(150) NULL AFTER address_region_code,
    ADD COLUMN address_province_code VARCHAR(20) NULL AFTER address_region_name,
    ADD COLUMN address_province_name VARCHAR(150) NULL AFTER address_province_code,
    ADD COLUMN address_city_code VARCHAR(20) NULL AFTER address_province_name,
    ADD COLUMN address_city_name VARCHAR(150) NULL AFTER address_city_code,
    ADD COLUMN address_barangay_code VARCHAR(20) NULL AFTER address_city_name,
    ADD COLUMN address_barangay_name VARCHAR(150) NULL AFTER address_barangay_code,
    ADD COLUMN default_service_area_city_code VARCHAR(20) NULL AFTER address_barangay_name,
    ADD INDEX idx_rider_address_city_code (address_city_code),
    ADD INDEX idx_rider_default_city_code (default_service_area_city_code);

-- 2) Optional: normalized additional service areas (default must match address city)
CREATE TABLE IF NOT EXISTS rider_service_areas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rider_id INT NOT NULL,
    city_code VARCHAR(20) NOT NULL,
    city_name VARCHAR(150) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_rider_city (rider_id, city_code),
    INDEX idx_rider_default (rider_id, is_default),
    CONSTRAINT fk_rider_service_areas_rider
        FOREIGN KEY (rider_id)
        REFERENCES riders(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
