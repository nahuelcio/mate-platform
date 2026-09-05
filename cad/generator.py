"""
Parametric 3D generator for mate-platform components.
Generates ready-to-3D-print ASCII / Binary STL files directly without external CAD dependencies.
"""
import struct
import math
import os

class Mesh3D:
    def __init__(self, name="object"):
        self.name = name
        self.triangles = []  # List of (normal, v1, v2, v3)

    def add_triangle(self, v1, v2, v3):
        # Calculate normal
        ux, uy, uz = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
        vx, vy, vz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        norm = math.sqrt(nx * nx + ny * ny + nz * nz)
        if norm > 1e-9:
            normal = (nx / norm, ny / norm, nz / norm)
        else:
            normal = (0.0, 0.0, 1.0)
        self.triangles.append((normal, v1, v2, v3))

    def add_quad(self, v1, v2, v3, v4):
        # Quad split into 2 triangles
        self.add_triangle(v1, v2, v3)
        self.add_triangle(v1, v3, v4)

    def add_box(self, x, y, z, dx, dy, dz):
        # 8 corners
        p0 = (x, y, z)
        p1 = (x + dx, y, z)
        p2 = (x + dx, y + dy, z)
        p3 = (x, y + dy, z)
        p4 = (x, y, z + dz)
        p5 = (x + dx, y, z + dz)
        p6 = (x + dx, y + dy, z + dz)
        p7 = (x, y + dy, z + dz)

        # Bottom (z)
        self.add_quad(p0, p3, p2, p1)
        # Top (z + dz)
        self.add_quad(p4, p5, p6, p7)
        # Front (y)
        self.add_quad(p0, p1, p5, p4)
        # Back (y + dy)
        self.add_quad(p3, p7, p6, p2)
        # Left (x)
        self.add_quad(p0, p4, p7, p3)
        # Right (x + dx)
        self.add_quad(p1, p2, p6, p5)

    def add_cylinder(self, cx, cy, cz, r, h, segments=36):
        top_pts = []
        bot_pts = []
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            bot_pts.append((x, y, cz))
            top_pts.append((x, y, cz + h))

        # Bottom face & Top face
        c_bot = (cx, cy, cz)
        c_top = (cx, cy, cz + h)
        for i in range(segments):
            next_i = (i + 1) % segments
            # Bottom (normal down)
            self.add_triangle(c_bot, bot_pts[next_i], bot_pts[i])
            # Top (normal up)
            self.add_triangle(c_top, top_pts[i], top_pts[next_i])
            # Side
            self.add_quad(bot_pts[i], bot_pts[next_i], top_pts[next_i], top_pts[i])

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

            # Bottom rim
            self.add_quad(b_out1, b_out2, b_in2, b_in1)
            # Top rim
            self.add_quad(t_out1, t_in1, t_in2, t_out2)
            # Outer wall
            self.add_quad(b_out1, t_out1, t_out2, b_out2)
            # Inner wall
            self.add_quad(b_in1, b_in2, t_in2, t_in1)

    def write_binary_stl(self, filepath):
        header = f"mate-platform {self.name}".encode('ascii')[:80].ljust(80, b'\0')
        count = len(self.triangles)
        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(struct.pack('<I', count))
            for normal, v1, v2, v3 in self.triangles:
                # normal (3 floats)
                f.write(struct.pack('<3f', normal[0], normal[1], normal[2]))
                # v1, v2, v3 (3 floats each)
                f.write(struct.pack('<3f', v1[0], v1[1], v1[2]))
                f.write(struct.pack('<3f', v2[0], v2[1], v2[2]))
                f.write(struct.pack('<3f', v3[0], v3[1], v3[2]))
                # attribute byte count (uint16)
                f.write(struct.pack('<H', 0))
        print(f"[STL] Saved: {filepath} ({count} triangles, {os.path.getsize(filepath)/1024:.1f} KB)")


# ----------------------------------------------------------------------------
# 1. PART 1: TILTING CRADLE (CUNA BASCULANTE 45 GRADOS)
# Holds the mate cup, houses GY-521 IMU underneath, connects to pivot trunnions
# ----------------------------------------------------------------------------
def build_tilting_cradle():
    m = Mesh3D("tilting_cradle")
    # Base disc
    r_cup_inner = 39.0   # Ø 78 mm cup inner seat
    r_cradle_outer = 43.0 # Ø 86 mm outer flange (wall thickness 4mm)
    base_floor_thick = 4.0
    wall_height = 25.0

    # Floor disc
    m.add_cylinder(0, 0, 0, r_cradle_outer, base_floor_thick, segments=48)
    # Cup retaining ring wall
    m.add_pipe_segment(0, 0, base_floor_thick, r_cup_inner, r_cradle_outer, wall_height, segments=48)

    # Pivot Trunnions (Left & Right cylindrical pins for rotation)
    trunnion_pin_r = 3.0    # Ø 6 mm pivot pin
    trunnion_length = 10.0
    # Left pin (pointing +X)
    m.add_cylinder(r_cradle_outer, 0, base_floor_thick + 10.0, trunnion_pin_r, trunnion_length, segments=24)
    # Right pin (pointing -X)
    m.add_cylinder(-r_cradle_outer - trunnion_length, 0, base_floor_thick + 10.0, trunnion_pin_r, trunnion_length, segments=24)

    # Servo horn linkage bracket (Front clevis tab on underside)
    m.add_box(-6.0, -r_cradle_outer + 4.0, -10.0, 12.0, 8.0, 10.0)

    # Under-cradle GY-521 pocket frame
    m.add_box(-12.0, -10.0, -5.0, 24.0, 20.0, 5.0)

    return m

# ----------------------------------------------------------------------------
# 2. PART 2: MAIN HOUSING BODY (CUERPO DE BASE)
# Accommodates ESP32, SG90 Servo, Buzzer, Microswitch, Wire Channels
# ----------------------------------------------------------------------------
def build_main_base():
    m = Mesh3D("main_enclosure_base")
    # Overall base envelope: 120 mm wide (X) x 110 mm deep (Y) x 55 mm high (Z)
    w, d, h = 120.0, 110.0, 55.0
    wall = 2.8

    # Base shell floor
    m.add_box(-w/2, -d/2, 0, w, d, wall)

    # Exterior perimeter walls
    # Back wall
    m.add_box(-w/2, d/2 - wall, 0, w, wall, h)
    # Front wall (lower to allow sensor ring access)
    m.add_box(-w/2, -d/2, 0, w, wall, h * 0.75)
    # Left wall
    m.add_box(-w/2, -d/2, 0, wall, d, h)
    # Right wall
    m.add_box(w/2 - wall, -d/2, 0, wall, d, h)

    # ESP32 Internal Slide-in Rails (centered back)
    esp_x, esp_y = -17.0, 5.0
    # Left rail
    m.add_box(esp_x - 3.0, esp_y, wall, 3.0, 52.0, 14.0)
    # Right rail
    m.add_box(esp_x + 30.0, esp_y, wall, 3.0, 52.0, 14.0)

    # Micro-USB / USB-C back cutout support
    m.add_box(-8.0, d/2 - wall, wall + 3.0, 16.0, wall, 10.0)

    # SG90 Servo Pocket Mounting Brackets (Rigid front-left)
    servo_w, servo_l = 13.0, 23.5
    m.add_box(-38.0, -25.0, wall, servo_w + 4.0, 4.0, 24.0)
    m.add_box(-38.0, -25.0 + servo_l, wall, servo_w + 4.0, 4.0, 24.0)

    # Buzzer acoustic cavity (Rigid rear-right)
    m.add_cylinder(35.0, 25.0, wall, 8.0, 12.0, segments=24)

    # Internal M3 corner screw bosses (4x)
    boss_r = 4.5
    for bx in [-w/2 + 8.0, w/2 - 8.0]:
        for by in [-d/2 + 8.0, d/2 - 8.0]:
            m.add_cylinder(bx, by, wall, boss_r, h - wall, segments=20)

    return m

# ----------------------------------------------------------------------------
# 3. PART 3: UPPER SENSOR BEZEL & OLED HOOD (ANILLO DE SENSORES Y PANTALLA)
# Houses SSD1306 0.96", HC-SR04 ultrasonic eyes, GY-MAX9814 mic grille
# ----------------------------------------------------------------------------
def build_upper_sensor_fascia():
    m = Mesh3D("upper_sensor_fascia")
    w, d, h = 120.0, 110.0, 18.0
    wall = 2.4

    # Top cover plate with large central recess for tilting cradle
    m.add_box(-w/2, -d/2, 0, w, d, wall)

    # Center cradle aperture boundary ring (Ø 92 mm inner)
    m.add_pipe_segment(0, 0, wall, 46.0, 49.0, 14.0, segments=48)

    # Front Angled Display Hood for SSD1306 OLED (angled 30 degrees toward user)
    # OLED frame: 32 mm wide x 30 mm tall
    m.add_box(-20.0, -d/2 - 6.0, 0, 40.0, 12.0, 22.0)

    # HC-SR04 Proximity Sensor Eye Mounts (Left and Right ultrasonic cylinders)
    # 26mm spacing between centers
    m.add_cylinder(-13.0, -d/2 + 15.0, 0, 9.5, 14.0, segments=24)
    m.add_cylinder(13.0, -d/2 + 15.0, 0, 9.5, 14.0, segments=24)

    # GY-MAX9814 Microphone internal retention clip
    m.add_box(32.0, -d/2 + 8.0, 0, 18.0, 12.0, 10.0)

    # Pivot Trunnion Stanchions / Bearings (Hold the cradle pivot pins)
    # Left support
    m.add_box(-52.0, -6.0, wall, 5.0, 12.0, 16.0)
    # Right support
    m.add_box(47.0, -6.0, wall, 5.0, 12.0, 16.0)

    return m

# ----------------------------------------------------------------------------
# 4. PART 4: BOTTOM SERVICE BASE LID (TAPA INFERIOR DE SERVICIO)
# ----------------------------------------------------------------------------
def build_bottom_lid():
    m = Mesh3D("bottom_service_lid")
    w, d, t = 118.0, 108.0, 2.5

    # Base flat lid
    m.add_box(-w/2, -d/2, 0, w, d, t)

    # 4x Rubber foot recesses (Ø 12 mm x 1.5 mm deep rim)
    for fx in [-w/2 + 10.0, w/2 - 10.0]:
        for fy in [-d/2 + 10.0, d/2 - 10.0]:
            m.add_pipe_segment(fx, fy, t, 4.5, 6.5, 1.5, segments=24)

    # Ventilation grid louvers (8 ribs across center)
    for i in range(-4, 4):
        vy = i * 8.0
        m.add_box(-30.0, vy, t, 60.0, 3.0, 1.2)

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
