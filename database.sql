DROP DATABASE IF EXISTS pharma_db;
CREATE DATABASE pharma_db;
USE pharma_db;

CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    allergy_warning TEXT,
    side_effects TEXT,
    dosage VARCHAR(255),
    instructions TEXT,
    image_paths TEXT -- Changed to TEXT to hold multiple comma-separated paths
);

CREATE TABLE IF NOT EXISTS similar_medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT,
    similar_medicine_id INT,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
    FOREIGN KEY (similar_medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);