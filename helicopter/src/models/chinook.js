// CH-47 Chinook — detailed procedural model. Nose toward +X.
// Tandem-rotor heavy-lift transport: short front rotor pylon + tall swept rear pylon,
// two 3-blade main rotors whose discs overlap, no tail rotor.
import * as THREE from 'three';
import { makeKit } from '../kit.js';

export function build() {
  const K = makeKit(THREE);
  const g = new THREE.Group();

  // --- materials (green/brown field camouflage over olive) ---
  const camo = K.camoTex(['#4b5338', '#6a5c3c', '#2f3626'], '#55603f');
  const body = K.mat('#55603f', { rough: .78, metal: .12, env: .6, map: camo });
  const body2 = K.mat('#434c33', { rough: .8, metal: .1, env: .55 });
  const dark = K.mat('#15181b', { rough: .5, metal: .55 });
  const metal = K.mat('#3a3f44', { rough: .3, metal: .9, env: 1 });
  const steel = K.mat('#23272b', { rough: .4, metal: .85 });
  const bright = K.mat('#9aa0a6', { rough: .22, metal: .95, env: 1.1 });
  const glass = K.glass('#0a1a20', .5);
  const rubber = K.mat('#0b0d0f', { rough: .92, metal: 0 });

  const parts = {};
  const part = (key, name, role, fn, mats, specs, objects) => { parts[key] = { name, role, fn, mats, specs, objects }; objects.forEach(o => g.add(o)); };

  /* ---- Fuselage (lofted boxy cargo hull, flatter belly, blunt ends) ---- */
  const hull = K.loft([
    { x: 7.7, w: .32, h: .5, y: -.35 },   // rounded nose tip
    { x: 7.1, w: .95, h: .95, y: -.25 },  // cockpit front
    { x: 6.3, w: 1.28, h: 1.2, y: -.1 },
    { x: 5.3, w: 1.42, h: 1.3, y: .0 },
    { x: 3.8, w: 1.46, h: 1.34, y: .05 },
    { x: 1.9, w: 1.47, h: 1.35, y: .05 },
    { x: 0.0, w: 1.47, h: 1.35, y: .05 }, // long constant slab cargo bay
    { x: -1.9, w: 1.46, h: 1.35, y: .05 },
    { x: -3.6, w: 1.44, h: 1.38, y: .08 },
    { x: -4.8, w: 1.4, h: 1.42, y: .15 }, // rear stays full under the pylon
    { x: -5.9, w: 1.3, h: 1.4, y: .3 },   // aft upsweep begins
    { x: -6.8, w: 1.08, h: 1.24, y: .55 },
    { x: -7.5, w: .78, h: 1.0, y: .82 },  // blunt tail, ramp opening below
  ], body, 26);
  part('fuselage', 'Fuselage', 'Primary airframe · cargo hull',
    'The long, tall, slab-sided aluminium hull is one big watertight cargo box with a flat cabin floor running the whole length. It carries up to 33–55 troops or heavy vehicles, with the tandem rotor pylons, engines and fuel all hung off this single load-bearing structure.',
    ['Aluminium-alloy frames', 'Riveted stressed skin', 'Watertight sealed hull', 'Roller-equipped cargo floor'],
    [['Cabin', '33–55 troops'], ['Floor length', '≈9.3 m'], ['Width', '≈2.3 m'], ['Floor', 'Flat · roller rails']], [hull]);

  /* ---- Cockpit: stepped windscreen + chin bubble windows + side glass ---- */
  const cockpit = new THREE.Group();
  const wsL = K.box(1.05, .95, .04, glass); wsL.position.set(6.85, .55, .55); wsL.rotation.set(0, .42, -.22); cockpit.add(wsL);
  const wsR = wsL.clone(); wsR.position.z = -.55; wsR.rotation.y = -.42; cockpit.add(wsR);
  const wsC = K.box(.8, .95, 1.0, glass); wsC.position.set(7.05, .5, 0); wsC.rotation.z = -.3; cockpit.add(wsC);
  // stepped lower windscreen band
  const stepL = K.box(.6, .5, .5, glass); stepL.position.set(7.2, -.1, .42); stepL.rotation.z = -.5; cockpit.add(stepL);
  const stepR = stepL.clone(); stepR.position.z = -.42; cockpit.add(stepR);
  // chin bubble windows (downward-vision glass under the nose)
  const chinL = K.sphere(.4, glass, 1, .7, .9); chinL.position.set(7.35, -.55, .35); cockpit.add(chinL);
  const chinR = chinL.clone(); chinR.position.z = -.35; cockpit.add(chinR);
  // cockpit side sliding windows
  for (const z of [1, -1]) { const sw = K.box(.04, .5, .7, glass); sw.position.set(6.3, .45, z * 1.3); cockpit.add(sw); }
  part('cockpit', 'Cockpit',
    'Crew station · flight deck',
    'Two pilots sit side-by-side behind a stepped, multi-panel windscreen with downward-looking chin bubble windows for precise load placement and brown-out landings. The glazing wraps around the blunt nose giving a wide field of view over the cargo hook work below.',
    ['Multi-pane windscreen', 'Chin bubble vision panels', 'Armoured crew seats'],
    [['Pilots', '2 side-by-side'], ['Crew', '3 (+flight engineer)'], ['Vision', 'Chin bubbles'], ['Windscreen', 'Stepped']], [cockpit]);

  /* ---- Front rotor pylon (short hump above the forward cabin) ---- */
  const frontPylon = new THREE.Group();
  const fpBase = K.box(1.9, 1.1, 2.4, body2); fpBase.position.set(4.6, 1.85, 0); frontPylon.add(fpBase);
  const fpTop = K.box(1.3, .8, 1.9, body2); fpTop.position.set(4.6, 2.5, 0); frontPylon.add(fpTop);
  const fpFair = K.sphere(1.0, body, 1.1, .6, 1.0); fpFair.position.set(5.3, 2.0, 0); frontPylon.add(fpFair); // forward transmission fairing
  const fpMast = new THREE.Mesh(new THREE.CylinderGeometry(.2, .28, .9, 14), metal); fpMast.position.set(4.6, 3.1, 0); frontPylon.add(fpMast);
  part('frontPylon', 'Forward Rotor Pylon', 'Transmission · rotor mount',
    'A short raised hump above the cockpit houses the forward transmission that drives the front rotor. Drive shafts run back along the cabin roof to synchronise it with the rear rotor so the overlapping blades never collide.',
    ['Magnesium gearbox casing', 'Composite fairing', 'Steel drive mast'],
    [['Houses', 'Forward transmission'], ['Height', 'Low (over cabin)'], ['Drive', 'Synchronising shaft']], [frontPylon]);

  /* ---- Rear rotor pylon (tall, swept back, houses engines + aft transmission) ---- */
  const rearPylon = new THREE.Group();
  const rpLow = K.box(2.2, 1.6, 2.6, body2); rpLow.position.set(-5.0, 1.9, 0); rearPylon.add(rpLow);
  const rpMid = K.box(1.9, 1.7, 2.3, body); rpMid.position.set(-5.3, 3.1, 0); rpMid.rotation.z = .16; rearPylon.add(rpMid); // swept upper fin
  const rpTop = K.box(1.4, 1.1, 1.9, body2); rpTop.position.set(-5.7, 4.1, 0); rpTop.rotation.z = .16; rearPylon.add(rpTop);
  const rpFair = K.sphere(1.0, body, 1.2, .7, 1.05); rpFair.position.set(-4.4, 4.0, 0); rpFair.rotation.z = .16; rearPylon.add(rpFair); // aft transmission fairing
  const rpMast = new THREE.Mesh(new THREE.CylinderGeometry(.22, .3, 1.0, 14), metal); rpMast.position.set(-5.75, 4.75, 0); rearPylon.add(rpMast);
  part('rearPylon', 'Rear Rotor Pylon', 'Tall swept pylon · engine bay',
    'The tall, aft-swept rear pylon is the tallest point of the aircraft and carries the rear rotor well above and behind the front one. Its base holds the aft transmission and the two engines, and its broad fin shape also steadies the aircraft in forward flight.',
    ['Load-bearing fin structure', 'Aft transmission bay', 'Combining gearbox'],
    [['Position', 'Aft · swept back'], ['Tallest', 'Yes'], ['Holds', 'Engines + aft gearbox']], [rearPylon]);

  /* ---- Engines: two turboshaft nacelles + bright round exhausts at pylon base ---- */
  const engine = new THREE.Group();
  for (const z of [1.15, -1.15]) {
    const nac = K.tube(.5, .55, 2.6, body2, 18); nac.position.set(-4.4, 2.15, z); engine.add(nac);
    const intake = new THREE.Mesh(new THREE.CylinderGeometry(.42, .42, .35, 16), dark); intake.rotation.z = -Math.PI / 2; intake.position.set(-3.2, 2.2, z); engine.add(intake);
    const screen = new THREE.Mesh(new THREE.CylinderGeometry(.36, .36, .12, 16), metal); screen.rotation.z = -Math.PI / 2; screen.position.set(-3.0, 2.2, z); engine.add(screen);
    // big polished-metal round exhaust pointing rearward, canted slightly outward
    const exh = K.tube(.4, .46, 1.0, bright, 20); exh.position.set(-5.7, 2.05, z); exh.rotation.y = z > 0 ? -.28 : .28; engine.add(exh);
    const mouth = new THREE.Mesh(new THREE.CylinderGeometry(.4, .4, .12, 20), dark); mouth.rotation.z = -Math.PI / 2; mouth.position.set(-6.2, 2.0, z * 1.12); engine.add(mouth);
  }
  part('engine', 'Twin Turboshaft Engines', 'Powerplant',
    'Two Lycoming/Honeywell T55 turboshaft engines are slung on the sides at the base of the rear pylon, feeding power forward and aft through a combining gearbox to both rotors. If one engine fails the other can still drive both rotors, and the large round exhausts vent sideways and rearward.',
    ['Nickel super-alloy turbines', 'Combining gearbox', 'Round metal exhaust ducts'],
    [['Engines', '2 × T55'], ['Power', '≈2 × 3,500–4,800 shp'], ['Feature', 'Either engine drives both rotors']], [engine]);

  /* ---- Rear loading ramp (angled box under the rear pylon) ---- */
  const ramp = new THREE.Group();
  const rampDeck = K.box(2.1, .12, 2.1, body2); rampDeck.position.set(-7.9, -.55, 0); rampDeck.rotation.z = -.3; ramp.add(rampDeck);
  const rampLip = K.box(.5, .1, 2.1, dark); rampLip.position.set(-8.75, -.95, 0); ramp.add(rampLip);
  const rampTop = K.box(1.6, 1.4, 2.0, body); rampTop.position.set(-7.4, .75, 0); ramp.add(rampTop); // upper ramp door fairing
  part('ramp', 'Rear Loading Ramp', 'Cargo loading · access',
    'The full-width hydraulic ramp at the back lowers to the ground so trucks, pallets and troops can drive or walk straight into the cargo bay. It can also be left open in flight for loading slung gear or air-dropping cargo.',
    ['Hydraulic actuation', 'Aluminium ramp deck', 'Non-slip walkway'],
    [['Width', 'Full cabin width'], ['Use', 'Vehicles · pallets · troops'], ['In-flight', 'Can open']], [ramp]);

  /* ---- Side sponsons (long lower fairings: fuel + landing gear) ---- */
  const sponson = new THREE.Group();
  for (const z of [1, -1]) {
    const sp = K.box(8.4, .95, .95, body); sp.position.set(0.0, -.85, z * 1.55); sponson.add(sp);
    const spNose = K.sphere(.55, body, 1.4, .95, 1.0); spNose.position.set(4.3, -.85, z * 1.55); sponson.add(spNose);
    const spTail = K.sphere(.55, body, 1.4, .95, 1.0); spTail.position.set(-4.3, -.85, z * 1.55); sponson.add(spTail);
    const fuelCap = new THREE.Mesh(new THREE.CylinderGeometry(.14, .14, .06, 12), metal); fuelCap.position.set(1.0, -.4, z * 1.55); sponson.add(fuelCap);
  }
  part('sponson', 'Side Sponsons', 'Fuel tanks · gear fairing',
    'Two long streamlined fairings run low along each side of the fuselage. They hold the main fuel tanks and form the mounting structure for the fixed landing gear, keeping the cabin floor completely clear for cargo.',
    ['Self-sealing fuel cells', 'Aluminium fairing skin', 'Gear mounting beams'],
    [['Fuel', 'Internal main tanks'], ['Also', 'Landing-gear mounts'], ['Count', '2 (one per side)']], [sponson]);

  /* ---- Landing gear: 4 fixed wheels on the sponsons (2 forward, 2 rear) ---- */
  const gear = new THREE.Group();
  const fwdL = K.wheel(.42, rubber, steel, .55, 0); fwdL.position.set(2.7, -1.35, 1.65); gear.add(fwdL);
  const fwdR = K.wheel(.42, rubber, steel, .55, 0); fwdR.position.set(2.7, -1.35, -1.65); gear.add(fwdR);
  const aftL = K.wheel(.42, rubber, steel, .55, 0); aftL.position.set(-3.3, -1.35, 1.65); gear.add(aftL);
  const aftR = K.wheel(.42, rubber, steel, .55, 0); aftR.position.set(-3.3, -1.35, -1.65); gear.add(aftR);
  part('gear', 'Landing Gear', 'Ground contact',
    'A fixed quadricycle undercarriage with four wheels mounted on the sponsons — two forward and two aft. The twin rear wheels steer, letting the big helicopter pivot tightly on the ground, and the sprung struts absorb heavy cargo landings.',
    ['Fixed non-retracting legs', 'Oleo shock struts', 'Steerable aft wheels'],
    [['Type', 'Fixed quadricycle'], ['Wheels', '4 (2 fwd · 2 aft)'], ['Aft wheels', 'Steerable']], [gear]);

  /* ---- Round cabin windows along each side ---- */
  const windows = new THREE.Group();
  for (const z of [1, -1]) {
    for (const x of [4.3, 3.1, 1.9, 0.7, -0.5, -1.7, -2.9]) {
      const w = new THREE.Mesh(new THREE.CircleGeometry(.26, 18), glass);
      w.position.set(x, .35, z * 1.47); w.rotation.y = z > 0 ? 0 : Math.PI;
      windows.add(w);
    }
  }
  g.add(windows);
  // tie the windows to the fuselage part for clicking context
  parts.fuselage.objects.push(windows);

  /* ---- Front rotor: 3-blade, mounted on the short front pylon ---- */
  const frontRotor = K.mainRotor({ blades: 3, radius: 9.1, chord: .62, thick: .12, mat: dark, hubMat: steel, hubR: .6, hubH: .45 });
  frontRotor.position.set(4.6, 3.65, 0);
  part('frontRotor', 'Forward Main Rotor', 'Lift · thrust (front)',
    'The forward of the two big three-blade rotors. It turns opposite to the rear rotor so their torques cancel — that is why the Chinook needs no tail rotor. The two discs overlap above the cabin and are geared together so the blades always interleave safely.',
    ['Fibreglass spar blades', 'Titanium hub', 'Counter-rotating (opposite rear)'],
    [['Blades', '3'], ['Diameter', '18.3 m'], ['Turns', 'Opposite rear rotor'], ['Disc', 'Overlaps rear']], [frontRotor]);

  /* ---- Rear rotor: 3-blade, high on the tall rear pylon ---- */
  const rearRotor = K.mainRotor({ blades: 3, radius: 9.1, chord: .62, thick: .12, mat: dark, hubMat: steel, hubR: .6, hubH: .45 });
  rearRotor.position.set(-5.75, 5.3, 0);
  part('rearRotor', 'Rear Main Rotor', 'Lift · thrust (rear) · anti-torque',
    'The rear three-blade rotor sits higher and further back on the tall pylon so its disc clears and overlaps the front one. Running opposite to the front rotor, this tandem layout both lifts the aircraft and balances torque, removing the need for a tail rotor and putting all engine power into lift.',
    ['Fibreglass spar blades', 'Titanium hub', 'Raised to overlap front disc'],
    [['Blades', '3'], ['Diameter', '18.3 m'], ['Turns', 'Opposite front rotor'], ['Mounting', 'High · aft pylon']], [rearRotor]);

  const info = {
    name: 'CH-47 Chinook', variant: 'Boeing · Heavy-Lift Transport',
    role: 'Heavy transport', origin: 'United States', year: 'In service 1962',
    desc: 'A twin-engine, tandem-rotor heavy-lift helicopter with two overlapping three-blade rotors and no tail rotor. In service since 1962, it hauls troops, artillery, vehicles and slung cargo for armies worldwide and remains one of the most capable lifters ever built.',
    specs: [['Crew', '3 + 33–55 troops'], ['Length', '≈30.1 m (incl. rotors)'], ['Rotor', '18.3 m × 2 · 3-blade each'], ['Max speed', '≈315 km/h'], ['Engines', '2 × Lycoming/Honeywell T55'], ['Payload', '≈10,000 kg']],
  };
  return { group: g, parts, info, rotors: { main: [frontRotor, rearRotor], mainAxis: 'y', tail: [], tailAxis: 'z' } };
}
