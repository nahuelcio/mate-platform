"""
Generador CAD 3D de alta gama para mate-platform:
ESTÉTICA: "Dock MagSafe Circular Fino"
- Perfil ultra bajo, elegante, sin caras ni ojos de juguete.
- Plato superior rasante magnético/apoyador de Ø 92 mm con bisel suave de 45°.
- Anillo sutil para inclinación motorizada pivotada al ras.
- Pantalla OLED rasante frontal como corte láser sutil.
- Sensores discretos integrados en el perímetro inferior como puertos de audio de Apple.
- Base circular tipo puck de aluminio con chaflán y apoyo de silicona perimetral.
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
# 1. DISCO DE APOYO BASCULANTE MAGSAFE (Tilting Pad Ultra-Slim)
# Plato circular fino con rebaje de silicona y bisel suave de 45°
# ----------------------------------------------------------------------------
def build_tilting_cradle():
    m = Mesh3D("tilting_cradle")
    r_disc = 45.0       # Ø 90 mm superficie de apoyo plana
    r_recess = 40.0     # Ø 80 mm área interna antideslizante
    t_pad = 6.0         # Solo 6 mm de espesor total
    chamfer_h = 2.0

    # Bisel inferior suave perimetral (estilo puck MagSafe)
    m.add_cone_frustum(0, 0, 0, r_disc - 2.0, r_disc, chamfer_h, segments=64)
    # Cuerpo cilíndrico del pad
    m.add_cylinder(0, 0, chamfer_h, r_disc, t_pad - chamfer_h, segments=64)
    # Rebaje superior milimétrico para almohadilla de silicona
    m.add_pipe_segment(0, 0, t_pad, r_recess, r_disc, 1.2, segments=64)

    # Pernos de pivote integrados ocultos al ras
    pin_r = 3.0
    pin_len = 8.0
    m.add_cylinder(r_disc - 1.0, 0, t_pad / 2.0, pin_r, pin_len, segments=24)
    m.add_cylinder(-r_disc - pin_len + 1.0, 0, t_pad / 2.0, pin_r, pin_len, segments=24)

    # Leva de empuje servo oculta en la parte inferior
    m.add_box(-4.0, -28.0, -6.0, 8.0, 8.0, 6.0)
    # Bolsillo rasante para acelerómetro GY-521 debajo
    m.add_box(-12.0, -10.0, -3.5, 24.0, 20.0, 3.5)

    return m

# ----------------------------------------------------------------------------
# 2. CHASIS DOCK CIRCULAR PRINCIPAL (Puck Unibody de Aluminio/Plástico Mate)
# Diámetro 118 mm, altura ultra baja de solo 26 mm con chaflán perimetral
# ----------------------------------------------------------------------------
def build_main_base():
    m = Mesh3D("main_enclosure_base")
    r_base = 59.0      # Ø 118 mm base
    r_top = 56.0       # Ø 112 mm parte superior
    h_dock = 26.0      # Perfil ultra bajo

    # Chaflán perimetral exterior suave (forma cónica sutil)
    m.add_cone_frustum(0, 0, 0, r_base, r_top, h_dock, segments=72)

    # Rebaje superior circular donde encaja al ras el pad basculante (Ø 93 mm)
    m.add_cylinder(0, 0, h_dock - 8.0, 47.0, 8.0, segments=64)

    # Cuna interna horizontal para alojar la placa ESP32 (30 pines)
    m.add_box(-15.0, -26.0, 3.0, 30.0, 52.0, 11.0)

    # Bahía horizontal compacta para el servo SG90
    m.add_box(-36.0, -12.0, 3.0, 13.0, 24.0, 14.0)

    # Cono acústico sutil para el buzzer integrado
    m.add_pipe_segment(28.0, 15.0, 3.0, 4.0, 7.5, 12.0, segments=24)

    # Puerto trasero sutil tipo USB-C / pasacables
    m.add_box(-8.0, r_base - 8.0, 4.0, 16.0, 8.0, 7.0)

    return m

# ----------------------------------------------------------------------------
# 3. BISEL Y ANILLO FRONTAL MINIMALISTA (Front Ring & Seamless Display)
# Hendidura sutil para la pantalla OLED rasante y micro-ranuras para sensores
# ----------------------------------------------------------------------------
def build_upper_sensor_fascia():
    m = Mesh3D("upper_sensor_fascia")
    r_fascia = 56.5
    h_ring = 8.0

    # Anillo rasante superior con borde pulido
    m.add_pipe_segment(0, 0, 0, 47.5, r_fascia, h_ring, segments=72)

    # Ventana frontal rasante tipo cristal negro para OLED 0.96" (sin marcos toscos)
    m.add_box(-16.0, -r_fascia + 1.0, 1.0, 32.0, 3.5, 6.0)

    # Micro-perforaciones discretas frontales (estilo altavoz MacBook) para sensor de proximidad
    m.add_cylinder(-10.0, -r_fascia + 3.0, 3.5, 3.5, 4.0, segments=24)
    m.add_cylinder(10.0, -r_fascia + 3.0, 3.5, 3.5, 4.0, segments=24)

    # Micrófono pinhole de 1.5 mm
    m.add_cylinder(25.0, -r_fascia + 3.0, 3.5, 1.5, 4.0, segments=16)

    # Alojamientos de giro laterales ocultos
    m.add_box(44.0, -5.0, 0, 4.0, 10.0, h_ring)
    m.add_box(-48.0, -5.0, 0, 4.0, 10.0, h_ring)

    return m

# ----------------------------------------------------------------------------
# 4. TAPA INFERIOR CON ANILLO DE GOMA CONTINUO (MagSafe Footprint)
# ----------------------------------------------------------------------------
def build_bottom_lid():
    m = Mesh3D("bottom_service_lid")
    r_lid = 58.0
    t_lid = 3.0

    # Base circular plana biselada
    m.add_cylinder(0, 0, 0, r_lid, t_lid, segments=72)

    # Anillo de goma perimetral continuo (estilo cargador inalámbrico de escritorio)
    m.add_pipe_segment(0, 0, -1.2, r_lid - 7.0, r_lid - 3.0, 1.2, segments=64)

    # Micro-ranuras de ventilación radiales sutiles en el fondo
    for i in range(12):
        ang = i * (math.pi / 6.0)
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
