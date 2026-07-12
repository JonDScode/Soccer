# Cómo se generan los datos de fútbol (y cómo hacerlo en un club pequeño)

Entender de dónde sale el dato es lo que separa a un analista que consume CSVs de uno que puede montarle un sistema a un club real. Primero el pipeline profesional, luego lo replicable con poco presupuesto.

## Cómo se genera el dato profesional

| Tipo de dato | Cómo se produce | Quién lo hace |
|---|---|---|
| **Event data** (pases, tiros, duelos con coordenadas) | Codificadores humanos viendo el video con software de tagging: ~2.000-3.500 eventos por partido, 2-3 personas por partido más control de calidad. Cada vez más asistido por IA, pero el humano sigue validando. | Opta (Stats Perform), StatsBomb/Hudl |
| **Tracking data** (posición de los 22 + balón, 25 veces por segundo) | Sistemas multicámara instalados en el estadio que triangulan a cada jugador, o visión por computador sobre la señal de TV (sin instalar nada en el estadio). | TRACAB, Second Spectrum, SkillCorner (broadcast) |
| **Datos físicos** (distancias, sprints, aceleraciones, carga) | Chalecos GPS de 10 Hz con acelerómetro y giroscopio que cada jugador lleva en entrenamientos y partidos. | Catapult, STATSports, WIMU |
| **xG y métricas derivadas** | Modelos entrenados sobre millones de eventos históricos; no se "recolectan", se calculan encima del event data. | Cada proveedor tiene el suyo |

La lección importante: **el dato de fútbol nace de video + trabajo manual (o modelos que lo imitan)**. No hay magia — y por eso un club pequeño puede generar una versión modesta del mismo dato.

## Escalera realista para un club de ciudad pequeña

### Nivel 0 — Costo cero: planilla de eventos propia
Un voluntario en la tribuna con una plantilla (Google Sheets o una app de tagging en el móvil) registrando eventos discretos: tiros con zona (dentro/fuera del área, sector), recuperaciones por tercio de cancha, centros, balones parados. 
- **Qué produce**: event data "de baja resolución", suficiente para tendencias por partido y por temporada.
- **Clave metodológica**: definir un diccionario de eventos ANTES (qué cuenta como "ocasión", qué zonas usar) para que el dato sea consistente entre partidos y personas.

### Nivel 1 — < 100 €: video + tagging con software libre
Grabar el partido con un móvil o cámara en trípode en posición elevada y taguear después con **LongoMatch** (open source) o similares. Del tagging se exporta CSV → entra directo al stack Python de este repo.
- **Qué produce**: event data propio con timestamps y video enlazado (clips por categoría para el cuerpo técnico — esto es lo que más valora un entrenador).

### Nivel 2 — 1.000-3.000 €/año: cámara automática + GPS
- **Cámara panorámica con seguimiento automático** (Veo, Pixellot): graba y sigue el juego sola, sube el video a la nube; algunas dan estadísticas básicas automáticas. Es el estándar de facto en clubes semiprofesionales y academias.
- **GPS individuales** (STATSports Apex Athlete, Playertek, ~200-300 € por unidad): con 5-10 unidades rotando ya se hace control de carga física del plantel — prevención de lesiones, el caso de uso con retorno más claro para un club pequeño.

### Nivel 3 — El que te diferencia como data scientist: visión por computador propia
Sobre el video del Nivel 1/2 se puede montar un pipeline casero de tracking: detección de jugadores con **YOLO**, seguimiento con **ByteTrack**, homografía para pasar de píxeles a coordenadas de cancha. Hay proyectos abiertos que sirven de base (el ecosistema de ejemplos deportivos de Roboflow, `soccertrack`, `narya`).
- **Qué produce**: tracking data casero — posiciones, distancias y mapas de ocupación sin pagar proveedor.
- **Realismo**: es un proyecto de meses, sensible a la calidad del video (altura de cámara y estabilidad importan más que la resolución). Perfecto como fase avanzada de este repo y como servicio concreto para el club.

## Qué puede hacer el club con cada nivel

| Necesidad del club | Nivel mínimo | Con qué se responde |
|---|---|---|
| "¿Cómo estamos rindiendo más allá del resultado?" | 0 | Tendencias de ocasiones/recuperaciones por partido |
| Clips de video por jugada para charlas técnicas | 1 | Tagging enlazado al video |
| Prevenir lesiones y dosificar cargas | 2 (GPS) | Reportes de distancia, sprints, aceleraciones |
| Análisis táctico de ocupación de espacios | 3 | Tracking casero + heatmaps como los de este repo |
| Scouting de rivales de la misma liga | 1 | Taguear los partidos del rival con la misma planilla |

## Conexión con este repo

El generador sintético ([generate_synthetic.py](../scripts/generate_synthetic.py)) produce datos con el mismo esquema que saldría de una planilla de Nivel 0-1 (partidos + tiros con coordenadas), así que todo lo que construyamos aquí — visualizaciones, xG, reportes — funcionaría igual con los datos reales del club el día que existan. Ese es el pitch para tu amigo: *el sistema se puede montar hoy con datos abiertos y conectarle los datos del club después.*
