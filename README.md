# Plataforma de Datos End-to-End para FinBank

> **Estado del proyecto:** En desarrollo
> **Autora:** Mariana Ospina Henao
> **Perfil:** Data Engineer
> **Fecha de inicio:** Agosto de 2026

## 1. Sector y plataforma seleccionados
### Escenario de negocio:
**Escenario A —Banca y Servicios Financieros**, correspondiente a **FinBank S.A.**, un banco digital con presencia en Colombia, México, Perú, Chile y Argentina.

El escenario fue seleccionado por la relevancia y familiaridad de sus necesidades de negocio, enfocadas en: consolidación de fuentes transaccionales, monitoreo de cartera, detección de operaciones sospechosas, cálculo de rentabilidad por cliente y generación de información confiable para equipos de riesgo, fraude y áreas comerciales.

### Plataforma cloud selccionada:

**Microsoft Azure**.

Se elige esta alternativa porque el servicio Cloud de Azure es el que se utiliza como requerimiento técnico en la vacante, además permite implementar los componentes de almacenamiento, procesamiento, seguridad, monitoreo y consumo analitico que se requieren para darle solución al reto. La arquitectura propuesta utilizará principalmente:

- Azure SQL Database como fuente relacional.
- Azure Data Factory para ingesta y orquestación.
- Azure Data Lake Storage Gen2 para las capas Bronze, Silver y Gold.
- Azure Databricks y PySpark para transformación y calidad de datos.
- Azure Key Vault para administración de secretos.
- Microsoft Entra ID y Azure RBAC para identidades y permisos.
- Log Analytics y Azure Monitor para observabilidad y alertas.
- Power BI para el consumo analítico de la capa Gold.


### Infraestructura como código (IaC)

**Terraform**.

Se escogió Terraform porque permite:

...(completar)

La solución soportará como mínimo los ambientes `dev` y `prod`

## 2. Contexto del problema

FinBank se encarga de procesar información de clientes, productos, movimientos financieros,
obligaciones, sucursales y comisiones mediante fuentes transaccionales separadas.

Por ahora se parte de procesos manuales para generar retrasos, incosistencias y riesgo operativo, de dichos procesos dependen los equipos de Riesgo Crediticio y Prevención de Fraude, es por ello que la plataforma propuesta unificará estas fuentes en un pipeline reproducible, monitoreado y seguro.

## 3. Objetivo general

Diseñar e implementar una plataforma de datos end-to-end sobre Microsoft Azure que ingeste, limpie, transforme y publique información bancaria mediante una arquitectura Medallion, produciendo datos confiables y optimizados para análisis de riesgo, detección de fraude, rentabilidad de clientes y reportería regulatoria.

## 4. Necesidades de negocio

La solución debe permitir:

- calcular diariamente indicadores de mora por cliente, producto y región.
- identificar transacciones con comportamiento atípico.
- calcular mensualmente el Customer Lifetime Value de cada cliente.
- generar insumos para reportes regulatorios.
- construir una vista consolidada del cliente para decisiones comerciales.

## 5. Alcance técnico

1. Generación reproducible de datos sintéticos.
2. Modelo relacional y carga en Azure SQL Database.
3. Aprovisionamiento de infraestructura con Terraform.
4. Ingesta incremental hacia Bronze.
5. Limpieza, calidad, seguridad y enriquecimiento en Silver.
6. Modelo dimensional y reglas de negocio en Gold.
7. Orquestación mediante Azure Data Factory.
8. Gobierno, roles, auditoría y protección de información sensible.
9. Monitoreo y notificaciones operacionales.

### 5.1 milla extra
10. Se decide realizar un Dashboard ejecutivo en Power BI como valor adicional.

## 6. Estructura del repositorio

.
 -data-generation/   # Generación y carga de datos sintéticos
 -docs/              # Arquitectura, modelos, catálogo, linaje y evidencias
 -infra/             # Infraestructura como código con Terraform
 -orchestration/     # Definiciones de Azure Data Factory
 -pipelines/         # Procesamiento Bronze, Silver, Gold y calidad
 -.gitignore         # Archivos excluidos del control de versiones
 -CHANGELOG.md       # Historial de cambios significativos
 -README.md          # Documentación principal del proyecto

## 7. Estrategia de versionado
Se decide utilizar Github flow (rama main y features) para mantener la rama main estable y poder separar cada cambio relevante en una rama independiente, se la utilizarán las siguientes convenciones:

- main: contiene únicamente cambios estables y revisados.
- feat/*: desarrollo de nuevas funcionalidades.
- fix/*: corrección de errores.
- docs/*: cambios de documentación.
- test/*: incorporación o modificación de pruebas.
- chore/*: configuración y mantenimiento.
- ci/*: automatización de integración y despliegue continuo.
En este proyecto puntual, no se utiliza una rama permanente develop porque el proyecto es desarrollado por una sola persona y tiene un alcance delimitado, es por ello que se elige esta alternativa, ya que permite crear las rmas de trabajo desde main e integrarlas mediante Pull requests.

### Flujo de trabajo

1. Actualizar la rama `main`.
2. Crear una rama con un nombre descriptivo.
3. Implementar y validar el cambio.
4. Crear commits pequeños y comprensibles.
5. Publicar la rama en GitHub.
6. Abrir un Pull Request hacia `main`.
7. Revisar los cambios y completar las validaciones.
8. Fusionar el Pull Request.
9. Eliminar la rama de trabajo.

### Convención de commits

Los commits siguen la estructura de:
tipo: descripción breve