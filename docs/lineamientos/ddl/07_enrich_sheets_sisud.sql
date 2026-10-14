--------------------------------------------------------------------------------
-- 07_enrich_sheets_sisud.sql
-- DEPRECADO (linux_v2): el enrich vive en logica/dwh/enrich.py.
-- Este SQL no se ejecuta en runtime. Se conserva como especificación histórica.
-- Tras DELETE+INSERT de DW_M_FACT_MC_CSEP / _OD / _SISUD:
-- arma DW_M_FACT_MULTA_COERCITIVA = (CSEP ∪ OD) LEFT JOIN SISUD
-- clave: resolución normalizada (sin ceros a la izquierda del correlativo) + MONTO_UIT.
-- Empates SISUD: primera fila por CUM/CAM (ROW_NUMBER).
-- Idempotente: DELETE hecho enriquecido + INSERT (DML → rollback si falla INSERT).
--------------------------------------------------------------------------------

DELETE FROM DW_M_FACT_MULTA_COERCITIVA;

INSERT INTO DW_M_FACT_MULTA_COERCITIVA (
    COD_MA, COD_PROY_MC, NUMERO_EXPEDIENTE, EXP_RES_MC, N_RES_MC,
    CUM, CAM, NUMERO_REGISTRO_SIGED,
    ID_ADMINISTRADO, ID_ORGANO, ID_MATERIA,
    ID_ESTADO_RESOLUCION, ID_ESTADO_MULTA, ID_ESTADO_PAGO,
    ID_UIT, ID_OD, ID_FUENTE, ID_TIEMPO_FIRMA,
    F_NOTIF_DCG, F_VENC_DCG, F_RPTA_ADM, F_INIC_ANALISIS, F_FIN_ANALISIS,
    F_FIRMA_RES_MC, F_NOTIF_RES_MC, F_VENC_MC, F_VERIF_POST_MC, F_PAGO, F_REMISION_MEMO,
    PRESENTO_DESCARGOS, AMERITA_MC, REQUIERE_VERIF_CAMPO,
    MEDIDA_ADMINISTRATIVA, MEMO_EF, SIGED, DOC_VERIF_MC,
    MONTO_UIT, VALOR_UIT_APLICADO, MONTO_S, MONTO_S_CALC, MONTO_MULTA_REC, MONTO_MULTA_TFA,
    DIAS_NOTIF_A_RESPUESTA, DIAS_ANALISIS, DIAS_NOTIF_A_FIRMA,
    DIAS_FIRMA_A_VENC, DIAS_VENC_A_PAGO, DIAS_RESOL_A_VERIF,
    FLAG_PRESENTO_DCG, FLAG_AMERITA_MC, FLAG_PAGADA, FLAG_EJECUCION_FORZOSA, FLAG_CUMPLIO_VERIF,
    JEFE, UF, N_PROY_MC, ETA_REG_PROY_MC, ETA_REG_MC, RESULT_PROY_MC,
    ESTADO_MC_TXT, ESTADO_PAGO_TXT,
    FECHA_CARGA
)
WITH
norm AS (
    /* Quita ceros a la izquierda del primer bloque numérico: 0153 ≡ 00153 ≡ 153 */
    SELECT
        s.*,
        CASE
            WHEN s.N_RES_MC IS NULL OR TRIM(s.N_RES_MC) IS NULL THEN NULL
            WHEN s.MONTO_UIT IS NULL THEN NULL
            ELSE REGEXP_REPLACE(UPPER(REPLACE(TRIM(s.N_RES_MC), ' ', '')), '^0+', '')
                 || '|' || TO_CHAR(ROUND(s.MONTO_UIT, 4), 'FM999999990.0000')
        END AS CLAVE_JOIN
    FROM (
        SELECT * FROM DW_M_FACT_MC_CSEP
        UNION ALL
        SELECT * FROM DW_M_FACT_MC_OD
    ) s
),
sisud_dedup AS (
    SELECT *
    FROM (
        SELECT
            t.*,
            CASE
                WHEN t.N_RES_MC IS NULL OR TRIM(t.N_RES_MC) IS NULL THEN NULL
                WHEN t.MONTO_UIT IS NULL THEN NULL
                ELSE REGEXP_REPLACE(UPPER(REPLACE(TRIM(t.N_RES_MC), ' ', '')), '^0+', '')
                     || '|' || TO_CHAR(ROUND(t.MONTO_UIT, 4), 'FM999999990.0000')
            END AS CLAVE_JOIN,
            ROW_NUMBER() OVER (
                PARTITION BY
                    CASE
                        WHEN t.N_RES_MC IS NULL OR TRIM(t.N_RES_MC) IS NULL THEN NULL
                        WHEN t.MONTO_UIT IS NULL THEN NULL
                        ELSE REGEXP_REPLACE(UPPER(REPLACE(TRIM(t.N_RES_MC), ' ', '')), '^0+', '')
                             || '|' || TO_CHAR(ROUND(t.MONTO_UIT, 4), 'FM999999990.0000')
                    END
                ORDER BY t.CUM NULLS LAST, t.CAM NULLS LAST, t.ID_MC
            ) AS RN
        FROM DW_M_FACT_MC_SISUD t
    ) z
    WHERE z.RN = 1 AND z.CLAVE_JOIN IS NOT NULL
)
SELECT
    n.COD_MA,
    n.COD_PROY_MC,
    n.NUMERO_EXPEDIENTE,
    n.EXP_RES_MC,
    n.N_RES_MC,
    CASE WHEN n.CUM IS NULL OR LENGTH(TRIM(n.CUM)) = 0 THEN d.CUM ELSE n.CUM END AS CUM,
    CASE WHEN n.CAM IS NULL OR LENGTH(TRIM(n.CAM)) = 0 THEN d.CAM ELSE n.CAM END AS CAM,
    CASE
        WHEN n.NUMERO_REGISTRO_SIGED IS NULL OR LENGTH(TRIM(n.NUMERO_REGISTRO_SIGED)) = 0
        THEN d.NUMERO_REGISTRO_SIGED
        ELSE n.NUMERO_REGISTRO_SIGED
    END AS NUMERO_REGISTRO_SIGED,
    n.ID_ADMINISTRADO,
    n.ID_ORGANO,
    n.ID_MATERIA,
    n.ID_ESTADO_RESOLUCION,
    n.ID_ESTADO_MULTA,
    n.ID_ESTADO_PAGO,
    n.ID_UIT,
    n.ID_OD,
    n.ID_FUENTE,
    n.ID_TIEMPO_FIRMA,
    n.F_NOTIF_DCG,
    n.F_VENC_DCG,
    n.F_RPTA_ADM,
    n.F_INIC_ANALISIS,
    n.F_FIN_ANALISIS,
    n.F_FIRMA_RES_MC,
    n.F_NOTIF_RES_MC,
    n.F_VENC_MC,
    n.F_VERIF_POST_MC,
    n.F_PAGO,
    n.F_REMISION_MEMO,
    n.PRESENTO_DESCARGOS,
    n.AMERITA_MC,
    n.REQUIERE_VERIF_CAMPO,
    n.MEDIDA_ADMINISTRATIVA,
    n.MEMO_EF,
    n.SIGED,
    n.DOC_VERIF_MC,
    n.MONTO_UIT,
    n.VALOR_UIT_APLICADO,
    n.MONTO_S,
    n.MONTO_S_CALC,
    n.MONTO_MULTA_REC,
    n.MONTO_MULTA_TFA,
    n.DIAS_NOTIF_A_RESPUESTA,
    n.DIAS_ANALISIS,
    n.DIAS_NOTIF_A_FIRMA,
    n.DIAS_FIRMA_A_VENC,
    n.DIAS_VENC_A_PAGO,
    n.DIAS_RESOL_A_VERIF,
    n.FLAG_PRESENTO_DCG,
    n.FLAG_AMERITA_MC,
    n.FLAG_PAGADA,
    n.FLAG_EJECUCION_FORZOSA,
    n.FLAG_CUMPLIO_VERIF,
    n.JEFE,
    n.UF,
    n.N_PROY_MC,
    n.ETA_REG_PROY_MC,
    n.ETA_REG_MC,
    n.RESULT_PROY_MC,
    n.ESTADO_MC_TXT,
    n.ESTADO_PAGO_TXT,
    n.FECHA_CARGA
FROM norm n
LEFT JOIN sisud_dedup d ON d.CLAVE_JOIN = n.CLAVE_JOIN;

COMMIT;
