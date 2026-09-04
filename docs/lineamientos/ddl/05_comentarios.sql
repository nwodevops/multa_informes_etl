--------------------------------------------------------------------------------
-- 05_comentarios.sql
-- Comentarios de tablas y columnas del modelo MI_* (Oracle REPOCSEP / APP).
-- Idempotente: COMMENT ON puede re-ejecutarse en cada corrida ETL.
-- Orden: después de 01–04. No requiere TABLESPACE.
--------------------------------------------------------------------------------

-- MI_DIM_TIEMPO
COMMENT ON TABLE MI_DIM_TIEMPO IS 'Dimensión calendario. Clave inteligente AAAAMMDD; miembro -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_DIM_TIEMPO.ID_TIEMPO IS 'Clave surrogate AAAAMMDD; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_DIM_TIEMPO.FECHA IS 'Fecha calendario del día.';
COMMENT ON COLUMN MI_DIM_TIEMPO.ANIO IS 'Año de la fecha.';
COMMENT ON COLUMN MI_DIM_TIEMPO.MES IS 'Mes numérico (1-12).';
COMMENT ON COLUMN MI_DIM_TIEMPO.NOMBRE_MES IS 'Nombre del mes en español.';
COMMENT ON COLUMN MI_DIM_TIEMPO.TRIMESTRE IS 'Trimestre calendario (1-4).';
COMMENT ON COLUMN MI_DIM_TIEMPO.SEMANA_ANIO IS 'Número de semana ISO del año.';
COMMENT ON COLUMN MI_DIM_TIEMPO.DIA IS 'Día del mes (1-31).';
COMMENT ON COLUMN MI_DIM_TIEMPO.DIA_SEMANA IS 'Nombre abreviado del día de la semana.';
COMMENT ON COLUMN MI_DIM_TIEMPO.NOMBRE_DIA IS 'Nombre completo del día de la semana.';
COMMENT ON COLUMN MI_DIM_TIEMPO.ES_FIN_DE_SEMANA IS '1 = sábado o domingo; 0 = día laborable.';
COMMENT ON COLUMN MI_DIM_TIEMPO.ES_FERIADO IS '1 = feriado nacional/regional; 0 = no feriado.';
COMMENT ON COLUMN MI_DIM_TIEMPO.ES_DIA_HABIL IS '1 = día hábil para cómputo de plazos; 0 = inhábil.';
COMMENT ON COLUMN MI_DIM_TIEMPO.DESCRIPCION_FERIADO IS 'Motivo del feriado cuando ES_FERIADO = 1.';

-- MI_DIM_ADMINISTRADO
COMMENT ON TABLE MI_DIM_ADMINISTRADO IS 'Dimensión de administrados fiscalizados (sujetos obligados).';
COMMENT ON COLUMN MI_DIM_ADMINISTRADO.ID_ADMINISTRADO IS 'Clave surrogate; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_DIM_ADMINISTRADO.COD_ADMINISTRADO IS 'Código único del administrado (ADM##### SISUD o NOM-razón social).';
COMMENT ON COLUMN MI_DIM_ADMINISTRADO.RAZON_SOCIAL IS 'Denominación legal del administrado.';
COMMENT ON COLUMN MI_DIM_ADMINISTRADO.RAZON_SOCIAL_NORM IS 'Razón social normalizada para búsqueda y cruce.';
COMMENT ON COLUMN MI_DIM_ADMINISTRADO.RUC IS 'Registro Único de Contribuyentes.';
COMMENT ON COLUMN MI_DIM_ADMINISTRADO.FECHA_ACTUALIZACION IS 'Fecha de última actualización del registro en el DW.';

-- MI_DIM_ORGANO_UNIDAD
COMMENT ON TABLE MI_DIM_ORGANO_UNIDAD IS 'Dimensión de órganos desconcentrados, coordinaciones y direcciones OEFA.';
COMMENT ON COLUMN MI_DIM_ORGANO_UNIDAD.ID_ORGANO IS 'Clave surrogate; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_DIM_ORGANO_UNIDAD.SIGLA IS 'Sigla del órgano (ej. DSIS-CRES, OD-LAM).';
COMMENT ON COLUMN MI_DIM_ORGANO_UNIDAD.NOMBRE IS 'Nombre descriptivo del órgano o unidad.';
COMMENT ON COLUMN MI_DIM_ORGANO_UNIDAD.TIPO IS 'Tipo: DIRECCION, COORDINACION, ODES u OD.';
COMMENT ON COLUMN MI_DIM_ORGANO_UNIDAD.ORGANO_SUPERIOR IS 'Sigla del órgano jerárquicamente superior.';
COMMENT ON COLUMN MI_DIM_ORGANO_UNIDAD.FECHA_ACTUALIZACION IS 'Fecha de última actualización del registro en el DW.';

-- MI_DIM_MATERIA_SUBSECTOR
COMMENT ON TABLE MI_DIM_MATERIA_SUBSECTOR IS 'Dimensión de materia o subsector ambiental (Hidrocarburos, Minería, etc.).';
COMMENT ON COLUMN MI_DIM_MATERIA_SUBSECTOR.ID_MATERIA IS 'Clave surrogate; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_DIM_MATERIA_SUBSECTOR.NOMBRE IS 'Nombre del subsector o materia ambiental.';
COMMENT ON COLUMN MI_DIM_MATERIA_SUBSECTOR.FECHA_ACTUALIZACION IS 'Fecha de última actualización del registro en el DW.';

-- MI_DIM_ESTADO
COMMENT ON TABLE MI_DIM_ESTADO IS 'Catálogo homologado de estados (resolución, multa, pago, etapa, descargos).';
COMMENT ON COLUMN MI_DIM_ESTADO.ID_ESTADO IS 'Clave surrogate; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_DIM_ESTADO.TIPO_ESTADO IS 'Dominio del estado: RESOLUCION, MULTA, PAGO, ETAPA o DESCARGOS.';
COMMENT ON COLUMN MI_DIM_ESTADO.CODIGO IS 'Código homologado del estado (ej. ACTIVO, PAGADO, PENDIENTE).';
COMMENT ON COLUMN MI_DIM_ESTADO.DESCRIPCION IS 'Descripción legible del estado.';
COMMENT ON COLUMN MI_DIM_ESTADO.GRUPO IS 'Agrupación analítica: VIGENTE, CERRADO, CUMPLIDO, INCUMPLIDO o PENDIENTE.';
COMMENT ON COLUMN MI_DIM_ESTADO.FECHA_ACTUALIZACION IS 'Fecha de última actualización del registro en el DW.';

-- MI_DIM_PARAMETRO_UIT
COMMENT ON TABLE MI_DIM_PARAMETRO_UIT IS 'Parámetro UIT anual (MEF) para conversión UIT ↔ soles.';
COMMENT ON COLUMN MI_DIM_PARAMETRO_UIT.ID_UIT IS 'Clave surrogate; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_DIM_PARAMETRO_UIT.ANIO IS 'Año fiscal al que aplica el valor UIT.';
COMMENT ON COLUMN MI_DIM_PARAMETRO_UIT.VALOR_UIT IS 'Valor oficial de la UIT en soles para el año.';
COMMENT ON COLUMN MI_DIM_PARAMETRO_UIT.FECHA_ACTUALIZACION IS 'Fecha de carga o actualización del parámetro.';

-- MI_FACT_MULTA_COERCITIVA
COMMENT ON TABLE MI_FACT_MULTA_COERCITIVA IS 'Hecho: una multa coercitiva integrando fuentes F1, F2, F4 y F5.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.ID_MC IS 'Clave surrogate del hecho multa.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.COD_MA IS 'Código de medida administrativa (clave natural Excel).';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.COD_PROY_MC IS 'Código del proyecto interno de elaboración de la multa (CAGR).';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.NUMERO_EXPEDIENTE IS 'Expediente administrativo; puente de amarre H9 entre fuentes de multa.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.EXP_RES_MC IS 'Expediente de la resolución de multa coercitiva.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.N_RES_MC IS 'Número de resolución de multa coercitiva.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.CUM IS 'Código único de medida (11 dígitos); conciliación F4/F5.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.CAM IS 'Código de acto de medida (13 caracteres); conciliación F4/F5.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.NUMERO_REGISTRO_SIGED IS 'Número de registro en SIGED del documento de resolución.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.ID_ADMINISTRADO IS 'FK a MI_DIM_ADMINISTRADO; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.ID_ORGANO IS 'FK a MI_DIM_ORGANO_UNIDAD; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.ID_MATERIA IS 'FK a MI_DIM_MATERIA_SUBSECTOR; -1 = NO ESPECIFICADO.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.ID_ESTADO_RESOLUCION IS 'FK a MI_DIM_ESTADO (TIPO_ESTADO=RESOLUCION).';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.ID_ESTADO_MULTA IS 'FK a MI_DIM_ESTADO (TIPO_ESTADO=MULTA).';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.ID_ESTADO_PAGO IS 'FK a MI_DIM_ESTADO (TIPO_ESTADO=PAGO).';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.ID_UIT IS 'FK a MI_DIM_PARAMETRO_UIT del año de la resolución.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_NOTIF_DCG IS 'Fecha de notificación de la carta de descargos.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_VENC_DCG IS 'Fecha de vencimiento para presentar descargos.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_RPTA_ADM IS 'Fecha de respuesta del administrado a los descargos.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_INIC_ANALISIS IS 'Fecha de inicio del análisis técnico-legal.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_FIN_ANALISIS IS 'Fecha de fin del análisis técnico-legal.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_FIRMA_RES_MC IS 'Fecha de firma de la resolución de multa coercitiva.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_NOTIF_RES_MC IS 'Fecha de notificación de la resolución al administrado.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_VENC_MC IS 'Fecha de vencimiento para el pago de la multa.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_VERIF_POST_MC IS 'Fecha de verificación posterior en campo.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_PAGO IS 'Fecha de pago efectivo de la multa.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.F_REMISION_MEMO IS 'Fecha de remisión del memo de ejecución forzosa.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.PRESENTO_DESCARGOS IS 'S/N: el administrado presentó descargos.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.AMERITA_MC IS 'S/N: el caso amerita imposición de multa coercitiva.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.REQUIERE_VERIF_CAMPO IS 'S/N: requiere verificación posterior en campo.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.MEDIDA_ADMINISTRATIVA IS 'Descripción de la medida administrativa asociada.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.MEMO_EF IS 'Identificador del memo de ejecución forzosa.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.SIGED IS 'Referencia SIGED del expediente o documento.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.DOC_VERIF_MC IS 'Documento de sustento de la verificación posterior.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.MONTO_UIT IS 'Monto de la multa expresado en UIT.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.VALOR_UIT_APLICADO IS 'Valor UIT en soles aplicado al cálculo.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.MONTO_S IS 'Monto en soles reportado por la fuente origen.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.MONTO_S_CALC IS 'Monto en soles recalculado: MONTO_UIT × VALOR_UIT_APLICADO.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.MONTO_MULTA_REC IS 'Monto de multa en etapa de reconsideración.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.MONTO_MULTA_TFA IS 'Monto de multa en etapa de trámite de apelación.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.DIAS_NOTIF_A_RESPUESTA IS 'Días hábiles entre notificación DCG y respuesta del administrado.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.DIAS_ANALISIS IS 'Días hábiles de duración del análisis.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.DIAS_NOTIF_A_FIRMA IS 'Días hábiles entre notificación DCG y firma de resolución (K2).';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.DIAS_FIRMA_A_VENC IS 'Días entre firma de resolución y vencimiento de pago.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.DIAS_VENC_A_PAGO IS 'Días entre vencimiento y pago efectivo.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.DIAS_RESOL_A_VERIF IS 'Días entre resolución y verificación posterior.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.FLAG_PRESENTO_DCG IS '1 = presentó descargos; 0 = no.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.FLAG_AMERITA_MC IS '1 = amerita multa coercitiva; 0 = no.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.FLAG_PAGADA IS '1 = multa pagada; 0 = pendiente o incumplida.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.FLAG_EJECUCION_FORZOSA IS '1 = en ejecución forzosa; 0 = no.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.FLAG_CUMPLIO_VERIF IS '1 = cumplió verificación posterior (K4); 0 = no.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.FUENTE_REGISTRO IS 'Fuente origen: LAM_OD, CAGR, GAPPS o SISUD_VW.';
COMMENT ON COLUMN MI_FACT_MULTA_COERCITIVA.FECHA_CARGA IS 'Fecha y hora de carga de la fila en el DW.';

-- MI_DET_ETAPA_MC
COMMENT ON TABLE MI_DET_ETAPA_MC IS 'Detalle de etapas del flujo interno de elaboración de la multa (F2-ET CAGR).';
COMMENT ON COLUMN MI_DET_ETAPA_MC.ID_ETAPA_MC IS 'Clave surrogate de la etapa.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.ID_MC IS 'FK al hecho multa padre; NULL si aún no amarra.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.COD_PROY_MC IS 'Código del proyecto de multa en CAGR.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.NRO_ETAPA IS 'Número secuencial de la etapa dentro del proyecto.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.ACCION IS 'Acción de la etapa: ELABORACION, REVISION, CALCULO o FIRMA.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.PERFIL_ENCARGADO IS 'Perfil o rol del encargado de la etapa.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.ENCARGADO IS 'Nombre del encargado de la etapa.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.F_ASIGNACION IS 'Fecha de asignación de la etapa.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.F_ENTREGA_DEV IS 'Fecha de entrega o devolución de la etapa.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.ESTADO_ETAPA IS 'Estado: TERMINADO o PENDIENTE.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.CONFORMIDAD IS 'Resultado de conformidad de la etapa.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.DIAS_ELABORACION IS 'Días hábiles de elaboración (MI_DIM_TIEMPO).';
COMMENT ON COLUMN MI_DET_ETAPA_MC.FUENTE_REGISTRO IS 'Fuente origen; valor fijo CAGR.';
COMMENT ON COLUMN MI_DET_ETAPA_MC.FECHA_CARGA IS 'Fecha y hora de carga de la fila en el DW.';

-- MI_DQ_HALLAZGO
COMMENT ON TABLE MI_DQ_HALLAZGO IS 'Bitácora de hallazgos de calidad de datos (reglas R01–R05); sin FK a hechos.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.ID_HALLAZGO IS 'Clave surrogate del hallazgo (identity).';
COMMENT ON COLUMN MI_DQ_HALLAZGO.ID_CARGA IS 'Identificador de la corrida ETL (YYYYMMDDHHMMSS).';
COMMENT ON COLUMN MI_DQ_HALLAZGO.FECHA_CARGA IS 'Fecha y hora de registro del hallazgo.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.REGLA_CODIGO IS 'Código de regla: R01 completitud, R02 formato, R03 temporal, R04 montos, R05 UIT.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.REGLA_DESCRIPCION IS 'Descripción legible de la regla violada.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.FUENTE_ORIGEN IS 'Fuente donde se detectó el defecto (F1–F5 o código STG).';
COMMENT ON COLUMN MI_DQ_HALLAZGO.TABLA_DESTINO IS 'Tabla del DW afectada, si aplica.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.REGISTRO_ID IS 'Clave natural del registro afectado (COD_MA, CUM+CAM, expediente, etc.).';
COMMENT ON COLUMN MI_DQ_HALLAZGO.CAMPO IS 'Nombre del campo con el defecto.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.VALOR_ENCONTRADO IS 'Valor observado que disparó el hallazgo.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.SEVERIDAD IS 'CRITICA o ADVERTENCIA.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.ESTADO IS 'PENDIENTE, CORREGIDO o ACEPTADO.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.OBSERVACION IS 'Notas adicionales sobre el hallazgo.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.FECHA_RESOLUCION IS 'Fecha en que se corrigió o aceptó el hallazgo.';
COMMENT ON COLUMN MI_DQ_HALLAZGO.RESUELTO_POR IS 'Usuario o área que resolvió el hallazgo.';

-- MI_INDICADOR_RESULTADO
COMMENT ON TABLE MI_INDICADOR_RESULTADO IS 'Indicadores K1–K5 precalculados por corrida ETL (cobertura, oportunidad, cobranza, verificación, calidad).';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.ID_RESULTADO IS 'Clave surrogate del resultado (identity).';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.ID_CARGA IS 'Identificador de la corrida ETL que generó el indicador.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.FECHA_CARGA IS 'Fecha y hora de materialización del indicador.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.COD_INDICADOR IS 'Código del indicador: K1 a K5.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.NOMBRE_INDICADOR IS 'Nombre descriptivo del indicador.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.ANIO IS 'Año de corte del indicador.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.ID_ORGANO IS 'FK analítica a órgano; -1 = total o no especificado.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.ID_MATERIA IS 'FK analítica a materia; -1 = total o no especificado.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.METRICA IS 'Nombre de la métrica (N_MULTAS, RATIO_COBRANZA_SOLES, PCT_AMARRE, etc.).';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.SUBGRANO IS 'Subdesglose: REGLA, PUENTE, SOLES, UIT o TOTAL.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.NUMERADOR IS 'Numerador de la métrica cuando aplica.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.DENOMINADOR IS 'Denominador de la métrica cuando aplica.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.VALOR IS 'Valor calculado del indicador.';
COMMENT ON COLUMN MI_INDICADOR_RESULTADO.UNIDAD IS 'Unidad de medida: CONTEO, DIAS, RATIO, PORCENTAJE, etc.';

COMMIT;
