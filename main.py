import cv2
import numpy as np
import time
import uuid
import threading
import tkinter as tk
from ultralytics import YOLO
from deepface import DeepFace
from concurrent.futures import ThreadPoolExecutor
import db_config

# ── MediaPipe (mejor detección facial) ──────────────────────────────
USE_MP = False
face_det_mp = None
try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    import urllib.request
    import os

    _model_path = os.path.join(
        os.path.dirname(__file__), "blaze_face_short_range.tflite"
    )
    if not os.path.exists(_model_path):
        print("Descargando modelo MediaPipe...")
        urllib.request.urlretrieve(
            "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
            _model_path,
        )
    _opts = mp_vision.FaceDetectorOptions(
        base_options=mp_python.BaseOptions(model_asset_path=_model_path),
        min_detection_confidence=0.45,
    )
    face_det_mp = mp_vision.FaceDetector.create_from_options(_opts)
    USE_MP = True
    print("MediaPipe FaceDetector: OK")
except Exception as _mpe:
    print(f"MediaPipe no disponible ({_mpe}), usando Haar Cascade")
    USE_MP = False

face_cas1 = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
face_cas2 = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
)

# ── Constantes ───────────────────────────────────────────────────────
REID_THR = 0.45
REID_MAX_AGE = 600
OBJ_COOL = 15
ANAL_COOL = 3.0
MIN_W = 55
REID_TIMEOUT = 8.0
DOOR_LINE_Y_PCT = 0.75   # Línea virtual de puerta (75% del alto)
DOOR_COOLDOWN   = 3.0   # Segundos mínimos entre eventos de puerta
FPS_DF_MIN      = 10    # FPS mínimo para ejecutar DeepFace
# Paleta DISPL (BGR)
C_PRPL = (255,  47, 123)   # #7B2FFF  bounding box
C_CYAN = (255, 230,   0)   # #00E6FF  línea de puerta
C_GRN  = (80,  210, 100)   # entrada
C_RED  = (60,   60, 230)   # salida
C_GREY = (150, 150, 150)   # identificando

ZONAS = {
    "#1 Escolar": {"id_db": 1, "coords": (0, 0, 640, 720)},
    "#2 Tecno": {"id_db": 2, "coords": (640, 0, 1280, 360)},
    "#3 Papelería": {"id_db": 3, "coords": (640, 360, 1280, 720)},
}

person_counter = 0
door_events = {"ENTRADA": 0, "SALIDA": 0}  # Contador diario

# ══════════════════════════════════════════════════════════════════
# SELECTOR DE CÁMARA (Tkinter)
# ══════════════════════════════════════════════════════════════════
def scan_cams():
    found = []
    for i in range(6):
        c = cv2.VideoCapture(i)
        if c.isOpened():
            ret, _ = c.read()
            if ret:
                found.append(i)
            c.release()
    return found or [0]

def select_cam_gui(cams):
    if len(cams) == 1:
        return cams[0]
    res = [cams[0]]
    root = tk.Tk()
    root.title("Retail Analytics - Camara")
    root.geometry("340x350")
    root.configure(bg="#0f0f1a")
    root.resizable(False, False)
    tk.Label(
        root,
        text="Sistema de Analitica Retail",
        bg="#0f0f1a",
        fg="#9b7fff",
        font=("Helvetica", 13, "bold"),
    ).pack(pady=14)
    tk.Label(
        root,
        text="Selecciona la camara:",
        bg="#0f0f1a",
        fg="#aaaacc",
        font=("Helvetica", 10),
    ).pack()
    var = tk.IntVar(value=cams[0])
    for i in cams:
        tk.Radiobutton(
            root,
            text=f"  Camara {i}",
            variable=var,
            value=i,
            bg="#0f0f1a",
            fg="white",
            selectcolor="#2a2a4e",
            font=("Helvetica", 11),
        ).pack(anchor="w", padx=40, pady=2)

    def ok():
        res[0] = var.get()
        root.destroy()

    tk.Button(
        root,
        text="  Iniciar  ",
        command=ok,
        bg="#7B2FFF",
        fg="white",
        font=("Helvetica", 11, "bold"),
        relief="flat",
        padx=20,
        pady=7,
        cursor="hand2",
    ).pack(pady=14)
    root.mainloop()
    return res[0]

# ══════════════════════════════════════════════════════════════════
# DETECCIÓN FACIAL MEJORADA
# ══════════════════════════════════════════════════════════════════
def detect_faces(img):
    h, w = img.shape[:2]
    if w < 20 or h < 20:
        return []
    boxes = []
    if USE_MP and face_det_mp:
        try:
            mp_img = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
            )
            res = face_det_mp.detect(mp_img)
            if res.detections:
                for det in res.detections:
                    bb = det.bounding_box
                    fx, fy = max(0, bb.origin_x), max(0, bb.origin_y)
                    fw, fh = bb.width, bb.height
                    if fw > 15 and fh > 15:
                        boxes.append((fx, fy, min(fw, w - fx), min(fh, h - fy)))
        except:
            pass
    if not boxes:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for cas in [face_cas1, face_cas2]:
            f = cas.detectMultiScale(gray, 1.05, 4, minSize=(22, 22))
            if len(f) > 0:
                boxes = list(f)
                break
    boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
    return boxes


# ══════════════════════════════════════════════════════════════════
# DB
# ══════════════════════════════════════════════════════════════════
conexion_db = db_config.conectar_bd()
cursor = None
db_lock = threading.Lock()
if conexion_db:
    cursor = conexion_db.cursor()


def db_run(q, p=None):
    with db_lock:
        try:
            if conexion_db and conexion_db.is_connected():
                cursor.execute(q, p or ())
                conexion_db.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"DB:{e}")
            try:
                conexion_db.reconnect(attempts=2, delay=1)
            except:
                pass
    return None


# ══════════════════════════════════════════════════════════════════
# RE-ID GALLERY
# ══════════════════════════════════════════════════════════════════
reid_gallery = []
reid_lock = threading.Lock()


def cosine_d(a, b):
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    n = np.linalg.norm(a) * np.linalg.norm(b)
    return 1.0 - float(np.dot(a, b) / n) if n else 1.0


def reid_search(emb):
    with reid_lock:
        best, bd = None, REID_THR
        now = time.time()
        for e in reid_gallery:
            if e["emb"] is None or now - e["t"] > REID_MAX_AGE:
                continue
            d = cosine_d(emb, e["emb"])
            if d < bd:
                bd, best = d, e
        return best


def reid_upsert(tid, emb):
    with reid_lock:
        for e in reid_gallery:
            if e["tid"] == tid:
                e["emb"] = emb
                e["t"] = time.time()
                return
        reid_gallery.append({"tid": tid, "emb": emb, "t": time.time()})


# ══════════════════════════════════════════════════════════════════
# MEMORIA DE PERSONAS
# ══════════════════════════════════════════════════════════════════
yolo_map = {}  # yolo_id -> track_id | None
personas = {}  # track_id -> datos
temp_yolo = {}  # yolo_id -> {first_seen, future}  (esperando Re-ID)
pend_anal = {}  # track_id -> Future
obj_logged = {}  # clase -> timestamp

executor = ThreadPoolExecutor(max_workers=4)


def get_embed(fc):
    try:
        r = DeepFace.represent(
            fc, model_name="Facenet", detector_backend="skip", enforce_detection=False
        )
        return r[0]["embedding"]
    except:
        return None


def new_person(yid, now, emb=None):
    global person_counter
    person_counter += 1
    tid = f"trk_{uuid.uuid4().hex[:8]}"
    yolo_map[yid] = tid
    personas[tid] = dict(
        track_id=tid, yid=yid, num=person_counter,
        age="--", gender="--", emotion="--",
        ingreso=now, zona_actual=None,
        id_visita_db=None, id_movimiento_db=None,
        last_face_c=None, last_face_t=0,
        reid_match=False, last_anal_t=0,
        prev_cy=None, last_door_t=0, door_flash=0,  # trip-wire
        last_seen_t=now,
    )
    lid = db_run("INSERT INTO fact_visitas_ia (track_id) VALUES (%s)", (tid,))
    if lid:
        personas[tid]["id_visita_db"] = lid
    if emb:
        reid_upsert(tid, emb)
    return tid


# ══════════════════════════════════════════════════════════════════
# DIBUJO (estilo DISPL)
# ══════════════════════════════════════════════════════════════════
def draw_corners(img, x1, y1, x2, y2, color, t=3, L=22):
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 1)  # thin full rect
    for px, py, dx, dy in [
        (x1, y1, 1, 1), (x2, y1, -1, 1),
        (x1, y2, 1, -1), (x2, y2, -1, -1),
    ]:
        cv2.line(img, (px, py), (px + dx * L, py), color, t)
        cv2.line(img, (px, py), (px, py + dy * L), color, t)


def fill_rrect(img, x1, y1, x2, y2, color, r=8):
    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
    for cx, cy in [
        (x1 + r, y1 + r), (x2 - r, y1 + r),
        (x1 + r, y2 - r), (x2 - r, y2 - r),
    ]:
        cv2.circle(img, (cx, cy), r, color, -1)


def cls_color(cid):
    h = int((cid * 137) % 180)
    b = cv2.cvtColor(np.uint8([[[h, 210, 230]]]), cv2.COLOR_HSV2BGR)[0][0]
    return (int(b[0]), int(b[1]), int(b[2]))


def draw_pill_label(frame, text, cx, top_y, color, ancho):
    """Etiqueta tipo píldora centrada — estilo DISPL."""
    (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.46, 1)
    pw, ph = tw + 22, 22
    lx = max(4, min(cx - pw // 2, ancho - pw - 4))
    ly = top_y - ph - 6
    if ly < 0:
        ly = top_y + 6
    fill_rrect(frame, lx, ly, lx + pw, ly + ph, color, r=11)
    cv2.putText(frame, text, (lx + 11, ly + ph - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1, cv2.LINE_AA)


def draw_info_panel(frame, datos, dwell, poi, x1, y1, x2, y2, ancho, alto):
    pw, ph = 245, 165
    px = x2 + 12 if x2 + 12 + pw < ancho else x1 - pw - 12
    if px < 0:
        px = max(4, x1 + 8)
    py = min(y1 + 5, alto - ph - 4)
    py = max(4, py)
    px2, py2 = px + pw, py + ph
    if not (0 <= px and px2 <= ancho and 0 <= py and py2 <= alto):
        return
    roi = frame[py:py2, px:px2]
    if roi.shape[:2] != (ph, pw):
        return
    blur = cv2.GaussianBlur(roi, (45, 45), 0)
    ov = np.zeros_like(blur)
    pan = cv2.addWeighted(blur, 0.40, ov, 0.60, 0)
    gm = np.zeros((ph, pw, 3), np.uint8)
    fill_rrect(gm, 0, 0, pw, ph, (255, 255, 255), 12)
    frame[py:py2, px:px2] = np.where(gm == 255, pan, roi)
    tx, sy, lh = px + 14, py + 24, 26
    G, W = (185, 185, 185), (255, 255, 255)
    rows = [
        ("Dwell time:", dwell),
        ("Zona POI:", poi),
        ("Género:", str(datos["gender"])),
        ("Edad:", str(datos["age"])),
        ("Expresión:", str(datos["emotion"])),
    ]
    for i, (lb, vl) in enumerate(rows):
        cv2.putText(frame, lb, (tx, sy + i * lh), cv2.FONT_HERSHEY_SIMPLEX, 0.44, G, 1)
        cv2.putText(
            frame, vl, (tx + 115, sy + i * lh), cv2.FONT_HERSHEY_SIMPLEX, 0.44, W, 1
        )


# ══════════════════════════════════════════════════════════════════
# INICIO
# ══════════════════════════════════════════════════════════════════
print("Escaneando camaras...")
cams = scan_cams()
cam_idx = select_cam_gui(cams)
print(f"Cargando YOLOv8s...")
modelo_yolo = YOLO("yolov8s.pt")
COCO = modelo_yolo.model.names


def open_cam(idx):
    c = cv2.VideoCapture(idx)
    c.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    c.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    c.set(cv2.CAP_PROP_FPS, 30)
    c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return c


cap = open_cam(cam_idx)
WN = "Retail Analytics SOTA v2"
cv2.namedWindow(WN, cv2.WINDOW_NORMAL)
fps_cnt = fps_t = 0
fps_display = 0
fps_t = time.time()
print(f"Sistema iniciado | MediaPipe={'SI' if USE_MP else 'NO (Haar)'}")

# ══════════════════════════════════════════════════════════════════
# BUCLE PRINCIPAL
# ══════════════════════════════════════════════════════════════════
frame_count = 0
last_ro = None

while True:
    ret, forig = cap.read()
    if not ret:
        print("Sin camara, reconectando...")
        cap.release()
        time.sleep(1)
        cap = open_cam(cam_idx)
        continue
    if cv2.getWindowProperty(WN, cv2.WND_PROP_VISIBLE) < 1:
        break

    frame = cv2.resize(forig, (1280, 720))
    alto, ancho = frame.shape[:2]
    now = time.time()
    fps_cnt += 1
    frame_count += 1
    if now - fps_t >= 1.0:
        fps_display = fps_cnt
        fps_cnt = 0
        fps_t = now

    # ── YOLO: personas + objetos en UNA sola pasada (Alta Res) ────
    rp = modelo_yolo.track(
        frame,
        persist=True,
        tracker="botsort.yaml",
        imgsz=640,
        conf=0.30,
        verbose=False,
        classes=[0, 24, 26, 28, 39, 41, 63, 67, 73],  # Filtro: persona, mochila, bolso, maleta, botella, taza, laptop, celular, libro
    )

    pc, oc = 0, 0
    obj_frame = {}
    personas_en_frame = []
    DOOR_Y = int(alto * DOOR_LINE_Y_PCT)

    if rp[0].boxes is not None and len(rp[0].boxes) > 0:
        has_ids = rp[0].boxes.id is not None
        ids = rp[0].boxes.id.int().cpu().tolist() if has_ids else [None] * len(rp[0].boxes)

        for box_idx, box_tensor in enumerate(rp[0].boxes):
            cid = int(box_tensor.cls[0])
            box = box_tensor.xyxy[0].cpu().numpy()
            
            # ══ PERSONAS (Clase 0) ════════════════════════════════
            if cid == 0:
                yid = ids[box_idx]
                if yid is None:
                    continue
                pc += 1
                x1, y1, x2, y2 = map(int, box)
                if (x2 - x1) < MIN_W:
                    continue
                crop = forig[max(0, y1) : min(alto, y2), max(0, x1) : min(ancho, x2)]

                # ── Nuevo yolo_id → iniciar Re-ID ──────────────────
                if yid not in yolo_map and yid not in temp_yolo:
                    faces = detect_faces(crop)
                    ft = None
                    if faces:
                        fx, fy, fw, fh = faces[0]
                        fc = crop[fy : fy + fh, fx : fx + fw].copy()
                        ft = executor.submit(get_embed, fc)
                    temp_yolo[yid] = {"t": now, "future": ft}

                # ── Resolver Re-ID pendiente ────────────────────────
                if yid in temp_yolo:
                    tp = temp_yolo[yid]
                    resolved = False
                    if tp["future"] and tp["future"].done():
                        emb = tp["future"].result()
                        if emb:
                            m = reid_search(emb)
                            if m:
                                old = m["tid"]
                                yolo_map[yid] = old
                                if old in personas:
                                    personas[old]["yid"] = yid
                                    personas[old]["reid_match"] = True
                                reid_upsert(old, emb)
                                print(f"Re-ID yolo#{yid} -> {old}")
                            else:
                                new_person(yid, now, emb)
                        else:
                            new_person(yid, now)
                        del temp_yolo[yid]
                        resolved = True
                    elif tp["future"] is None or (now - tp["t"]) > REID_TIMEOUT:
                        new_person(yid, now)
                        del temp_yolo[yid]
                        resolved = True
                    if not resolved:
                        draw_corners(frame, x1, y1, x2, y2, C_GREY)
                        draw_pill_label(
                            frame, "Identificando...", (x1 + x2) // 2, y1, C_GREY, ancho
                        )
                        continue

                tid = yolo_map.get(yid)
                if not tid or tid not in personas:
                    continue
                d = personas[tid]
                d["yid"] = yid
                d["last_seen_t"] = now

                # ── Detección facial en crop (Limitada a 5 FPS) ────────
                if "last_face_t" not in d or (now - d.get("last_face_t", 0)) > 0.2:
                    faces = detect_faces(crop)
                    if faces:
                        fx, fy, fw, fh = faces[0]
                        bw, bh = max(1, x2 - x1), max(1, y2 - y1)
                        d["last_face_c"] = (fx / bw, fy / bh, fw / bw, fh / bh)
                        d["last_face_t"] = now

                fc_rel = d.get("last_face_c")
                fc_age = now - d.get("last_face_t", 0)

                if fc_rel and fc_age < 3.0:
                    rfx, rfy, rfw, rfh = fc_rel
                    bw, bh = x2 - x1, y2 - y1
                    fxa = int(x1 + rfx * bw)
                    fya = int(y1 + rfy * bh)
                    fwa = int(rfw * bw)
                    fha = int(rfh * bh)
                    bx1, by1 = max(0, fxa), max(0, fya)
                    bx2, by2 = min(ancho, fxa + fwa), min(alto, fya + fha)
                    if bx2 > bx1 and by2 > by1:
                        roi = frame[by1:by2, bx1:bx2]
                        kw = max(3, (bx2 - bx1) // 2) | 1
                        kh = max(3, (by2 - by1) // 2) | 1
                        frame[by1:by2, bx1:bx2] = cv2.GaussianBlur(roi, (kw * 3, kh * 3), 0)
                    draw_corners(
                        frame, fxa, fya, fxa + fwa, fya + fha, (230, 130, 230), t=2, L=12
                    )

                    # ── Análisis facial async ──────────────────────
                    done_k = tid in pend_anal and pend_anal[tid].done()
                    free_k = tid not in pend_anal
                    if done_k:
                        try:
                            r = pend_anal.pop(tid).result()
                            if r:
                                d["age"], d["gender"], d["emotion"] = r
                                if d.get("id_visita_db"):
                                    db_run(
                                        "UPDATE fact_visitas_ia SET edad_estimada=%s,"
                                        "genero=%s,emocion_dominante=%s WHERE id_visita=%s",
                                        (r[0], r[1], r[2], d["id_visita_db"]),
                                    )
                        except:
                            pass
                    if (
                        (free_k or done_k)
                        and (now - d.get("last_anal_t", 0)) > ANAL_COOL
                        and fc_age < 3.0
                    ):
                        d["last_anal_t"] = now
                        local_x = int(rfx * bw)
                        local_y = int(rfy * bh)
                        cara = crop[local_y : local_y + fha, local_x : local_x + fwa].copy()

                        def _anal(c):
                            try:
                                a = DeepFace.analyze(
                                    c,
                                    actions=["age", "gender", "emotion"],
                                    detector_backend="skip",
                                    enforce_detection=False,
                                    silent=True,
                                )
                                return (
                                    int(a[0]["age"]),
                                    (
                                        "Hombre"
                                        if a[0]["dominant_gender"] == "Man"
                                        else "Mujer"
                                    ),
                                    {
                                        "angry": "Enojado", "disgust": "Disgusto", "fear": "Miedo",
                                        "happy": "Feliz", "sad": "Triste", "surprise": "Sorpresa", "neutral": "Neutral"
                                    }.get(a[0]["dominant_emotion"].lower(), a[0]["dominant_emotion"].capitalize()),
                                )
                            except:
                                return None

                        pend_anal[tid] = executor.submit(_anal, cara)

                # ── Dwell + Geofencing ────────────────────────────
                seg = int(now - d["ingreso"])
                m, s = divmod(seg, 60)
                dwell = f"{m:02d}:{s:02d}"
                pxc = (x1 + x2) // 2
                poi = "Ninguna"
                for nz, iz in ZONAS.items():
                    zx1, zy1, zx2, zy2 = iz["coords"]
                    if zx1 <= pxc <= zx2 and zy1 <= y2 <= zy2:
                        poi = nz
                        if d["zona_actual"] != nz:
                            if d["id_movimiento_db"]:
                                db_run(
                                    "UPDATE fact_movimientos_ia SET fecha_salida=NOW() "
                                    "WHERE id_movimiento=%s",
                                    (d["id_movimiento_db"],),
                                )
                            d["zona_actual"] = nz
                            if d.get("id_visita_db"):
                                lid = db_run(
                                    "INSERT INTO fact_movimientos_ia "
                                    "(id_visita,id_zona,fecha_ingreso) VALUES(%s,%s,NOW())",
                                    (d["id_visita_db"], iz["id_db"]),
                                )
                                d["id_movimiento_db"] = lid
                        break
                if poi == "Ninguna" and d["zona_actual"]:
                    if d["id_movimiento_db"]:
                        db_run(
                            "UPDATE fact_movimientos_ia SET fecha_salida=NOW() "
                            "WHERE id_movimiento=%s",
                            (d["id_movimiento_db"],),
                        )
                    d["zona_actual"] = None
                    d["id_movimiento_db"] = None

                # ── Trip-wire: detección entrada/salida ─────────────────
                cy_curr = y2  # Usar la base de la persona (pies)
                prev_cy = d.get("prev_cy")
                if prev_cy is not None and (now - d.get("last_door_t", 0)) > DOOR_COOLDOWN:
                    if prev_cy < DOOR_Y <= cy_curr:      # cruzó hacia abajo → SALIDA
                        door_events["SALIDA"] += 1
                        d["last_door_t"] = now
                        d["door_flash"] = 15
                        d["last_door_tipo"] = "SALIDA"
                        db_run("INSERT INTO fact_entradas_salidas (track_id,tipo,reid_match) VALUES(%s,%s,%s)",
                               (tid, "SALIDA", d["reid_match"]))
                        print(f"[PUERTA] SALIDA  {tid}")
                    elif prev_cy > DOOR_Y >= cy_curr:    # cruzó hacia arriba → ENTRADA
                        door_events["ENTRADA"] += 1
                        d["last_door_t"] = now
                        d["door_flash"] = 15
                        d["last_door_tipo"] = "ENTRADA"
                        db_run("INSERT INTO fact_entradas_salidas (track_id,tipo,reid_match) VALUES(%s,%s,%s)",
                               (tid, "ENTRADA", d["reid_match"]))
                        print(f"[PUERTA] ENTRADA {tid}")
                d["prev_cy"] = cy_curr

                # ── Render DISPL-style ────────────────────────────────
                col = C_GRN if d["reid_match"] else C_PRPL
                if d.get("door_flash", 0) > 0:
                    col = C_GRN if d.get("last_door_tipo") == "ENTRADA" else C_RED
                draw_corners(frame, x1, y1, x2, y2, col)
                personas_en_frame.append((tid, x1, y1, x2, y2))
                label = f"Anonymous Hash #{d['num']:03d}"
                draw_pill_label(frame, label, (x1 + x2) // 2, y1, col, ancho)
                draw_info_panel(frame, d, dwell, poi, x1, y1, x2, y2, ancho, alto)

            # ══ OTROS OBJETOS ════════════════════════════════════════
            else:
                MAPA_NOMBRES_OBJ = {24: 'Mochila', 67: 'Celular', 39: 'Botella', 73: 'Libro', 26: 'Bolso', 28: 'Maleta', 41: 'Taza', 63: 'Laptop'}
                MAPA_PRODUCTOS = {24: 1, 67: 2, 39: 3, 73: 4}
                cn = MAPA_NOMBRES_OBJ.get(cid, COCO.get(cid, f"obj{cid}"))
                cf = float(box_tensor.conf[0])
                ox1, oy1, ox2, oy2 = map(int, box)
                col = cls_color(cid)
                oc += 1
                obj_frame[cn] = obj_frame.get(cn, 0) + 1
                draw_corners(frame, ox1, oy1, ox2, oy2, col, t=2, L=10)
                lbl = f"{cn} {cf:.0%}"
                (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)
                if oy1 - 16 >= 0:
                    cv2.rectangle(frame, (ox1, oy1 - 16), (ox1 + tw + 8, oy1), col, -1)
                    cv2.putText(
                        frame,
                        lbl,
                        (ox1 + 4, oy1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.38,
                        (255, 255, 255),
                        1,
                    )
                mid_x = (ox1 + ox2) // 2
                mid_y = (oy1 + oy2) // 2
                zona_o = "Fuera de zona"
                for nz, iz in ZONAS.items():
                    zc = iz["coords"]
                    if zc[0] <= mid_x <= zc[2] and zc[1] <= mid_y <= zc[3]:
                        zona_o = nz
                        break
                if now - obj_logged.get(cn, 0) > OBJ_COOL:
                    obj_logged[cn] = now
                    db_run(
                        "INSERT INTO fact_objetos_detectados "
                        "(clase_objeto,confianza,zona_detectada) VALUES(%s,%s,%s)",
                        (cn, round(cf, 3), zona_o),
                    )

                # ── Interacciones IA (Persona + Objeto) ──
                if cid in MAPA_PRODUCTOS:
                    for ptid, px1, py1, px2, py2 in personas_en_frame:
                        # Comprobar intersección de cajas (bounding boxes)
                        if not (px2 < ox1 or px1 > ox2 or py2 < oy1 or py1 > oy2):
                            id_prod = MAPA_PRODUCTOS[cid]
                            d_p = personas.get(ptid)
                            if d_p and d_p.get("id_visita_db"):
                                k = f"int_{ptid}_{id_prod}"
                                if now - obj_logged.get(k, 0) > OBJ_COOL:
                                    obj_logged[k] = now
                                    db_run("INSERT INTO fact_interacciones_ia (id_visita, id_producto, tipo_accion, emocion_detectada, fecha_hora) VALUES (%s, %s, %s, %s, NOW())",
                                        (d_p["id_visita_db"], id_prod, "interaccion_fisica", d_p.get("emotion", "Neutral")))
                            break

    # ── Limpieza de personas que salieron del cuadro ───────────────
    TIEMPO_GRACIA = 10.0
    for tid_cl, d_cl in list(personas.items()):
        if now - d_cl.get("last_seen_t", now) > TIEMPO_GRACIA:
            if d_cl.get("id_movimiento_db"):
                db_run(
                    "UPDATE fact_movimientos_ia SET fecha_salida=NOW() "
                    "WHERE id_movimiento=%s",
                    (d_cl["id_movimiento_db"],),
                )
            if d_cl.get("yid") in yolo_map:
                del yolo_map[d_cl["yid"]]
            del personas[tid_cl]
            print(f"[LIMPIEZA] Persona {tid_cl} salio del cuadro.")

    # ── Linea de puerta animada (pulso cian) ──────────────────────
    pulse = 1 if (frame_count // 15) % 2 == 0 else 2
    cv2.line(frame, (0, DOOR_Y), (ancho, DOOR_Y), C_CYAN, pulse)
    cv2.putText(frame, "< PUERTA >", (ancho // 2 - 50, DOOR_Y - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_CYAN, 1, cv2.LINE_AA)
    # Flashes de entrada/salida
    for tid_f, d_f in personas.items():
        if d_f.get("door_flash", 0) > 0:
            d_f["door_flash"] -= 1

    # ── HUD DISPL ────────────────────────────────────────────────
    top = np.zeros((44, ancho, 3), np.uint8)
    cv2.rectangle(top, (0, 0), (ancho, 44), (14, 10, 22), -1)
    cv2.putText(top, "RETAIL ANALYTICS", (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.60, C_CYAN, 2, cv2.LINE_AA)
    hud_right = (f"FPS:{fps_display}  IN:{door_events['ENTRADA']}  "
                 f"OUT:{door_events['SALIDA']}  Personas:{pc}")
    (hw, _), _ = cv2.getTextSize(hud_right, cv2.FONT_HERSHEY_SIMPLEX, 0.46, 1)
    cv2.putText(top, hud_right, (ancho - hw - 10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.46, (200, 200, 220), 1, cv2.LINE_AA)
    # Punto LIVE parpadeante
    live_col = C_GRN if (frame_count // 20) % 2 == 0 else (50, 150, 50)
    cv2.circle(top, (ancho // 2, 22), 5, live_col, -1)
    cv2.putText(top, "LIVE", (ancho // 2 + 10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.40, live_col, 1, cv2.LINE_AA)
    frame[0:44] = cv2.addWeighted(frame[0:44], 0.15, top, 0.85, 0)

    cv2.imshow(WN, frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

executor.shutdown(wait=False)
cap.release()
cv2.destroyAllWindows()
if conexion_db and conexion_db.is_connected():
    cursor.close()
    conexion_db.close()
print("Sistema cerrado.")