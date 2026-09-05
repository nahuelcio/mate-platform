"""
Generador CAD 3D de alta gama para mate-platform:
ESTÉTICA: "Dock MagSafe Circular Fino"
- Cuenco hundido 22 mm anti-caídas (abrazamiento cónico del mate).
- Pantalla OLED SSD1306 (0.96") rasante frontal.
- Botón físico cilíndrico de aluminio CNC (Ø 12 mm) para pasar turno manual (GPIO 15).
- NUEVO: LED INDICADOR FRONTAL (Pinhole rasante Ø 2.5 mm con guía de luz acrílica difusa, GPIO 2).
- NUEVO: SLOT PARA PARLANTE / BUZZER CON REJILLA INFERIOR OCULTA:
  * Cámara acústica orientada hacia la base inferior (down-firing speaker).
  * Rejilla de audio micro-ranurada oculta en la tapa inferior, invisible para el usuario de frente.
  * Sonido amplificado por rebote acústico sobre la mesa de trabajo (efecto subwoofer de escritorio).
- Chasis circular compacto de perfil bajo (Ø 118 mm x 34 mm).
"""
import struct
import math
import os

class Mesh3D:
    def __init__(self, name="object"):
        self.name = name
        self.triangles = []

    def add_triangle(self, v1, v2, v3):
        ux, uy, uz = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
        vx, vy, vz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        norm = math.sqrt(nx * nx + ny * ny + nz * nz)
        normal = (nx / norm, ny / norm, nz / norm) if norm > 1e-9 else (0.0, 0.0, 1.0)
        self.triangles.append((normal, v1, v2, v3))

    def add_quad(self, v1, v2, v3, v4):
        self.add_triangle(v1, v2, v3)
        self.add_triangle(v1, v3, v4)

    def add_box(self, x, y, z, dx, dy, dz):
        p0, p1 = (x, y, z), (x + dx, y, z)
        p2, p3 = (x + dx, y + dy, z), (x, y + dy, z)
        p4, p5 = (x, y, z + dz), (x + dx, y, z + dz)
        p6, p7 = (x + dx, y + dy, z + dz), (x, y + dy, z + dz)
        self.add_quad(p0, p3, p2, p1)
        self.add_quad(p4, p5, p6, p7)
        self.add_quad(p0, p1, p5, p4)
        self.add_quad(p3, p7, p6, p2)
        self.add_quad(p0, p4, p7, p3)
        self.add_quad(p1, p2, p6, p5)

    def add_cylinder(self, cx, cy, cz, r, h, segments=64):
        top_pts, bot_pts = [], []
        for i in range(segments):
            th = 2.0 * math.pi * i / segments
            bot_pts.append((cx + r * math.cos(th), cy + r * math.sin(th), cz))
            top_pts.append((cx + r * math.cos(th), cy + r * math.sin(th), cz + h))

        c_bot, c_top = (cx, cy, cz), (cx, cy, cz + h)
        for i in range(segments):
            ni = (i + 1) % segments
            self.add_triangle(c_bot, bot_pts[ni], bot_pts[i])
            self.add_triangle(c_top, top_pts[i], top_pts[ni])
            self.add_quad(bot_pts[i], bot_pts[ni], top_pts[ni], top_pts[i])

    def add_cone_frustum(self, cx, cy, cz, r_bot, r_top, h, segments=64):
        top_pts, bot_pts = [], []
        for i in range(segments):
            th = 2.0 * math.pi * i / segments
            bot_pts.append((cx + r_bot * math.cos(th), cy + r_bot * math.sin(th), cz))
            top_pts.append((cx + r_top * math.cos(th), cy + r_top * math.sin(th), cz + h))

        c_bot, c_top = (cx, cy, cz), (cx, cy, cz + h)
        for i in range(segments):
            ni = (i + 1) % segments
            self.add_triangle(c_bot, bot_pts[ni], bot_pts[i])
            self.add_triangle(c_top, top_pts[i], top_pts[ni])
            self.add_quad(bot_pts[i], bot_pts[ni], top_pts[ni], top_pts[i])

    def add_pipe_segment(self, cx, cy, cz, r_in, r_out, h, segments=64):
        for i in range(segments):
            th1 = 2.0 * math.pi * i / segments
            th2 = 2.0 * math.pi * (i + 1) / segments

            b_in1 = (cx + r_in * math.cos(th1), cy + r_in * math.sin(th1), cz)
            b_in2 = (cx + r_in * math.cos(th2), cy + r_in * math.sin(th2), cz)
            b_out1 = (cx + r_out * math.cos(th1), cy + r_out * math.sin(th1), cz)
            b_out2 = (cx + r_out * math.cos(th2), cy + r_out * math.sin(th2), cz)

            t_in1 = (b_in1[0], b_in1[1], cz + h)
            t_in2 = (b_in2[0], b_in2[1], cz + h)
            t_out1 = (b_out1[0], b_out1[1], cz + h)
            t_out2 = (b_out2[0], b_out2[1], cz + h)

            self.add_quad(b_out1, b_out2, b_in2, b_in1)
            self.add_quad(t_out1, t_in1, t_in2, t_out2)
            self.add_quad(b_out1, t_out1, t_out2, b_out2)
            self.add_quad(b_in1, b_in2, t_in2, t_in1)

    def write_binary_stl(self, filepath):
        header = f"mate-platform {self.name}".encode('ascii')[:80].ljust(80, b'\0')
        count = len(self.triangles)
        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(struct.pack('<I', count))
            for normal, v1, v2, v3 in self.triangles:
                f.write(struct.pack('<3f', normal[0], normal[1], normal[2]))
                f.write(struct.pack('<3f', v1[0], v1[1], v1[2]))
                f.write(struct.pack('<3f', v2[0], v2[1], v2[2]))
                f.write(struct.pack('<3f', v3[0], v3[1], v3[2]))
                f.write(struct.pack('<H', 0))
        print(f"[STL OK] {os.path.basename(filepath)}: {count} tris ({os.path.getsize(filepath)/1024:.1f} KB)")


# ----------------------------------------------------------------------------
# 1. PIEZA 1: CUENCO HUNDIDO BASCULANTE 45° (Deep Anti-Fall Cradle)
# ----------------------------------------------------------------------------
def build_tilting_cradle():
    m = Mesh3D("tilting_cradle")
    r_cup_bottom = 31.0   # Ø 62 mm en fondo
    r_cup_top = 39.0      # Ø 78 mm en boca
    r_cradle_outer = 45.0 # Ø 90 mm exterior
    depth = 22.0          # 22 mm de hundimiento
    floor_thick = 4.0

    m.add_cylinder(0, 0, 0, r_cup_bottom + 4.0, floor_thick, segments=64)
    m.add_pipe_segment(0, 0, floor_thick, r_cup_bottom, r_cradle_outer, 10.0, segments=64)
    m.add_pipe_segment(0, 0, floor_thick + 10.0, r_cup_top - 2.0, r_cradle_outer, depth - 10.0, segments=64)
    m.add_cone_frustum(0, 0, floor_thick + depth, r_cradle_outer, r_cradle_outer - 1.5, 2.0, segments=64)

    # Nervios interiores de retención
    for i in range(4):
        ang = i * (math.pi / 2.0)
        nx = (r_cup_bottom - 1.0) * math.cos(ang)
        ny = (r_cup_bottom - 1.0) * math.sin(ang)
        m.add_box(nx - 1.5, ny - 1.5, floor_thick, 3.0, 3.0, depth * 0.7)

    # Pernos de pivote laterales reforzados (Ø 7 mm)
    pin_r = 3.5
    pin_len = 8.0
    pivot_z = floor_thick + 10.0
    m.add_cylinder(r_cradle_outer - 1.0, 0, pivot_z, pin_r, pin_len, segments=24)
    m.add_cylinder(-r_cradle_outer - pin_len + 1.0, 0, pivot_z, pin_r, pin_len, segments=24)

    # Horquilla de empuje servo & alojamiento sensor IMU GY-521
    m.add_box(-4.5, -28.0, -8.0, 9.0, 9.0, 8.0)
    m.add_box(-12.0, -10.0, -4.0, 24.0, 20.0, 4.0)

    return m

# ----------------------------------------------------------------------------
# 2. PIEZA 2: CHASIS CIRCULAR DOCK UNIBODY
# Con slot down-firing para parlante/buzzer oculto hacia abajo
# ----------------------------------------------------------------------------
def build_main_base():
    m = Mesh3D("main_enclosure_base")
    r_base = 59.0      # Ø 118 mm
    r_top = 56.5       # Ø 113 mm
    h_dock = 34.0

    # Chaflán perimetral exterior suave MagSafe
    m.add_cone_frustum(0, 0, 0, r_base, r_top, h_dock, segments=72)

    # Fosa circular central donde oscila libre el cuenco (Ø 94 mm)
    m.add_cylinder(0, 0, 4.0, 47.0, h_dock - 4.0, segments=64)

    # Cuna interna baja para placa ESP32 (30 pines)
    m.add_box(-15.0, -26.0, 3.0, 30.0, 52.0, 12.0)

    # Bahía horizontal rígida para servo SG90
    m.add_box(-42.0, -12.0, 3.0, 13.5, 24.0, 16.0)

    # 🔊 SLOT DE PARLANTE / BUZZER OCULTO (DOWN-FIRING ACOUSTIC CAVITY)
    # Ubicado hacia el fondo (Z = 0 a 16 mm), apuntando hacia la rejilla de la base inferior
    spk_x, spk_y = 30.0, 15.0
    spk_r_inner = 14.0 # Cavidad para transductor/parlante de hasta Ø 28 mm o buzzer de 12 mm
    spk_r_outer = 17.0
    m.add_pipe_segment(spk_x, spk_y, 0, spk_r_inner, spk_r_outer, 16.0, segments=36)
    # Labio de sujeción para parlante
    m.add_pipe_segment(spk_x, spk_y, 14.0, spk_r_inner - 2.0, spk_r_outer, 2.0, segments=36)

    # Alojamiento para botón físico de aluminio frontal (ángulo -38°)
    btn_ang = math.radians(-38)
    btn_x = (r_top - 6.0) * math.cos(btn_ang)
    btn_y = (r_top - 6.0) * math.sin(btn_ang)
    m.add_cylinder(btn_x, btn_y, 4.0, 7.5, h_dock - 6.0, segments=32)

    # Alojamiento para microswitch de base
    m.add_box(8.0, -12.0, 3.0, 8.0, 20.0, 14.0)

    # Puerto posterior USB-C
    m.add_box(-9.0, r_base - 8.0, 4.0, 18.0, 8.0, 9.0)

    return m

# ----------------------------------------------------------------------------
# 3. PIEZA 3: ANILLO CON DISPLAY OLED, BOTÓN FÍSICO Y LED STATUS INTEGRADO
# ----------------------------------------------------------------------------
def build_upper_sensor_fascia():
    m = Mesh3D("upper_sensor_fascia")
    r_fascia = 56.5
    h_ring = 10.0

    # Anillo rasante superior con borde perimetral pulido
    m.add_pipe_segment(0, 0, 0, 47.5, r_fascia, h_ring, segments=72)

    # 📺 VENTANA FRONTAL DISPLAY OLED 0.96" SSD1306 (28 x 16 mm activa)
    m.add_box(-17.0, -r_fascia + 0.5, 1.0, 34.0, 5.0, 8.5)
    m.add_box(-14.0, -r_fascia + 2.5, 2.0, 28.0, 2.5, 6.5)

    # 🔘 BOTÓN FÍSICO INTEGRADO (Corona táctil de aluminio Ø 12 mm en frontal derecho)
    btn_ang = math.radians(-38)
    btn_x = (r_fascia - 6.0) * math.cos(btn_ang)
    btn_y = (r_fascia - 6.0) * math.sin(btn_ang)
    m.add_pipe_segment(btn_x, btn_y, 0, 5.2, 7.2, h_ring, segments=32)
    m.add_cylinder(btn_x, btn_y, h_ring - 1.5, 4.8, 3.0, segments=32)
    m.add_cone_frustum(btn_x, btn_y, h_ring + 1.5, 4.8, 4.0, 0.8, segments=32)

    # 💡 LED INDICADOR DE ESTADO (Pinhole rasante Ø 2.5 mm con bisel, frontal izquierdo ángulo -142°)
    led_ang = math.radians(-142)
    led_x = (r_fascia - 5.0) * math.cos(led_ang)
    led_y = (r_fascia - 5.0) * math.sin(led_ang)
    # Lente cilíndrica del LED rasante
    m.add_cylinder(led_x, led_y, 2.0, 1.8, h_ring - 2.0, segments=24)
    # Bisel cónico exterior tipo Apple indicator
    m.add_cone_frustum(led_x, led_y, h_ring - 0.5, 1.8, 2.5, 0.5, segments=24)

    # Micro-perforaciones discretas para proximidad y micrófono
    m.add_cylinder(-35.0, -r_fascia + 8.0, 2.5, 2.5, 5.0, segments=20)
    m.add_cylinder(-40.0, -r_fascia + 12.0, 2.5, 2.5, 5.0, segments=20)
    m.add_cylinder(0, -r_fascia + 3.0, 0.5, 1.2, 3.0, segments=16)

    # Bancadas de giro laterales
    m.add_box(44.0, -5.0, 0, 4.0, 10.0, h_ring)
    m.add_box(-48.0, -5.0, 0, 4.0, 10.0, h_ring)

    return m

# ----------------------------------------------------------------------------
# 4. PIEZA 4: TAPA INFERIOR CON REJILLA DE AUDIO OCULTA (Down-Firing Grille)
# ----------------------------------------------------------------------------
def build_bottom_lid():
    m = Mesh3D("bottom_service_lid")
    r_lid = 58.0
    t_lid = 3.5

    # Base circular plana biselada
    m.add_cylinder(0, 0, 0, r_lid, t_lid, segments=72)

    # Anillo de goma perimetral continuo
    m.add_pipe_segment(0, 0, -1.2, r_lid - 7.0, r_lid - 3.0, 1.2, segments=64)

    # 🔊 REJILLA ACÚSTICA OCULTA PARA PARLANTE (DOWN-FIRING SPEAKER GRILLE)
    # Coincide exactamente debajo de la cámara del parlante (30, 15)
    spk_cx, spk_cy = 30.0, 15.0
    # Anillos concéntricos perforados para salida de audio sin restricciones
    for r in [3.5, 7.0, 10.5]:
        m.add_pipe_segment(spk_cx, spk_cy, 0, r - 0.8, r + 0.8, t_lid, segments=32)

    # Micro-ranuras de ventilación radiales para electrónica (lado opuesto)
    for i in range(8):
        ang = math.pi + i * (math.pi / 4.0)
        rx = 26.0 * math.cos(ang)
        ry = 26.0 * math.sin(ang)
        m.add_box(rx - 1.0, ry - 3.0, 0, 2.0, 6.0, t_lid)

    return m

def main():
    target_dir = "/Users/nahuelcioffi/Proyectos/esp32/cad/models"
    os.makedirs(target_dir, exist_ok=True)

    parts = [
        ("01_tilting_cradle_45deg.stl", build_tilting_cradle()),
        ("02_main_enclosure_base.stl", build_main_base()),
        ("03_upper_sensor_fascia.stl", build_upper_sensor_fascia()),
        ("04_bottom_service_lid.stl", build_bottom_lid())
    ]

    for filename, mesh in parts:
        filepath = os.path.join(target_dir, filename)
        mesh.write_binary_stl(filepath)

if __name__ == "__main__":
    main()
