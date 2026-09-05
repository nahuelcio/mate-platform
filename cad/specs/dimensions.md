# Mechanical Dimensions & Component Tolerances

All dimensions in millimeters (mm). Tolerances for FDM 3D printing (PLA/PETG, 0.4mm nozzle, 0.2mm layer height) included.

---

## 1. Electronic Components Dimensions

### 1.1 ESP32 DOIT DevKit V1 (30-pin)
- PCB Outline: `51.5 mm (L) × 28.5 mm (W) × 12.0 mm (H)` (including pin headers).
- Pin pitch: `2.54 mm`. Row spacing: `25.4 mm (1.0")`.
- Micro-USB connector protrusion: `1.5 mm` beyond PCB edge.
- Mounting hole spacing: `46.0 mm × 23.0 mm`, hole diameter: `2.8 mm` (for M2.5 / self-tapping screws).
- Clearance envelope for cad cradle: `53.0 mm × 30.0 mm × 14.0 mm`.

### 1.2 SSD1306 0.96" OLED I2C Display
- PCB Size: `27.0 mm (W) × 27.5 mm (H) × 3.5 mm (D)`.
- Active glass screen: `24.0 mm × 14.0 mm` (viewable area: `21.74 mm × 10.86 mm`).
- Screen offset from PCB top: `4.5 mm`.
- Mounting holes: 4× `M2` holes (`2.0 mm`), center-to-center: `23.0 mm (W) × 23.5 mm (H)`.
- Front bezel cutout required: `24.5 mm × 14.5 mm`, inner recess depth `1.8 mm`.

### 1.3 SG90 Micro Servo
- Body Dimensions: `22.8 mm (L) × 12.2 mm (W) × 24.5 mm (H)` (overall height with output spline: `28.5 mm`).
- Mounting flange: `32.0 mm (L) × 12.2 mm (W) × 2.5 mm (T)` at height `16.0 mm` from base.
- Flange mounting screw pitch: `28.0 mm` (2× holes, `2.0 mm` dia).
- Output shaft center: `5.5 mm` from one edge, diameter `4.8 mm` (21T spline).
- Horn swing radius: `15.0 mm` clearance envelope.

### 1.4 GY-521 (MPU6050 6-DoF IMU)
- PCB Dimensions: `20.5 mm (L) × 15.6 mm (W) × 3.2 mm (H)`.
- Mounting holes: 2× `M3` holes (`3.0 mm` dia) spaced `15.0 mm` apart.
- Placement: Mounted directly under the tilting cradle to track real inclination.

### 1.5 HC-SR04 Ultrasonic Distance Sensor
- PCB Dimensions: `45.2 mm (L) × 20.4 mm (W) × 15.0 mm (H)`.
- Transducers (Transmitter + Receiver): 2× cylinders, `16.0 mm` outer diameter each.
- Transducer center-to-center distance: `26.0 mm`.
- Transducer protrusion above PCB: `12.5 mm`.
- Front plate cutouts: 2× `16.5 mm` circular holes spaced `26.0 mm` center-to-center.

### 1.6 GY-MAX9814 Microphone Module
- PCB Dimensions: `25.5 mm (L) × 14.2 mm (W) × 8.0 mm (H)`.
- Mic capsule diameter: `6.0 mm`, protrusion: `3.0 mm`.
- Front sound grille aperture: 3× `1.5 mm` acoustic slot array.

### 1.7 Passive/Active Buzzer Module (12mm)
- Body: Cylinder `12.0 mm` diameter × `9.5 mm` height.
- Sound port: `2.0 mm` central top hole.
- Internal acoustic cavity: `14.0 mm` chamber with sound director funnel.

### 1.8 Microswitch / Limit Switch (Dock Sensor)
- KW12 / Omron style micro lever switch: `19.8 mm (L) × 6.4 mm (W) × 10.2 mm (H)`.
- Lever arm length: `18.0 mm` with roller or curved tip.
- Actuation stroke: `1.2 mm - 1.8 mm`.
- Pre-travel contact: Triggered by 25g+ mate weight resting on dock plate.

---

## 2. Platform Architecture (4 Main Assemblies)

```
       +---------------------------------------------+
       |             MATE CUP (Calabaza/Termo)       |
       +---------------------------------------------+
                            |
                   [Dock Switch Lever]
                            |
  +-------------------------------------------------------+
  |  PART 1: Tilting Cradle (Cuna Basculante 45°)         |
  |  - Inner Ø 78 mm cup seat                             |
  |  - Built-in GY-521 IMU pocket                         |
  |  - Pivot trunnion pins (Ø 6 mm)                       |
  |  - Servo push-rod linkage receiver                    |
  +-------------------------------------------------------+
                            |
          Pivot Axis (Ø 6mm Pin) + SG90 Servo Arm
                            |
  +-------------------------------------------------------+
  |  PART 2: Upper Housing & Sensor Ring                  |
  |  - HC-SR04 dual front apertures (Ø 16.5 mm)           |
  |  - SSD1306 0.96" OLED bezel angled at 30°             |
  |  - Mic acoustic duct for GY-MAX9814                   |
  |  - Trunnion pivot supports (Left & Right)             |
  +-------------------------------------------------------+
                            |
                    Snap-fit / M3 Standoffs
                            |
  +-------------------------------------------------------+
  |  PART 3: Main Base Enclosure (Cuerpo Principal)       |
  |  - ESP32 slide-in rails with USB-C / micro-USB port   |
  |  - SG90 servo rigid pocket & cable raceways           |
  |  - Internal cable routing channels & tie anchors      |
  |  - Buzzer resonant sound chamber                      |
  +-------------------------------------------------------+
                            |
                    4x M3 Threaded Inserts
                            |
  +-------------------------------------------------------+
  |  PART 4: Bottom Service Lid (Tapa Inferior)           |
  |  - 4x Non-slip rubber feet recesses (Ø 10 mm x 2 mm)  |
  |  - Passive cooling vents (angled louvers)             |
  |  - Access to reset/boot buttons                       |
  +-------------------------------------------------------+
```

---

## 3. Clearances & 3D Print Tolerances

- **FDM Press-fit (tight):** Component nominal + `0.15 mm`.
- **FDM Sliding-fit / Pivot:** Shaft nominal - `0.20 mm`, Hole nominal + `0.25 mm` (Total clearance `0.45 mm`).
- **Snap-fit cantilever tabs:** Width `5.0 mm`, thickness `1.6 mm`, length `12.0 mm`, hook depth `0.8 mm`.
- **Wall thickness guidelines:**
  - Structural outer shell: `2.4 mm` (6 perimeters with 0.4mm nozzle).
  - Internal ribs & dividers: `1.6 mm` (4 perimeters).
  - Component cradle clips: `1.2 mm`.
- **M3 Threaded heat-set inserts:** Hole diameter `4.2 mm`, depth `5.5 mm`.
