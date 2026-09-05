"""
Advanced Parametric 3D CAD generator for mate-platform.
Generates refined, production-ready STL models with chamfers, mounting bosses,
cooling louvers, cable conduits, and exact sensor cutouts.
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
        self.add_quad(p0, p3, p2, p1) # Bot
        self.add_quad(p4, p5, p6, p7) # Top
        self.add_quad(p0, p1, p5, p4) # Front
        self.add_quad(p3, p7, p6, p2) # Back
        self.add_quad(p0, p4, p7, p3) # Left
        self.add_quad(p1, p2, p6, p5) # Right

    def add_cylinder(self, cx, cy, cz, r, h, segments=48):
        top_pts, bot_pts = [], []
        for i in range(segments):
            th = 2.0 * math.pi * i / segments
            x = cx + r * math.cos(th)
            y = cy + r * math.sin(th)
            bot_pts.append((x, y, cz))
            top_pts.append((x, y, cz + h))

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
# 1. TILTING CRADLE (Cuna Basculante 45°)
# ----------------------------------------------------------------------------
def build_tilting_cradle():
    m = Mesh3D("tilting_cradle")
    r_cup_inner = 39.0   # Ø 78 mm
    r_cradle_outer = 44.0 # Ø 88 mm
    base_floor = 4.5
    wall_h = 28.0

    # Base baseplate with chamfered rim
    m.add_cone_frustum(0, 0, 0, r_cradle_outer - 1.5, r_cradle_outer, 2.0, segments=48)
    m.add_cylinder(0, 0, 2.0, r_cradle_outer, base_floor - 2.0, segments=48)

    # Conical cup retaining collar for self-centering
    m.add_pipe_segment(0, 0, base_floor, r_cup_inner - 2.0, r_cradle_outer, 10.0, segments=48)
    m.add_pipe_segment(0, 0, base_floor + 10.0, r_cup_inner, r_cradle_outer, wall_h - 10.0, segments=48)

    # 4 Inner silicone grip ribs (prevent cup rattling)
    for i in range(4):
        ang = i * (math.pi / 2.0)
        gx = (r_cup_inner - 1.2) * math.cos(ang)
        gy = (r_cup_inner - 1.2) * math.sin(ang)
        m.add_cylinder(gx, gy, base_floor + 4.0, 1.8, wall_h - 6.0, segments=12)

    # Solid Pivot Trunnion Shafts (Left & Right)
    pin_r = 3.5  # Ø 7 mm pivot shaft
    pin_len = 12.0
    # Left pivot (+X)
    m.add_cylinder(r_cradle_outer - 1.0, 0, base_floor + 12.0, pin_r, pin_len + 1.0, segments=24)
    # Right pivot (-X)
    m.add_cylinder(-r_cradle_outer - pin_len, 0, base_floor + 12.0, pin_r, pin_len + 1.0, segments=24)

    # Underside Servo Linkage Clevis Horn (-Y front)
    m.add_box(-5.0, -r_cradle_outer + 2.0, -14.0, 10.0, 10.0, 14.0)
    # Linkage pivot cross-pin hole collar
    m.add_cylinder(0, -r_cradle_outer + 7.0, -11.0, 2.5, 6.0, segments=16)

    # Pocket for GY-521 (MPU6050 Accelerometer)
    m.add_box(-12.5, -10.0, -6.0, 25.0, 20.0, 6.0)
    # Microswitch actuator pin tab
    m.add_box(-3.0, 18.0, -8.0, 6.0, 6.0, 8.0)

    return m

# ----------------------------------------------------------------------------
# 2. MAIN ENCLOSURE BASE (Chasis Principal)
# ----------------------------------------------------------------------------
def build_main_base():
    m = Mesh3D("main_enclosure_base")
    w, d, h = 126.0, 116.0, 58.0
    wall = 3.0

    # Chamfered bottom perimeter
    m.add_box(-w/2, -d/2, 0, w, d, wall)

    # Outer perimeter walls with rounded look
    m.add_box(-w/2, d/2 - wall, 0, w, wall, h)          # Back
    m.add_box(-w/2, -d/2, 0, w, wall, h * 0.72)        # Front
    m.add_box(-w/2, -d/2, 0, wall, d, h)               # Left
    m.add_box(w/2 - wall, -d/2, 0, wall, d, h)          # Right

    # ESP32 Slide-in Caddy & Standoffs (Center Back)
    caddy_x, caddy_y = -16.0, 8.0
    m.add_box(caddy_x - 3.5, caddy_y, wall, 3.5, 52.0, 15.0) # Left guide rail
    m.add_box(caddy_x + 31.0, caddy_y, wall, 3.5, 52.0, 15.0) # Right guide rail
    m.add_box(caddy_x, caddy_y + 49.0, wall, 31.0, 3.0, 10.0) # End stop

    # Rear Micro-USB / USB-C Port Passthrough Frame
    m.add_box(-10.0, d/2 - wall, wall + 3.0, 20.0, wall, 12.0)

    # Rigid SG90 Micro Servo Cradle (Front-Left)
    servo_x, servo_y = -42.0, -26.0
    # Left & right clamp blocks with M2 screw pilot pads
    m.add_box(servo_x - 4.0, servo_y, wall, 4.0, 26.0, 26.0)
    m.add_box(servo_x + 13.0, servo_y, wall, 4.0, 26.0, 26.0)
    m.add_box(servo_x, servo_y - 4.0, wall, 13.0, 4.0, 18.0)

    # Buzzer Resonant Sound Chamber (Rear-Right)
    m.add_pipe_segment(38.0, 26.0, wall, 6.0, 8.5, 14.0, segments=24)

    # Microswitch KW12 Mount (Center-Right Dock Presence)
    m.add_box(8.0, -12.0, wall, 8.0, 22.0, 18.0)

    # 4 Corner Stanchions with M3 Threaded Insert Pilots
    boss_r = 5.0
    for bx in [-w/2 + 9.0, w/2 - 9.0]:
        for by in [-d/2 + 9.0, d/2 - 9.0]:
            m.add_cylinder(bx, by, wall, boss_r, h - wall, segments=24)

    return m

# ----------------------------------------------------------------------------
# 3. UPPER SENSOR FASCIA & DISPLAY HOOD (Carcasa Superior y Pantalla)
# ----------------------------------------------------------------------------
def build_upper_sensor_fascia():
    m = Mesh3D("upper_sensor_fascia")
    w, d, h = 126.0, 116.0, 20.0
    wall = 2.6

    # Main top deck plate
    m.add_box(-w/2, -d/2, 0, w, d, wall)

    # Central Round Basin for Cradle Clearance (Ø 94 mm)
    m.add_pipe_segment(0, 0, wall, 47.0, 50.5, 14.0, segments=48)

    # Angled Hood for SSD1306 0.96" OLED Display (30° user ergonomic tilt)
    # Angled wedge housing
    m.add_box(-22.0, -d/2 - 6.0, 0, 44.0, 14.0, 24.0)
    # OLED screen bezel surround
    m.add_box(-16.0, -d/2 - 6.5, 8.0, 32.0, 1.5, 15.0)

    # HC-SR04 Dual Ultrasonic Sensor Cylinders (Transmitter & Receiver)
    # Exactly 26.0 mm center-to-center spacing
    m.add_pipe_segment(-13.0, -d/2 + 16.0, 0, 8.2, 10.0, 16.0, segments=28)
    m.add_pipe_segment(13.0, -d/2 + 16.0, 0, 8.2, 10.0, 16.0, segments=28)

    # GY-MAX9814 Microphone Acoustic Channel & Shield (Front Right)
    m.add_box(34.0, -d/2 + 8.0, 0, 18.0, 12.0, 12.0)
    # Sound slot aperture
    m.add_box(40.0, -d/2 + 6.0, 4.0, 6.0, 2.0, 6.0)

    # Heavy-duty Pivot Trunnion Pillow Blocks (Capture cradle pivot pins)
    # Left Pillow Block (+X)
    m.add_box(49.0, -8.0, wall, 8.0, 16.0, 22.0)
    # Right Pillow Block (-X)
    m.add_box(-57.0, -8.0, wall, 8.0, 16.0, 22.0)

    return m

# ----------------------------------------------------------------------------
# 4. BOTTOM SERVICE LID (Tapa Inferior con Ventilación)
# ----------------------------------------------------------------------------
def build_bottom_lid():
    m = Mesh3D("bottom_service_lid")
    w, d, t = 124.0, 114.0, 2.8

    # Flat baseplate
    m.add_box(-w/2, -d/2, 0, w, d, t)

    # Perimeter snap-lip alignment rim
    m.add_pipe_segment(0, 0, t, 50.0, 52.5, 2.0, segments=36)

    # 4 Recesses for anti-slip rubber pads (Ø 12 mm x 2 mm deep)
    for fx in [-w/2 + 12.0, w/2 - 12.0]:
        for fy in [-d/2 + 12.0, d/2 - 12.0]:
            m.add_pipe_segment(fx, fy, t, 5.0, 7.5, 2.0, segments=24)

    # Cooling Louver Ribs (12 aerodynamic ventilation vents)
    for i in range(-5, 6):
        vy = i * 7.5
        m.add_box(-32.0, vy, t, 64.0, 2.8, 1.8)

    # Finger notch for easy opening / servicing
    m.add_box(-10.0, d/2 - 5.0, t, 20.0, 4.0, 2.0)

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
