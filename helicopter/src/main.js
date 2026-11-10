// LCH — interactive attack-helicopter teardown.
// Procedural cinematic 3D (Three.js r160, vendored) + OrbitControls + bloom + full
// procedural Web Audio (rotor thrum, swoosh, typing, clicks). Original work. By Akash M.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const $ = s => document.querySelector(s);
const rand = (a, b) => a + Math.random() * (b - a);
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const damp = (a, b, l, dt) => a + (b - a) * (1 - Math.exp(-l * dt));
const easeIO = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

/* ------------------------------------------------------------------ *
 * Subsystem data (name, role, function, materials, specs)
 * ------------------------------------------------------------------ */
const PARTS = {
  mainRotor: { name: 'Main Rotor', role: 'Lift · thrust · control',
    fn: 'Four hingeless blades spin to generate the lift and directional thrust for hover, climb and manoeuvre. The swashplate changes blade pitch — collectively for altitude and cyclically for direction.',
    mats: ['Carbon-fibre composite blades', 'Titanium hub', 'Elastomeric bearings'],
    specs: [['Blades', '4 · hingeless'], ['Diameter', '13.3 m'], ['Tip speed', '≈210 m/s'], ['Head', 'Soft inplane']] },
  tailRotor: { name: 'Tail Rotor', role: 'Anti-torque · yaw',
    fn: 'Counters the torque of the main rotor so the airframe does not spin, and gives the pilot yaw control through foot pedals.',
    mats: ['Composite blades', 'Steel pitch links', 'Aluminium hub'],
    specs: [['Blades', '4'], ['Type', 'Anti-torque'], ['Control', 'Pedal / collective']] },
  cockpit: { name: 'Tandem Cockpit', role: 'Crew station',
    fn: 'Stepped two-seat crew station — gunner in front, pilot raised behind for visibility. Armoured, with a wide-angle canopy, multi-function glass displays and a helmet-mounted sight.',
    mats: ['Bullet-resistant acrylic canopy', 'Boron / Kevlar armour', 'Composite tub'],
    specs: [['Crew', '2 · tandem'], ['Displays', 'Glass cockpit'], ['Sight', 'Helmet-mounted']] },
  fuselage: { name: 'Fuselage', role: 'Primary airframe',
    fn: 'The structural backbone that carries the cockpit, engines, fuel and rotor loads. A narrow low-drag cross-section and crashworthy, self-sealing design keep the crew protected.',
    mats: ['Aluminium-alloy frames', 'Composite skin panels', 'Crashworthy sub-floor'],
    specs: [['Length', '15.8 m'], ['Section', 'Narrow low-drag'], ['Fuel', 'Self-sealing tanks']] },
  tailBoom: { name: 'Tail Boom', role: 'Structure · stability',
    fn: 'The slender rear structure carries the tail rotor and stabilisers far behind the centre of gravity, giving the long moment arm that keeps the aircraft stable and controllable.',
    mats: ['Monocoque composite', 'Aluminium longerons'],
    specs: [['Carries', 'Tail rotor + fin'], ['Stabiliser', 'Horizontal + vertical']] },
  engine: { name: 'Turboshaft Engines', role: 'Powerplant',
    fn: 'Twin turboshaft engines spin the main and tail rotors through the gearbox. Infra-red-suppressed exhausts mix cool air into the hot gas to reduce the heat signature to missiles.',
    mats: ['Nickel super-alloy turbine', 'Titanium compressor', 'IR-suppressing cowl'],
    specs: [['Config', 'Twin turboshaft'], ['Power', '≈2 × 1000 kW'], ['Exhaust', 'IR-suppressed']] },
  stubWing: { name: 'Stub Wings', role: 'Weapon carriage',
    fn: 'Short fixed wings either side of the fuselage carry the weapon pylons, offload some rotor lift in forward flight and route the firing and release wiring to the stores.',
    mats: ['Composite spar', 'Aluminium ribs'],
    specs: [['Hardpoints', '4'], ['Role', 'Stores + lift'], ['Wiring', 'MIL-STD stores bus']] },
  weapons: { name: 'Weapon Stores', role: 'Armament',
    fn: 'Rocket pods and air-to-air / anti-tank guided missiles on the stub-wing pylons. Launched through the fire-control computer and cued by the nose sensor and helmet sight.',
    mats: ['Steel rocket tubes', 'Composite missile bodies', 'Shaped-charge warheads'],
    specs: [['Rockets', '70 mm pods'], ['Missiles', 'ATGM / AAM'], ['Cueing', 'Sensor + HMS']] },
  sensor: { name: 'Electro-Optical Turret', role: 'Targeting · vision',
    fn: 'A gyro-stabilised turret with a daylight TV camera, thermal imager and laser range-finder/designator. It finds, tracks and lazes targets day or night for the weapons.',
    mats: ['Germanium IR optics', 'Gimbal-stabilised head', 'Magnesium housing'],
    specs: [['Sensors', 'TV · IR · Laser'], ['Stabilised', 'Gyro gimbal'], ['Range', 'Multi-km']] },
  cannon: { name: 'Nose Turret Cannon', role: 'Close support',
    fn: 'A chin-mounted turret cannon slaved to the gunner\'s helmet sight — it points wherever the crew looks for fast, accurate fire against ground targets.',
    mats: ['Chrome-lined steel barrel', 'Titanium turret ring'],
    specs: [['Calibre', '20 mm'], ['Slaving', 'Helmet-cued'], ['Traverse', '±110°']] },
  gear: { name: 'Landing Gear', role: 'Ground contact',
    fn: 'A rugged non-retractable wheeled undercarriage with long-stroke shock struts that absorb hard and emergency landings to protect the crew and airframe.',
    mats: ['High-strength steel struts', 'Oleo-pneumatic dampers', 'Rubber tyres'],
    specs: [['Type', 'Fixed tricycle'], ['Struts', 'Long-stroke oleo'], ['Role', 'Crashworthy']] },
};
const ORDER = ['mainRotor', 'tailRotor', 'cockpit', 'fuselage', 'tailBoom', 'engine', 'stubWing', 'weapons', 'sensor', 'cannon', 'gear'];

/* ------------------------------------------------------------------ *
 * Renderer / scene
 * ------------------------------------------------------------------ */
const canvas = $('#scene');
let renderer;
try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' }); }
catch (e) { $('#fallback').classList.add('show'); throw e; }
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.8));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.background = new THREE.Color('#05080c');
scene.fog = new THREE.FogExp2('#05080c', 0.019);

const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.1, 400);
camera.position.set(11, 5.5, 13);

/* lights — cinematic key + cyan/amber rims */
scene.add(new THREE.HemisphereLight('#9fc4ff', '#0a0f14', 0.5));
const key = new THREE.DirectionalLight('#fff4e6', 2.4);
key.position.set(9, 14, 7); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); key.shadow.camera.near = 1; key.shadow.camera.far = 60;
key.shadow.camera.left = -18; key.shadow.camera.right = 18; key.shadow.camera.top = 18; key.shadow.camera.bottom = -18;
key.shadow.bias = -0.0004; scene.add(key);
const rimC = new THREE.PointLight('#5fe6ff', 90, 60); rimC.position.set(-12, 5, -9); scene.add(rimC);
const rimA = new THREE.PointLight('#ff8a3c', 60, 55); rimA.position.set(10, 3, -11); scene.add(rimA);
const topSpot = new THREE.SpotLight('#dfeeff', 120, 45, 0.5, 0.6, 1.2); topSpot.position.set(0, 20, 2); scene.add(topSpot);

/* HDRI env for reflections */
const pmrem = new THREE.PMREMGenerator(renderer); pmrem.compileEquirectangularShader();
new RGBELoader().setPath('./assets/').load('env.hdr', (hdr) => {
  hdr.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = pmrem.fromEquirectangular(hdr).texture;
  hdr.dispose();
}, undefined, () => {});

/* ------------------------------------------------------------------ *
 * Textures (procedural)
 * ------------------------------------------------------------------ */
function camoTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 512; const x = c.getContext('2d');
  x.fillStyle = '#48592f'; x.fillRect(0, 0, 512, 512);
  const cols = ['#2d3b20', '#5a4a2c', '#6c7a42', '#38482a', '#20291a'];
  for (let i = 0; i < 90; i++) {
    x.fillStyle = cols[(Math.random() * cols.length) | 0];
    const cx = Math.random() * 512, cy = Math.random() * 512, r = 26 + Math.random() * 64;
    x.beginPath();
    for (let a = 0; a <= 9; a++) { const ang = a / 9 * 6.283, rr = r * (0.55 + Math.random() * 0.8); const px = cx + Math.cos(ang) * rr, py = cy + Math.sin(ang) * rr; a ? x.lineTo(px, py) : x.moveTo(px, py); }
    x.closePath(); x.fill();
  }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
function padTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 1024; const x = c.getContext('2d');
  x.fillStyle = '#12161b'; x.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 9000; i++) { const g = 18 + Math.random() * 34 | 0; x.fillStyle = `rgba(${g},${g + 4},${g + 8},${Math.random() * .5})`; x.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 2); }
  x.strokeStyle = 'rgba(255,194,77,.5)'; x.lineWidth = 16; x.beginPath(); x.arc(512, 512, 340, 0, 7); x.stroke();
  x.setLineDash([46, 30]); x.lineWidth = 9; x.beginPath(); x.arc(512, 512, 300, 0, 7); x.stroke(); x.setLineDash([]);
  x.fillStyle = 'rgba(255,194,77,.55)'; x.font = 'bold 320px ui-monospace, monospace'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('H', 512, 530);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

/* ground helipad */
const pad = new THREE.Mesh(new THREE.CircleGeometry(26, 64), new THREE.MeshStandardMaterial({ map: padTexture(), roughness: .92, metalness: .05, envMapIntensity: .35 }));
pad.rotation.x = -Math.PI / 2; pad.position.y = -2.2; pad.receiveShadow = true; scene.add(pad);
const grid = new THREE.GridHelper(80, 80, 0x17323f, 0x0d1c24); grid.position.y = -2.19; grid.material.transparent = true; grid.material.opacity = .35; scene.add(grid);

/* ------------------------------------------------------------------ *
 * Materials
 * ------------------------------------------------------------------ */
const camoTex = camoTexture();
const M = {
  camo: new THREE.MeshStandardMaterial({ map: camoTex, roughness: .72, metalness: .18, envMapIntensity: .7 }),
  dark: new THREE.MeshStandardMaterial({ color: '#15181b', roughness: .5, metalness: .55, envMapIntensity: .8 }),
  metal: new THREE.MeshStandardMaterial({ color: '#40464c', roughness: .32, metalness: .9, envMapIntensity: 1 }),
  steel: new THREE.MeshStandardMaterial({ color: '#2a2e33', roughness: .4, metalness: .85, envMapIntensity: 1 }),
  glass: new THREE.MeshPhysicalMaterial({ color: '#0b1c24', roughness: .06, metalness: 0, transparent: true, opacity: .62, envMapIntensity: 1.3, clearcoat: 1, clearcoatRoughness: .1 }),
  rubber: new THREE.MeshStandardMaterial({ color: '#0b0d0f', roughness: .92, metalness: 0 }),
  olive: new THREE.MeshStandardMaterial({ color: '#39431f', roughness: .7, metalness: .25, envMapIntensity: .6 }),
  warn: new THREE.MeshStandardMaterial({ color: '#d7b325', roughness: .55, metalness: .3, envMapIntensity: .7 }),
};

/* ------------------------------------------------------------------ *
 * Build helicopter (procedural). Nose toward +X.
 * ------------------------------------------------------------------ */
const heli = new THREE.Group(); scene.add(heli);
const partMeshes = {};
function reg(obj, key) {
  obj.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.material = o.material.clone(); o.userData.part = key; o.userData.baseEmis = (o.material.emissive || new THREE.Color(0)).clone(); (partMeshes[key] = partMeshes[key] || []).push(o); } });
  heli.add(obj); return obj;
}
// cylinder with axis along +X (top radius faces nose)
function tube(rT, rB, len, mat, seg) { const m = new THREE.Mesh(new THREE.CylinderGeometry(rT, rB, len, seg || 24), mat); m.rotation.z = -Math.PI / 2; return m; }
function box(w, h, d, mat) { return new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); }

/* --- Fuselage group --- */
(() => {
  const g = new THREE.Group();
  const body = tube(1.0, 1.15, 4.4, M.camo, 28); body.scale.set(1, 1.18, 0.9); body.position.set(0.2, 0, 0); g.add(body);
  const belly = tube(0.75, 0.95, 3.6, M.camo, 24); belly.scale.set(1, 0.8, 0.95); belly.position.set(0.1, -0.55, 0); g.add(belly);
  const nose = tube(0.12, 0.85, 2.1, M.camo, 24); nose.scale.set(1, 1.05, 0.82); nose.position.set(2.9, -0.15, 0); g.add(nose);
  reg(g, 'fuselage');
})();

/* --- Tail boom + fin + stabiliser --- */
(() => {
  const g = new THREE.Group();
  const boom = tube(0.2, 0.55, 5.4, M.camo, 20); boom.scale.set(1, 1.1, 0.85); boom.position.set(-4.4, 0.18, 0); g.add(boom);
  const fin = box(1.5, 2.3, 0.22, M.camo); fin.position.set(-7.0, 1.0, 0); fin.rotation.z = 0.12; g.add(fin);
  const finTip = box(0.7, 0.5, 0.26, M.warn); finTip.position.set(-7.25, 2.05, 0); g.add(finTip);
  const hstab = box(0.9, 0.12, 3.0, M.camo); hstab.position.set(-6.5, 0.4, 0); g.add(hstab);
  reg(g, 'tailBoom');
})();

/* --- Engine deck + IR exhausts --- */
(() => {
  const g = new THREE.Group();
  const deck = box(2.6, 0.9, 1.5, M.olive); deck.position.set(-0.6, 0.85, 0); g.add(deck);
  const intakeL = tube(0.3, 0.3, 0.5, M.dark, 16); intakeL.position.set(0.7, 1.0, 0.5); g.add(intakeL);
  const intakeR = intakeL.clone(); intakeR.position.z = -0.5; g.add(intakeR);
  for (const z of [0.55, -0.55]) { const ex = tube(0.3, 0.36, 1.1, M.steel, 18); ex.position.set(-1.9, 0.7, z); ex.rotation.y = z > 0 ? -0.18 : 0.18; g.add(ex); const cap = tube(0.02, 0.33, 0.1, M.dark, 18); cap.position.set(-2.45, 0.7, z * 1.1); g.add(cap); }
  reg(g, 'engine');
})();

/* --- Cockpit canopy (tandem, stepped) --- */
(() => {
  const g = new THREE.Group();
  const frontSeat = box(1.1, 0.9, 1.05, M.camo); frontSeat.position.set(2.2, 0.35, 0); g.add(frontSeat);
  const c1 = box(1.0, 0.8, 1.0, M.glass); c1.position.set(2.2, 0.55, 0); c1.rotation.z = -0.08; g.add(c1);
  const c2 = box(1.1, 0.95, 1.05, M.glass); c2.position.set(1.0, 0.8, 0); g.add(c2);
  const frame = box(0.08, 1.0, 1.08, M.dark); frame.position.set(1.65, 0.6, 0); g.add(frame);
  reg(g, 'cockpit');
})();

/* --- Main rotor (mast, hub, 4 blades, disc) --- */
let rotorGroup, rotorDisc;
(() => {
  const g = rotorGroup = new THREE.Group(); g.position.set(-0.3, 1.5, 0);
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.18, 0.7, 16), M.metal); mast.position.y = 0.1; g.add(mast);
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.5, 0.32, 20), M.steel); hub.position.y = 0.42; g.add(hub);
  const swash = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.1, 20), M.metal); swash.position.y = 0.2; g.add(swash);
  for (let i = 0; i < 4; i++) {
    const a = i / 4 * Math.PI * 2;
    const blade = box(6.4, 0.07, 0.4, M.dark); blade.geometry.translate(3.2, 0, 0);
    const bg = new THREE.Group(); bg.rotation.y = a; bg.position.y = 0.42; bg.add(blade);
    const grip = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.5, 10), M.steel); grip.rotation.z = Math.PI / 2; grip.position.set(0.4, 0, 0); grip.rotation.y = a; grip.position.x = Math.cos(a) * 0.4; grip.position.z = -Math.sin(a) * 0.4; g.add(grip);
    const tip = box(0.5, 0.08, 0.42, M.warn); tip.geometry.translate(6.1, 0, 0); const tg = new THREE.Group(); tg.rotation.y = a; tg.position.y = 0.42; tg.add(tip); g.add(tg);
    g.add(bg);
  }
  rotorDisc = new THREE.Mesh(new THREE.RingGeometry(1.2, 6.5, 48), new THREE.MeshBasicMaterial({ color: '#1a2630', transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }));
  rotorDisc.rotation.x = Math.PI / 2; rotorDisc.position.y = 0.42; g.add(rotorDisc);
  reg(g, 'mainRotor');
})();

/* --- Tail rotor --- */
let tailRotorGroup;
(() => {
  const g = tailRotorGroup = new THREE.Group(); g.position.set(-7.0, 1.0, 0.2);
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.24, 14), M.steel); hub.rotation.x = Math.PI / 2; g.add(hub);
  for (let i = 0; i < 4; i++) { const a = i / 4 * Math.PI * 2; const bl = box(1.3, 0.05, 0.18, M.dark); bl.geometry.translate(0.65, 0, 0); const bg = new THREE.Group(); bg.rotation.x = Math.PI / 2; bg.rotation.z = a; bg.add(bl); g.add(bg); }
  reg(g, 'tailRotor');
})();

/* --- Stub wings + pylons + weapons --- */
(() => {
  const wings = new THREE.Group();
  for (const z of [1, -1]) {
    const wing = box(1.1, 0.16, 1.9, M.camo); wing.position.set(0.1, -0.1, z * 1.45); wing.rotation.x = z > 0 ? 0.04 : -0.04; wings.add(wing);
    const tipw = box(0.5, 0.5, 0.14, M.olive); tipw.position.set(0.1, -0.1, z * 2.35); wings.add(tipw);
  }
  reg(wings, 'stubWing');

  const wep = new THREE.Group();
  for (const z of [1, -1]) {
    const pylon = box(0.5, 0.4, 0.12, M.dark); pylon.position.set(0.1, -0.45, z * 1.7); wep.add(pylon);
    const pod = tube(0.26, 0.26, 1.1, M.olive, 16); pod.position.set(0.3, -0.75, z * 1.7); wep.add(pod);
    const cap = tube(0.27, 0.27, 0.06, M.dark, 16); cap.position.set(0.86, -0.75, z * 1.7); wep.add(cap);
    for (const zz of [z * 2.3]) {
      const rail = box(0.8, 0.1, 0.1, M.steel); rail.position.set(0.2, -0.3, zz); wep.add(rail);
      const msl = tube(0.09, 0.11, 1.4, M.olive, 12); msl.position.set(0.25, -0.45, zz); wep.add(msl);
      const mnose = tube(0.0, 0.1, 0.3, M.dark, 12); mnose.position.set(1.0, -0.45, zz); wep.add(mnose);
      for (let f = 0; f < 4; f++) { const fin = box(0.25, 0.02, 0.22, M.dark); fin.position.set(-0.35, -0.45, zz); fin.rotation.x = f / 4 * Math.PI * 2; fin.position.y = -0.45 + Math.cos(f / 4 * 6.28) * 0.02; wep.add(fin); }
    }
  }
  reg(wep, 'weapons');
})();

/* --- Nose electro-optical sensor turret --- */
(() => {
  const g = new THREE.Group();
  const ball = new THREE.Mesh(new THREE.SphereGeometry(0.42, 24, 20), M.dark); ball.position.set(3.7, -0.55, 0); ball.scale.set(1, 0.9, 1); g.add(ball);
  const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.1, 20), new THREE.MeshPhysicalMaterial({ color: '#0a2630', roughness: .05, metalness: .3, clearcoat: 1, emissive: '#0a3b4a', emissiveIntensity: .4, envMapIntensity: 1.4 })); lens.rotation.z = -Math.PI / 2; lens.position.set(4.1, -0.55, 0); g.add(lens);
  reg(g, 'sensor');
})();

/* --- Chin cannon turret --- */
(() => {
  const g = new THREE.Group();
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.34, 0.25, 16), M.steel); ring.position.set(3.2, -0.95, 0); g.add(ring);
  const yoke = box(0.3, 0.3, 0.5, M.dark); yoke.position.set(3.35, -1.15, 0); g.add(yoke);
  const barrel = tube(0.05, 0.06, 1.1, M.metal, 12); barrel.position.set(3.95, -1.15, 0); g.add(barrel);
  reg(g, 'cannon');
})();

/* --- Landing gear (fixed tricycle wheels) --- */
(() => {
  const g = new THREE.Group();
  function wheel(x, z, r) {
    const strut = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 1.1, 10), M.steel); strut.position.set(x, -1.4, z); strut.rotation.x = z === 0 ? 0 : (z > 0 ? -0.18 : 0.18); g.add(strut);
    const tyre = new THREE.Mesh(new THREE.TorusGeometry(r, r * 0.42, 12, 20), M.rubber); tyre.rotation.y = Math.PI / 2; tyre.position.set(x, -1.95, z); g.add(tyre);
    const hubw = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.4, r * 0.4, 0.2, 12), M.metal); hubw.rotation.x = Math.PI / 2; hubw.position.set(x, -1.95, z); g.add(hubw);
  }
  wheel(0.6, 1.5, 0.42); wheel(0.6, -1.5, 0.42); wheel(-5.6, 0, 0.3);
  reg(g, 'gear');
})();

/* markings decal-ish: ARMY text plate (simple) */
(() => {
  const c = document.createElement('canvas'); c.width = 256; c.height = 128; const x = c.getContext('2d');
  x.clearRect(0, 0, 256, 128); x.fillStyle = '#eef3ee'; x.font = 'bold 70px ui-monospace, monospace'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('ARMY', 128, 54); x.font = 'bold 34px ui-monospace, monospace'; x.fillText('-6102', 128, 100);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const pl = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 1.1), new THREE.MeshBasicMaterial({ map: t, transparent: true }));
  pl.position.set(-5.0, 0.2, 0.92); heli.add(pl);
  const pl2 = pl.clone(); pl2.position.z = -0.92; pl2.rotation.y = Math.PI; heli.add(pl2);
})();

heli.rotation.y = -0.5;

/* ------------------------------------------------------------------ *
 * Post-processing
 * ------------------------------------------------------------------ */
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.42, 0.7, 0.85);
composer.addPass(bloom);
composer.addPass(new OutputPass());

/* ------------------------------------------------------------------ *
 * Controls
 * ------------------------------------------------------------------ */
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.07;
controls.minDistance = 7; controls.maxDistance = 30;
controls.maxPolarAngle = Math.PI * 0.52; controls.minPolarAngle = 0.15;
controls.target.set(0, 0.2, 0); controls.autoRotate = true; controls.autoRotateSpeed = 0.55;
controls.addEventListener('start', () => { canvas.classList.add('grab'); controls.autoRotate = false; firstGesture(); });
controls.addEventListener('end', () => canvas.classList.remove('grab'));

/* ------------------------------------------------------------------ *
 * Cinematic audio
 * ------------------------------------------------------------------ */
class Audio {
  constructor() { this.ready = false; this.on = false; this.rotorLevel = 0; }
  init() { if (this.ready) return; try {
    const AC = window.AudioContext || window.webkitAudioContext; const ctx = this.ctx = new AC();
    const master = this.master = ctx.createGain(); master.gain.value = 0; const comp = ctx.createDynamicsCompressor(); master.connect(comp); comp.connect(ctx.destination);
    const verb = ctx.createConvolver(); verb.buffer = this._imp(2.4, 3); const vg = ctx.createGain(); vg.gain.value = .5; verb.connect(vg); vg.connect(master); this.verb = verb;
    // rotor thrum: sawtooth -> lowpass -> chop (blade pass AM) + turbine whine
    const rg = this.rg = ctx.createGain(); rg.gain.value = 0; rg.connect(master);
    const osc = this.rosc = ctx.createOscillator(); osc.type = 'sawtooth'; osc.frequency.value = 40;
    const lp = this.rlp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 180;
    const chop = ctx.createGain(); chop.gain.value = 0.6;
    const lfo = this.rlfo = ctx.createOscillator(); lfo.type = 'sine'; lfo.frequency.value = 8;
    const lfoG = ctx.createGain(); lfoG.gain.value = 0.55; lfo.connect(lfoG); lfoG.connect(chop.gain);
    osc.connect(lp); lp.connect(chop); chop.connect(rg);
    const whine = ctx.createOscillator(); whine.type = 'triangle'; whine.frequency.value = 520; const wg = this.rwg = ctx.createGain(); wg.gain.value = 0; whine.connect(wg); wg.connect(rg);
    osc.start(); lfo.start(); whine.start();
    this.pent = [392, 523.25, 659.25, 783.99, 1046.5]; this.ready = true;
  } catch (e) { this.ready = false; } }
  _noise(s) { const n = this.ctx.sampleRate * s, b = this.ctx.createBuffer(1, n, this.ctx.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; return b; }
  _imp(s, dc) { const n = this.ctx.sampleRate * s, b = this.ctx.createBuffer(2, n, this.ctx.sampleRate); for (let c = 0; c < 2; c++) { const a = b.getChannelData(c); for (let i = 0; i < n; i++) a[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, dc); } return b; }
  enable() { this.init(); if (!this.ready) return false; this.ctx.resume(); this.on = true; this.master.gain.setTargetAtTime(0.85, this.ctx.currentTime, .4); return true; }
  disable() { this.on = false; if (this.ready) this.master.gain.setTargetAtTime(0, this.ctx.currentTime, .3); }
  setRotor(l) { if (!this.ready) return; const t = this.ctx.currentTime; this.rotorLevel = l; this.rg.gain.setTargetAtTime(0.16 * l, t, .4); this.rlfo.frequency.setTargetAtTime(6 + l * 16, t, .5); this.rosc.frequency.setTargetAtTime(36 + l * 20, t, .5); this.rlp.frequency.setTargetAtTime(140 + l * 520, t, .5); this.rwg.gain.setTargetAtTime(0.028 * l, t, .5); }
  _tone(f, dur, g, type) { if (!this.on) return; const t = this.ctx.currentTime, o = this.ctx.createOscillator(), gn = this.ctx.createGain(), pan = this.ctx.createStereoPanner(); o.type = type || 'sine'; o.frequency.value = f; pan.pan.value = rand(-.4, .4); gn.gain.setValueAtTime(0, t); gn.gain.linearRampToValueAtTime(g, t + .006); gn.gain.exponentialRampToValueAtTime(.0004, t + dur); o.connect(gn); gn.connect(pan); pan.connect(this.master); pan.connect(this.verb); o.start(t); o.stop(t + dur + .03); }
  swoosh() { if (!this.on) return; const t = this.ctx.currentTime; const s = this.ctx.createBufferSource(); s.buffer = this._noise(0.7); const bp = this.ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = 1.1; bp.frequency.setValueAtTime(280, t); bp.frequency.exponentialRampToValueAtTime(3600, t + .22); bp.frequency.exponentialRampToValueAtTime(360, t + .6); const g = this.ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.2, t + .07); g.gain.exponentialRampToValueAtTime(.001, t + .62); s.connect(bp); bp.connect(g); g.connect(this.master); g.connect(this.verb); s.start(); this._boom(); }
  _boom() { const t = this.ctx.currentTime, o = this.ctx.createOscillator(), g = this.ctx.createGain(); o.type = 'sine'; o.frequency.setValueAtTime(130, t); o.frequency.exponentialRampToValueAtTime(42, t + .5); g.gain.setValueAtTime(.14, t); g.gain.exponentialRampToValueAtTime(.001, t + .55); o.connect(g); g.connect(this.master); o.start(t); o.stop(t + .6); }
  click() { if (!this.on) return; const t = this.ctx.currentTime; const s = this.ctx.createBufferSource(); s.buffer = this._noise(.12); const hp = this.ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 900; const g = this.ctx.createGain(); g.gain.setValueAtTime(.12, t); g.gain.exponentialRampToValueAtTime(.001, t + .09); s.connect(hp); hp.connect(g); g.connect(this.master); s.start(); this._tone(180, .14, .1, 'square'); this._tone(880, .5, .05, 'triangle'); }
  hover() { this._tone(this.pent[(Math.random() * this.pent.length) | 0] * 2, .5, .03, 'triangle'); }
  tick() { this._tone(1400 + Math.random() * 1600, .03, .02, 'square'); }
  digital() { if (!this.on) return; [0, 1, 2, 3].forEach(i => setTimeout(() => this._tone(this.pent[i], .25, .05, 'triangle'), i * 55)); }
  power() { if (!this.on) return; [392, 523, 659, 880].forEach((f, i) => setTimeout(() => this._tone(f, .6, .07, 'sawtooth'), i * 90)); }
}
const audio = new Audio();

/* ------------------------------------------------------------------ *
 * Interaction
 * ------------------------------------------------------------------ */
const raycaster = new THREE.Raycaster(); const ndc = new THREE.Vector2();
const pickables = []; Object.values(partMeshes).forEach(a => a.forEach(m => pickables.push(m)));
let hovered = null, selected = null;
const tag = $('#tag');

addEventListener('pointermove', e => {
  ndc.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  tag.style.left = e.clientX + 'px'; tag.style.top = e.clientY + 'px';
  if (selected) return;
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObjects(pickables, false)[0];
  const key = hit ? hit.object.userData.part : null;
  canvas.classList.toggle('aim', !!key);
  if (key) { tag.textContent = PARTS[key].name; tag.classList.add('show'); } else tag.classList.remove('show');
  if (key !== hovered) { setHover(key); if (key) audio.hover(); }
}, { passive: true });

renderer.domElement.addEventListener('pointerdown', e => { _downX = e.clientX; _downY = e.clientY; });
let _downX = 0, _downY = 0;
renderer.domElement.addEventListener('pointerup', e => {
  firstGesture();
  if (Math.abs(e.clientX - _downX) + Math.abs(e.clientY - _downY) > 6) return; // was a drag
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObjects(pickables, false)[0];
  if (hit) select(hit.object.userData.part); else if (selected) select(null);
});
addEventListener('keydown', e => { if (e.key === 'Escape') select(null); });

function setHover(key) {
  hovered = key;
  for (const k in partMeshes) { const on = (k === key); partMeshes[k].forEach(m => { if (m.material.emissive) m.material.emissive.copy(m.userData.baseEmis).lerp(new THREE.Color('#1b6b7a'), on ? 1 : 0); }); }
}

/* panel + hacker reveal */
const P = { id: $('#pId'), name: $('#pName'), role: $('#pRole'), purpose: $('#pPurpose'), mats: $('#pMats'), specs: $('#pSpecs'), panel: $('#panel') };
$('#pX').onclick = () => select(null);
const GLY = '!<>-_\\/[]{}=+*^?#01ABCDEFGHJKLMNPQRSTUVWXYZ';
let revealTok = 0;
function decodeInto(el, text, dur, snd) {
  const id = (el.__tok = (el.__tok || 0) + 1); const start = performance.now();
  (function step(now) {
    if (id !== el.__tok) return; const t = clamp((now - start) / dur, 0, 1); const res = Math.floor(text.length * t);
    let s = ''; for (let i = 0; i < text.length; i++) s += i < res ? text[i] : (text[i] === ' ' ? ' ' : GLY[(Math.random() * GLY.length) | 0]); el.textContent = s;
    if (snd && Math.random() < .5) audio.tick();
    if (t < 1) requestAnimationFrame(step); else el.textContent = text;
  })(start);
}
function typeInto(el, text, dur, snd) {
  const id = (el.__tok = (el.__tok || 0) + 1); const start = performance.now();
  (function step(now) {
    if (id !== el.__tok) return; const t = clamp((now - start) / dur, 0, 1); const n = Math.floor(text.length * t);
    el.textContent = text.slice(0, n) + (t < 1 ? '▌' : ''); if (snd && n % 2 === 0) audio.tick();
    if (t < 1) requestAnimationFrame(step); else el.textContent = text;
  })(start);
}

/* dots */
const dotsEl = $('#dots');
ORDER.forEach((k, i) => { const d = document.createElement('div'); d.className = 'dot'; d.innerHTML = `<span>${PARTS[k].name}</span>`; d.onclick = () => select(k); dotsEl.appendChild(d); });
const dotEls = [...dotsEl.children];
$('#partcount').textContent = ORDER.length;

/* camera focus tween */
const _c = new THREE.Vector3(), _box = new THREE.Box3(), _ctr = new THREE.Vector3();
let tw = null;
function tweenTo(toTarget, toPos, dur) { tw = { t0: performance.now(), dur, fromT: controls.target.clone(), toT: toTarget.clone(), fromP: camera.position.clone(), toP: toPos.clone() }; }
function partCenter(key) { _box.makeEmpty(); partMeshes[key].forEach(m => _box.expandByObject(m)); return _box.getCenter(_ctr).clone(); }

function select(key) {
  if (key === selected) return;
  selected = key;
  dotEls.forEach((d, i) => d.classList.toggle('active', ORDER[i] === key));
  if (key) {
    const d = PARTS[key];
    P.id.textContent = '// SUBSYSTEM ' + String(ORDER.indexOf(key) + 1).padStart(2, '0');
    decodeInto(P.name, d.name, 650, true);
    P.role.textContent = ''; setTimeout(() => decodeInto(P.role, d.role.toUpperCase(), 500, false), 120);
    setTimeout(() => typeInto(P.purpose, d.fn, 900, true), 260);
    P.mats.innerHTML = d.mats.map(m => `<span>${m}</span>`).join('');
    P.specs.innerHTML = d.specs.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
    P.panel.classList.add('open');
    setHover(key); audio.swoosh(); setTimeout(() => audio.digital(), 120);
    // frame the part, offset so panel (right) doesn't cover it
    const c = partCenter(key); controls.autoRotate = false;
    const dir = camera.position.clone().sub(controls.target).normalize();
    const dist = clamp(key === 'mainRotor' || key === 'fuselage' || key === 'tailBoom' ? 15 : 9, controls.minDistance, controls.maxDistance);
    const camGoal = c.clone().add(dir.multiplyScalar(dist)).add(new THREE.Vector3(0, 1.5, 0));
    tweenTo(c, camGoal, 1100);
    canvas.classList.remove('aim'); tag.classList.remove('show');
  } else {
    P.panel.classList.remove('open'); setHover(null);
    if (audio.on) audio.swoosh();
    tweenTo(new THREE.Vector3(0, 0.2, 0), camera.position.clone().sub(controls.target).normalize().multiplyScalar(16).add(new THREE.Vector3(0, 2, 0)), 1000);
    setTimeout(() => { if (!selected) controls.autoRotate = true; }, 2600);
  }
}

/* sound toggle + gesture */
const sndBtn = $('#sound');
sndBtn.onclick = () => { if (!audio.on) { if (audio.enable()) { sndBtn.classList.add('on'); sndBtn.textContent = '◼ SOUND ON'; audio.setRotor(bootDone ? 1 : 0); } } else { audio.disable(); sndBtn.classList.remove('on'); sndBtn.textContent = '◼ SOUND OFF'; } };
let gestured = false; function firstGesture() { if (gestured) return; gestured = true; if (audio.enable()) { sndBtn.classList.add('on'); sndBtn.textContent = '◼ SOUND ON'; audio.setRotor(bootDone ? 1 : 0); } }

addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight); });

/* ------------------------------------------------------------------ *
 * Boot sequence
 * ------------------------------------------------------------------ */
const boot = $('#boot'), bootD = $('#bootD'), bootFill = $('#bootFill'), bootStat = $('#bootStat'), bootPct = $('#bootPct'), bootHint = $('#bootHint');
const BSTAT = ['AWAITING OPERATOR', 'POWERING AVIONICS', 'SPOOLING ENGINES', 'ROTOR ENGAGE', 'SENSORS NOMINAL', 'SYSTEMS ONLINE'];
let bootDone = false, booting = false, rotorSpin = 0, rotorGoal = 0;
function runBoot(withSound) {
  if (booting || bootDone) return; booting = true; boot.classList.add('booting');
  if (withSound) { audio.enable(); sndBtn.classList.add('on'); sndBtn.textContent = '◼ SOUND ON'; }
  let p = 0;
  const iv = setInterval(() => {
    p = Math.min(100, p + (Math.random() < .12 ? 0 : rand(2, 7)));
    bootFill.style.right = (100 - p) + '%'; bootPct.textContent = String(p | 0).padStart(2, '0');
    bootStat.textContent = BSTAT[Math.min(BSTAT.length - 1, Math.floor(p / 100 * BSTAT.length))];
    bootD.textContent = p >= 100 ? 'ACCESS GRANTED' : BSTAT[Math.min(BSTAT.length - 1, Math.floor(p / 100 * BSTAT.length))];
    audio.tick(); if (Math.random() < .3) audio.hover();
    rotorGoal = (p / 100) * 1.0;
    if (p >= 100) { clearInterval(iv); finishBoot(); }
  }, 80);
}
function finishBoot() {
  bootDone = true; audio.power(); audio.swoosh(); audio.setRotor(1); rotorGoal = 1;
  setTimeout(() => boot.classList.add('done'), 500);
  // cinematic intro sweep
  tweenTo(new THREE.Vector3(0, 0.2, 0), new THREE.Vector3(13, 6, 15), 2200);
  controls.autoRotate = true;
}
['pointerdown', 'keydown', 'touchstart'].forEach(ev => boot.addEventListener(ev, () => runBoot(true), { once: true }));
setTimeout(() => runBoot(false), 2600);

/* ------------------------------------------------------------------ *
 * Loop
 * ------------------------------------------------------------------ */
const clock = new THREE.Clock();
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05), t = clock.elapsedTime;
  rotorSpin = damp(rotorSpin, rotorGoal, 1.2, dt);
  rotorGroup.rotation.y += dt * (2 + rotorSpin * 38);
  tailRotorGroup.rotation.x += dt * (2 + rotorSpin * 46);
  rotorDisc.material.opacity = clamp((rotorSpin - 0.5) * 0.5, 0, 0.22);
  heli.position.y = Math.sin(t * 0.6) * 0.04;
  rimC.position.x = Math.sin(t * 0.3) * 13; rimC.position.z = Math.cos(t * 0.3) * 11;

  if (tw) { const k = easeIO(clamp((performance.now() - tw.t0) / tw.dur, 0, 1)); controls.target.lerpVectors(tw.fromT, tw.toT, k); camera.position.lerpVectors(tw.fromP, tw.toP, k); if (k >= 1) tw = null; }
  controls.update();
  composer.render();
}
renderer.setAnimationLoop(() => { if (!document.hidden) frame(); });
