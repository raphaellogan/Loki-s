CREATE TABLE `usuarios`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nome` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `senha` VARCHAR(255) NOT NULL,
    `perfil` VARCHAR(255) NOT NULL,
    `status` ENUM('ativo', 'inativo') NOT NULL DEFAULT 'ativo',
    `created_at` DATETIME NOT NULL,
    `cpf` VARCHAR(255) NOT NULL,
    `setor` VARCHAR(255) NULL,
    `cargo` VARCHAR(255) NULL,
    `data_admissao` DATE NOT NULL,
    `telefone` VARCHAR(255) NOT NULL
);
ALTER TABLE
    `usuarios` ADD UNIQUE `usuarios_email_unique`(`email`);
ALTER TABLE
    `usuarios` ADD UNIQUE `usuarios_cpf_unique`(`cpf`);
ALTER TABLE
    `usuarios` ADD UNIQUE `usuarios_telefone_unique`(`telefone`);
CREATE TABLE `entregas_epis`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `usuario_id` BIGINT NOT NULL,
    `epi_id` BIGINT NOT NULL,
    `data_entrega` DATETIME NOT NULL,
    `data_devolucao` DATETIME NOT NULL,
    `data_vencimento` DATE NOT NULL,
    `assinatura` VARCHAR(255) NOT NULL,
    `observacao` VARCHAR(255) NULL,
    `created_at` DATETIME NOT NULL
);
CREATE TABLE `epis`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nome` VARCHAR(255) NOT NULL,
    `codigo` VARCHAR(255) NOT NULL,
    `categoria` VARCHAR(255) NOT NULL,
    `fabricante` VARCHAR(255) NOT NULL,
    `ca_certificado` VARCHAR(255) NOT NULL,
    `validade_ca` DATE NOT NULL,
    `status` ENUM('ativo', 'inativo') NOT NULL DEFAULT 'ativo',
    `created_at` DATETIME NOT NULL,
    `estoque_id` BIGINT NOT NULL
);
CREATE TABLE `estoques`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nome` VARCHAR(255) NOT NULL,
    `categoria` VARCHAR(255) NOT NULL,
    `descricao` VARCHAR(255) NULL,
    `quantidade_em_estoque` BIGINT NOT NULL DEFAULT 0,
    `quantidade_emprestado` BIGINT NOT NULL DEFAULT 0
);
CREATE TABLE `alertas`(
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `usuario_id` BIGINT NOT NULL,
    `epi_id` BIGINT NOT NULL,
    `tipo` VARCHAR(255) NOT NULL,
    `mensagem` TEXT NOT NULL,
    `visualizado` BOOLEAN NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL
);
ALTER TABLE
    `entregas_epis` ADD CONSTRAINT `entregas_epis_epi_id_foreign` FOREIGN KEY(`epi_id`) REFERENCES `epis`(`id`);
ALTER TABLE
    `epis` ADD CONSTRAINT `epis_estoque_id_foreign` FOREIGN KEY(`estoque_id`) REFERENCES `estoques`(`id`);
ALTER TABLE
    `alertas` ADD CONSTRAINT `alertas_epi_id_foreign` FOREIGN KEY(`epi_id`) REFERENCES `epis`(`id`);
ALTER TABLE
    `alertas` ADD CONSTRAINT `alertas_usuario_id_foreign` FOREIGN KEY(`usuario_id`) REFERENCES `usuarios`(`id`);
ALTER TABLE
    `entregas_epis` ADD CONSTRAINT `entregas_epis_usuario_id_foreign` FOREIGN KEY(`usuario_id`) REFERENCES `usuarios`(`id`);