// AH-64 Apache — detailed procedural attack helicopter. Nose toward +X.
import * as THREE from 'three';
import { makeKit } from '../kit.js';

export function build() {
  const K = makeKit(THREE);
  const g = new THREE.Group();

  const body = K.mat('#3c4433', { rough: .8, metal: .16, env: .6 });
  const body2 = K.mat('#333b2b', { rough: .82, metal: .14, env: .55 });
  const panel = K.mat('#2f3627', { rough: .78, metal: .18 });
  const dark = K.mat('#14171a', { rough: .5, metal: .55 });
  const metal = K.mat('#3a3f44', { rough: .32, metal: .9, env: 1 });
  const steel = K.mat('#22262a', { rough: .42, metal: .85 });
  const gunMetal = K.mat('#1a1d20', { rough: .35, metal: .8 });
  const glass = K.glass('#13241d', .5);
  const rubber = K.mat('#0b0d0f', { rough: .92, metal: 0 });
  const warhead = K.mat('#5a4a2a', { rough: .7, metal: .3 });
  const lightR = K.mat('#ff3344', { emissive: '#ff2233', emissiveI: 1.4, rough: .4 });
  const lightG = K.mat('#33ff88', { emissive: '#22ff77', emissiveI: 1.4, rough: .4 });

  const parts = {};
  const part = (key, name, role, fn, mats, specs, objects) => { parts[key] = { name, role, fn, mats, specs, objects }; objects.forEach(o => g.add(o)); };

  /* ---- Fuselage (slim lofted hull) ---- */
  const hull = K.loft([
    { x: 6.7, w: .13, h: .17, y: -.28 },
    { x: 6.1, w: .34, h: .42, y: -.14 },
    { x: 5.3, w: .5, h: .66, y: -.02 },
    { x: 4.2, w: .6, h: .9, y: .06 },
    { x: 2.6, w: .66, h: 1.04, y: .12 },
    { x: 1.0, w: .66, h: 1.08, y: .14 },
    { x: -0.6, w: .6, h: .96, y: .14 },
    { x: -1.9, w: .47, h: .72, y: .2 },
    { x: -3.2, w: .31, h: .48, y: .3 },
    { x: -4.7, w: .24, h: .36, y: .37 },
    { x: -6.4, w: .2, h: .31, y: .42 },
    { x: -8.0, w: .18, h: .29, y: .48 },
  ], body, 24);
  part('fuselage', 'Fuselage', 'Primary airframe',
    'The narrow, flat-sided aluminium-and-composite airframe is built around armoured tandem crew bays and a central rotor mast. Its slim cross-section and boron armour panels let it absorb cannon hits while keeping a small head-on target for the enemy.',
    ['Aluminium-alloy frames', 'Composite skin', 'Boron carbide crew armour', 'Crashworthy structure'],
    [['Length', '17.73 m'], ['Height', '3.87 m'], ['Fuselage width', '1.0 m'], ['Empty', '5165 kg']], [hull]);

  /* ---- Stepped tandem cockpit (gunner low front, pilot raised behind) ---- */
  const cockpit = new THREE.Group();
  const frame = body2;
  // gunner (front, lower) greenhouse
  const gWind = K.box(.06, .62, .86, glass); gWind.position.set(5.0, .5, 0); gWind.rotation.z = -.5; cockpit.add(gWind);
  for (const z of [1, -1]) { const gs = K.box(.78, .5, .05, glass); gs.position.set(4.7, .5, z * .42); gs.rotation.y = z * .16; cockpit.add(gs); }
  const gTop = K.box(.8, .05, .82, frame); gTop.position.set(4.68, .78, 0); cockpit.add(gTop);
  // step frame between the two cockpits
  const step = K.box(.1, .55, .86, frame); step.position.set(4.25, .78, 0); cockpit.add(step);
  // pilot (rear, raised) greenhouse
  const pWind = K.box(.06, .6, .9, glass); pWind.position.set(4.15, .95, 0); pWind.rotation.z = -.42; cockpit.add(pWind);
  for (const z of [1, -1]) { const ps = K.box(.82, .58, .05, glass); ps.position.set(3.75, 1.0, z * .45); ps.rotation.y = z * .14; cockpit.add(ps); }
  const pTop = K.box(.86, .06, .86, frame); pTop.position.set(3.72, 1.32, 0); cockpit.add(pTop);
  const pRear = K.box(.06, .62, .84, glass); pRear.position.set(3.32, 1.0, 0); pRear.rotation.z = .4; cockpit.add(pRear);
  // canopy pillars
  for (const z of [1, -1]) { const pil = K.box(.9, .05, .05, frame); pil.position.set(4.3, .78, z * .44); cockpit.add(pil); const pil2 = K.box(.85, .05, .05, frame); pil2.position.set(3.75, 1.3, z * .46); cockpit.add(pil2); }
  part('cockpit', 'Tandem Cockpit', 'Crew station',
    'Two crew sit in a stepped tandem layout — the co-pilot/gunner low in front and the pilot raised behind — so both see forward past each other. Flat, bullet-resistant canopy panels and kevlar seat tubs protect the crew from 23 mm fire.',
    ['Flat bullet-resistant glass', 'Boron/kevlar seat armour', 'Integrated helmet sight'],
    [['Crew', '2 tandem'], ['Gunner', 'Front · low'], ['Pilot', 'Rear · raised'], ['Protection', 'Dual-redundant']], [cockpit]);

  /* ---- Nose sensors: stacked TADS (lower) + PNVS (upper) ---- */
  const sensors = new THREE.Group();
  // TADS — large lower rotating turret with flat optical faces
  const tadsBody = new THREE.Mesh(new THREE.CylinderGeometry(.34, .34, .5, 20), gunMetal); tadsBody.rotation.x = Math.PI / 2; tadsBody.position.set(6.35, -.28, 0); sensors.add(tadsBody);
  const tadsFace = K.box(.12, .5, .56, dark); tadsFace.position.set(6.62, -.28, 0); sensors.add(tadsFace);
  const tadsLens = new THREE.Mesh(new THREE.CylinderGeometry(.12, .12, .06, 16), K.mat('#0a2630', { metal: .3, rough: .05, emissive: '#0a3b4a', emissiveI: .5 })); tadsLens.rotation.z = -Math.PI / 2; tadsLens.position.set(6.7, -.33, .14); sensors.add(tadsLens);
  const tadsLens2 = tadsLens.clone(); tadsLens2.position.z = -.14; sensors.add(tadsLens2);
  // PNVS — smaller upper turret
  const pnvsBody = new THREE.Mesh(new THREE.CylinderGeometry(.2, .2, .34, 18), gunMetal); pnvsBody.rotation.x = Math.PI / 2; pnvsBody.position.set(6.3, .18, 0); sensors.add(pnvsBody);
  const pnvsFace = K.box(.1, .3, .36, dark); pnvsFace.position.set(6.48, .18, 0); sensors.add(pnvsFace);
  const pnvsLens = new THREE.Mesh(new THREE.CylinderGeometry(.09, .09, .05, 16), K.mat('#102a1e', { metal: .3, rough: .06, emissive: '#1a4a2a', emissiveI: .4 })); pnvsLens.rotation.z = -Math.PI / 2; pnvsLens.position.set(6.55, .18, 0); sensors.add(pnvsLens);
  // mounting yoke
  const yoke = K.box(.18, .5, .7, panel); yoke.position.set(6.1, -.05, 0); sensors.add(yoke);
  part('sensors', 'TADS / PNVS Turrets', 'Targeting · night vision',
    'The nose carries two stacked gyro-stabilised turrets: the larger lower TADS (Target Acquisition and Designation Sight) with day TV, thermal imager and laser designator, and the smaller upper PNVS (Pilot Night Vision Sensor) that feeds the pilot a thermal image for flying in total darkness.',
    ['Germanium thermal optics', 'Day-TV camera', 'Laser designator/rangefinder', 'Gyro-stabilised gimbals'],
    [['Lower', 'TADS'], ['Upper', 'PNVS'], ['Range', 'Laser designation'], ['Slaved', 'Helmet sight']], [sensors]);

  /* ---- Chin-mounted M230 30 mm chain gun ---- */
  const cannon = new THREE.Group();
  const turret = K.box(.6, .42, .6, gunMetal); turret.position.set(2.3, -.78, 0); cannon.add(turret);
  const pivot = new THREE.Mesh(new THREE.CylinderGeometry(.16, .16, .36, 14), steel); pivot.position.set(2.3, -.55, 0); cannon.add(pivot);
  const barrel = new THREE.Mesh(new THREE.CylinderGeometry(.055, .055, 1.5, 14), gunMetal); barrel.rotation.z = -Math.PI / 2; barrel.position.set(3.1, -.82, 0); cannon.add(barrel);
  const muzzle = new THREE.Mesh(new THREE.CylinderGeometry(.08, .08, .18, 12), dark); muzzle.rotation.z = -Math.PI / 2; muzzle.position.set(3.8, -.82, 0); cannon.add(muzzle);
  const ammoBox = K.box(.5, .3, .7, panel); ammoBox.position.set(1.95, -.78, 0); cannon.add(ammoBox);
  part('cannon', 'M230 Chain Gun', 'Primary cannon',
    'A belly-mounted 30 mm M230 single-barrel chain gun hangs under the fuselage between the main wheels and slaves to the gunner\'s helmet sight, so it points wherever the crew looks. It fires high-explosive dual-purpose rounds that defeat light armour and troops out to about 1500 m.',
    ['Chrome-lined steel barrel', 'Electric chain-driven action', 'HEDP 30 mm ammunition'],
    [['Calibre', '30 mm'], ['Rate', '≈625 rnd/min'], ['Load', '1200 rounds'], ['Aim', 'Helmet-slaved']], [cannon]);

  /* ---- Stub wings ---- */
  const stubWing = new THREE.Group();
  const wingMesh = (z) => {
    const w = K.box(.55, .22, 2.3, body); w.position.set(.9, .32, z * 1.55); w.rotation.x = z * .06; // slight anhedral
    stubWing.add(w);
    const tip = K.box(.5, .3, .22, body2); tip.position.set(.9, .28, z * 2.75); stubWing.add(tip);
    const plyIn = K.box(.4, .16, .14, panel); plyIn.position.set(.95, .14, z * 1.2); stubWing.add(plyIn);
    const plyOut = K.box(.4, .16, .14, panel); plyOut.position.set(.95, .12, z * 2.35); stubWing.add(plyOut);
  };
  wingMesh(1); wingMesh(-1);
  part('stubWing', 'Stub Wings', 'Weapon pylons · lift',
    'Two short mid-fuselage wings each carry two hard-points and off-load the rotor by adding a little lift in fast cruise. Their drooped profile keeps the heavy weapon loads clear of the fuselage and rotor downwash.',
    ['Aluminium torque-box', 'Composite skin', 'BRU weapon racks'],
    [['Hard-points', '4 total'], ['Span', '≈5.8 m'], ['Load', 'Rockets · missiles'], ['Function', 'Pylons + lift']], [stubWing]);

  /* ---- Weapons: rocket pods (inboard) + Hellfire racks (outboard) ---- */
  const weapons = new THREE.Group();
  const loadSide = (z) => {
    // Hydra-70 rocket pod — fat inboard tube
    const pod = K.tube(.21, .21, 1.5, dark, 18); pod.position.set(.55, .0, z * 1.2);
    const podFace = new THREE.Mesh(new THREE.CylinderGeometry(.21, .21, .06, 18), steel); podFace.rotation.z = -Math.PI / 2; podFace.position.set(1.3, 0, z * 1.2);
    weapons.add(pod, podFace);
    for (let i = 0; i < 7; i++) { const a = i / 7 * Math.PI * 2; const h = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, .04, 10), gunMetal); h.rotation.z = -Math.PI / 2; h.position.set(1.33, Math.sin(a) * .11, z * 1.2 + Math.cos(a) * .11); weapons.add(h); }
    const hc = new THREE.Mesh(new THREE.CylinderGeometry(.05, .05, .04, 10), gunMetal); hc.rotation.z = -Math.PI / 2; hc.position.set(1.33, 0, z * 1.2); weapons.add(hc);
    // M299 launcher rail with 4 Hellfire missiles (2x2) — outboard
    const rail = K.box(1.3, .12, .5, steel); rail.position.set(.55, -.04, z * 2.35); weapons.add(rail);
    const offs = [[.1, .14], [.1, -.14], [-.1, .14], [-.1, -.14]];
    for (const [dy, dz] of offs) {
      const body_ = new THREE.Mesh(new THREE.CylinderGeometry(.07, .07, 1.3, 12), K.mat('#4a4330', { rough: .7, metal: .3 })); body_.rotation.z = -Math.PI / 2; body_.position.set(.6, -.22 + dy, z * 2.35 + dz); weapons.add(body_);
      const nose = new THREE.Mesh(new THREE.CylinderGeometry(.005, .07, .3, 12), warhead); nose.rotation.z = -Math.PI / 2; nose.position.set(1.4, -.22 + dy, z * 2.35 + dz); weapons.add(nose);
      for (const fx of [.1, -.1]) { const fin = K.box(.18, .14, .02, dark); fin.position.set(fx, -.22 + dy, z * 2.35 + dz); weapons.add(fin); const fin2 = K.box(.18, .02, .14, dark); fin2.position.set(fx, -.22 + dy, z * 2.35 + dz); weapons.add(fin2); }
    }
  };
  loadSide(1); loadSide(-1);
  part('weapons', 'Rockets & Hellfires', 'Ordnance',
    'Each wing mounts a 19-shot Hydra-70 rocket pod inboard and a four-rail launcher of AGM-114 Hellfire laser-guided anti-tank missiles outboard. The Hellfires kill main battle tanks beyond 8 km while the rockets saturate soft and area targets.',
    ['Hydra-70 folding-fin rockets', 'AGM-114 Hellfire missiles', 'M299 smart launcher'],
    [['Rockets', '2 × 19-tube pods'], ['Missiles', 'up to 16 Hellfire'], ['Hellfire range', '≈8+ km'], ['Guidance', 'Semi-active laser']], [weapons]);

  /* ---- Engine nacelles with exhausts (either side, above wings) ---- */
  const engine = new THREE.Group();
  for (const z of [1, -1]) {
    const nac = K.tube(.42, .5, 2.4, body2, 20); nac.position.set(.4, .75, z * .82); engine.add(nac);
    const intake = new THREE.Mesh(new THREE.CylinderGeometry(.34, .36, .3, 18), dark); intake.rotation.z = -Math.PI / 2; intake.position.set(1.65, .8, z * .82); engine.add(intake);
    const exh = K.tube(.26, .36, .8, steel, 16); exh.position.set(-1.05, .72, z * .82); exh.rotation.y = -z * .25; engine.add(exh);
    const supp = new THREE.Mesh(new THREE.CylinderGeometry(.04, .3, .14, 16), dark); supp.rotation.z = -Math.PI / 2; supp.position.set(-1.55, .68, z * .95); engine.add(supp);
    const fairing = K.box(1.6, .5, .5, panel); fairing.position.set(.5, .95, z * .55); engine.add(fairing);
  }
  part('engine', 'Twin T700 Turboshafts', 'Powerplant',
    'Two General Electric T700 turboshaft engines sit in nacelles either side of the rotor mast and drive a common gearbox. Their upturned "black hole" infra-red suppressors mix cool air into the exhaust to defeat heat-seeking missiles.',
    ['Nickel super-alloy turbine', 'Titanium compressor', 'Black-hole IR suppressor'],
    [['Engines', '2 × GE T700'], ['Power', '≈2 × 1490 kW'], ['Layout', 'Side nacelles'], ['Exhaust', 'IR-suppressed']], [engine]);

  /* ---- Main rotor + mast ---- */
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(.16, .22, 1.1, 16), metal); mast.position.set(.3, 1.75, 0);
  const swash = new THREE.Mesh(new THREE.CylinderGeometry(.3, .34, .22, 18), steel); swash.position.set(.3, 2.08, 0);
  const rotor = K.mainRotor({ blades: 4, radius: 7.0, chord: .54, thick: .1, mat: dark, hubMat: steel, hubR: .5, hubH: .42 });
  rotor.position.set(.3, 2.35, 0);
  // pitch links / dampers for a busy rotor head
  for (let i = 0; i < 4; i++) { const a = i / 4 * Math.PI * 2; const link = new THREE.Mesh(new THREE.CylinderGeometry(.03, .03, .4, 8), metal); link.position.set(.3 + Math.cos(a) * .55, 2.2, Math.sin(a) * .55); g.add(link); }
  part('mainRotor', 'Main Rotor', 'Lift · thrust · control',
    'Four fully-articulated composite blades with swept tips mount on a steel-and-elastomeric hub atop the mast. The blades use a laminated stainless-steel spar and composite skin tough enough to keep flying after a 23 mm cannon strike.',
    ['Stainless-steel spar blades', 'Composite / fibreglass skin', 'Elastomeric lead-lag bearings'],
    [['Blades', '4'], ['Diameter', '14.63 m'], ['Tip', 'Swept'], ['RPM', '≈289']], [mast, swash, rotor]);

  /* ---- Tail: boom end, swept fin, side tail rotor ---- */
  const fin = K.box(.9, 2.3, .28, body); fin.geometry.translate(0, 1.15, 0); fin.position.set(-7.9, .5, 0); fin.rotation.z = .28; // swept
  const finTip = K.box(.7, .45, .3, body2); finTip.position.set(-8.4, 2.6, 0);
  // tail rotor mounted on side of fin, disc in XY plane, spins about Z
  const trMount = new THREE.Group(); trMount.position.set(-8.2, 2.0, .3);
  const trHub = new THREE.Mesh(new THREE.CylinderGeometry(.14, .14, .3, 14), steel); trHub.rotation.x = Math.PI / 2; trMount.add(trHub);
  const trSpin = new THREE.Group();
  for (let i = 0; i < 4; i++) { const a = i / 4 * Math.PI * 2; const bl = K.box(1.3, .05, .2, dark); bl.geometry.translate(.65, 0, 0); const bg = new THREE.Group(); bg.rotation.z = a; bg.add(bl); trSpin.add(bg); }
  trSpin.position.z = .18; trMount.add(trSpin);
  part('tailRotor', 'Tail Rotor & Fin', 'Anti-torque · yaw',
    'A four-blade tail rotor set in an offset twin-pair arrangement on the port side of the swept vertical fin cancels the main-rotor torque and gives yaw control. The load-bearing fin also carries flight loads and the low-set stabilator.',
    ['Composite blades', 'Steel pitch housing', 'Load-bearing fin'],
    [['Blades', '4'], ['Diameter', '2.79 m'], ['Fin', 'Swept · load-bearing'], ['Side', 'Port']], [fin, finTip, trMount]);

  /* ---- Low horizontal stabilator near the tail ---- */
  const stab = new THREE.Group();
  const stabO = K.box(.9, .11, 3.3, body); stabO.position.set(-7.0, .32, 0); stab.add(stabO);
  for (const z of [1.4, -1.4]) { const ep = K.box(.6, .22, .12, body2); ep.position.set(-7.0, .36, z); stab.add(ep); }
  part('stabilator', 'Stabilator', 'Pitch control',
    'A low-mounted all-moving horizontal tailplane under the fin that the flight computer tilts with airspeed to hold the fuselage level and steady the gun platform. It unloads the rotor in a dive and improves pitch control at speed.',
    ['Composite skin', 'Electro-mechanical actuator'],
    [['Type', 'All-moving'], ['Control', 'Computer-scheduled'], ['Span', '3.3 m'], ['Position', 'Low aft']], [stab]);

  /* ---- Tail-dragger landing gear ---- */
  const gear = new THREE.Group();
  const mwL = K.wheel(.42, rubber, steel, 1.9, .18); mwL.position.set(1.2, -1.0, 1.25); gear.add(mwL);
  const mwR = K.wheel(.42, rubber, steel, 1.9, -.18); mwR.position.set(1.2, -1.0, -1.25); gear.add(mwR);
  // drag strut braces
  for (const z of [1, -1]) { const brace = new THREE.Mesh(new THREE.CylinderGeometry(.05, .05, 1.6, 8), steel); brace.position.set(.5, -.1, z * 1.0); brace.rotation.z = .5; brace.rotation.x = z * .25; gear.add(brace); }
  const tw = K.wheel(.24, rubber, steel, .9, 0); tw.position.set(-7.9, -.1, 0); gear.add(tw);
  part('gear', 'Landing Gear', 'Ground contact',
    'A fixed tail-dragger undercarriage with two tall, trailing-arm main wheels and a small castoring tail wheel. The long energy-absorbing struts give the weapon pylons ground clearance and crush on a crash to save the crew.',
    ['Trailing-arm oleo struts', 'High-strength steel', 'Energy-absorbing stroke', 'Rubber tyres'],
    [['Type', 'Fixed tail-dragger'], ['Mains', '2 tall'], ['Tail', 'Castoring wheel'], ['Role', 'Crashworthy']], [gear]);

  /* nav lights */
  const nL = new THREE.Mesh(new THREE.SphereGeometry(.07, 8, 8), lightR); nL.position.set(.9, .3, 2.78); g.add(nL);
  const nR = new THREE.Mesh(new THREE.SphereGeometry(.07, 8, 8), lightG); nR.position.set(.9, .3, -2.78); g.add(nR);

  const info = {
    name: 'AH-64 Apache', variant: 'Boeing · Attack Helicopter',
    role: 'Attack / Anti-armour', origin: 'United States', year: 'In service 1986',
    desc: 'A twin-engine, four-blade attack helicopter built around a stepped tandem cockpit, a chin-mounted 30 mm cannon and stub wings of rockets and Hellfire missiles. Flown by a pilot and a co-pilot/gunner, it hunts armour and provides close air support day or night with its nose TADS/PNVS sensor suite.',
    specs: [['Crew', '2 tandem'], ['Length', '17.73 m'], ['Rotor', '14.63 m · 4-blade'], ['Max speed', '293 km/h'], ['Engines', '2 × GE T700'], ['Main gun', '30 mm M230'], ['Missiles', 'AGM-114 Hellfire']],
  };
  return { group: g, parts, info, rotors: { main: [rotor], mainAxis: 'y', tail: [trSpin], tailAxis: 'z' } };
}
