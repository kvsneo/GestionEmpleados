-- Crear la base de datos si no existe
create database if not exists basegestionempleados;
-- Usar la base de datos creada
use basegestionempleados;

-- Cambiar el delimitador para permitir el uso de múltiples declaraciones en el trigger
DELIMITER //

-- Crear un trigger que se ejecuta después de una inserción en la tabla match_info
CREATE TRIGGER if not exists after_match_info_insert
    AFTER INSERT
    ON match_info
    FOR EACH ROW
BEGIN
    -- Declarar variables locales
    DECLARE diferencia_min INT;
    DECLARE estado_nuevo VARCHAR(255);
    DECLARE schedule_start TIME;
    DECLARE schedule_month INT;
    DECLARE current_month INT;
    DECLARE attendance_count INT;

    -- Obtener el schedule_start y el mes de integracion_employeeschedule
    SELECT ies.schedule_start, MONTH(ies.month)
    INTO schedule_start, schedule_month
    FROM integracion_employeeschedule ies
    WHERE ies.username = NEW.name;

    -- Obtener el mes actual
    SET current_month = MONTH(NOW());

    -- Verificar si el mes corresponde al actual
    IF schedule_month = current_month THEN
        -- Verificar si ya existe una entrada de asistencia para el usuario en la fecha actual
        SELECT COUNT(*)
        INTO attendance_count
        FROM integracion_asistencia
        WHERE employee = NEW.name
          AND date = CURDATE();

        -- Si no existe una entrada, proceder con la inserción
        IF attendance_count = 0 THEN
            -- Calcular la diferencia en minutos entre schedule_start y la hora actual
            SET diferencia_min = ABS(TIMESTAMPDIFF(MINUTE, schedule_start, NOW()));

            -- Determinar el estado basado en la diferencia
            IF diferencia_min <= 10 THEN
                SET estado_nuevo = 'a'; -- a tiempo
            ELSEIF diferencia_min <= 15 THEN
                SET estado_nuevo = 'r'; -- retrasado
            ELSE
                SET estado_nuevo = 'sn'; -- sin notificación
            END IF;

            -- Insertar en la tabla asistencia
            INSERT INTO integracion_asistencia (employee, date, hora, status)
            VALUES (NEW.name, CURDATE(), NOW(), estado_nuevo);
        END IF;
    END IF;
END;
//

-- Restaurar el delimitador
DELIMITER ;