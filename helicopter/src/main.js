// Multi-helicopter interactive viewer — tabbed, orbit, clickable parts, cinematic HUD + audio.
// Each aircraft is an original detailed procedural model (Three.js r160, vendored). By Akash M.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { build as buildBlackhawk } from './models/blackhawk.js';
import { build as buildApache } from './models/apache.js';
import { build as buildChinook } from './models/chinook.js';
import { build as buildHind } from './models/hind.js';

const $ = s => document.querySelector(s);
const rand = (a, b) => a + Math.random() * (b - a);
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const damp = (a, b, l, dt) => a + (b - a) * (1 - Math.exp(-l * dt));
const easeIO = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

const MODELS = [
  { id: 'blackhawk', tab: 'UH-60 BLACK HAWK', build: buildBlackhawk },
  { id: 'apache', tab: 'AH-64 APACHE', build: buildApache },
  { id: 'chinook', tab: 'CH-47 CHINOOK', build: buildChinook },
  { id: 'hind', tab: 'Mi-24 HIND', build: buildHind },
];

/* renderer / scene ------------------------------------------------- */
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
scene.fog = new THREE.FogExp2('#05080c', 0.016);
const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.1, 500);
camera.position.set(16, 8, 20);

scene.add(new THREE.HemisphereLight('#9fc4ff', '#0a0f14', 0.5));
const key = new THREE.DirectionalLight('#fff4e6', 2.5); key.position.set(12, 18, 9); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); key.shadow.camera.near = 1; key.shadow.camera.far = 80;
key.shadow.camera.left = -24; key.shadow.camera.right = 24; key.shadow.camera.top = 24; key.shadow.camera.bottom = -24; key.shadow.bias = -0.0004; scene.add(key);
const rimC = new THREE.PointLight('#5fe6ff', 110, 80); rimC.position.set(-16, 6, -12); scene.add(rimC);
const rimA = new THREE.PointLight('#ff8a3c', 70, 70); rimA.position.set(13, 4, -14); scene.add(rimA);
scene.add((() => { const s = new THREE.SpotLight('#dfeeff', 140, 60, 0.5, 0.6, 1.2); s.position.set(0, 26, 3); return s; })());

const pmrem = new THREE.PMREMGenerator(renderer); pmrem.compileEquirectangularShader();
new RGBELoader().setPath('./assets/').load('env.hdr', (hdr) => { hdr.mapping = THREE.EquirectangularReflectionMapping; scene.environment = pmrem.fromEquirectangular(hdr).texture; hdr.dispose(); }, undefined, () => {});

/* helipad ---------------------------------------------------------- */
function padTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 1024; const x = c.getContext('2d');
  x.fillStyle = '#12161b'; x.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 9000; i++) { const g = 18 + Math.random() * 34 | 0; x.fillStyle = `rgba(${g},${g + 4},${g + 8},${Math.random() * .5})`; x.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 2); }
  x.strokeStyle = 'rgba(255,194,77,.45)'; x.lineWidth = 16; x.beginPath(); x.arc(512, 512, 400, 0, 7); x.stroke();
  x.setLineDash([46, 30]); x.lineWidth = 9; x.beginPath(); x.arc(512, 512, 360, 0, 7); x.stroke(); x.setLineDash([]);
  x.fillStyle = 'rgba(255,194,77,.5)'; x.font = 'bold 360px ui-monospace, monospace'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('H', 512, 540);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const PAD_Y = -3.0;
const pad = new THREE.Mesh(new THREE.CircleGeometry(34, 64), new THREE.MeshStandardMaterial({ map: padTexture(), roughness: .92, metalness: .05, envMapIntensity: .35 }));
pad.rotation.x = -Math.PI / 2; pad.position.y = PAD_Y; pad.receiveShadow = true; scene.add(pad);
const grid = new THREE.GridHelper(100, 100, 0x17323f, 0x0d1c24); grid.position.y = PAD_Y + 0.01; grid.material.transparent = true; grid.material.opacity = .32; scene.add(grid);

const modelHolder = new THREE.Group(); scene.add(modelHolder);

/* post ------------------------------------------------------------- */
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.38, 0.7, 0.9);
composer.addPass(bloom);
composer.addPass(new OutputPass());

/* controls --------------------------------------------------------- */
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.07;
controls.minDistance = 8; controls.maxDistance = 48;
controls.maxPolarAngle = Math.PI * 0.54; controls.minPolarAngle = 0.12;
controls.target.set(0, 0, 0); controls.autoRotate = true; controls.autoRotateSpeed = 0.5;
controls.addEventListener('start', () => { canvas.classList.add('grab'); controls.autoRotate = false; firstGesture(); });
controls.addEventListener('end', () => canvas.classList.remove('grab'));

/* audio ------------------------------------------------------------ */
class Audio {
  constructor() { this.ready = false; this.on = false; }
  init() { if (this.ready) return; try {
    const AC = window.AudioContext || window.webkitAudioContext; const ctx = this.ctx = new AC();
    const master = this.master = ctx.createGain(); master.gain.value = 0; const comp = ctx.createDynamicsCompressor(); master.connect(comp); comp.connect(ctx.destination);
    const verb = ctx.createConvolver(); verb.buffer = this._imp(2.4, 3); const vg = ctx.createGain(); vg.gain.value = .5; verb.connect(vg); vg.connect(master); this.verb = verb;
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
  setRotor(l) { if (!this.ready) return; const t = this.ctx.currentTime; this.rg.gain.setTargetAtTime(0.16 * l, t, .4); this.rlfo.frequency.setTargetAtTime(6 + l * 16, t, .5); this.rosc.frequency.setTargetAtTime(36 + l * 20, t, .5); this.rlp.frequency.setTargetAtTime(140 + l * 520, t, .5); this.rwg.gain.setTargetAtTime(0.028 * l, t, .5); }
  _tone(f, dur, g, type) { if (!this.on) return; const t = this.ctx.currentTime, o = this.ctx.createOscillator(), gn = this.ctx.createGain(), pan = this.ctx.createStereoPanner(); o.type = type || 'sine'; o.frequency.value = f; pan.pan.value = rand(-.4, .4); gn.gain.setValueAtTime(0, t); gn.gain.linearRampToValueAtTime(g, t + .006); gn.gain.exponentialRampToValueAtTime(.0004, t + dur); o.connect(gn); gn.connect(pan); pan.connect(this.master); pan.connect(this.verb); o.start(t); o.stop(t + dur + .03); }
  swoosh() { if (!this.on) return; const t = this.ctx.currentTime; const s = this.ctx.createBufferSource(); s.buffer = this._noise(0.7); const bp = this.ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = 1.1; bp.frequency.setValueAtTime(280, t); bp.frequency.exponentialRampToValueAtTime(3600, t + .22); bp.frequency.exponentialRampToValueAtTime(360, t + .6); const g = this.ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.2, t + .07); g.gain.exponentialRampToValueAtTime(.001, t + .62); s.connect(bp); bp.connect(g); g.connect(this.master); g.connect(this.verb); s.start(); const o = this.ctx.createOscillator(), og = this.ctx.createGain(); o.type = 'sine'; o.frequency.setValueAtTime(130, t); o.frequency.exponentialRampToValueAtTime(42, t + .5); og.gain.setValueAtTime(.12, t); og.gain.exponentialRampToValueAtTime(.001, t + .55); o.connect(og); og.connect(this.master); o.start(t); o.stop(t + .6); }
  click() { if (!this.on) return; const t = this.ctx.currentTime; const s = this.ctx.createBufferSource(); s.buffer = this._noise(.12); const hp = this.ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 900; const g = this.ctx.createGain(); g.gain.setValueAtTime(.12, t); g.gain.exponentialRampToValueAtTime(.001, t + .09); s.connect(hp); hp.connect(g); g.connect(this.master); s.start(); this._tone(180, .14, .1, 'square'); this._tone(880, .5, .05, 'triangle'); }
  hover() { this._tone(this.pent[(Math.random() * this.pent.length) | 0] * 2, .5, .03, 'triangle'); }
  tick() { this._tone(1400 + Math.random() * 1600, .03, .02, 'square'); }
  digital() { if (!this.on) return; [0, 1, 2, 3].forEach(i => setTimeout(() => this._tone(this.pent[i], .25, .05, 'triangle'), i * 55)); }
  power() { if (!this.on) return; [392, 523, 659, 880].forEach((f, i) => setTimeout(() => this._tone(f, .6, .07, 'sawtooth'), i * 90)); }
}
const audio = new Audio();

/* ------------------------------------------------------------------ *
 * Model manager
 * ------------------------------------------------------------------ */
let active = -1, current = null, rotorSpin = 0, rotorGoal = 0, frozen = false;
function setupModel(built) {
  const { parts, rotors, info } = built, inner = built.group;
  const pickables = [];
  for (const k in parts) parts[k].objects.forEach(o => o.traverse(m => { if (m.isMesh) { m.userData.part = k; m.castShadow = true; m.receiveShadow = true; m.material.emissive = m.material.emissive || new THREE.Color(0); m.userData.baseEmis = m.material.emissive.clone(); pickables.push(m); } }));
  inner.updateWorldMatrix(true, true);
  let box = new THREE.Box3().setFromObject(inner); const size = box.getSize(new THREE.Vector3()), ctr = box.getCenter(new THREE.Vector3());
  inner.position.sub(ctr); // centre geometry
  const outer = new THREE.Group(); outer.add(inner);
  const s = 16 / Math.max(size.x, size.y, size.z); outer.scale.setScalar(s);
  outer.updateWorldMatrix(true, true); box = new THREE.Box3().setFromObject(outer); outer.position.y += (PAD_Y + 0.15 - box.min.y);
  outer.visible = false; modelHolder.add(outer);
  return { group: outer, parts, rotors, info, pickables };
}
function showModel(i) {
  if (i === active) return;
  if (current) current.group.visible = false;
  active = i; const M = MODELS[i];
  try { if (!M.cache) M.cache = setupModel(M.build()); } catch (e) { console.error('model build failed', M.id, e); return; }
  current = M.cache; current.group.visible = true;
  $('#mName').textContent = current.info.name; $('#mVariant').textContent = current.info.variant;
  $('#partcount').textContent = Object.keys(current.parts).length;
  [...$('#tabs').children].forEach((b, k) => b.classList.toggle('on', k === i));
  buildDots(); selected = null; hovered = null; [...$('#dots').children].forEach(d => d.classList.remove('active')); fillDossier(); frameModel();
  if (audio.on) audio.swoosh();
}
function frameModel() {
  const box = new THREE.Box3().setFromObject(current.group); const c = box.getCenter(new THREE.Vector3()); const r = box.getSize(new THREE.Vector3()).length();
  tweenTo(c, new THREE.Vector3(c.x + r * 0.7, c.y + r * 0.35, c.z + r * 0.85), 1200);
}

/* tabs UI */
const tabsEl = $('#tabs');
MODELS.forEach((m, i) => { const b = document.createElement('button'); b.className = 'tab mono'; b.textContent = m.tab; b.onclick = () => { firstGesture(); showModel(i); }; tabsEl.appendChild(b); });

/* ------------------------------------------------------------------ *
 * Interaction + panel
 * ------------------------------------------------------------------ */
const raycaster = new THREE.Raycaster(); const ndc = new THREE.Vector2();
let hovered = null, selected = null, _downX = 0, _downY = 0;
const tag = $('#tag');
addEventListener('pointermove', e => {
  ndc.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  tag.style.left = e.clientX + 'px'; tag.style.top = e.clientY + 'px';
  if (selected || !current) return;
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObjects(current.pickables, false)[0];
  const key = hit ? hit.object.userData.part : null;
  canvas.classList.toggle('aim', !!key);
  if (key) { tag.textContent = current.parts[key].name; tag.classList.add('show'); } else tag.classList.remove('show');
  if (key !== hovered) { setHover(key); if (key) audio.hover(); }
}, { passive: true });
renderer.domElement.addEventListener('pointerdown', e => { _downX = e.clientX; _downY = e.clientY; });
addEventListener('pointerup', e => {
  firstGesture();
  if (Math.abs(e.clientX - _downX) + Math.abs(e.clientY - _downY) > 6 || !current) return;
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObjects(current.pickables, false)[0];
  if (hit) select(hit.object.userData.part); else if (selected) select(null);
});
addEventListener('keydown', e => { if (e.key === 'Escape') select(null); });

function setHover(key) {
  hovered = key; if (!current) return;
  current.pickables.forEach(m => { const on = (m.userData.part === key); if (m.material.emissive) m.material.emissive.copy(m.userData.baseEmis).lerp(new THREE.Color('#1b6b7a'), on ? 1 : 0); });
}

const P = { id: $('#pId'), name: $('#pName'), role: $('#pRole'), purpose: $('#pPurpose'), mats: $('#pMats'), specs: $('#pSpecs'), panel: $('#panel'), secMat: $('#secMat'), secSpec: $('#secSpec') };
$('#pX').onclick = () => select(null);
const GLY = '!<>-_\\/[]{}=+*^?#01ABCDEFGHJKLMNPQRSTUVWXYZ';
function decodeInto(el, text, dur, snd) { const id = (el.__t = (el.__t || 0) + 1), st = performance.now(); (function s(n) { if (id !== el.__t) return; const t = clamp((n - st) / dur, 0, 1), r = Math.floor(text.length * t); let o = ''; for (let i = 0; i < text.length; i++) o += i < r ? text[i] : (text[i] === ' ' ? ' ' : GLY[(Math.random() * GLY.length) | 0]); el.textContent = o; if (snd && Math.random() < .5) audio.tick(); t < 1 ? requestAnimationFrame(s) : el.textContent = text; })(st); }
function typeInto(el, text, dur, snd) { const id = (el.__t = (el.__t || 0) + 1), st = performance.now(); (function s(n) { if (id !== el.__t) return; const t = clamp((n - st) / dur, 0, 1), c = Math.floor(text.length * t); el.textContent = text.slice(0, c) + (t < 1 ? '▌' : ''); if (snd && c % 2 === 0) audio.tick(); t < 1 ? requestAnimationFrame(s) : el.textContent = text; })(st); }

function fillDossier() {
  const d = current.info;
  P.id.textContent = '// AIRCRAFT DOSSIER'; P.secMat.textContent = 'Origin & Class'; P.secSpec.textContent = 'Specification';
  decodeInto(P.name, d.name, 650, true); P.role.textContent = d.variant.toUpperCase();
  typeInto(P.purpose, d.desc, 1000, true);
  P.mats.innerHTML = [d.origin, d.role, d.year].filter(Boolean).map(m => `<span>${m}</span>`).join('');
  P.specs.innerHTML = d.specs.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
}
const _box = new THREE.Box3(), _ctr = new THREE.Vector3();
function partCenter(key) { _box.makeEmpty(); current.parts[key].objects.forEach(o => _box.expandByObject(o)); return _box.getCenter(_ctr).clone(); }
function select(key) {
  if (key === selected) return; selected = key;
  const dots = [...$('#dots').children]; dots.forEach(d => d.classList.toggle('active', d.dataset.k === key));
  if (key) {
    const d = current.parts[key];
    P.id.textContent = '// SUBSYSTEM'; P.secMat.textContent = 'Materials'; P.secSpec.textContent = 'Specification';
    decodeInto(P.name, d.name, 600, true); P.role.textContent = ''; setTimeout(() => decodeInto(P.role, (d.role || '').toUpperCase(), 450, false), 120);
    setTimeout(() => typeInto(P.purpose, d.fn, 900, true), 240);
    P.mats.innerHTML = (d.mats || []).map(m => `<span>${m}</span>`).join('');
    P.specs.innerHTML = (d.specs || []).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
    setHover(key); audio.swoosh(); setTimeout(() => audio.digital(), 120);
    controls.autoRotate = false; if (!frozen) { rotorGoal = 0.22; audio.setRotor(0.22); }
    const c = partCenter(key); const dir = camera.position.clone().sub(controls.target).normalize();
    const r = new THREE.Box3().setFromObject(current.group).getSize(new THREE.Vector3()).length();
    tweenTo(c, c.clone().add(dir.multiplyScalar(r * 0.42)).add(new THREE.Vector3(0, r * 0.06, 0)), 1050);
    canvas.classList.remove('aim'); tag.classList.remove('show');
  } else {
    if (current) fillDossier(); setHover(null); if (!frozen) { rotorGoal = 1; audio.setRotor(1); }
    if (audio.on) audio.swoosh(); frameModel();
    setTimeout(() => { if (!selected && !frozen) controls.autoRotate = true; }, 2600);
  }
}

/* part dots */
function buildDots() {
  const el = $('#dots'); el.innerHTML = '';
  Object.entries(current.parts).forEach(([k, p]) => { const d = document.createElement('div'); d.className = 'dot'; d.dataset.k = k; d.innerHTML = `<span>${p.name}</span>`; d.onclick = () => select(k); el.appendChild(d); });
}

/* camera tween */
let tw = null;
function tweenTo(toT, toP, dur) { tw = { t0: performance.now(), dur, fT: controls.target.clone(), tT: toT.clone(), fP: camera.position.clone(), tP: toP.clone() }; }

/* controls: sound + freeze + gesture ------------------------------- */
const sndBtn = $('#sound');
sndBtn.onclick = () => { if (!audio.on) { if (audio.enable()) { sndBtn.classList.add('on'); sndBtn.textContent = '◼ SOUND ON'; audio.setRotor(bootDone && !frozen ? 1 : 0); } } else { audio.disable(); sndBtn.classList.remove('on'); sndBtn.textContent = '◼ SOUND OFF'; } };
let gestured = false; function firstGesture() { if (gestured) return; gestured = true; if (audio.enable()) { sndBtn.classList.add('on'); sndBtn.textContent = '◼ SOUND ON'; audio.setRotor(bootDone && !frozen ? 1 : 0); } }
const frzBtn = $('#freeze');
frzBtn.onclick = () => { frozen = !frozen; frzBtn.classList.toggle('on', frozen); frzBtn.textContent = frozen ? '▶ RESUME' : '⏸ FREEZE'; if (frozen) { rotorGoal = 0; controls.autoRotate = false; audio.setRotor(0); } else { rotorGoal = bootDone ? (selected ? 0.22 : 1) : rotorGoal; if (!selected) controls.autoRotate = true; audio.setRotor(bootDone ? rotorGoal : 0); } };

addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight); });

/* boot ------------------------------------------------------------- */
const boot = $('#boot'), bootFill = $('#bootFill'), bootStat = $('#bootStat'), bootPct = $('#bootPct'), bootD = $('#bootD');
const BSTAT = ['AWAITING OPERATOR', 'POWERING AVIONICS', 'LOADING AIRFRAME', 'SPOOLING ENGINES', 'ROTOR ENGAGE', 'SYSTEMS ONLINE'];
let bootDone = false, booting = false;
function runBoot(withSound) {
  if (booting || bootDone) return; booting = true; boot.classList.add('booting');
  if (withSound) { audio.enable(); sndBtn.classList.add('on'); sndBtn.textContent = '◼ SOUND ON'; }
  let p = 0;
  const iv = setInterval(() => {
    p = Math.min(100, p + (Math.random() < .12 ? 0 : rand(2, 7)));
    bootFill.style.right = (100 - p) + '%'; bootPct.textContent = String(p | 0).padStart(2, '0');
    const st = BSTAT[Math.min(BSTAT.length - 1, Math.floor(p / 100 * BSTAT.length))]; bootStat.textContent = st; bootD.textContent = p >= 100 ? 'ACCESS GRANTED' : st;
    audio.tick(); if (Math.random() < .3) audio.hover(); rotorGoal = (p / 100);
    if (p >= 100) { clearInterval(iv); bootDone = true; audio.power(); audio.swoosh(); audio.setRotor(1); rotorGoal = 1; setTimeout(() => boot.classList.add('done'), 500); controls.autoRotate = true; }
  }, 80);
}
['pointerdown', 'keydown', 'touchstart'].forEach(ev => boot.addEventListener(ev, () => runBoot(true), { once: true }));
setTimeout(() => runBoot(false), 2600);

/* loop ------------------------------------------------------------- */
showModel(0);
const clock = new THREE.Clock();
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05), t = clock.elapsedTime;
  rotorSpin = damp(rotorSpin, rotorGoal, 1.2, dt);
  if (current && current.rotors) {
    const R = current.rotors;
    (R.main || []).forEach(g => g.rotation[R.mainAxis || 'y'] += dt * rotorSpin * 16);
    (R.tail || []).forEach(g => g.rotation[R.tailAxis || 'x'] += dt * rotorSpin * 22);
  }
  rimC.position.x = Math.sin(t * 0.3) * 16; rimC.position.z = Math.cos(t * 0.3) * 13;
  if (tw) { const k = easeIO(clamp((performance.now() - tw.t0) / tw.dur, 0, 1)); controls.target.lerpVectors(tw.fT, tw.tT, k); camera.position.lerpVectors(tw.fP, tw.tP, k); if (k >= 1) tw = null; }
  controls.update(); composer.render();
}
renderer.setAnimationLoop(() => { if (!document.hidden) frame(); });
