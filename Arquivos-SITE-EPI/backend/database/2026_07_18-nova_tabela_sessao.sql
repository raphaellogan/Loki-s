CREATE TABLE sessoes (

    id INT AUTO_INCREMENT PRIMARY KEY,

    sessao CHAR(16) NOT NULL UNIQUE,

    usuario_id BIGINT UNSIGNED,

    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_id) 
        REFERENCES usuarios(id)
        ON DELETE CASCADE

);