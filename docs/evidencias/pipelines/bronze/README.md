# Evidencias de la ingesta Bronze

Esta carpeta contiene las evidencias de configuración, ejecución y validación de la canalización incremental desde Azure SQL Database hacia la capa Bronze de Azure Data Lake Storage Gen2.

## Evidencias disponibles

### 1. Configuración incremental

![Configuración incremental de las seis tablas](./01-configuracion-incremental-seis-tablas.png)

Configuración de las seis tablas fuente y de las estrategias Change Tracking y watermark.

### 2. Controles de Bronze

![Controles Bronze verificados](./02-controles-bronze-verificados.png)

Validación de las configuraciones, tablas con Change Tracking y procedimientos almacenados de control.

### 3. Servicios vinculados

![Servicios vinculados de Azure Data Factory](./03-servicios-vinculados-adf.png)

Servicios vinculados para Azure SQL Database, Azure Key Vault y Azure Data Lake Storage Gen2.

### 4. Ejecución inicial

![Ejecución inicial Bronze exitosa](./04-ejecucion-inicial-bronze-exitosa.png)

Ejecución completa de las seis tablas con todas las actividades en estado correcto.

### 5. Métricas de movimientos

![Métricas de movimientos en Bronze](./05-metricas-movimientos-bronze.png)

Resultado de la copia de 500.000 movimientos financieros desde Azure SQL hacia ADLS Gen2.

### 6. Directorios de las tablas

![Directorios de las tablas en Bronze](./06-directorios-tablas-bronze.png)

Directorios creados para las seis tablas fuente dentro del contenedor Bronze.

### 7. Partición Parquet de movimientos

![Partición Parquet de movimientos](./07-particion-parquet-movimientos-bronze.png)

Archivo Parquet de movimientos almacenado mediante particiones de año, mes y día.

### 8. Log de la ejecución inicial

![Log de ejecución inicial](./08-log-ejecucion-inicial-bronze.png)

Conteos, métricas, rutas y estados registrados para la carga inicial de 620.250 filas.

### 9. Cambios incrementales controlados

![Cambios controlados para la prueba incremental](./09-cambios-controlados-prueba-incremental.png)

Modificación de un cliente e inserción de un movimiento utilizadas para validar la extracción incremental.

### 10. Ejecución incremental

![Ejecución incremental Bronze](./10-ejecucion-incremental-bronze.png)

Segunda ejecución de la canalización, finalizada correctamente para las seis tablas.

### 11. Log de la ejecución incremental

![Log de ejecución incremental](./11-log-ejecucion-incremental-bronze.png)

La ejecución incremental procesó dos registros: un cliente modificado y un movimiento nuevo. Las demás tablas registraron cero filas nuevas.

> Las capturas fueron seleccionadas para evidenciar la configuración y los resultados sin publicar contraseñas, secretos ni valores sensibles.
