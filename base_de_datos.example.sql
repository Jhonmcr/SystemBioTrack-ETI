-- Resumen: Este script SQL crea la estructura de la base de datos para SystemBioTrack.
-- Crea las tablas, define las llaves primarias autoincrementales,
-- establece las llaves foráneas para las relaciones e inserta los datos semilla.

-- ==========================================
-- MÓDULO 1: USUARIOS, ROLES Y AUTENTICACIÓN
-- ==========================================

CREATE TABLE rol ( -- Crea la tabla 'rol'
    id SERIAL PRIMARY KEY, -- Crea la columna 'id' como un número autoincremental y llave principal
    nombre_rol VARCHAR NOT NULL -- Crea la columna 'nombre_rol' como texto que no puede estar vacío
);

CREATE TABLE usuario ( -- Crea la tabla 'usuario'
    id SERIAL PRIMARY KEY, -- Crea el ID único del usuario (autoincremental)
    empleado_id INTEGER NOT NULL UNIQUE, -- Guarda el ID del empleado (único para relación 1 a 1)
    correo VARCHAR UNIQUE NOT NULL, -- Guarda el correo del usuario, debe ser único y obligatorio
    contrasena_hash VARCHAR NOT NULL, -- Guarda la contraseña encriptada obligatoriamente
    rol_id INTEGER NOT NULL -- Guarda el ID del rol al que pertenece este usuario
);

-- ==========================================
-- MÓDULO 2: GESTIÓN DE PERSONAL Y HORARIOS
-- ==========================================

CREATE TABLE cargo ( -- Crea la tabla 'cargo'
    id SERIAL PRIMARY KEY, -- ID único autoincremental para el cargo
    nombre_cargo VARCHAR NOT NULL -- Nombre del cargo, campo obligatorio
);

CREATE TABLE horario ( -- Crea la tabla 'horario'
    id SERIAL PRIMARY KEY, -- ID único autoincremental para el horario
    nombre_horario VARCHAR NOT NULL, -- Nombre descriptivo del turno u horario
    hora_entrada_teorica TIME NOT NULL, -- Define la hora de entrada en formato de tiempo
    hora_salida_teorica TIME NOT NULL -- Define la hora de salida en formato de tiempo
);

CREATE TABLE empleado ( -- Crea la tabla 'empleado'
    id SERIAL PRIMARY KEY, -- ID único autoincremental del empleado
    nombre VARCHAR NOT NULL, -- Nombre del empleado, obligatorio
    apellido VARCHAR NOT NULL, -- Apellido del empleado, obligatorio
    cedula VARCHAR UNIQUE NOT NULL, -- Cédula única del empleado, no puede repetirse
    id_empleado_biometrico INTEGER UNIQUE, -- ID asignado en el reloj biométrico compatible con ISAPI/HTTP, debe ser único
    cargo_id INTEGER NOT NULL, -- Guarda el ID del cargo asignado
    horario_id INTEGER NOT NULL -- Guarda el ID del horario asignado
);

-- ==========================================
-- MÓDULO 3: MOTOR BIOMÉTRICO Y ASISTENCIA
-- ==========================================

CREATE TABLE marcaje_crudo ( -- Crea la tabla que recibe los datos directos del reloj
    id SERIAL PRIMARY KEY, -- ID único autoincremental del marcaje
    id_empleado_biometrico INTEGER NOT NULL, -- ID del reloj del empleado que marcó
    fecha_hora_marcaje TIMESTAMP NOT NULL, -- Fecha y hora exacta del momento del marcaje
    tipo_marcaje VARCHAR -- Indica si el marcaje fue de entrada o salida
);

CREATE TABLE estatus_asistencia ( -- Crea la tabla de los estados de asistencia
    id SERIAL PRIMARY KEY, -- ID único autoincremental del estado
    nombre_estatus VARCHAR NOT NULL -- Nombre del estado (ej. A tiempo, Inasistente)
);

CREATE TABLE asistencia_diaria ( -- Crea la tabla de asistencia ya procesada
    id SERIAL PRIMARY KEY, -- ID único autoincremental del registro diario
    empleado_id INTEGER NOT NULL, -- ID del empleado al que pertenece el registro
    fecha DATE NOT NULL, -- Fecha específica de la asistencia
    hora_entrada TIME, -- Hora real a la que entró
    hora_salida TIME, -- Hora real a la que salió
    minutos_tarde INTEGER, -- Cantidad de minutos de retraso calculados
    estatus_id INTEGER NOT NULL, -- ID del estatus final de esa asistencia
    modificado_manualmente BOOLEAN DEFAULT false -- Indicador si un administrador editó el registro manualmente
);

-- ==========================================
-- MÓDULO 4: PERMISOS Y JUSTIFICATIVOS
-- ==========================================

CREATE TABLE tipo_ausencia ( -- Crea la tabla con los tipos de justificaciones
    id SERIAL PRIMARY KEY, -- ID único autoincremental del tipo
    nombre_tipo VARCHAR NOT NULL -- Nombre del tipo (ej. Reposo médico)
);

CREATE TABLE ausencia ( -- Crea la tabla que guarda las solicitudes de permisos
    id SERIAL PRIMARY KEY, -- ID único autoincremental de la solicitud
    empleado_id INTEGER NOT NULL, -- ID del empleado que pide el permiso
    tipo_ausencia_id INTEGER NOT NULL, -- ID del tipo de permiso solicitado
    fecha_inicio DATE NOT NULL, -- Fecha en la que inicia la ausencia
    fecha_fin DATE NOT NULL, -- Fecha en la que termina la ausencia
    descripcion TEXT, -- Texto detallado con el motivo de la ausencia
    archivo_pdf_ruta VARCHAR, -- Ruta del documento PDF adjunto como respaldo
    estado_aprobacion VARCHAR DEFAULT 'Pendiente', -- Estado actual de la solicitud, pendiente por defecto
    aprobado_por_usuario_id INTEGER, -- ID del administrador que aprobó la solicitud
    fecha_solicitud TIMESTAMP -- Fecha y hora en la que se creó la solicitud
);

-- ==========================================
-- RELACIONES (Llaves foráneas)
-- ==========================================

ALTER TABLE usuario ADD FOREIGN KEY (rol_id) REFERENCES rol(id); -- Conecta la tabla usuario con la tabla rol
ALTER TABLE usuario ADD FOREIGN KEY (empleado_id) REFERENCES empleado(id); -- Conecta la tabla usuario con su respectivo empleado
ALTER TABLE empleado ADD FOREIGN KEY (cargo_id) REFERENCES cargo(id); -- Conecta al empleado con su cargo
ALTER TABLE empleado ADD FOREIGN KEY (horario_id) REFERENCES horario(id); -- Conecta al empleado con su horario asignado
ALTER TABLE marcaje_crudo ADD FOREIGN KEY (id_empleado_biometrico) REFERENCES empleado(id_empleado_biometrico); -- Conecta el marcaje crudo con el empleado usando el ID del reloj
ALTER TABLE asistencia_diaria ADD FOREIGN KEY (empleado_id) REFERENCES empleado(id); -- Conecta el resumen de asistencia con el empleado
ALTER TABLE asistencia_diaria ADD FOREIGN KEY (estatus_id) REFERENCES estatus_asistencia(id); -- Conecta la asistencia diaria con su estatus final
ALTER TABLE ausencia ADD FOREIGN KEY (empleado_id) REFERENCES empleado(id); -- Conecta el permiso solicitado con el empleado
ALTER TABLE ausencia ADD FOREIGN KEY (tipo_ausencia_id) REFERENCES tipo_ausencia(id); -- Conecta la ausencia con su tipo (reposo, etc.)
ALTER TABLE ausencia ADD FOREIGN KEY (aprobado_por_usuario_id) REFERENCES usuario(id); -- Conecta la ausencia con el usuario que la aprobó

-- ==========================================
-- DATOS DE EJEMPLO (Datos Semilla)
-- ==========================================

INSERT INTO rol (id, nombre_rol) VALUES (1, 'Superadmin'), (2, 'Admin'), (3, 'User'); -- Inserta los tres roles del sistema
INSERT INTO cargo (id, nombre_cargo) VALUES (1, 'Administrativo'), (2, 'Docente'), (3, 'Obrero'); -- Inserta los tres cargos básicos
INSERT INTO horario (id, nombre_horario, hora_entrada_teorica, hora_salida_teorica) VALUES (1, 'Mañana', '07:00:00', '13:00:00'), (2, 'Tarde', '13:00:00', '18:00:00'), (3, 'Mixto', '08:00:00', '16:00:00'); -- Inserta los turnos predefinidos
INSERT INTO estatus_asistencia (id, nombre_estatus) VALUES (1, 'A Tiempo'), (2, 'Retrasado'), (3, 'Inasistente'); -- Inserta las calificaciones de asistencia
INSERT INTO tipo_ausencia (id, nombre_tipo) VALUES (1, 'Justificativo'), (2, 'Permiso'), (3, 'Reposo'), (4, 'Falta Injustificada'); -- Inserta los tipos de inasistencias