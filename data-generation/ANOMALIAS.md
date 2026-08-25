# Anomalías intencionales de los datos sintéticos

## Objetivo

Los datos incluyen errores controlados para demostrar que el pipeline no asume que la fuente es perfecta. Las anomalías se conservan en Bronze para trazabilidad y posteriormente serán detectadas, tratadas y auditadas en Silver.

Estas anomalías de calidad son diferentes de una transacción sospechosa de negocio. El indicador `ind_sospechoso` se calculará en Silver comparando `vr_mov` con el promedio más tres desviaciones estándar del mismo cliente durante los 30 días anteriores.

## Patrones implementados

| Patrón | Configuración | Resultado detectado | Propósito |
|---|---:|---:|---|
| Movimientos duplicados | 0,3 % | 1.500 | Probar deduplicación e idempotencia. |
| Fechas fuera de rango | 0,2 % | 1.001 | Probar controles temporales. |
| Canal transaccional inválido | 0,3 % | 1.502 | Probar validación contra catálogos. |

Los conteos detectados en los dos últimos patrones pueden superar ligeramente la cantidad inicialmente alterada porque una fila anómala también puede quedar seleccionada entre los duplicados. Esta superposición es determinística debido a la semilla fija.

## 1. Movimientos duplicados

El generador replica filas completas de `TB_MOV_FINANCIEROS`, incluido `id_mov`.

Detección prevista:

```sql
SELECT id_mov, COUNT(*) AS cantidad
FROM TB_MOV_FINANCIEROS
GROUP BY id_mov
HAVING COUNT(*) > 1;
```

Tratamiento en Silver:

- conservar una sola fila mediante `ROW_NUMBER()`;
- usar `id_mov` como llave de comparación;
- enviar las copias descartadas a una zona de cuarentena;
- registrar la regla de calidad incumplida.

## 2. Fechas fuera del rango configurado

Una proporción de `fec_mov` se genera antes del 1 de agosto de 2025.

Detección prevista:

```sql
SELECT *
FROM TB_MOV_FINANCIEROS
WHERE fec_mov < '2025-08-01'
   OR fec_mov > '2026-08-24';
```

Tratamiento en Silver:

- marcar la fila como inválida para el periodo;
- conservarla en Bronze;
- excluirla de indicadores correspondientes al rango oficial;
- enviarla a cuarentena para análisis.

## 3. Canal transaccional inválido

Algunos movimientos reciben el valor `CANAL_INVALIDO` en `cod_canal`.

Detección prevista:

```sql
SELECT *
FROM TB_MOV_FINANCIEROS
WHERE cod_canal NOT IN
    ('APP', 'WEB', 'ATM', 'PSE', 'ACH', 'CORRESPONSAL', 'SUCURSAL');
```

Tratamiento en Silver:

- validar `cod_canal` contra el catálogo permitido;
- mapear el valor analítico a `DESCONOCIDO` cuando proceda;
- conservar el valor original para auditoría;
- registrar la fila en cuarentena.

## Valores nulos controlados

Se introduce aproximadamente 5 % de nulos en campos no críticos:

- `TB_CLIENTES_CORE.score_buro`;
- `TB_CLIENTES_CORE.canal_adquis`;
- `TB_MOV_FINANCIEROS.id_dispositivo`;
- `TB_OBLIGACIONES.calif_riesgo`;
- `TB_COMISIONES_LOG.tip_comision`.

Las llaves primarias y foráneas no reciben nulos.

## Evidencia

La ejecución completa detectó los tres patrones y superó 65 controles. Los resultados se encuentran en [`docs/evidencias/datos-sinteticos`](../docs/evidencias/datos-sinteticos/README.md).
