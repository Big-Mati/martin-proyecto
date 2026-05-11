/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- creacion de la base de datos
CREATE DATABASE IF NOT EXISTS `analitica_tienda` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `analitica_tienda`;

-- tabla de dimensiones: empleados
CREATE TABLE IF NOT EXISTS `dim_empleados` (
  `id_empleado` int NOT NULL AUTO_INCREMENT,
  `nombre_vendedor` varchar(150) NOT NULL,
  `rol` varchar(100) DEFAULT NULL,
  `ruta_foto_facial` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_empleado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- tabla de dimensiones: productos
CREATE TABLE IF NOT EXISTS `dim_productos` (
  `id_producto` int NOT NULL AUTO_INCREMENT,
  `nombre_producto` varchar(150) NOT NULL,
  `categoria` varchar(100) DEFAULT NULL,
  `precio` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_producto`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT IGNORE INTO `dim_productos` (`id_producto`, `nombre_producto`, `categoria`, `precio`) VALUES 
(1, 'Mochila Escolar', 'Escolar', 45.00),
(2, 'Celular Smartphone', 'Tecno', 250.00),
(3, 'Refresco / Botella', 'Escolar', 1.50),
(4, 'Cuaderno / Libro', 'Papelería', 3.00);

-- tabla de dimensiones: zonas de la tienda
CREATE TABLE IF NOT EXISTS `dim_zonas` (
  `id_zona` int NOT NULL AUTO_INCREMENT,
  `nombre_zona` varchar(100) NOT NULL,
  PRIMARY KEY (`id_zona`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT IGNORE INTO `dim_zonas` (`id_zona`, `nombre_zona`) VALUES 
(1, 'Escolar'),
(2, 'Tecno'),
(3, 'Papelería');

-- tabla de hechos: registro de entradas y salidas en puerta
CREATE TABLE IF NOT EXISTS `fact_entradas_salidas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `track_id` varchar(100) NOT NULL,
  `tipo` enum('ENTRADA','SALIDA') NOT NULL,
  `fecha_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  `reid_match` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- tabla de hechos: interacciones con productos
CREATE TABLE IF NOT EXISTS `fact_interacciones_ia` (
  `id_interaccion` int NOT NULL AUTO_INCREMENT,
  `id_visita` int NOT NULL,
  `id_producto` int NOT NULL,
  `tipo_accion` varchar(50) DEFAULT NULL,
  `emocion_detectada` varchar(50) DEFAULT NULL,
  `fecha_hora` datetime NOT NULL,
  PRIMARY KEY (`id_interaccion`),
  KEY `id_visita` (`id_visita`),
  KEY `id_producto` (`id_producto`),
  CONSTRAINT `fact_interacciones_ia_ibfk_1` FOREIGN KEY (`id_visita`) REFERENCES `fact_visitas_ia` (`id_visita`),
  CONSTRAINT `fact_interacciones_ia_ibfk_2` FOREIGN KEY (`id_producto`) REFERENCES `dim_productos` (`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- tabla de hechos: tracking de movimientos entre zonas (dwell time)
CREATE TABLE IF NOT EXISTS `fact_movimientos_ia` (
  `id_movimiento` int NOT NULL AUTO_INCREMENT,
  `id_visita` int NOT NULL,
  `id_zona` int NOT NULL,
  `fecha_ingreso` datetime NOT NULL,
  `fecha_salida` datetime DEFAULT NULL,
  PRIMARY KEY (`id_movimiento`),
  KEY `id_visita` (`id_visita`),
  KEY `id_zona` (`id_zona`),
  CONSTRAINT `fact_movimientos_ia_ibfk_1` FOREIGN KEY (`id_visita`) REFERENCES `fact_visitas_ia` (`id_visita`),
  CONSTRAINT `fact_movimientos_ia_ibfk_2` FOREIGN KEY (`id_zona`) REFERENCES `dim_zonas` (`id_zona`)
) ENGINE=InnoDB AUTO_INCREMENT=339 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- tabla de hechos: registro de objetos detectados (mochilas, laptops, etc)
CREATE TABLE IF NOT EXISTS `fact_objetos_detectados` (
  `id_objeto` int NOT NULL AUTO_INCREMENT,
  `clase_objeto` varchar(100) NOT NULL,
  `confianza` float NOT NULL DEFAULT '0',
  `zona_detectada` varchar(100) DEFAULT 'Desconocida',
  `fecha_hora` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_objeto`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- tabla de hechos: registro de ventas del erp
CREATE TABLE IF NOT EXISTS `fact_ventas` (
  `id_ticket` int NOT NULL AUTO_INCREMENT,
  `id_producto` int NOT NULL,
  `cantidad` int NOT NULL,
  `total_pagado` decimal(10,2) NOT NULL,
  `fecha_hora` datetime NOT NULL,
  PRIMARY KEY (`id_ticket`),
  KEY `id_producto` (`id_producto`),
  CONSTRAINT `fact_ventas_ibfk_1` FOREIGN KEY (`id_producto`) REFERENCES `dim_productos` (`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- tabla de hechos: registro principal de visitas detectadas por ia
CREATE TABLE IF NOT EXISTS `fact_visitas_ia` (
  `id_visita` int NOT NULL AUTO_INCREMENT,
  `track_id` varchar(100) NOT NULL,
  `genero` varchar(20) DEFAULT NULL,
  `edad_estimada` int DEFAULT NULL,
  `emocion_dominante` varchar(50) DEFAULT NULL,
  `es_empleado` tinyint(1) DEFAULT '0',
  `id_empleado_detectado` int DEFAULT NULL,
  `vector_facial` mediumtext,
  `fecha_visita` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_visita`),
  KEY `id_empleado_detectado` (`id_empleado_detectado`),
  CONSTRAINT `fact_visitas_ia_ibfk_1` FOREIGN KEY (`id_empleado_detectado`) REFERENCES `dim_empleados` (`id_empleado`)
) ENGINE=InnoDB AUTO_INCREMENT=74 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- estructura temporal para la vista de metricas
CREATE TABLE `vw_metricas_dashboard` (
	`track_id` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_0900_ai_ci',
	`genero` VARCHAR(1) NULL COLLATE 'utf8mb4_0900_ai_ci',
	`edad_estimada` INT NULL,
	`emocion_dominante` VARCHAR(1) NULL COLLATE 'utf8mb4_0900_ai_ci',
	`id_zona` INT NOT NULL,
	`nombre_zona` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_0900_ai_ci',
	`fecha_ingreso` DATETIME NOT NULL,
	`fecha_salida` DATETIME NULL,
	`dwell_time_segundos` BIGINT NULL
) ENGINE=MyISAM;

-- estructura temporal para la vista de objetos
CREATE TABLE `vw_objetos_dashboard` (
	`clase_objeto` VARCHAR(1) NOT NULL COLLATE 'utf8mb4_0900_ai_ci',
	`zona_detectada` VARCHAR(1) NULL COLLATE 'utf8mb4_0900_ai_ci',
	`total_detecciones` BIGINT NOT NULL,
	`confianza_prom_pct` DOUBLE NULL,
	`ultima_vez` DATETIME NULL,
	`hora` INT NULL
) ENGINE=MyISAM;

-- vista analitica: consolida metricas de visitas, zonas y calcula dwell time
DROP TABLE IF EXISTS `vw_metricas_dashboard`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_metricas_dashboard` AS select `v`.`track_id` AS `track_id`,`v`.`genero` AS `genero`,`v`.`edad_estimada` AS `edad_estimada`,`v`.`emocion_dominante` AS `emocion_dominante`,`m`.`id_zona` AS `id_zona`,`z`.`nombre_zona` AS `nombre_zona`,`m`.`fecha_ingreso` AS `fecha_ingreso`,`m`.`fecha_salida` AS `fecha_salida`,timestampdiff(SECOND,`m`.`fecha_ingreso`,ifnull(`m`.`fecha_salida`,now())) AS `dwell_time_segundos` from ((`fact_visitas_ia` `v` join `fact_movimientos_ia` `m` on((`v`.`id_visita` = `m`.`id_visita`))) join `dim_zonas` `z` on((`m`.`id_zona` = `z`.`id_zona`))) where (`v`.`es_empleado` = false);

-- vista analitica: frecuencia de objetos por hora
DROP TABLE IF EXISTS `vw_objetos_dashboard`;
CREATE ALGORITHM=UNDEFINED SQL SECURITY DEFINER VIEW `vw_objetos_dashboard` AS select `fact_objetos_detectados`.`clase_objeto` AS `clase_objeto`,`fact_objetos_detectados`.`zona_detectada` AS `zona_detectada`,count(0) AS `total_detecciones`,round((avg(`fact_objetos_detectados`.`confianza`) * 100),1) AS `confianza_prom_pct`,max(`fact_objetos_detectados`.`fecha_hora`) AS `ultima_vez`,hour(`fact_objetos_detectados`.`fecha_hora`) AS `hora` from `fact_objetos_detectados` group by `fact_objetos_detectados`.`clase_objeto`,`fact_objetos_detectados`.`zona_detectada`,hour(`fact_objetos_detectados`.`fecha_hora`);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
