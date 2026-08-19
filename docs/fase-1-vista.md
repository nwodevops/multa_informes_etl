# Fase 1 — vista general

Qué se hizo en el entregable 1 (TDR **a, b, c**). El detalle está en [`fase-1.md`](fase-1.md). Dónde vive el dato (inputs → H2 → Oracle): [`antes-durante-fase1.md`](antes-durante-fase1.md). Nombres: [`glosario.md`](glosario.md).

La fase 1 **consolida y diagnostica**. No depura.

```mermaid
flowchart LR
  a["a consolidar"]
  b["b revisar estructura"]
  c["c validar calidad"]
  out["INT_ + QA_ + Excel"]

  a --> out
  b --> out
  c --> out
```

## Flujo

Fuentes 1:1 a H2. Python une sin filtrar y marca defectos. El resultado vive en BD_CURSOR y en Excel.

```mermaid
flowchart TB
  subgraph src [Fuentes]
    XL["Excel CAGR y Lambayeque"]
    SIS["Oracle SISUD"]
    MY["MySQL GAPP"]
  end

  subgraph bronze [Bronze efimero]
    H2["H2 STG_*"]
  end

  subgraph silver [Landing]
    INT["INT_* sin filtrar"]
  end

  subgraph ctrl [Control]
    QA["QA_CORRIDA y QA_EXCEPCION"]
  end

  subgraph dest [Persistente]
    DW["Oracle APP BD_CURSOR"]
    XLS["output/fase1.xlsx"]
  end

  XL --> H2
  SIS --> H2
  MY --> H2
  H2 --> INT
  INT --> QA
  INT --> DW
  QA --> DW
  INT --> XLS
  QA --> XLS
```

## Universos (sin cruce)

Tres mundos de multas más informes. No se inventa una llave común.

```mermaid
flowchart TB
  subgraph mc [Multas coercitivas]
    EX["INT_MC_EXCEL<br/>UNION GS1 + GS2"]
    ET["INT_MC_ETAPAS"]
    SI["INT_MC_SISUD"]
    GA["INT_MC_GAPP"]
  end

  subgraph inf [Informes de supervision]
    IN["INT_INFORMES"]
  end

  EX -.->|"mismo archivo CAGR"| ET
  EX -.-x SI
  EX -.-x GA
  SI -.-x GA
  mc -.-x inf
```

## Calidad: marcar, no borrar

El pipeline avisa (`WARN`). Las filas malas se quedan en `INT_*`.

```mermaid
flowchart LR
  STG["STG_ copia fiel"]
  INT["INT_ todo lo que llego"]
  AUD{"llave nula duplicado fecha monto"}
  OK["CHECK_STS OK"]
  WARN["CHECK_STS WARN + QA_EXCEPCION"]

  STG -->|"1 a 1"| INT
  INT --> AUD
  AUD -->|"cumple"| OK
  AUD -->|"falla"| WARN
```

## Qué no se hizo (entregable 2+)

```mermaid
flowchart LR
  f1["Fase 1 hecha"]
  f2["Fase 2: depurar FCT_ FG_VALIDO trazabilidad"]
  f3["Fase 3: cuadros y hallazgos"]

  f1 --> f2 --> f3
```
