// UH-60 Black Hawk — detailed procedural model. Nose toward +X.
import * as THREE from 'three';
import { makeKit } from '../kit.js';

export function build() {
  const K = makeKit(THREE);
  const g = new THREE.Group();
  const body = K.mat('#434e38', { rough: .74, metal: .14, env: .7 });
  const body2 = K.mat('#3a4430', { rough: .76, metal: .12, env: .6 });
  const dark = K.mat('#15181b', { rough: .5, metal: .55 });
  const metal = K.mat('#3a3f44', { rough: .3, metal: .9, env: 1 });
  const steel = K.mat('#23272b', { rough: .4, metal: .85 });
  const glass = K.glass('#0a1a20', .5);
  const rubber = K.mat('#0b0d0f', { rough: .92, metal: 0 });
  const lightR = K.mat('#ff3344', { emissive: '#ff2233', emissiveI: 1.4, rough: .4 });
  const lightG = K.mat('#33ff88', { emissive: '#22ff77', emissiveI: 1.4, rough: .4 });

  const parts = {};
  const part = (key, name, role, fn, mats, specs, objects) => { parts[key] = { name, role, fn, mats, specs, objects }; objects.forEach(o => g.add(o)); };

  /* ---- Fuselage (lofted hull) ---- */
  const hull = K.loft([
    { x: 7.4, w: .12, h: .16, y: -.1 },
    { x: 6.7, w: .55, h: .5, y: -.2 },
    { x: 6.0, w: .95, h: .78, y: -.1 },
    { x: 5.1, w: 1.25, h: 1.0, y: .0 },
    { x: 4.0, w: 1.55, h: 1.12, y: .05 },
    { x: 2.6, w: 1.75, h: 1.25, y: .05 },
    { x: 0.8, w: 1.8, h: 1.3, y: .05 },
    { x: -1.1, w: 1.72, h: 1.3, y: .08 },
    { x: -2.4, w: 1.5, h: 1.2, y: .14 },
    { x: -3.7, w: 1.0, h: .9, y: .26 },
    { x: -5.4, w: .55, h: .6, y: .5 },
    { x: -7.4, w: .33, h: .42, y: .95 },
    { x: -8.8, w: .22, h: .32, y: 1.4 },
  ], body, 24);
  part('fuselage', 'Fuselage', 'Primary airframe',
    'The crashworthy aluminium-and-composite airframe carries the cockpit, 11-troop cabin, engines, fuel and rotor loads. A wide sliding door each side loads troops and cargo fast.',
    ['Aluminium-alloy frames', 'Composite skin', 'Kevlar armour floor', 'Self-sealing tanks'],
    [['Cabin', '11 troops'], ['Length', '19.76 m'], ['Width', '2.36 m'], ['Doors', '2 × sliding']], [hull]);

  /* ---- Cockpit + cabin glazing ---- */
  const cockpit = new THREE.Group();
  const wsL = K.box(1.2, 1.0, 0.04, glass); wsL.position.set(5.0, .55, .62); wsL.rotation.set(0, .5, -.25); cockpit.add(wsL);
  const wsR = wsL.clone(); wsR.position.z = -.62; wsR.rotation.y = -.5; cockpit.add(wsR);
  const wsC = K.box(0.9, 1.0, 1.15, glass); wsC.position.set(5.2, .5, 0); wsC.rotation.z = -.28; cockpit.add(wsC);
  const chinL = K.box(0.8, 0.5, 0.5, glass); chinL.position.set(5.5, -.35, .45); cockpit.add(chinL);
  const chinR = chinL.clone(); chinR.position.z = -.45; cockpit.add(chinR);
  for (const z of [1, -1]) { const dw = K.box(0.04, .75, 1.6, glass); dw.position.set(1.4, .35, z * 1.78); cockpit.add(dw); const cw = K.box(0.04, .5, .5, glass); cw.position.set(-.8, .5, z * 1.72); cockpit.add(cw); }
  part('cockpit', 'Cockpit & Cabin', 'Crew · troop station',
    'Side-by-side pilots fly behind an armoured wrap-around windscreen with a glass-cockpit instrument display. Behind them the cabin seats a full infantry squad with wide sliding doors and gunner windows.',
    ['Bullet-resistant windscreen', 'Armoured crew seats', 'Glass-cockpit displays'],
    [['Pilots', '2 side-by-side'], ['Seating', '11 troops'], ['Windows', 'Gunner / cabin']], [cockpit]);

  /* ---- Nose FLIR sensor ---- */
  const sensor = new THREE.Group();
  const ball = K.sphere(.34, dark, 1, .9, 1); ball.position.set(6.3, -.55, .35); sensor.add(ball);
  const lens = new THREE.Mesh(new THREE.CylinderGeometry(.16, .16, .08, 16), K.mat('#0a2630', { metal: .3, rough: .05, emissive: '#0a3b4a', emissiveI: .5 })); lens.rotation.z = -Math.PI / 2; lens.position.set(6.65, -.55, .35); sensor.add(lens);
  const pitot = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, 1.0, 8), metal); pitot.rotation.z = -Math.PI / 2; pitot.position.set(7.6, .1, .3); sensor.add(pitot);
  part('sensor', 'FLIR / Sensor Suite', 'Vision · targeting',
    'A nose-mounted forward-looking infra-red turret with thermal and low-light cameras lets the crew fly and find targets in total darkness, dust or smoke.',
    ['Germanium IR optics', 'Gyro-stabilised gimbal', 'Magnesium housing'],
    [['Sensors', 'FLIR · LLTV'], ['Use', 'Night / brown-out'], ['Stabilised', 'Yes']], [sensor]);

  /* ---- Engines (twin, with IR exhausts) ---- */
  const engine = new THREE.Group();
  for (const z of [.72, -.72]) {
    const nac = K.tube(.42, .5, 2.2, body2, 18); nac.position.set(-.4, 1.0, z); engine.add(nac);
    const intake = new THREE.Mesh(new THREE.CylinderGeometry(.34, .34, .3, 16), dark); intake.rotation.z = -Math.PI / 2; intake.position.set(1.0, 1.05, z); engine.add(intake);
    const exh = K.tube(.3, .36, .7, steel, 16); exh.position.set(-1.9, .95, z); exh.rotation.y = z > 0 ? -.3 : .3; engine.add(exh);
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(.02, .3, .1, 16), dark); cap.rotation.z = -Math.PI / 2; cap.position.set(-2.35, .9, z * 1.18); engine.add(cap);
  }
  part('engine', 'Twin Turboshafts', 'Powerplant',
    'Two General Electric T700 turboshaft engines drive the rotors through a central gearbox. Infra-red-suppressing exhausts cool the hot gas to hide the aircraft from heat-seeking missiles.',
    ['Nickel super-alloy turbine', 'Titanium compressor', 'IR-suppressing cowl'],
    [['Engines', '2 × GE T700'], ['Power', '≈2 × 1420 kW'], ['Gearbox', 'Central main']], [engine]);

  /* ---- Main rotor ---- */
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(.18, .24, 1.0, 14), metal); mast.position.set(-.4, 2.0, 0);
  const rotor = K.mainRotor({ blades: 4, radius: 7.6, chord: .52, thick: .09, mat: dark, hubMat: steel, hubR: .55, hubH: .4 });
  rotor.position.set(-.4, 2.55, 0);
  for (let i = 0; i < 4; i++) { const a = i / 4 * Math.PI * 2; const damp = new THREE.Mesh(new THREE.BoxGeometry(.5, .18, .16), metal); damp.position.set(Math.cos(a) * .7, 2.55, -Math.sin(a) * .7); damp.rotation.y = a; g.add(damp); }
  part('mainRotor', 'Main Rotor', 'Lift · thrust · control',
    'Four wide-chord composite blades on a titanium hub generate all the lift and directional thrust. Swept blade tips cut noise and improve high-speed efficiency; the whole disc tilts to move the aircraft.',
    ['Titanium / graphite spar blades', 'Titanium hub', 'Elastomeric bearings'],
    [['Blades', '4'], ['Diameter', '16.36 m'], ['Tip', 'Swept'], ['RPM', '≈258']], [mast, rotor]);

  /* ---- Tail: fin, canted tail rotor, stabilator ---- */
  const fin = K.box(1.6, 2.6, 0.3, body); fin.geometry.translate(0, 1.3, 0); fin.position.set(-8.7, .7, 0); fin.rotation.z = .15;
  const finTip = K.box(0.8, .5, .34, body2); finTip.position.set(-9.0, 3.1, 0);
  const trMount = new THREE.Group(); trMount.position.set(-8.9, 2.4, .35); trMount.rotation.x = .35; // cant
  const trHub = new THREE.Mesh(new THREE.CylinderGeometry(.18, .18, .28, 14), steel); trHub.rotation.x = Math.PI / 2; trMount.add(trHub);
  const trSpin = new THREE.Group();
  for (let i = 0; i < 4; i++) { const a = i / 4 * Math.PI * 2; const bl = K.box(1.55, .05, .22, dark); bl.geometry.translate(.78, 0, 0); const bg = new THREE.Group(); bg.rotation.z = a; bg.add(bl); trSpin.add(bg); }
  trMount.add(trSpin);
  part('tailRotor', 'Tail Rotor & Fin', 'Anti-torque · yaw',
    'A canted four-blade tail rotor cancels the main-rotor torque so the airframe does not spin, and gives the pilot yaw control. Its 20° tilt also adds a little lift at the tail.',
    ['Composite blades', 'Cross-beam titanium hub', 'Steel pitch links'],
    [['Blades', '4'], ['Cant', '20°'], ['Fin', 'Load-bearing']], [fin, finTip, trMount]);

  const stab = new THREE.Group();
  const stabO = K.box(1.0, .12, 4.4, body); stabO.position.set(-7.6, .5, 0); stab.add(stabO);
  for (const z of [1.9, -1.9]) { const ep = K.box(.8, .5, .12, body2); ep.position.set(-7.6, .55, z); stab.add(ep); }
  part('stabilator', 'Stabilator', 'Pitch stability',
    'A moving horizontal tailplane that the flight computer tilts automatically with speed, keeping the nose level and the ride stable through the whole flight envelope.',
    ['Composite skin', 'Electric actuators'],
    [['Type', 'Variable-incidence'], ['Control', 'Automatic'], ['Span', '4.4 m']], [stab]);

  /* ---- Landing gear (tricycle) ---- */
  const gear = new THREE.Group();
  const mw1 = K.wheel(.42, rubber, steel, 1.0, .25); mw1.position.set(2.2, -1.3, 1.5); gear.add(mw1);
  const mw2 = K.wheel(.42, rubber, steel, 1.0, -.25); mw2.position.set(2.2, -1.3, -1.5); gear.add(mw2);
  const tw = K.wheel(.3, rubber, steel, 1.1, 0); tw.position.set(-7.4, -.6, 0); gear.add(tw);
  part('gear', 'Landing Gear', 'Ground contact',
    'A fixed tricycle undercarriage with two forward main wheels and a tail wheel. Energy-absorbing struts soak up hard and crash landings to protect the crew.',
    ['High-strength steel struts', 'Oleo-pneumatic dampers', 'Rubber tyres'],
    [['Type', 'Fixed tailwheel'], ['Mains', '2 forward'], ['Role', 'Crashworthy']], [gear]);

  /* nav lights */
  const nL = new THREE.Mesh(new THREE.SphereGeometry(.08, 8, 8), lightR); nL.position.set(2.6, .1, 1.82); g.add(nL);
  const nR = new THREE.Mesh(new THREE.SphereGeometry(.08, 8, 8), lightG); nR.position.set(2.6, .1, -1.82); g.add(nR);

  const info = {
    name: 'UH-60 Black Hawk', variant: 'Sikorsky · Utility Tactical Transport',
    role: 'Utility / Assault', origin: 'United States', year: 'In service 1979',
    desc: "A four-blade, twin-engine medium utility helicopter — the US Army's tactical transport workhorse. It carries an 11-troop squad, casualties or slung cargo, and flies assault, medevac, special-operations and VIP missions worldwide.",
    specs: [['Crew', '2 + 11 troops'], ['Length', '19.76 m'], ['Rotor', '16.36 m · 4-blade'], ['Max speed', '294 km/h'], ['Engines', '2 × GE T700'], ['Introduced', '1979']],
  };
  return { group: g, parts, info, rotors: { main: [rotor], mainAxis: 'y', tail: [trSpin], tailAxis: 'z' } };
}
