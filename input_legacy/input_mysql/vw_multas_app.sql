-- gappsdb — vista ancha al molde del Excel / fact
--
-- El usuario modeló T_MVC_* a partir de:
--   F2 CAGR  «1) Multas coercitivas»  48 cols  (sede)
--   F1 OD    «5) Multas Coercitivas»  32 cols  (subconjunto de F2)
-- Este SELECT usa los CÓDIGOS del Excel (fila 3), en el mismo orden que F2.
-- 1 fila = 1 multa (NU_IDMC). 1:N descargos/análisis/cobranza → último id.
--
-- Excel F2                          MySQL                                      Fact
-- COD_MA                            MEDIDAS_MED.TX_CODMEDIDA                   COD_MA
-- COD_PROY_MC                       INFORMACIONMULTA.TX_CODPROYMC              COD_PROY_MC
-- JEFE                              INFORMACIONMULTA.TX_JEFEEQUIPO             JEFE
-- ETA_REG_PROY_MC                   INFORMACIONMULTA.TX_ESTADOPROYECTO         ETA_REG_PROY_MC
-- N_PROY_MC                         INFORMACIONMULTA.NU_N_PROYMC               N_PROY_MC
-- COORD                             INFORMACIONMULTA.TX_COORDINACION           COORD (vía dim)
-- ADM                               T_MAP_ADMINISTRADO.TX_NOM_ADMINISTRADO     ADMINISTRADO
-- UF                                T_MAP_UNIDAD_FISCALIZABLE.TX_UNIDAD…       UF
-- EXP_INF_INCUMP                    VERIFICACION_MED.EXP_VERIFICACION          NUMERO_EXPEDIENTE
-- N_CARTA_DCG / FN_MC / F_VENC_DCG  DESCARGOS_MC                               N_CARTA_DCG / F_NOTIF_DCG / F_VENC_DCG
-- PRESENT_DCG_ADM                   DESCARGOS_MC.FG_PRESENTODCG (0/1→NO/SI)    PRESENTO_DESCARGOS
-- F_RPTA_ADM / DOC_SIGED            DESCARGOS_MC                               F_RPTA_ADM / DOC_SIGED_DESCARGOS
-- EST_DCG                           DESCARGOS_MC.FG_ESTADODCG (sin catálogo)   (fuera del fact)
-- F_INIC_ANALISIS … AMERIT_MC       ANALISISDESCARGOS_MC + catálogo A_MC       mismas fechas / AMERITA_MC
-- N_DOC_NO_AMERIT … MOTIVO          DOCNOAMERITAMC_MC                          MOTIVO_NO_AMERIT
-- EXP_RES_MC / N_RES_MC / fechas    INFORMACIONMULTA_MC                        EXP_RES_MC / N_RES_MC / F_*
-- MULTA_UIT / MULTA_S               MULTACOERCITIVA.NU_MONTOMCUIT/S            MONTO_UIT / MONTO_S
-- RECORD_SEG … EXP_SIGED_DOC        MULTACOERCITIVA_MC                         RECORD_SEG / F_VERIF_POST_MC / DOC_VERIF_MC
-- ESTADO_MC                         FG_ESTADOMULTA; cat EST_MC si existe       ESTADO_MC_TXT
-- F_PAGO / MEMO_EF / F_REMIS / SIGED COBRANZA_MC                               F_PAGO / MEMO_EF / F_REMISION_MEMO / SIGED
-- ESTADO_PAGO_MC                    no hay columna en la app                   ESTADO_PAGO_TXT
-- AUX_* / URESOL_*                  réplica Excel (formulas, no hay tabla)     —
-- CUM / CAM                         MULTACOERCITIVA.TX_IDCUM / TX_IDCAM        CUM / CAM (en enrich = SISUD)
--
-- AUX_* y URESOL_* en el Excel eran fórmulas. Aquí se replican con N_RES_MC / COD_MA.
-- TX_ESTADOPROYECTO no tiene catálogo MC; se deja el código (1/3/4).
-- gappsdb.VW_MULTA_COERCITIVA es un dump SISUD (541 filas), no esta vista.

SELECT
    -- ===== CÓDIGOS / ESTADO / INF. GENERAL (F2, no están en F1 OD) =====
    md.TX_CODMEDIDA                         AS COD_MA,
    i.TX_CODPROYMC                          AS COD_PROY_MC,
    i.TX_JEFEEQUIPO                         AS JEFE,
    i.TX_ESTADOPROYECTO                     AS ETA_REG_PROY_MC,
    i.NU_N_PROYMC                           AS N_PROY_MC,
    UPPER(i.TX_COORDINACION)                AS COORD,
    adm.TX_NOM_ADMINISTRADO                 AS ADM,
    uf.TX_UNIDADFISCALIZABLE                AS UF,

    -- ===== DESCARGOS (F1 + F2) =====
    v.EXP_VERIFICACION                      AS EXP_INF_INCUMP,
    d.TX_N_CARTA_DCG                        AS N_CARTA_DCG,
    d.FE_FN_CARTA_DCG                       AS FN_MC,
    d.FE_FV_CARTA_DCG                       AS F_VENC_DCG,
    CASE d.FG_PRESENTODCG
        WHEN '1' THEN 'SI'
        WHEN '0' THEN 'NO'
    END                                     AS PRESENT_DCG_ADM,
    d.FE_FERPTADCG                          AS F_RPTA_ADM,
    NULLIF(d.TX_EXPSIGED, '')               AS DOC_SIGED,
    d.FG_ESTADODCG                          AS EST_DCG,

    -- ===== ANÁLISIS =====
    a.FE_F_INIC_ANALISIS                    AS F_INIC_ANALISIS,
    CASE a.TX_REQ_VERIF_CAMPO
        WHEN '1' THEN 'SI'
        WHEN '0' THEN 'NO'
    END                                     AS REQ_VERIF_CAMPO,
    a.FE_F_VERIF_CAMPO                      AS F_VERIF_CAMPO,
    a.FE_F_FIN_ANALISIS                     AS F_FIN_ANALISIS,
    COALESCE(cat_amerita.TX_DETALLE_CAT, a.FG_RESULTADO)
                                            AS AMERIT_MC,
    na.TX_N_DOC_NO_AMERIT                   AS N_DOC_NO_AMERIT,
    na.FE_F_DOC_NO_AMERIT                   AS F_DOC_NO_AMERIT,
    na.TX_MOTIVO_NO_AMERIT                  AS MOTIVO_NO_AMERIT,

    -- ===== RESULTADO / ETAPA REGISTRO (F2) =====
    a.TX_SUSTENTO                           AS RESULT_PROY_MC,
    COALESCE(cat_acc.TX_DETALLE_CAT, et_act.FG_ETAPA)
                                            AS ETA_REG_MC,

    -- ===== IMPOSICIÓN =====
    i.TX_EXP_RES_MC                         AS EXP_RES_MC,
    i.TX_N_RES_MC                           AS N_RES_MC,
    i.FE_F_FIRMA_RES_MC                     AS F_FIRMA_RES_MC,
    i.FE_FN_RES_MC                          AS FN_RES_MC,
    i.FE_F_VENC_MC                          AS F_VENC_MC,
    m.NU_MONTOMCUIT                         AS MULTA_UIT,
    m.NU_MONTOMCS                           AS MULTA_S,

    -- ===== SEGUIMIENTO =====
    m.TX_RECORD_SEG                         AS RECORD_SEG,
    m.FE_F_VERIF_POST_MC                    AS F_VERIF_POST_MC,
    m.TX_DOC_VERIF_MC                       AS DOC_VERIF_MC,
    m.TX_EXP_SIGED_DOC                      AS EXP_SIGED_DOC,

    -- ===== COBRANZA =====
    COALESCE(cat_estmc.TX_DETALLE_CAT, m.FG_ESTADOMULTA)
                                            AS ESTADO_MC,
    c.FE_F_PAGO                             AS F_PAGO,
    c.TX_MEMO_EC                            AS MEMO_EF,
    c.FE_F_REMIS                            AS F_REMIS,
    c.TX_EXPEDIENTESIGED                    AS SIGED,
    NULL                                    AS ESTADO_PAGO_MC,

    -- ===== AUXILIARES Excel (formulas, se replican) =====
    CASE WHEN et_act.FG_ULTI_REG = '1' THEN 0 ELSE 1 END
                                            AS AUX_FIN_MC,
    md.TX_CODMEDIDA                         AS AUX_COD_MA,
    COALESCE(cat_estmc.TX_DETALLE_CAT, m.FG_ESTADOMULTA)
                                            AS AUX_EST_MC,
    i.TX_N_RES_MC                           AS URESOL_MC,
    i.FE_FN_RES_MC                          AS FN_URESOL_MC,

    -- ===== extras que el Excel no tiene y el fact sí (CUM/CAM, medida) =====
    m.TX_IDCUM                              AS CUM,
    m.TX_IDCAM                              AS CAM,
    md.TX_DESCRIPCIONMEDIDA                 AS MEDIDA_ADMINISTRATIVA,
    adm.TX_COD_ADM                          AS COD_ADM,
    uf.TX_CODUF                             AS COD_UF,
    ig.TX_EXPEDIENTE                        AS EXP_MEDIDA,
    ig.TX_SECTOR                            AS SECTOR,
    m.NU_IDMC,
    'GAPPS'                                 AS FUENTE_ORIGEN
FROM T_MVC_MULTACOERCITIVA_MC m
LEFT JOIN T_MVC_INFORMACIONMULTA_MC i
       ON i.NU_IDINFORMACIONMC = m.NU_IDINFORMACIONMC
LEFT JOIN T_MVC_VERIFICACION_MED v
       ON v.NU_IDVERIFICACION = m.NU_IDVERIFICACIONMA
LEFT JOIN T_MVC_MEDIDAS_MED md
       ON md.NU_IDMEDIDA = v.NU_IDCODMEDIDA
LEFT JOIN T_MVC_INFORMACIONMEDIDAS_MED ig
       ON ig.NU_IDMEDIDAS = md.NU_ID_MEDIDAS
LEFT JOIN T_MVC_ADM_UF_MED au
       ON au.NU_IDADMUF = md.NU_IDADMUF
LEFT JOIN T_MAP_ADMINISTRADO adm
       ON adm.NU_ID_ADMINISTRADO = au.NU_ID_ADM
LEFT JOIN T_MAP_UNIDAD_FISCALIZABLE uf
       ON uf.NU_ID_UNIDAD_FISC = au.NU_IDUF
LEFT JOIN (
    SELECT d1.*
    FROM T_MVC_DESCARGOS_MC d1
    INNER JOIN (
        SELECT NU_IDMC, MAX(NU_IDDESCARGOS) AS ID
        FROM T_MVC_DESCARGOS_MC
        GROUP BY NU_IDMC
    ) dx ON dx.ID = d1.NU_IDDESCARGOS
) d ON d.NU_IDMC = m.NU_IDMC
LEFT JOIN (
    SELECT a1.*
    FROM T_MVC_ANALISISDESCARGOS_MC a1
    INNER JOIN (
        SELECT NU_IDMC, MAX(NU_IDANLISIS) AS ID
        FROM T_MVC_ANALISISDESCARGOS_MC
        GROUP BY NU_IDMC
    ) ax ON ax.ID = a1.NU_IDANLISIS
) a ON a.NU_IDMC = m.NU_IDMC
LEFT JOIN T_MAP_CATALOGO cat_amerita
       ON cat_amerita.TX_TIPO_CAT = 'A_MC'
      AND cat_amerita.TX_CODIGO_CAT = a.FG_RESULTADO
LEFT JOIN T_MAP_CATALOGO cat_estmc
       ON cat_estmc.TX_TIPO_CAT = 'EST_MC'
      AND cat_estmc.TX_CODIGO_CAT = m.FG_ESTADOMULTA
LEFT JOIN T_MVC_DOCNOAMERITAMC_MC na
       ON na.NU_IDANALISISDESCARGOS = a.NU_IDANLISIS
LEFT JOIN (
    SELECT c1.*
    FROM T_MVC_COBRANZA_MC c1
    INNER JOIN (
        SELECT NU_IDMC, MAX(NU_IDCOBRANZA) AS ID
        FROM T_MVC_COBRANZA_MC
        GROUP BY NU_IDMC
    ) cx ON cx.ID = c1.NU_IDCOBRANZA
) c ON c.NU_IDMC = m.NU_IDMC
LEFT JOIN (
    SELECT e1.*
    FROM T_MVC_ETAPASPROYECTO_MC e1
    INNER JOIN (
        SELECT NU_IDPROYECTO, MAX(NU_ID_ACT_ETAPA) AS ID
        FROM T_MVC_ETAPASPROYECTO_MC
        GROUP BY NU_IDPROYECTO
    ) ex ON ex.ID = e1.NU_ID_ACT_ETAPA
) et_act ON et_act.NU_IDPROYECTO = i.NU_IDINFORMACIONMC
LEFT JOIN T_MAP_CATALOGO cat_acc
       ON cat_acc.TX_TIPO_CAT = et_act.FG_ETAPA
      AND cat_acc.TX_CODIGO_CAT = NULLIF(et_act.FG_ACCION, '')
ORDER BY m.NU_IDMC
;


-- ---------------------------------------------------------------------------
-- Hoja Excel «2) Etapas» (1:N; no mezclar con el SELECT de arriba)
-- ---------------------------------------------------------------------------
-- SELECT
--     i.TX_CODPROYMC                          AS COD_PROY_MC,
--     e.NU_IDACTIVIDAD                        AS NRO_ETAPA_MC,
--     NULL                                    AS PERF_ENCARG_MC,
--     COALESCE(cat.TX_DETALLE_CAT, e.FG_ACCION) AS ACCION_MC,
--     e.NU_IDRESPONSABLE                      AS ENCARGADO_MC,
--     e.FE_F_ASIGNACION                       AS F_ASIG_MC,
--     CASE
--         WHEN e.FE_F_FIN_ACT IS NOT NULL THEN 'TERMINADO'
--         ELSE 'EN PROCESO'
--     END                                     AS EST_ETAPA_MC,
--     COALESCE(cat_cf.TX_DETALLE_CAT, NULLIF(e.FG_CONFORMIDAD, ''))
--                                             AS CONFORMIDAD_MC,
--     e.FE_F_FIN_ACT                          AS F_ENT_DEV_MC,
--     DATEDIFF(e.FE_F_FIN_ACT, e.FE_F_ASIGNACION) AS T_ELAB_MC,
--     e.FG_ETAPA                              AS COD_ETAPA_MC,
--     CASE WHEN e.FG_ULTI_REG = '1' THEN 1 ELSE 0 END AS AUX_FIN_MC
-- FROM T_MVC_ETAPASPROYECTO_MC e
-- JOIN T_MVC_INFORMACIONMULTA_MC i
--   ON i.NU_IDINFORMACIONMC = e.NU_IDPROYECTO
-- LEFT JOIN T_MAP_CATALOGO cat
--   ON cat.TX_TIPO_CAT = e.FG_ETAPA
--  AND cat.TX_CODIGO_CAT = NULLIF(e.FG_ACCION, '')
-- LEFT JOIN T_MAP_CATALOGO cat_cf
--   ON cat_cf.TX_TIPO_CAT = 'ETAPA_MA_CONFORMIDAD'
--  AND cat_cf.TX_CODIGO_CAT = NULLIF(e.FG_CONFORMIDAD, '')
-- ORDER BY i.TX_CODPROYMC, e.NU_IDACTIVIDAD;
