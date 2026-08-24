# Convenciones de nombres y etiquetas
En este archivo se definirán los nombres consistentes para identificar el tipo de recurso, la plataforma, el entorno y la región en la que se encuentra desplegado el proyecto, dicha convención está basada en las recomendaciones del Cloud Adoption Framework de Microsoft Azure.

## Componentes de los nombres

| Componente | Valor | Descripción |
|---|---|---|
| Proyecto | `finbank` | Plataforma de datos de FinBank |
| Entorno | `dev` | Entorno de desarrollo |
| Región de Azure | `eastus` | Región seleccionada para el despliegue |
| Código de región | `eus` | Abreviatura utilizada en los nombres |
| Sufijo | Cinco caracteres | Valor generado por Terraform para garantizar unicidad |

El patrón general será:

```text
<tipo>-<proyecto>-<entorno>-<region>-<sufijo>