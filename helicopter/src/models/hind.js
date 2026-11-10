// Mi-24 Hind — detailed procedural gunship model. Nose toward +X.
import * as THREE from 'three';
import { makeKit } from '../kit.js';

export function build() {
  const K = makeKit(THREE);
  const g = new THREE.Group();

  // ---- Materials (Soviet green/tan/brown blotch camo over a lighter base) ----
  const camo = K.camoTex(['#5c6440', '#726a44', '#3d4a2c', '#7e744f'], '#929470');
  const body = K.mat('#929470', { map: camo, rough: .82, metal: .1, env: .6 });
  const body2 = K.mat('#6d6a45', { rough: .8, metal: .12, env: .6 });
  const belly = K.mat('#8fa6b2', { rough: .7, metal: .12, env: .7 }); // light blue-grey underside
  const dark = K.mat('#14171a', { rough: .5, metal: .5 });
  const metal = K.mat('#3a3f44', { rough: .32, metal: .88, env: 1 });
  const steel = K.mat('#23272b', { rough: .4, metal: .82 });
  const glass = K.glass('#13261f', .5);
  const rubber = K.mat('#0b0d0f', { rough: .92, metal: 0 });
  const olive = K.mat('#4c5436', { rough: .7, metal: .2 });
  const lightR = K.mat('#ff3344', { emissive: '#ff2233', emissiveI: 1.4, rough: .4 });
  const lightG = K.mat('#33ff88', { emissive: '#22ff77', emissiveI: 1.4, rough: .4 });

  const parts = {};
  const part = (key, name, role, fn, mats, specs, objects) => { parts[key] = { name, role, fn, mats, specs, objects }; objects.forEach(o => g.add(o)); };

  /* ---- Fuselage (lofted hull): fat forward cabin tapering to a slim tail boom ---- */
  const hull = K.loft([
    { x: 8.4, w: .16, h: .2, y: -.35 },   // gun nose tip (low)
    { x: 7.9, w: .40, h: .48, y: -.22 },
    { x: 7.2, w: .62, h: .72, y: -.05 },  // gunner station bulge
    { x: 6.3, w: .80, h: .92, y: .05 },
    { x: 5.2, w: .92, h: 1.10, y: .14 },  // pilot step-up
    { x: 3.8, w: 1.00, h: 1.24, y: .15 }, // cabin
    { x: 2.2, w: 1.04, h: 1.32, y: .15 }, // widest (troop cabin)
    { x: 0.6, w: .98, h: 1.30, y: .20 },  // engine deck
    { x: -1.0, w: .82, h: 1.14, y: .26 },
    { x: -2.6, w: .60, h: .88, y: .36 },  // taper to boom
    { x: -4.2, w: .40, h: .58, y: .50 },
    { x: -6.0, w: .32, h: .46, y: .62 },  // slim tail boom
    { x: -7.8, w: .30, h: .44, y: .70 },
    { x: -8.8, w: .28, h: .42, y: .86 },
  ], body, 26);
  // Light blue-grey belly accent (second thin shell, dropped down so only the underside shows)
  const bellyPan = K.loft([
    { x: 8.2, w: .14, h: .18, y: -.5 },
    { x: 7.2, w: .50, h: .55, y: -.28 },
    { x: 5.2, w: .74, h: .82, y: -.18 },
    { x: 3.0, w: .82, h: .95, y: -.16 },
    { x: 0.8, w: .78, h: .95, y: -.12 },
    { x: -1.2, w: .62, h: .82, y: -.05 },
  ], belly, 22);
  part('fuselage', 'Fuselage', 'Primary airframe',
    'A long, heavily-armoured all-metal hull that is fat in the forward crew-and-cabin section and tapers into a slim tail boom. Behind the two-man cockpit sits a sealed troop bay — the Hind is unique in carrying up to eight soldiers while still fighting like a gunship.',
    ['Welded steel / aluminium frames', 'Titanium cockpit tub armour', 'Self-sealing fuel tanks'],
    [['Length', '~17.5 m'], ['Cabin', 'Up to 8 troops'], ['Armour', 'Titanium tub'], ['Config', 'Gunship + transport']], [hull, bellyPan]);

  /* ---- Cockpit: the signature DOUBLE-BUBBLE tandem canopy ---- */
  const cockpit = new THREE.Group();
  // Low gunner bubble at the very front
  const gunBubble = K.sphere(.68, glass, 1.25, .92, 1.0); gunBubble.position.set(7.0, .0, 0); cockpit.add(gunBubble);
  const gunFrameT = K.box(1.3, .06, .9, dark); gunFrameT.position.set(7.0, .52, 0); gunFrameT.rotation.z = .08; cockpit.add(gunFrameT);
  const gunFrameM = K.box(.05, .5, .9, dark); gunFrameM.position.set(6.55, .1, 0); cockpit.add(gunFrameM);
  // Raised pilot bubble, stepped UP and behind the gunner
  const pilotBubble = K.sphere(.78, glass, 1.15, 1.05, .98); pilotBubble.position.set(5.35, .9, 0); cockpit.add(pilotBubble);
  const step = K.box(.55, .55, 1.0, body2); step.position.set(6.05, .55, 0); step.rotation.z = -.55; cockpit.add(step); // armoured step between the two bubbles
  const pilotFrameT = K.box(1.5, .06, 1.0, dark); pilotFrameT.position.set(5.35, 1.55, 0); cockpit.add(pilotFrameT);
  const pilotFrameM = K.box(.05, .9, 1.0, dark); pilotFrameM.position.set(4.7, .95, 0); cockpit.add(pilotFrameM);
  // Cabin troop windows along the sides
  for (const z of [1, -1]) for (const x of [3.6, 2.7]) { const cw = K.box(.04, .42, .5, glass); cw.position.set(x, .35, z * 1.03); cockpit.add(cw); }
  part('cockpit', 'Tandem Double-Bubble Canopy', 'Crew station',
    'The Hind\'s unmistakable feature: a low bubble canopy for the weapons officer at the very nose, with a second bubble canopy for the pilot stepped up and back behind it. Both crew sit in heavily glazed, armoured stations stacked one above the other.',
    ['Bullet-resistant laminated glass', 'Armoured bulkhead between bubbles', 'Steel canopy frames'],
    [['Crew', '2–3'], ['Layout', 'Tandem stepped'], ['Front', 'Gunner (low)'], ['Rear', 'Pilot (raised)']], [cockpit]);

  /* ---- Chin turret: nose gun + sensor blisters (registered as 'sensor') ---- */
  const sensor = new THREE.Group();
  const turret = K.sphere(.42, dark, 1.2, .85, 1.0); turret.position.set(7.2, -.6, 0); sensor.add(turret);
  for (const z of [.12, -.12]) { const barrel = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, 1.3, 10), metal); barrel.rotation.z = -Math.PI / 2; barrel.position.set(8.0, -.62, z); sensor.add(barrel); }
  // Twin round sensor/searchlight blisters below the gunner bubble
  for (const z of [.3, -.3]) { const bl = K.sphere(.2, metal, 1, 1, 1); bl.position.set(7.55, -.25, z); sensor.add(bl); const lens = new THREE.Mesh(new THREE.CylinderGeometry(.13, .13, .06, 14), K.mat('#0a2630', { metal: .3, rough: .05, emissive: '#0a3b4a', emissiveI: .5 })); lens.rotation.z = -Math.PI / 2; lens.position.set(7.74, -.25, z); sensor.add(lens); }
  part('sensor', 'Chin Turret & Sensors', 'Gun · targeting',
    'A powered chin turret under the nose carries a 12.7 mm machine gun that the weapons officer slews onto targets, flanked by low-light and infra-red sensor blisters for aiming in poor visibility. It lets the Hind strafe ground targets independently of the fixed wing weapons.',
    ['Gyro-stabilised turret', '12.7 mm Yak-B gun', 'IR / low-light optics'],
    [['Turret', 'Chin, powered'], ['Gun', '12.7 mm 4-barrel'], ['Sensors', 'FLIR · searchlight']], [sensor]);

  /* ---- Mid-mounted ANHEDRAL stub wings + weapons (rocket pods & ATGMs) ---- */
  const wings = new THREE.Group();
  const weapons = new THREE.Group();
  for (const s of [1, -1]) { // s=+1 left (+Z), s=-1 right (-Z)
    // Wing surface (droops downward = anhedral)
    const wg = new THREE.Group(); wg.position.set(2.3, .45, s * .9); wg.rotation.x = s * .26;
    const wing = K.box(1.7, .26, 2.5, olive); wing.geometry.translate(0, 0, s * 1.3); wg.add(wing);
    const tipPlate = K.box(1.9, .5, .14, body2); tipPlate.position.set(0, 0, s * 2.55); wg.add(tipPlate); // endplate pylon
    const pylonIn = K.box(.5, .4, .3, steel); pylonIn.position.set(.1, -.28, s * 1.4); wg.add(pylonIn);
    wings.add(wg);

    // Weapons hung under the same drooped wing transform
    const wp = new THREE.Group(); wp.position.set(2.3, .45, s * .9); wp.rotation.x = s * .26;
    // Inner rocket pod (B-8 / UB-32 type)
    const pod = K.tube(.26, .26, 1.6, dark, 16); pod.position.set(.1, -.58, s * 1.4); wp.add(pod);
    const podFace = new THREE.Mesh(new THREE.CylinderGeometry(.24, .24, .08, 18), steel); podFace.rotation.z = -Math.PI / 2; podFace.position.set(.9, -.58, s * 1.4); wp.add(podFace);
    for (let r = 0; r < 7; r++) { const a = r / 7 * Math.PI * 2; const tubeH = new THREE.Mesh(new THREE.CylinderGeometry(.05, .05, .1, 7), dark); tubeH.rotation.z = -Math.PI / 2; tubeH.position.set(.95, -.58 + Math.sin(a) * .12, s * 1.4 + Math.cos(a) * .12); wp.add(tubeH); }
    // Wingtip ATGM launch rails (Shturm/Ataka) — two stacked tubes
    for (const dy of [.02, -.22]) { const rail = K.tube(.09, .09, 1.5, olive, 10); rail.position.set(.2, dy, s * 2.62); wp.add(rail); const nose = new THREE.Mesh(new THREE.ConeGeometry(.09, .28, 10), dark); nose.rotation.z = -Math.PI / 2; nose.position.set(1.05, dy, s * 2.62); wp.add(nose); }
    weapons.add(wp);
  }
  part('stubWing', 'Anhedral Stub Wings', 'Lift · weapon pylons',
    'Short mid-fuselage wings that droop sharply downward (anhedral) and carry up to six weapon pylons. In fast forward flight they offload the rotor by producing a quarter of the lift, and they double the Hind\'s weapon capacity over a pure helicopter.',
    ['Metal torsion-box spar', 'Six hardpoints', 'Endplate launch rails'],
    [['Hardpoints', '6'], ['Dihedral', 'Anhedral (droop)'], ['Lift share', '~25% in cruise']], [wings]);
  part('weapons', 'Rocket Pods & ATGMs', 'Firepower',
    'The wings carry B-8/UB-type unguided rocket pods on the inner pylons and radio-guided anti-tank missiles on the wingtip rails, so one aircraft can hit soft targets, fortifications and armour in a single pass.',
    ['57/80 mm rocket pods', 'Shturm/Ataka ATGM tubes', 'Pylon ejector racks'],
    [['Rockets', '2 × pods'], ['ATGM', '4 × wingtip'], ['Guns', 'Chin 12.7 mm']], [weapons]);

  /* ---- Engines: twin turboshafts on top, big forward round intakes ---- */
  const engine = new THREE.Group();
  const deck = K.box(2.4, .7, 1.6, body2); deck.position.set(.2, 1.55, 0); engine.add(deck);
  for (const z of [.5, -.5]) {
    const intake = new THREE.Mesh(new THREE.CylinderGeometry(.42, .42, .7, 20), body2); intake.rotation.z = -Math.PI / 2; intake.position.set(1.35, 1.7, z); engine.add(intake);
    const inMouth = new THREE.Mesh(new THREE.CylinderGeometry(.34, .34, .3, 20), dark); inMouth.rotation.z = -Math.PI / 2; inMouth.position.set(1.62, 1.7, z); engine.add(inMouth);
    const exh = K.tube(.3, .34, .9, steel, 16); exh.position.set(-1.1, 1.5, z * 1.05); exh.rotation.y = z > 0 ? -.2 : .2; engine.add(exh);
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(.04, .3, .12, 16), dark); cap.rotation.z = -Math.PI / 2; cap.position.set(-1.6, 1.46, z * 1.1); engine.add(cap);
  }
  part('engine', 'Twin Turboshafts', 'Powerplant',
    'Two Isotov TV3-117 turboshaft engines sit side-by-side above the cabin, breathing through the Hind\'s distinctive round dust-filtered intakes and driving the single main gearbox. They give the heavy gunship its high cruise speed and good hot-and-high performance.',
    ['TV3-117 turboshaft', 'PZU dust filters', 'Common main gearbox'],
    [['Engines', '2 × Isotov TV3-117'], ['Intakes', 'Round, filtered'], ['Drive', 'Single main gearbox']], [engine]);

  /* ---- Main rotor: FIVE blades on a tall rotor head ---- */
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(.2, .28, 1.3, 16), metal); mast.position.set(.3, 2.25, 0);
  const swash = new THREE.Mesh(new THREE.CylinderGeometry(.45, .5, .2, 20), steel); swash.position.set(.3, 2.55, 0);
  const rotor = K.mainRotor({ blades: 5, radius: 8.5, chord: .5, thick: .1, mat: dark, hubMat: steel, hubR: .5, hubH: .5 });
  rotor.position.set(.3, 2.9, 0);
  for (let i = 0; i < 5; i++) { const a = i / 5 * Math.PI * 2; const link = new THREE.Mesh(new THREE.BoxGeometry(.5, .14, .12), metal); link.position.set(.3 + Math.cos(a) * .65, 2.72, -Math.sin(a) * .65); link.rotation.y = a; g.add(link); }
  part('mainRotor', 'Five-Blade Main Rotor', 'Lift · thrust · control',
    'A tall rotor head carries five all-metal blades — one more than most gunships — to lift the Hind\'s heavy combined weapon and troop load. The whole disc tilts to drive the aircraft and gives it an unusually high top speed for an armed helicopter.',
    ['Metal spar blades', 'Steel / titanium hub', 'Hydraulic swashplate'],
    [['Blades', '5'], ['Diameter', '17.3 m'], ['Top speed', '~335 km/h'], ['RPM', '~240']], [mast, swash, rotor]);

  /* ---- Tail: swept fin, port-side 3-blade tail rotor, horizontal stabilisers ---- */
  const fin = K.box(1.5, 2.6, .34, body); fin.geometry.translate(0, 1.3, 0); fin.position.set(-8.7, .8, 0); fin.rotation.z = .22; // swept vertical fin
  const finTip = K.box(.7, .5, .36, body2); finTip.position.set(-9.25, 3.1, 0);
  // Horizontal stabilisers near the end of the boom
  const stab = new THREE.Group();
  const stabO = K.box(.9, .12, 3.2, body); stabO.position.set(-7.4, .66, 0); stab.add(stabO);
  for (const z of [1.4, -1.4]) { const ep = K.box(.7, .4, .12, body2); ep.position.set(-7.4, .7, z); stab.add(ep); }
  // 3-blade tail rotor on the LEFT (+Z) side near the top of the fin
  const trMount = new THREE.Group(); trMount.position.set(-9.0, 2.35, .42);
  const trHub = new THREE.Mesh(new THREE.CylinderGeometry(.16, .16, .26, 14), steel); trHub.rotation.x = Math.PI / 2; trMount.add(trHub);
  const trSpin = new THREE.Group();
  for (let i = 0; i < 3; i++) { const a = i / 3 * Math.PI * 2; const bl = K.box(1.35, .05, .24, dark); bl.geometry.translate(.68, 0, 0); const bg = new THREE.Group(); bg.rotation.z = a; bg.add(bl); trSpin.add(bg); }
  trMount.add(trSpin);
  part('tailRotor', 'Tail Rotor & Fin', 'Anti-torque · yaw',
    'A three-blade tail rotor mounted on the port side near the top of a swept load-bearing fin cancels the main-rotor torque and gives yaw control. Small horizontal stabilisers at the base of the boom trim the aircraft in pitch through its speed range.',
    ['Composite / metal blades', 'Load-bearing swept fin', 'Trim stabilisers'],
    [['Blades', '3'], ['Side', 'Port (left)'], ['Fin', 'Swept, offset']], [fin, finTip, stab, trMount]);

  /* ---- Retractable tricycle landing gear (shown extended) ---- */
  const gear = new THREE.Group();
  const nw = K.wheel(.3, rubber, steel, 1.0, 0); nw.position.set(5.6, -1.55, 0); gear.add(nw);
  const mwL = K.wheel(.42, rubber, steel, 1.1, .2); mwL.position.set(1.4, -1.55, 1.35); gear.add(mwL);
  const mwR = K.wheel(.42, rubber, steel, 1.1, -.2); mwR.position.set(1.4, -1.55, -1.35); gear.add(mwR);
  part('gear', 'Retractable Tricycle Gear', 'Ground contact',
    'A tricycle undercarriage — a single nose wheel forward and two larger main wheels — that normally folds up in flight to cut drag and is shown here extended. The long oleo struts absorb the shock of landings carrying a full weapon and troop load.',
    ['Oleo-pneumatic struts', 'Twin-tyre main units', 'Retraction jacks'],
    [['Type', 'Retractable tricycle'], ['Nose', '1 wheel'], ['Mains', '2 wheels']], [gear]);

  /* ---- Antennas + nav lights ---- */
  const pitot = new THREE.Mesh(new THREE.CylinderGeometry(.025, .025, 1.1, 8), metal); pitot.rotation.z = -Math.PI / 2; pitot.position.set(8.6, .1, .25); g.add(pitot);
  const nL = new THREE.Mesh(new THREE.SphereGeometry(.08, 8, 8), lightR); nL.position.set(2.3, .3, 1.06); g.add(nL);
  const nR = new THREE.Mesh(new THREE.SphereGeometry(.08, 8, 8), lightG); nR.position.set(2.3, .3, -1.06); g.add(nR);

  const info = {
    name: 'Mi-24 Hind', variant: 'Mil · Attack + Transport Gunship',
    role: 'Gunship / Assault transport', origin: 'Soviet Union / Russia', year: 'In service 1972',
    desc: 'A heavily armoured Soviet gunship that is unique in combining a hard-hitting weapons fit with a sealed cabin for up to eight troops. Nicknamed the "flying tank", it can strafe a target with rockets, missiles and a chin gun and then land to insert or recover its infantry squad.',
    specs: [['Crew', '2–3 + up to 8 troops'], ['Length', '~17.5 m'], ['Rotor', '17.3 m · 5-blade'], ['Max speed', '~335 km/h'], ['Engines', '2 × Isotov TV3-117'], ['Armament', '12.7 mm gun + rockets + ATGM']],
  };
  return { group: g, parts, info, rotors: { main: [rotor], mainAxis: 'y', tail: [trSpin], tailAxis: 'z' } };
}
