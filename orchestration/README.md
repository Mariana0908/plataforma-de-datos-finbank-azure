# Orquestación

Esta carpeta contiene las definiciones del pipeline principal en Azure Data Factory.

El flujo esperado es:

`Trigger → Source Extraction → Bronze → Silver → Gold → Quality Checks → Notification`

La orquestación incluirá dependencias explícitas, ejecución diaria, reintentos,
timeouts, manejo de errores, monitoreo y notificaciones de éxito o fallo.

> Estado: pendiente de implementación.