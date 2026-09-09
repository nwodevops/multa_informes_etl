--------------------------------------------------------------------------------
-- 06_vistas.sql
-- Vistas de reporte: evidencia 1:1 + hecho enriquecido (Sheets←SISUD).
-- Idempotente: CREATE OR REPLACE VIEW.
--------------------------------------------------------------------------------

CREATE OR REPLACE VIEW VW_MC_CSEP AS
SELECT
    f.*,
    fu.CODIGO   AS COD_FUENTE,
    fu.NOMBRE   AS NOMBRE_FUENTE,
    fu.FAMILIA_TDR
FROM MI_FACT_MC_CSEP f
LEFT JOIN MI_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE;

CREATE OR REPLACE VIEW VW_MC_OD AS
SELECT
    f.*,
    fu.CODIGO   AS COD_FUENTE,
    fu.NOMBRE   AS NOMBRE_FUENTE,
    fu.FAMILIA_TDR
FROM MI_FACT_MC_OD f
LEFT JOIN MI_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE;

CREATE OR REPLACE VIEW VW_MC_SISUD AS
SELECT
    f.*,
    fu.CODIGO   AS COD_FUENTE,
    fu.NOMBRE   AS NOMBRE_FUENTE,
    fu.FAMILIA_TDR
FROM MI_FACT_MC_SISUD f
LEFT JOIN MI_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE;

-- Negocio: Sheets enriquecidos con CUM/CAM de SISUD
CREATE OR REPLACE VIEW VW_MC_ENRIQUECIDA AS
SELECT
    f.*,
    fu.CODIGO   AS COD_FUENTE,
    fu.NOMBRE   AS NOMBRE_FUENTE,
    fu.FAMILIA_TDR
FROM MI_FACT_MULTA_COERCITIVA f
LEFT JOIN MI_DIM_FUENTE_REGISTRO fu ON fu.ID_FUENTE = f.ID_FUENTE;

COMMIT;
