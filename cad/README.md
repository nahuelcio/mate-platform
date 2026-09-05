# mate-platform: 3D CAD Blueprint & Assembly Guide

Este documento detalla la arquitectura mecánica, despiece, tolerancias y especificaciones para fabricar las piezas de la estación inteligente de mate en impresión 3D (FDM / SLA) o para su importación directa en Shapr3D.

---

## 1. Arquitectura del Conjunto (4 Módulos)

```
                       [ MATE / CALABAZA ]
                                │
                      (Pulsador de Presencia)
                                │
    ┌────────────────────────────────────────────────────────┐
    │  PIEZA 1: Cuna Basculante 45° (Tilting Cradle)         │
    │  - Asiento cónico Ø 78 mm para el mate                 │
    │  - Pernos de pivote Ø 6 mm integrados                  │
    │  - Alojamiento inferior para IMU GY-521 (MPU6050)      │
    │  - Ojo de biela para brazo de servo SG90               │
    └───────────────────────────┬────────────────────────────┘
                                │ Eje de Giro (Pivote 45°)
    ┌───────────────────────────┴────────────────────────────┐
    │  PIEZA 2: Carcasa Superior & Sensores (Sensor Fascia)  │
    │  - Bisel para Pantalla OLED SSD1306 a 30°              │
    │  - Soportes cilíndricos para HC-SR04 (ojos ultrasonido)│
    │  - Guía acústica para micrófono GY-MAX9814             │
    │  - Bancadas de apoyo para los pernos de giro           │
    └───────────────────────────┬────────────────────────────┘
                                │ Encastre M3 / Snap-Fit
    ┌───────────────────────────┴────────────────────────────┐
    │  PIEZA 3: Chasis Principal (Main Enclosure Base)       │
    │  - Cuna y correderas para placa ESP32 (30 pines)       │
    │  - Bahía de fijación rígida para Micro Servo SG90      │
    │  - Cámara acústica de resonancia para Buzzer 12mm      │
    │  - Pasacables internos con amarre para zunchos         │
    │  - Salida trasera para cable Micro-USB / Type-C        │
    └───────────────────────────┬────────────────────────────┘
                                │ 4x Tornillos M3 avellanados
    ┌───────────────────────────┴────────────────────────────┐
    │  PIEZA 4: Tapa Inferior de Servicio (Bottom Lid)       │
    │  - Ranuras de ventilación tipo persiana (louver vents) │
    │  - 4x Alojamientos para patas de silicona (Ø 12 x 2 mm)│
    │  - Acceso directo para mantenimiento y cableado        │
    └────────────────────────────────────────────────────────┘
```

---

## 2. Dimensiones y Medidas Críticas (Nominales & Tolerancias)

| Componente | Medida Real (mm) | Tolerancia 3D (Cavitación) | Detalle de Encastre |
| :--- | :--- | :--- | :--- |
| **Mate / Vaso** | Ø 60 a 76 mm | Asiento Ø 78 mm cónico | Admite mates de calabaza, madera o acero térmico |
| **ESP32 DOIT 30-Pin** | 51.5 x 28.5 x 12.0 mm | Riel de 52.5 x 29.5 mm (+1.0mm) | Deslizamiento suave sobre guías laterales |
| **OLED 0.96" SSD1306** | 27.0 x 27.5 x 3.5 mm | Bisel de 24.5 x 14.5 mm (área activa) | Inclinado a 30° hacia el usuario para lectura fácil |
| **Servo SG90** | 22.8 x 12.2 x 24.5 mm | Bolsillo de 23.5 x 12.8 mm (+0.6mm) | Fijado con orejeras de 2 tornillos M2 |
| **Sensor HC-SR04** | 45.2 x 20.4 mm, conos Ø 16 mm | 2x orificios de Ø 16.5 mm c-to-c 26 mm | Alojamiento a presión frontal para censar presencia |
| **Micrófono GY-MAX9814** | 25.5 x 14.2 mm, cápsula Ø 6mm | Cavidad frontal + rejilla acústica | Aislado mecánicamente de la vibración del servo |
| **Buzzer 12mm** | Ø 12.0 mm x 9.5 mm | Cámara resonante Ø 14.0 mm | Salida de audio acústica en la base |
| **Switch Base (Dock)** | KW12 (19.8 x 6.4 x 10.2 mm) | Soporte con resorte de retorno | Se activa con > 25 g al apoyar el mate |

---

## 3. Archivos STL Generados y Listos para Imprimir

Ubicación: `/cad/models/`

1. **`01_tilting_cradle_45deg.stl`**
   - Peso estimado: ~28 g PLA.
   - Tiempo de impresión: ~1h 45m.
   - Soportes recomendados: Soportes tipo árbol solo en los pernos de pivote.
2. **`02_main_enclosure_base.stl`**
   - Peso estimado: ~65 g PLA.
   - Tiempo de impresión: ~3h 30m.
   - Infill: 20% Gyroid (para máxima rigidez y resonancia del buzzer).
3. **`03_upper_sensor_fascia.stl`**
   - Peso estimado: ~38 g PLA.
   - Tiempo de impresión: ~2h 15m.
   - Permite montar la pantalla inclinada y los sensores frontales.
4. **`04_bottom_service_lid.stl`**
   - Peso estimado: ~22 g PLA.
   - Tiempo de impresión: ~1h 10m.
   - Fondo plano, no requiere soportes.

---

## 4. Parámetros de Impresión Recomendados (FDM)

- **Material:** PLA, PLA+ o PETG (recomendado PETG si se expone a salpicaduras de agua caliente).
- **Altura de capa:** `0.20 mm` (ó `0.16 mm` para mejor acabado en las curvas de la cuna).
- **Perímetros (Paredes):** 4 a 6 perímetros (`1.6 mm - 2.4 mm`) para tornillos e insertos de rosca M3.
- **Relleno (Infill):** `20% - 25%` Gyroid o Honeycomb.
- **Insertos:** Agujeros preparados para insertos de latón M3 (roscado en caliente / calor con cautín).

---

## 5. Edición y Ajustes Paramétricos

Para regenerar o cambiar cualquier medida (por ejemplo ampliar el diámetro del mate a 85mm o ajustar el ángulo del display):
```bash
python3 cad/generator.py
```
El script exporta los binarios STL estándar que pueden abrirse directamente en **Shapr3D**, **Bambu Studio**, **PrusaSlicer**, **OrcaSlicer** o **Cura**.
