CREATE TABLE IF NOT EXISTS otp_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    email VARCHAR(190) NULL,
    phone VARCHAR(20) NULL,
    otp_code VARCHAR(10) NOT NULL,
    otp_type ENUM('email', 'sms', 'both') NOT NULL DEFAULT 'email',
    purpose ENUM('registration', 'login', 'password_reset', 'phone_verify') NOT NULL DEFAULT 'registration',
    attempts INT DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP NULL,
    ip_address VARCHAR(45),
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_user (user_id),
    INDEX idx_expires (expires_at),
    INDEX idx_verified (is_verified),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS phone_verified_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255) NULL;
