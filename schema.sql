CREATE DATABASE IF NOT EXISTS oneparfum_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE oneparfum_db;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO roles (nombre) VALUES ('admin'), ('cliente');

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) UNIQUE,
    correo VARCHAR(150) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL DEFAULT 2,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (rol_id) REFERENCES roles(id),
    CONSTRAINT chk_contacto CHECK (telefono IS NOT NULL OR correo IS NOT NULL)
);