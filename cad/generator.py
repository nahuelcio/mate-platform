"""
Generador CAD 3D de alta onda para mate-platform:
- Forma Cilíndrica/Orgánica estilo Termo / Maceta Cyberpunk
- Ojitos "Wall-E / Minion" salientes para el sensor ultrasonido
- Sonrisa/Boca que aloja la pantalla OLED SSD1306
- Biselado curvo ergonómico, cero cajas cuadradas aburridas
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

    def add_cylinder(self, cx, cy, cz, r, h, segments=48):
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

    def add_cone_frustum(self, cx, cy, cz, r_bot, r_top, h, segments=48):
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

    def add_pipe_segment(self, cx, cy, cz, r_in, r_out, h, segments=48):
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
# 1. CUNA BASCULANTE ORGÁNICA (Forma de mate/cuenco ahuecado)
# ----------------------------------------------------------------------------
def build_tilting_cradle():
    m = Mesh3D("tilting_cradle")
    r_cup_inner = 39.0   # Ø 78 mm
    r_cradle_outer = 45.0 # Ø 90 mm exterior curvo
    h_cradle = 30.0

    # Base redondeada estilo calabaza
    m.add_cone_frustum(0, 0, 0, 36.0, r_cradle_outer, 12.0, segments=48)
    m.add_cone_frustum(0, 0, 12.0, r_cradle_outer, r_cradle_outer - 1.5, h_cradle - 12.0, segments=48)

    # Hueco interno cónico para clavar el mate
    m.add_pipe_segment(0, 0, 5.0, r_cup_inner - 3.0, r_cradle_outer - 1.0, 10.0, segments=48)
    m.add_pipe_segment(0, 0, 15.0, r_cup_inner, r_cradle_outer - 1.5, h_cradle - 15.0, segments=48)

    # Pernos de giro cilíndricos laterales robustos (Ø 8 mm)
    pin_r = 4.0
    pin_len = 12.0
    m.add_cylinder(r_cradle_outer - 1.0, 0, 15.0, pin_r, pin_len, segments=24)
    m.add_cylinder(-r_cradle_outer - pin_len + 1.0, 0, 15.0, pin_r, pin_len, segments=24)

    # Nariz / oreja de articulación servo debajo
    m.add_box(-5.0, -r_cradle_outer + 4.0, -12.0, 10.0, 10.0, 12.0)
    # Bolsillo inferior para el sensor IMU GY-521
    m.add_box(-12.5, -10.0, -5.0, 25.0, 20.0, 5.0)

    return m

# ----------------------------------------------------------------------------
# 2. CHASIS PRINCIPAL (Cilíndrico / Cápsula estilo Minion/Termo)
# ----------------------------------------------------------------------------
def build_main_base():
    m = Mesh3D("main_enclosure_base")
    r_base_bot = 58.0   # Ø 116 mm base acampanada estable
    r_base_mid = 54.0   # Ø 108 mm cintura
    r_base_top = 56.0   # Ø 112 mm cuello
    h_base = 56.0

    # Perfil cilíndrico curvo aerodinámico
    m.add_cone_frustum(0, 0, 0, r_base_bot, r_base_mid, 24.0, segments=56)
    m.add_cone_frustum(0, 0, 24.0, r_base_mid, r_base_top, h_base - 24.0, segments=56)

    # Ahuecado interior amplio para alojar electrónica
    m.add_cylinder(0, 0, 4.0, 47.0, h_base - 4.0, segments=48)

    # Cuna interna centrada para el ESP32
    m.add_box(-15.0, -25.0, 4.0, 30.0, 52.0, 12.0)
    # Soporte rígido para servo SG90
    m.add_box(-38.0, -10.0, 4.0, 14.0, 24.0, 22.0)
    # Vaso acústico para el buzzer 12mm
    m.add_cylinder(28.0, 20.0, 4.0, 8.5, 14.0, segments=24)

    # Puertita trasera estilizada para cable USB
    m.add_box(-12.0, r_base_bot - 10.0, 6.0, 24.0, 12.0, 12.0)

    return m

# ----------------------------------------------------------------------------
# 3. CARCASA SUPERIOR "FACE" (Ojitos salientes + Sonrisa OLED)
# ----------------------------------------------------------------------------
def build_upper_sensor_fascia():
    m = Mesh3D("upper_sensor_fascia")
    r_fascia = 56.5
    h_fascia = 22.0

    # Cuello circular superior con anillo redondeado
    m.add_cone_frustum(0, 0, 0, r_fascia, r_fascia - 2.0, h_fascia, segments=56)

    # Hueco central redondo amplio para que la cuna basculante gire libre
    m.add_cylinder(0, 0, 0, 48.0, h_fascia + 2.0, segments=48)

    # 👀 "OJOS DE WALL-E / MINION": Dos tubos gemelos salientes para el HC-SR04
    # Distancia entre centros exacta de 26 mm
    eye_r = 10.0
    eye_h = 14.0
    eye_y = -r_fascia + 2.0
    # Ojo Izquierdo
    m.add_cylinder(-13.0, eye_y, 4.0, eye_r, eye_h, segments=32)
    m.add_cylinder(-13.0, eye_y, 4.0, eye_r - 2.0, eye_h + 1.0, segments=32)
    # Ojo Derecho
    m.add_cylinder(13.0, eye_y, 4.0, eye_r, eye_h, segments=32)
    m.add_cylinder(13.0, eye_y, 4.0, eye_r - 2.0, eye_h + 1.0, segments=32)

    # 👄 "BOCA / SONRISA": Bisel curvo que enmarca la pantalla OLED
    m.add_box(-20.0, eye_y + 4.0, -8.0, 40.0, 12.0, 10.0)

    # Bancadas laterales para apoyar los pernos de la cuna
    m.add_box(47.0, -8.0, 2.0, 7.0, 16.0, 18.0)
    m.add_box(-54.0, -8.0, 2.0, 7.0, 16.0, 18.0)

    return m

# ----------------------------------------------------------------------------
# 4. TAPA INFERIOR (Plato base con patas estilo ovni)
# ----------------------------------------------------------------------------
def build_bottom_lid():
    m = Mesh3D("bottom_service_lid")
    r_lid = 58.0
    t = 4.0

    # Disco con borde biselado
    m.add_cone_frustum(0, 0, 0, r_lid, r_lid - 2.0, t, segments=56)

    # 3 Patas redondas tipo OVNI para máxima estabilidad
    for i in range(3):
        ang = i * (2.0 * math.pi / 3.0)
        px = 44.0 * math.cos(ang)
        py = 44.0 * math.sin(ang)
        m.add_cylinder(px, py, -3.0, 8.0, 3.0, segments=24)

    # Rejillas de ventilación radiales
    for i in range(8):
        ang = i * (math.pi / 4.0)
        rx = 24.0 * math.cos(ang)
        ry = 24.0 * math.sin(ang)
        m.add_cylinder(rx, ry, 0, 3.0, t + 1.0, segments=12)

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
