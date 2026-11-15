// Rotary-Wing Archive — cinematic multi-helicopter viewer. By Akash M.
// Aircraft are Blender-built GLBs (../blender/*.py) rendered with HDRI image-based lighting, sun shadows,
// GTAO, bloom, depth of field, filmic tone mapping and a film-grade pass. three.js r160 (vendored).

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { AIRCRAFT } from './aircraft.js';

const $ = s => document.querySelector(s);
const rand = (a, b) => a + Math.random() * (b - a);
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const damp = (a, b, l, dt) => a + (b - a) * (1 - Math.exp(-l * dt));
const easeIO = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const MOBILE = matchMedia('(max-width: 720px)').matches;

/* ------------------------------------------------------------------ *
 * Looks: grade / light / mood presets
 * ------------------------------------------------------------------ */
const GRADES = {
  'Soft glow': { tm: 'AgX', exp: 1.0, bloom: [.6, .75, 2.2], con: 1.06, sat: .92, lift: [0, .006, .012], gain: [1, 1, .99], sh: [0, .012, .03], hi: [.03, .018, 0], vig: .42, ca: .55 },
  'Nordic slate': { tm: 'AgX', exp: .95, bloom: [.4, .6, 3], con: 1.14, sat: .58, lift: [.004, .01, .02], gain: [.98, 1, 1.03], sh: [0, .016, .035], hi: [.01, .012, .016], vig: .5, ca: .5 },
  'Bleach bypass': { tm: 'ACES', exp: .85, bloom: [.3, .5, 3.5], con: 1.28, sat: .42, lift: [0, 0, 0], gain: [1.02, 1.01, 1], sh: [0, .008, .016], hi: [.012, .01, .004], vig: .58, ca: .6 },
  'Teal & orange': { tm: 'ACES', exp: .9, bloom: [.45, .65, 2.6], con: 1.14, sat: 1.08, lift: [0, .01, .02], gain: [1.03, 1, .96], sh: [-.02, .028, .06], hi: [.065, .025, -.03], vig: .48, ca: .55 },
  'Noir': { tm: 'ACES', exp: .88, bloom: [.35, .5, 3], con: 1.38, sat: 0, lift: [0, 0, 0], gain: [1, 1, 1], sh: [0, 0, 0], hi: [0, 0, 0], vig: .7, ca: .35 },
  'Natural': { tm: 'AgX', exp: 1.0, bloom: [.25, .5, 4], con: 1.0, sat: 1.0, lift: [0, 0, 0], gain: [1, 1, 1], sh: [0, 0, 0], hi: [0, 0, 0], vig: .25, ca: .2 },
};
const LIGHTS = {
  'Storm front': { file: 'approaching_storm', bg: 1.0, sun: 1.0, flare: .5 },
  'Overcast': { file: 'kloofendal_overcast_puresky', bg: 1.0, sun: .55, flare: 0 },
  'Golden dusk': { file: 'evening_road_01_puresky', bg: 1.0, sun: 1.25, flare: 1 },
  'Night ops': { file: 'dikhololo_night', bg: .65, sun: .6, flare: 0, exp: .85, night: true },
};
const MOODS = {
  'Haze': { fog: .0065, dust: .7, rain: 0, wet: 0, wind: .35, exp: 1, env: 1, fogMul: .95 },
  'Rain': { fog: .009, dust: .15, rain: 1, wet: 1, wind: .6, exp: .62, env: .55, fogMul: .5 },
  'Dust': { fog: .016, dust: 1.6, rain: 0, wet: 0, wind: .8, exp: .95, env: .9, fogMul: .85, tint: [.55, .42, .3] },
  'Clear': { fog: .0022, dust: .45, rain: 0, wet: 0, wind: .2, exp: 1.05, env: 1, fogMul: 1 },
};
const SHOTS = ['Hero', 'Orbit', 'Fly-by', 'Crane', 'Free'];
const look = { grade: 'Soft glow', light: 'Storm front', mood: 'Haze', shot: 'Hero', blur: true, bars: false, fov: 32, grain: .35 };

/* ------------------------------------------------------------------ *
 * Renderer / composer
 * ------------------------------------------------------------------ */
const canvas = $('#scene');
let renderer;
try { renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' }); }
catch (e) { $('#fallback').classList.add('show'); throw e; }
let DPR = Math.min(devicePixelRatio, MOBILE ? 1.25 : 1.5);
renderer.setPixelRatio(DPR);
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x8a96a0, .0065);
const camera = new THREE.PerspectiveCamera(look.fov, innerWidth / innerHeight, 0.1, 2500);
camera.position.set(28, 4, 30);

const rt = new THREE.WebGLRenderTarget(innerWidth * DPR, innerHeight * DPR, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, rt);
composer.addPass(new RenderPass(scene, camera));
// HDR safety: a single NaN/Inf pixel (e.g. a light grazing a surface) would be smeared across the frame by
// GTAO / bokeh / bloom blurs; scrub it and cap extreme highlights before any of them run
composer.addPass(new ShaderPass({
  uniforms: { tDiffuse: { value: null } },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `uniform sampler2D tDiffuse; varying vec2 vUv;
    void main(){ vec4 c = texture2D(tDiffuse, vUv); bvec3 bad = bvec3(isnan(c.r) || isinf(c.r), isnan(c.g) || isinf(c.g), isnan(c.b) || isinf(c.b));
      gl_FragColor = vec4(any(bad) ? vec3(0.) : min(c.rgb, vec3(400.)), 1.); }`,
}));
const gtao = new GTAOPass(scene, camera, innerWidth, innerHeight);
gtao.output = GTAOPass.OUTPUT.Default;
gtao.blendIntensity = .9;
gtao.updateGtaoMaterial({ radius: .9, distanceExponent: 2, thickness: 1.5, scale: 1.1, samples: 16 });
gtao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16 });
composer.addPass(gtao);
const bokeh = new BokehPass(scene, camera, { focus: 30, aperture: .00006, maxblur: .0075 });
composer.addPass(bokeh);
// translucent FX (rotor-blur discs, searchlight beam, rain, dust) must not feed the AO normal buffer or DOF depth
const noFX = new Set();
function withoutFX(run) { const vis = []; for (const o of noFX) { vis.push(o.visible); o.visible = false; } try { run(); } finally { let i = 0; for (const o of noFX) o.visible = vis[i++]; } }
for (const pass of [gtao, bokeh]) { const r = pass.render.bind(pass); pass.render = (...a) => withoutFX(() => r(...a)); }
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth / 2, innerHeight / 2), .5, .7, .8);
composer.addPass(bloom);
composer.addPass(new OutputPass());

const GradeShader = {
  uniforms: {
    tDiffuse: { value: null }, time: { value: 0 }, res: { value: new THREE.Vector2(innerWidth, innerHeight) },
    con: { value: 1 }, sat: { value: 1 }, lift: { value: new THREE.Vector3() }, gain: { value: new THREE.Vector3(1, 1, 1) },
    sh: { value: new THREE.Vector3() }, hi: { value: new THREE.Vector3() }, vig: { value: .4 }, ca: { value: .5 },
    grain: { value: .35 }, bars: { value: 0 }, flash: { value: 0 }, sunUv: { value: new THREE.Vector2(-9, -9) }, sunOn: { value: 0 },
  },
  vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float time, con, sat, vig, ca, grain, bars, flash, sunOn; uniform vec2 res, sunUv;
    uniform vec3 lift, gain, sh, hi; varying vec2 vUv;
    float hash(vec2 p){ p = fract(p * vec2(443.897, 441.423)); p += dot(p, p.yx + 19.19); return fract((p.x + p.y) * p.x); }
    void main(){
      vec2 d = vUv - .5; float r2 = dot(d, d);
      vec2 off = d * r2 * ca * .045;
      vec3 c = vec3(texture2D(tDiffuse, vUv + off).r, texture2D(tDiffuse, vUv).g, texture2D(tDiffuse, vUv - off).b);
      c = clamp(c * gain + lift * (1. - c), 0., 1.);
      c = clamp((c - .5) * con + .5, 0., 1.);
      float l = dot(c, vec3(.2126, .7152, .0722));
      c = mix(vec3(l), c, sat);
      c += sh * (1. - smoothstep(0., .55, l)) + hi * smoothstep(.45, 1., l);
      c += flash * vec3(.75, .82, 1.) * (1. - l * .5);
      if (sunOn > 0.) {   // anamorphic flare; visibility = is the sun pixel actually bright (occluded by the aircraft => off)
        float vis = smoothstep(.8, .96, dot(texture2D(tDiffuse, sunUv).rgb, vec3(.3333)));
        vec2 asp = vec2(res.x / res.y, 1.), dv = (vUv - sunUv) * asp, ax = vec2(.5) - sunUv;
        vec3 fl = vec3(.35, .6, 1.) * exp(-abs(dv.y) * 170.) * exp(-abs(dv.x) * 1.4) * .6 + vec3(1., .8, .58) * exp(-length(dv) * 7.) * .3;
        fl += vec3(.25, .55, .45) * smoothstep(.07, .05, length((vUv - sunUv - ax * 1.1) * asp)) * .1;
        fl += vec3(.6, .35, .2) * smoothstep(.12, .0, length((vUv - sunUv - ax * 1.6) * asp)) * .1;
        fl += vec3(.3, .4, .9) * smoothstep(.04, .02, length((vUv - sunUv - ax * .6) * asp)) * .1;
        c += fl * vis * sunOn;
      }
      c *= mix(1., smoothstep(1.05, .22, length(d * vec2(1.15, 1.))), vig);
      float g = hash(vUv * res + fract(time * 13.7) * 91.7) - .5;
      c += g * grain * .16 * (1. - l * .6);
      float bh = bars * (.5 - .5 * (res.x / res.y) / 2.39);
      if (abs(d.y) > .5 - bh) c = vec3(0.);
      gl_FragColor = vec4(c, 1.);
    }`,
};
const grade = new ShaderPass(GradeShader);
composer.addPass(grade);

/* ------------------------------------------------------------------ *
 * Lighting, sky and ground
 * ------------------------------------------------------------------ */
const pmrem = new THREE.PMREMGenerator(renderer);
const sun = new THREE.DirectionalLight(0xffffff, 2);
sun.castShadow = true;
sun.shadow.mapSize.set(MOBILE ? 2048 : 4096, MOBILE ? 2048 : 4096);
sun.shadow.bias = -.00015; sun.shadow.normalBias = .03; sun.shadow.radius = 3;
scene.add(sun, sun.target);
const flashLight = new THREE.HemisphereLight(0xdde8ff, 0x223040, 0); scene.add(flashLight);

const envCache = {};
let horizon = new THREE.Color(0x8a96a0);
function analyseHDR(tex) {
  // brightest region = sun direction; mean horizon band = fog colour
  const { data, width: W, height: H } = tex.image, half = data instanceof Uint16Array;
  const f = half ? THREE.DataUtils.fromHalfFloat : v => v;
  let best = -1, bi = 0, bj = 0, sumL = 0, n = 0;
  const hz = [0, 0, 0]; let hn = 0;
  for (let j = 0; j < H; j += 2) for (let i = 0; i < W; i += 2) {
    const k = (j * W + i) * 4, r = f(data[k]), g = f(data[k + 1]), b = f(data[k + 2]);
    const L = .2126 * r + .7152 * g + .0722 * b;
    const v = 1 - (j + .5) / H;
    if (v > .5 && L > best) { best = L; bi = i; bj = j; }
    if (v > .5) { sumL += L; n++; }
    if (v > .495 && v < .53) { hz[0] += r; hz[1] += g; hz[2] += b; hn++; }
  }
  const u = (bi + .5) / W, v = 1 - (bj + .5) / H;
  const phi = (u - .5) * Math.PI * 2, lat = (v - .5) * Math.PI;
  const dir = new THREE.Vector3(Math.cos(phi) * Math.cos(lat), Math.sin(lat), Math.sin(phi) * Math.cos(lat));
  const k = (bj * W + bi) * 4;
  const sc = new THREE.Color(f(data[k]), f(data[k + 1]), f(data[k + 2]));
  const ratio = best / Math.max(1e-4, sumL / n);
  return { dir, sunColor: sc.multiplyScalar(1 / Math.max(sc.r, sc.g, sc.b, 1e-4)), strength: clamp((ratio - 1.5) / 25, .12, 1), horizon: new THREE.Color(hz[0] / hn, hz[1] / hn, hz[2] / hn) };
}
function loadEnv(name, onProgress) {
  const L = LIGHTS[name];
  if (envCache[name]) return Promise.resolve(envCache[name]);
  return new Promise((res, rej) => new RGBELoader().load(`./assets/env/${L.file}.hdr`, tex => {
    tex.mapping = THREE.EquirectangularReflectionMapping;
    const a = analyseHDR(tex);
    envCache[name] = { tex, pm: pmrem.fromEquirectangular(tex).texture, ...a };
    res(envCache[name]);
  }, onProgress, rej));
}
let envState = null;
function applyLight(name) {
  const L = LIGHTS[name], e = envCache[name];
  if (!e) return;
  envState = e;
  scene.background = e.tex; scene.backgroundIntensity = L.bg; scene.backgroundBlurriness = 0;
  scene.environment = e.pm;
  horizon.copy(e.horizon);
  sun.color.copy(L.night ? new THREE.Color(.55, .66, 1) : e.sunColor);
  sun.userData.base = L.night ? .5 : 3.2 * L.sun * e.strength;
  const d = L.night ? new THREE.Vector3(-.45, .62, .5).normalize() : e.dir.clone(); if (d.y < .12) { d.y = .12; d.normalize(); }
  sun.userData.dir = d;
  applyMood();
}

// ground: tiled CC0 concrete with macro variation, wet puddles and a painted helipad
const texL = new THREE.TextureLoader();
const tile = (url, srgb) => { const t = texL.load(url); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = renderer.capabilities.getMaxAnisotropy(); if (srgb) t.colorSpace = THREE.SRGBColorSpace; return t; };
const gTex = { map: tile('./assets/tex/concrete_diffuse.jpg', true), nor: tile('./assets/tex/concrete_nor_gl.jpg'), arm: tile('./assets/tex/concrete_arm.jpg') };
const groundMat = new THREE.MeshStandardMaterial({ map: gTex.map, normalMap: gTex.nor, roughnessMap: gTex.arm, aoMap: gTex.arm, metalness: 0, roughness: 1, normalScale: new THREE.Vector2(.9, .9), envMapIntensity: .8 });
const groundU = { uWet: { value: 0 } };
groundMat.onBeforeCompile = sh => {
  sh.uniforms.uWet = groundU.uWet;
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWP;').replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWP = (modelMatrix * vec4(transformed, 1.0)).xyz;');
  sh.fragmentShader = sh.fragmentShader
    .replace('#include <common>', `#include <common>
      varying vec3 vWP; uniform float uWet;
      float gh(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float gn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f); return mix(mix(gh(i), gh(i + vec2(1, 0)), f.x), mix(gh(i + vec2(0, 1)), gh(i + vec2(1, 1)), f.x), f.y); }
      float fbm(vec2 p){ float s = 0., a = .5; for (int i = 0; i < 4; i++) { s += a * gn(p); p *= 2.03; a *= .5; } return s; }`)
    .replace('#include <map_fragment>', `#include <map_fragment>
      float macro = fbm(vWP.xz * .045);
      diffuseColor.rgb *= mix(.72, 1.12, macro) * mix(.92, 1.04, fbm(vWP.xz * .4));
      float puddle = smoothstep(.56, .64, fbm(vWP.xz * .09 + 7.3));`)
    .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
      roughnessFactor = mix(roughnessFactor, mix(.55, .12, puddle), uWet * mix(.55, 1., puddle));
      diffuseColor.rgb *= 1. - .5 * uWet * puddle;`);
};
const GROUND = 1600;
const groundGeo = new THREE.PlaneGeometry(GROUND, GROUND, 1, 1);
groundGeo.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0, GROUND / 5, GROUND / 5, GROUND / 5, 0, 0, GROUND / 5, 0]), 2));
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);

function padTexture() {
  const s = 2048, c = document.createElement('canvas'); c.width = c.height = s;
  const x = c.getContext('2d'), m = s / 2;
  x.clearRect(0, 0, s, s);
  x.strokeStyle = 'rgba(232,228,214,.92)'; x.fillStyle = 'rgba(232,228,214,.92)';
  x.lineWidth = s * .018; x.beginPath(); x.arc(m, m, s * .47, 0, Math.PI * 2); x.stroke();
  x.setLineDash([s * .045, s * .03]); x.lineWidth = s * .008; x.beginPath(); x.arc(m, m, s * .43, 0, Math.PI * 2); x.stroke(); x.setLineDash([]);
  const hw = s * .05, hh = s * .26, hs = s * .11;
  x.fillRect(m - hs - hw, m - hh, hw * 2 - hw * .0, hh * 2); x.fillRect(m + hs - hw, m - hh, hw * 2, hh * 2); x.fillRect(m - hs, m - hw * .7, hs * 2, hw * 1.4);
  x.fillStyle = 'rgba(255,196,64,.9)'; x.font = `bold ${s * .045}px monospace`; x.textAlign = 'center'; x.fillText('MAX 22.7 t', m, m + s * .36);
  // wear: organic value-noise erosion of the paint, plus faint tyre scuffs
  const img = x.getImageData(0, 0, s, s), px = img.data;
  const mk = n => { const g = new Float32Array((n + 2) * (n + 2)); for (let i = 0; i < g.length; i++) g[i] = Math.random(); return g; };
  const G1 = 48, G2 = 420, g1 = mk(G1), g2 = mk(G2);
  const vn = (g, n, u, v) => { const x0 = u | 0, y0 = v | 0, fx = u - x0, fy = v - y0, sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy), i = y0 * (n + 2) + x0, a = g[i], b = g[i + 1], c = g[i + n + 2], e = g[i + n + 3]; return a + (b - a) * sx + (c - a) * sy + (a - b - c + e) * sx * sy; };
  for (let j = 0; j < s; j++) for (let i = 0; i < s; i++) {
    const k = (j * s + i) * 4; if (!px[k + 3]) continue;
    const n = vn(g1, G1, i / s * G1, j / s * G1) * .62 + vn(g2, G2, i / s * G2, j / s * G2) * .38;
    px[k + 3] *= clamp((n - .3) / .2, 0, 1);
  }
  x.putImageData(img, 0, 0);
  x.globalCompositeOperation = 'destination-out';
  x.globalAlpha = .14; for (let i = 0; i < 40; i++) { x.save(); x.translate(Math.random() * s, Math.random() * s); x.rotate(Math.random() * 3); x.fillRect(0, 0, s * rand(.1, .3), s * rand(.01, .03)); x.restore(); }
  x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return t;
}
const pad = new THREE.Mesh(new THREE.CircleGeometry(19, 96), new THREE.MeshStandardMaterial({ map: padTexture(), transparent: true, roughness: .78, metalness: 0, polygonOffset: true, polygonOffsetFactor: -2, depthWrite: false }));
pad.rotation.x = -Math.PI / 2; pad.position.y = .005; pad.receiveShadow = true; scene.add(pad);
// edge lights
const edgeMat = new THREE.MeshStandardMaterial({ color: 0x111111, emissive: 0xffb347, emissiveIntensity: 6 });
const edgeGeo = new THREE.CylinderGeometry(.09, .12, .1, 12);
for (let i = 0; i < 20; i++) { const a = i / 20 * Math.PI * 2, m = new THREE.Mesh(edgeGeo, edgeMat); m.position.set(Math.cos(a) * 19.6, .05, Math.sin(a) * 19.6); scene.add(m); }

/* ------------------------------------------------------------------ *
 * Atmosphere: rotor-wash dust, rain, lightning
 * ------------------------------------------------------------------ */
function softSprite() {
  const c = document.createElement('canvas'); c.width = c.height = 64; const x = c.getContext('2d');
  const g = x.createRadialGradient(32, 32, 0, 32, 32, 32); g.addColorStop(0, 'rgba(255,255,255,.9)'); g.addColorStop(.4, 'rgba(255,255,255,.35)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c);
}
const DUST_N = MOBILE ? 700 : 1600;
const dustGeo = new THREE.BufferGeometry();
const dustPos = new Float32Array(DUST_N * 3), dust = [];
for (let i = 0; i < DUST_N; i++) dust.push({ a: rand(0, 7), r: rand(2, 20), y: rand(0, 2), life: rand(0, 1), sp: rand(.6, 1.4) });
dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
const dustMat = new THREE.PointsMaterial({ map: softSprite(), size: 2.2, sizeAttenuation: true, transparent: true, depthWrite: false, opacity: 0, color: 0x9a8f80, fog: true });
const dustPts = new THREE.Points(dustGeo, dustMat); dustPts.frustumCulled = false; scene.add(dustPts); noFX.add(dustPts);

const RAIN_N = MOBILE ? 1800 : 4500;
const rainGeo = new THREE.BufferGeometry(), rainPos = new Float32Array(RAIN_N * 6);
const rainD = []; for (let i = 0; i < RAIN_N; i++) rainD.push([rand(-18, 18), rand(0, 22), rand(-18, 18), rand(.8, 1.2)]);
rainGeo.setAttribute('position', new THREE.BufferAttribute(rainPos, 3));
const rainMat = new THREE.LineBasicMaterial({ color: 0xa9b8c6, transparent: true, opacity: 0, depthWrite: false, fog: false });
const rain = new THREE.LineSegments(rainGeo, rainMat); rain.frustumCulled = false; scene.add(rain); noFX.add(rain);
let nextBolt = 6, boltT = -1;

/* ------------------------------------------------------------------ *
 * Audio — cinematic procedural rotor + UI sound design
 * ------------------------------------------------------------------ */
class Audio {
  constructor() { this.ready = false; this.on = false; }
  init() {
    if (this.ready) return; try {
      const AC = window.AudioContext || window.webkitAudioContext; const ctx = this.ctx = new AC();
      const master = this.master = ctx.createGain(); master.gain.value = 0;
      const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -16; comp.ratio.value = 4;
      master.connect(comp); comp.connect(ctx.destination);
      const verb = this.verb = ctx.createConvolver(); verb.buffer = this._imp(3.2, 2.6); const vg = ctx.createGain(); vg.gain.value = .45; verb.connect(vg); vg.connect(master);
      // rotor bus: distance low-pass + level
      const bus = this.bus = ctx.createGain(); bus.gain.value = 0;
      const dlp = this.dlp = ctx.createBiquadFilter(); dlp.type = 'lowpass'; dlp.frequency.value = 3000;
      bus.connect(dlp); dlp.connect(master); dlp.connect(verb);
      const noise = this._noise(4), brown = this._brown(4);
      // blade slap: band-passed noise gated at blade-pass frequency
      const slapSrc = this._loop(noise), slapBp = ctx.createBiquadFilter(); slapBp.type = 'bandpass'; slapBp.frequency.value = 520; slapBp.Q.value = .7;
      const slapG = ctx.createGain(); slapG.gain.value = 0; slapSrc.connect(slapBp); slapBp.connect(slapG); slapG.connect(bus);
      const lfo = this.lfo = ctx.createOscillator(); lfo.type = 'sawtooth'; lfo.frequency.value = 17;
      const lfoG = ctx.createGain(); lfoG.gain.value = .5; lfo.connect(lfoG); lfoG.connect(slapG.gain);
      const slapBase = ctx.createConstantSource(); slapBase.offset.value = .5; slapBase.connect(slapG.gain);
      // low thump: blade-pass harmonics
      const th = this.thump = ctx.createOscillator(); th.type = 'sawtooth'; th.frequency.value = 17;
      const thLp = ctx.createBiquadFilter(); thLp.type = 'lowpass'; thLp.frequency.value = 140; const thG = ctx.createGain(); thG.gain.value = .55;
      th.connect(thLp); thLp.connect(thG); thG.connect(bus);
      // rumble bed + turbine whine + hiss
      const rum = this._loop(brown), rumLp = ctx.createBiquadFilter(); rumLp.type = 'lowpass'; rumLp.frequency.value = 220; const rumG = ctx.createGain(); rumG.gain.value = .9;
      rum.connect(rumLp); rumLp.connect(rumG); rumG.connect(bus);
      const w1 = this.w1 = ctx.createOscillator(); w1.type = 'sine'; w1.frequency.value = 5200; const w2 = this.w2 = ctx.createOscillator(); w2.type = 'triangle'; w2.frequency.value = 2610;
      const wG = this.wG = ctx.createGain(); wG.gain.value = 0; w1.connect(wG); w2.connect(wG); wG.connect(bus);
      const hs = this._loop(noise), hsBp = ctx.createBiquadFilter(); hsBp.type = 'bandpass'; hsBp.frequency.value = 4200; hsBp.Q.value = .9; const hsG = ctx.createGain(); hsG.gain.value = .05;
      hs.connect(hsBp); hsBp.connect(hsG); hsG.connect(bus);
      // ambience: wind + rain
      const wind = this._loop(brown), wLp = this.windLp = ctx.createBiquadFilter(); wLp.type = 'lowpass'; wLp.frequency.value = 380; const windG = this.windG = ctx.createGain(); windG.gain.value = 0;
      wind.connect(wLp); wLp.connect(windG); windG.connect(master);
      const rn = this._loop(noise), rHp = ctx.createBiquadFilter(); rHp.type = 'highpass'; rHp.frequency.value = 1800; const rG = this.rainG = ctx.createGain(); rG.gain.value = 0;
      rn.connect(rHp); rHp.connect(rG); rG.connect(master);
      [lfo, th, w1, w2, slapBase].forEach(o => o.start());
      this.pent = [392, 523.25, 659.25, 783.99, 1046.5]; this.ready = true;
    } catch (e) { this.ready = false; }
  }
  _noise(s) { const n = this.ctx.sampleRate * s, b = this.ctx.createBuffer(1, n, this.ctx.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; return b; }
  _brown(s) { const n = this.ctx.sampleRate * s, b = this.ctx.createBuffer(1, n, this.ctx.sampleRate), d = b.getChannelData(0); let l = 0; for (let i = 0; i < n; i++) { l = (l + .02 * (Math.random() * 2 - 1)) / 1.02; d[i] = l * 3.5; } return b; }
  _loop(buf) { const s = this.ctx.createBufferSource(); s.buffer = buf; s.loop = true; s.start(0, Math.random() * buf.duration); return s; }
  _imp(s, dc) { const n = this.ctx.sampleRate * s, b = this.ctx.createBuffer(2, n, this.ctx.sampleRate); for (let c = 0; c < 2; c++) { const a = b.getChannelData(c); for (let i = 0; i < n; i++) a[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, dc); } return b; }
  enable() { this.init(); if (!this.ready) return false; this.ctx.resume(); this.on = true; this.master.gain.setTargetAtTime(.9, this.ctx.currentTime, .4); return true; }
  disable() { this.on = false; if (this.ready) this.master.gain.setTargetAtTime(0, this.ctx.currentTime, .3); }
  rotor(level, bladeHz, dist) {
    if (!this.ready) return; const t = this.ctx.currentTime;
    const near = clamp(1.25 - dist / 90, .25, 1.15);
    this.bus.gain.setTargetAtTime(.22 * level * near, t, .25);
    this.lfo.frequency.setTargetAtTime(Math.max(1, bladeHz * level), t, .4);
    this.thump.frequency.setTargetAtTime(Math.max(1, bladeHz * level), t, .4);
    this.dlp.frequency.setTargetAtTime(600 + 4200 * near, t, .3);
    this.wG.gain.setTargetAtTime(.012 * level * near, t, .5);
    this.w1.frequency.setTargetAtTime(3000 + 2600 * level, t, .8); this.w2.frequency.setTargetAtTime(1500 + 1300 * level, t, .8);
  }
  ambience(wind, rain) { if (!this.ready) return; const t = this.ctx.currentTime; this.windG.gain.setTargetAtTime(.16 * wind, t, .8); this.rainG.gain.setTargetAtTime(.05 * rain, t, .8); }
  thunder(delay) {
    if (!this.on) return; const t = this.ctx.currentTime + delay, s = this.ctx.createBufferSource(); s.buffer = this._brown(5);
    const lp = this.ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.setValueAtTime(900, t); lp.frequency.exponentialRampToValueAtTime(90, t + 4);
    const g = this.ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.9, t + .08); g.gain.exponentialRampToValueAtTime(.001, t + 4.6);
    s.connect(lp); lp.connect(g); g.connect(this.master); g.connect(this.verb); s.start(t); s.stop(t + 5);
  }
  _tone(f, dur, g, type) { if (!this.on) return; const t = this.ctx.currentTime, o = this.ctx.createOscillator(), gn = this.ctx.createGain(), pan = this.ctx.createStereoPanner(); o.type = type || 'sine'; o.frequency.value = f; pan.pan.value = rand(-.4, .4); gn.gain.setValueAtTime(0, t); gn.gain.linearRampToValueAtTime(g, t + .006); gn.gain.exponentialRampToValueAtTime(.0004, t + dur); o.connect(gn); gn.connect(pan); pan.connect(this.master); pan.connect(this.verb); o.start(t); o.stop(t + dur + .03); }
  swoosh() { if (!this.on) return; const t = this.ctx.currentTime; const s = this.ctx.createBufferSource(); s.buffer = this._noise(.8); const bp = this.ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = 1.1; bp.frequency.setValueAtTime(260, t); bp.frequency.exponentialRampToValueAtTime(3400, t + .24); bp.frequency.exponentialRampToValueAtTime(340, t + .7); const g = this.ctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.2, t + .08); g.gain.exponentialRampToValueAtTime(.001, t + .72); s.connect(bp); bp.connect(g); g.connect(this.master); g.connect(this.verb); s.start(); const o = this.ctx.createOscillator(), og = this.ctx.createGain(); o.type = 'sine'; o.frequency.setValueAtTime(120, t); o.frequency.exponentialRampToValueAtTime(38, t + .55); og.gain.setValueAtTime(.14, t); og.gain.exponentialRampToValueAtTime(.001, t + .6); o.connect(og); og.connect(this.master); o.start(t); o.stop(t + .65); }
  click() { if (!this.on) return; const t = this.ctx.currentTime; const s = this.ctx.createBufferSource(); s.buffer = this._noise(.12); const hp = this.ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 900; const g = this.ctx.createGain(); g.gain.setValueAtTime(.12, t); g.gain.exponentialRampToValueAtTime(.001, t + .09); s.connect(hp); hp.connect(g); g.connect(this.master); s.start(); this._tone(180, .14, .1, 'square'); this._tone(880, .5, .05, 'triangle'); }
  hover() { this._tone(this.pent[(Math.random() * this.pent.length) | 0] * 2, .5, .03, 'triangle'); }
  tick() { this._tone(1400 + Math.random() * 1600, .03, .02, 'square'); }
  digital() { if (!this.on) return; [0, 1, 2, 3].forEach(i => setTimeout(() => this._tone(this.pent[i], .25, .05, 'triangle'), i * 55)); }
  power() { if (!this.on) return; [392, 523, 659, 880].forEach((f, i) => setTimeout(() => this._tone(f, .6, .07, 'sawtooth'), i * 90)); }
}
const audio = new Audio();

/* ------------------------------------------------------------------ *
 * Aircraft loading (GLB + Draco) and preparation
 * ------------------------------------------------------------------ */
const draco = new DRACOLoader().setDecoderPath('./vendor/jsm/libs/draco/gltf/');
const gltfLoader = new GLTFLoader().setDRACOLoader(draco);
const holder = new THREE.Group(); scene.add(holder);
const BLADES = { blackhawk: 4 * 4.3, apache: 4 * 4.8, chinook: 3 * 3.75 * 2, hind: 5 * 3.9 };

function searchBeam(a, b) {
  const L = a.distanceTo(b) * 1.08, r = Math.tan(.3) * L;
  const geo = new THREE.CylinderGeometry(.12, r, L, 48, 1, true); geo.translate(0, -L / 2, 0);
  const mat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: { uI: { value: 0 } },
    vertexShader: `varying float vT, vD; varying vec3 vN, vV;
      void main(){ vT = -position.y / ${L.toFixed(3)}; vec4 mv = modelViewMatrix * vec4(position, 1.); vD = -mv.z; vV = normalize(-mv.xyz); vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * mv; }`,
    // soft edges, fades along the beam, and fades out near the lens so the camera never sits inside a white wall
    fragmentShader: `uniform float uI; varying float vT, vD; varying vec3 vN, vV;
      void main(){ float a = uI * pow(abs(dot(vN, vV)), 3.) * pow(1. - vT, 1.8) * smoothstep(0., .06, vT) * smoothstep(3., 14., vD); gl_FragColor = vec4(vec3(.75, .82, 1.) * a, a); }`,
  });
  const m = new THREE.Mesh(geo, mat);
  m.position.copy(a); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), b.clone().sub(a).normalize());
  m.renderOrder = 5; return m;
}

function blurDisc(r0, R) {
  const geo = new THREE.RingGeometry(r0, R, 128, 1); geo.rotateX(-Math.PI / 2);
  const mat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide, fog: true,
    uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, { uO: { value: 0 }, uN: { value: 4 }, uPh: { value: 0 }, uR: { value: new THREE.Vector2(r0, R) } }]),
    vertexShader: `varying vec3 vP;
      #include <fog_pars_vertex>
      void main(){
        vP = position; vec4 mvPosition = modelViewMatrix * vec4(position, 1.); gl_Position = projectionMatrix * mvPosition;
        #include <fog_vertex>
      }`,
    fragmentShader: `uniform float uO, uN, uPh; uniform vec2 uR; varying vec3 vP;
      #include <fog_pars_fragment>
      void main(){
        float r = length(vP.xz), k = (r - uR.x) / (uR.y - uR.x), th = atan(vP.z, vP.x);
        float ghost = pow(.5 + .5 * cos(uN * th - uPh), 18.);
        float a = uO * (.16 + .28 * ghost) * smoothstep(0., .08, k) * (1. - smoothstep(.94, 1., k)) * (.65 + .35 * k);
        float tip = smoothstep(.96, .99, k) * (1. - smoothstep(.99, 1., k));
        gl_FragColor = vec4(mix(vec3(.035), vec3(.22), tip), a + tip * uO * .25);
        #include <fog_fragment>
      }`,
  });
  return new THREE.Mesh(geo, mat);
}

const ASSET_V = '2';
function spinnerOf(o) { for (let p = o; p; p = p.parent) if (/^spin_/.test(p.name)) return p.name; return null; }
function prepare(def, gltf) {
  const root = gltf.scene;
  const parts = {}, pickables = [], spinners = [], beacons = [], matCache = new Map();
  root.traverse(o => { if (o.name.startsWith('part_')) parts[o.name.slice(5)] = o; });
  for (const [key, node] of Object.entries(parts)) {
    node.traverse(m => {
      if (!m.isMesh) return;
      m.castShadow = true; m.receiveShadow = true; m.userData.part = key;
      const spin = spinnerOf(m), id = key + '|' + (spin || '') + '|' + m.material.uuid;
      if (!matCache.has(id)) {
        const c = m.material.clone(); c.userData.part = key; c.userData.name = m.material.name; c.userData.spin = spin;
        if (c.transmission > 0) { c.transmission = 0; c.transparent = true; c.opacity = .42; c.roughness = .04; c.metalness = .1; c.envMapIntensity = 1.6; c.color.multiplyScalar(.35); }
        if (spin) c.transparent = true;   // blades fade into the motion-blur disc
        c.depthWrite = !(c.transparent && c.opacity < 1);
        c.userData.baseOpacity = c.opacity; c.userData.baseTransparent = c.transparent; c.userData.baseRough = c.roughness; c.userData.baseEnv = c.envMapIntensity;
        matCache.set(id, c);
      }
      m.material = matCache.get(id);
      if (/^emit_/.test(m.material.userData.name)) { m.castShadow = false; if (m.material.userData.name === 'emit_beacon') beacons.push(m); }
      pickables.push(m);
    });
  }
  root.updateWorldMatrix(true, true);
  root.traverse(o => {
    if (!/^spin_/.test(o.name)) return;
    let R = 0; const inv = o.matrixWorld.clone().invert(), v = new THREE.Vector3();
    o.traverse(m => { if (!m.isMesh) return; const p = m.geometry.attributes.position; for (let i = 0; i < p.count; i += 5) { v.fromBufferAttribute(p, i).applyMatrix4(m.matrixWorld).applyMatrix4(inv); R = Math.max(R, Math.hypot(v.x, v.z)); } });
    const blades = o.children.filter(c => /blade/i.test(c.name)).length || 4;
    const disc = blurDisc(R * .12, R * 1.005); disc.material.uniforms.uN.value = blades;
    disc.position.copy(o.position); disc.quaternion.copy(o.quaternion); o.parent.add(disc); noFX.add(disc);
    spinners.push({ node: o, name: o.name, dir: (o.userData.spin_dir || 1), tail: /tail/.test(o.name), disc, R, angle: 0, blur: 0 });
  });
  const lights = beacons.slice(0, 2).map(b => { const l = new THREE.PointLight(0xff2a1a, 0, 9, 2); b.getWorldPosition(l.position); root.worldToLocal(l.position); root.add(l); return l; });
  // nose searchlight (Night ops): placed in open air ahead of / below the nose so no surface sits in its 1/d² hot spot
  const fb = new THREE.Box3(); pickables.forEach(m => { if (!spinnerOf(m)) fb.expandByObject(m); });
  const sp = new THREE.Vector3(fb.max.x + .35, fb.min.y + (fb.max.y - fb.min.y) * .18, 0), st = new THREE.Vector3(sp.x + 10, 0, 0);
  const spot = new THREE.SpotLight(0xe4ecff, 0, 80, .3, .5, 2); spot.position.copy(sp); spot.target.position.copy(st);
  spot.castShadow = true; spot.shadow.mapSize.set(1024, 1024); spot.shadow.bias = -.0005; root.add(spot, spot.target);
  const beam = searchBeam(sp, st); beam.visible = false; root.add(beam); noFX.add(beam);
  // bounds from the aircraft meshes only (not the beam / blur discs / lights)
  const meshBox = () => { const b = new THREE.Box3(); pickables.forEach(m => b.expandByObject(m)); return b; };
  root.updateWorldMatrix(true, true);
  const box = meshBox(), ctr = box.getCenter(new THREE.Vector3());
  root.position.x -= ctr.x; root.position.z -= ctr.z; root.position.y -= box.min.y;
  const g = new THREE.Group(); g.add(root); g.rotation.y = -0.35;
  g.updateWorldMatrix(true, true);
  const wb = meshBox();
  return { def, group: g, parts, pickables, spinners, beacons, lights, spot, beam, box: wb, size: wb.getSize(new THREE.Vector3()), center: wb.getCenter(new THREE.Vector3()), mats: [...matCache.values()] };
}

const cache = {};
function loadAircraft(def, onProgress) {
  if (cache[def.id]) return Promise.resolve(cache[def.id]);
  return new Promise((res, rej) => gltfLoader.load(def.file + '?v=' + ASSET_V, g => { cache[def.id] = prepare(def, g); res(cache[def.id]); }, onProgress, rej));
}

/* ------------------------------------------------------------------ *
 * State, controls, camera shots
 * ------------------------------------------------------------------ */
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = .07;
controls.minDistance = 5; controls.maxDistance = 120;
controls.maxPolarAngle = Math.PI * .495; controls.minPolarAngle = .08;
let userDriving = false;
controls.addEventListener('start', () => { canvas.classList.add('grab'); userDriving = true; firstGesture(); if (look.shot !== 'Free') setShot('Free', true); });
controls.addEventListener('end', () => { canvas.classList.remove('grab'); userDriving = false; });

let active = -1, current = null, rotorSpin = 0, rotorGoal = 0, frozen = false, shotT = 0, tw = null, panelOpen = !MOBILE, viewOff = 0;

function frameDist(c) { const r = c.size.length() * .5; return r / Math.sin(THREE.MathUtils.degToRad(camera.fov) / 2) * .64; }
function shotPose(name, t, c, out) {
  const ctr = c.center, r = c.size.length() * .5, d = frameDist(c);
  const tgt = out.t.set(ctr.x, c.size.y * .38, ctr.z);
  switch (name) {
    case 'Hero': { const a = .55 + Math.sin(t * .05) * .5; const dd = d * (1.02 - .12 * Math.sin(t * .07)); out.p.set(ctr.x + Math.cos(a) * dd, 1.25 + .3 * Math.sin(t * .11), ctr.z + Math.sin(a) * dd); tgt.y = c.size.y * .45; break; }
    case 'Orbit': { const a = t * .1; out.p.set(ctr.x + Math.cos(a) * d, r * .32, ctr.z + Math.sin(a) * d); break; }
    case 'Fly-by': { const L = r * 2.4, u = ((t * .055) % 2), x = u < 1 ? u : 2 - u; const s = easeIO(x) * 2 - 1; out.p.set(ctr.x + s * L, 1.6, ctr.z + d * .48); tgt.x = ctr.x + s * L * .25; break; }
    case 'Crane': { const a = t * .06 + 1; out.p.set(ctr.x + Math.cos(a) * d * .6, d * .62, ctr.z + Math.sin(a) * d * .6); tgt.y = 0; break; }
  }
  return out;
}
const pose = { p: new THREE.Vector3(), t: new THREE.Vector3() };
function setShot(name, quiet) {
  look.shot = name; shotT = 0; syncCine();
  controls.autoRotate = false;
  if (!quiet && current && name !== 'Free') { shotPose(name, 0, current, pose); tweenTo(pose.t, pose.p, 1600); }
}
function tweenTo(toT, toP, dur) { tw = { t0: performance.now(), dur, fT: controls.target.clone(), tT: toT.clone(), fP: camera.position.clone(), tP: toP.clone() }; }

/* ------------------------------------------------------------------ *
 * Model switching + loader overlay
 * ------------------------------------------------------------------ */
const loader = $('#loader'), loadPct = $('#loadPct'), loadTxt = $('#loadTxt');
let loadToken = 0;
async function showModel(i) {
  if (i === active) return;
  active = i; const def = AIRCRAFT[i], token = ++loadToken;
  [...$('#tabs').children].forEach((b, k) => b.classList.toggle('on', k === i));
  $('#mName').textContent = def.info.name; $('#mVariant').textContent = def.info.variant; $('#partcount').textContent = Object.keys(def.parts).length;
  if (audio.on) audio.swoosh();
  if (!cache[def.id]) { loader.classList.add('show'); loadTxt.textContent = 'LOADING ' + def.tab; loadPct.textContent = '00'; }
  let c;
  try { c = await loadAircraft(def, e => { if (e.total) loadPct.textContent = String(Math.min(99, Math.round(e.loaded / e.total * 100))).padStart(2, '0'); }); }
  catch (e) { console.error('aircraft load failed', def.id, e); loadTxt.textContent = 'AIRFRAME UNAVAILABLE'; return; }
  if (token !== loadToken) return;
  loader.classList.remove('show');
  if (current && current !== c) { holder.remove(current.group); current.mats.forEach(m => ['map', 'normalMap', 'roughnessMap', 'metalnessMap'].forEach(k => m[k] && m[k].dispose())); }
  current = c; holder.add(c.group);
  sun.shadow.camera.left = sun.shadow.camera.bottom = -c.size.length() * .62; sun.shadow.camera.right = sun.shadow.camera.top = c.size.length() * .62;
  sun.shadow.camera.near = 1; sun.shadow.camera.far = 400; sun.shadow.camera.updateProjectionMatrix();
  buildDots(); selected = null; hovered = null; fillDossier(); applyMood();
  // intro: sweep in low from distance, then hand to the active shot
  const sp = look.shot === 'Free' ? 'Hero' : look.shot; shotT = 0; shotPose(sp, 0, c, pose);
  camera.position.copy(pose.p).sub(c.center).multiplyScalar(1.9).add(c.center); camera.position.y = Math.max(1.2, pose.p.y * .8);
  controls.target.copy(pose.t);
  if (look.shot === 'Free') setShot('Hero', true);
  tweenTo(pose.t, pose.p, 2600);
}
const tabsEl = $('#tabs');
AIRCRAFT.forEach((m, i) => { const b = document.createElement('button'); b.className = 'tab mono'; b.textContent = m.tab; b.onclick = () => { firstGesture(); audio.click(); showModel(i); }; tabsEl.appendChild(b); });

/* ------------------------------------------------------------------ *
 * Interaction + dossier panel
 * ------------------------------------------------------------------ */
const raycaster = new THREE.Raycaster(); const ndc = new THREE.Vector2();
let hovered = null, selected = null, _downX = 0, _downY = 0;
const tag = $('#tag');
const HL = new THREE.Color('#1f8aa0');
addEventListener('pointermove', e => {
  ndc.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  tag.style.left = e.clientX + 'px'; tag.style.top = e.clientY + 'px';
  if (!current || e.target !== canvas) { tag.classList.remove('show'); return; }
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObjects(current.pickables, false).find(h => !h.object.material.userData.faded);
  const key = hit ? hit.object.userData.part : null;
  canvas.classList.toggle('aim', !!key);
  if (key) { tag.textContent = current.def.parts[key].name; tag.classList.add('show'); } else tag.classList.remove('show');
  if (key !== hovered) { hovered = key; if (key) audio.hover(); }
}, { passive: true });
canvas.addEventListener('pointerdown', e => { _downX = e.clientX; _downY = e.clientY; });
canvas.addEventListener('pointerup', e => {
  firstGesture();
  if (Math.abs(e.clientX - _downX) + Math.abs(e.clientY - _downY) > 6 || !current) return;
  raycaster.setFromCamera(ndc, camera);
  const hit = raycaster.intersectObjects(current.pickables, false).find(h => !h.object.material.userData.faded);
  if (hit) select(hit.object.userData.part); else if (selected) select(null);
});
addEventListener('keydown', e => {
  if (e.key === 'Escape') select(null);
  if (e.key === 'Tab') { e.preventDefault(); showModel((active + (e.shiftKey ? AIRCRAFT.length - 1 : 1)) % AIRCRAFT.length); }
});

const P = { id: $('#pId'), name: $('#pName'), role: $('#pRole'), purpose: $('#pPurpose'), mats: $('#pMats'), specs: $('#pSpecs'), panel: $('#panel'), secMat: $('#secMat'), secSpec: $('#secSpec') };
$('#pX').onclick = () => { audio.click(); if (selected) select(null); else setPanel(false); };
$('#dossier').onclick = () => { audio.click(); setPanel(!panelOpen); };
function setPanel(open) { panelOpen = open; document.body.classList.toggle('panel-off', !open); $('#dossier').classList.toggle('on', open); if (audio.on) audio.swoosh(); }
document.body.classList.toggle('panel-off', !panelOpen); $('#dossier').classList.toggle('on', panelOpen);
const GLY = '!<>-_\\/[]{}=+*^?#01ABCDEFGHJKLMNPQRSTUVWXYZ';
function decodeInto(el, text, dur, snd) { const id = (el.__t = (el.__t || 0) + 1), st = performance.now(); (function s(n) { if (id !== el.__t) return; const t = clamp((n - st) / dur, 0, 1), r = Math.floor(text.length * t); let o = ''; for (let i = 0; i < text.length; i++) o += i < r ? text[i] : (text[i] === ' ' ? ' ' : GLY[(Math.random() * GLY.length) | 0]); el.textContent = o; if (snd && Math.random() < .5) audio.tick(); t < 1 ? requestAnimationFrame(s) : el.textContent = text; })(st); }
function typeInto(el, text, dur, snd) { const id = (el.__t = (el.__t || 0) + 1), st = performance.now(); (function s(n) { if (id !== el.__t) return; const t = clamp((n - st) / dur, 0, 1), c = Math.floor(text.length * t); el.textContent = text.slice(0, c) + (t < 1 ? '▌' : ''); if (snd && c % 2 === 0) audio.tick(); t < 1 ? requestAnimationFrame(s) : el.textContent = text; })(st); }

function fillDossier() {
  const d = AIRCRAFT[active].info;
  P.id.textContent = '// AIRCRAFT DOSSIER'; P.secMat.textContent = 'Origin & Class'; P.secSpec.textContent = 'Specification';
  decodeInto(P.name, d.name, 650, true); P.role.textContent = d.variant.toUpperCase();
  typeInto(P.purpose, d.desc, 1000, true);
  P.mats.innerHTML = [d.origin, d.role, d.year].filter(Boolean).map(m => `<span>${m}</span>`).join('');
  P.specs.innerHTML = d.specs.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
}
function partBox(key) { const b = new THREE.Box3(); current.parts[key].traverse(m => { if (m.isMesh) b.expandByObject(m); }); return b; }
function select(key) {
  if (!current || key === selected) return; selected = key;
  [...$('#dots').children].forEach(d => d.classList.toggle('active', d.dataset.k === key));
  if (key) {
    if (!panelOpen) setPanel(true);
    const d = current.def.parts[key];
    P.id.textContent = '// SUBSYSTEM'; P.secMat.textContent = 'Materials'; P.secSpec.textContent = 'Specification';
    decodeInto(P.name, d.name, 600, true); P.role.textContent = ''; setTimeout(() => decodeInto(P.role, (d.role || '').toUpperCase(), 450, false), 120);
    setTimeout(() => typeInto(P.purpose, d.fn, 900, true), 240);
    P.mats.innerHTML = (d.mats || []).map(m => `<span>${m}</span>`).join('');
    P.specs.innerHTML = (d.specs || []).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
    audio.swoosh(); setTimeout(() => audio.digital(), 120);
    if (!frozen) rotorGoal = .2;
    setShot('Free', true);
    const b = partBox(key), c = b.getCenter(new THREE.Vector3()), s = Math.max(2.5, b.getSize(new THREE.Vector3()).length());
    const dir = camera.position.clone().sub(controls.target).normalize(); if (dir.y < .12) { dir.y = .12; dir.normalize(); }
    const p = c.clone().add(dir.multiplyScalar(s * 1.15 + 3)); p.y = Math.max(p.y, .6);
    tweenTo(c, p, 1150);
    canvas.classList.remove('aim'); tag.classList.remove('show');
  } else {
    fillDossier(); if (!frozen) rotorGoal = 1;
    if (audio.on) audio.swoosh();
    setShot('Hero');
  }
}
function buildDots() {
  const el = $('#dots'); el.innerHTML = '';
  Object.entries(current.def.parts).forEach(([k, p]) => { if (!current.parts[k]) return; const d = document.createElement('div'); d.className = 'dot'; d.dataset.k = k; d.innerHTML = `<span>${p.name}</span>`; d.onclick = () => { audio.click(); select(k); }; el.appendChild(d); });
}

/* ------------------------------------------------------------------ *
 * Cinematic control bar
 * ------------------------------------------------------------------ */
const cycle = (obj, cur) => { const k = Object.keys(obj); return k[(k.indexOf(cur) + 1) % k.length]; };
function syncCine() {
  document.querySelectorAll('#cine [data-k]').forEach(b => {
    const k = b.dataset.k, v = look[k];
    b.querySelector('b').textContent = typeof v === 'boolean' ? (v ? 'On' : 'Off') : v;
  });
}
document.querySelectorAll('#cine [data-k]').forEach(b => b.addEventListener('click', () => {
  firstGesture(); audio.click();
  const k = b.dataset.k;
  if (k === 'grade') { look.grade = cycle(GRADES, look.grade); applyGrade(); }
  else if (k === 'light') { const next = cycle(LIGHTS, look.light); look.light = next; syncCine(); b.classList.add('busy'); loadEnv(next).then(() => { b.classList.remove('busy'); if (look.light === next) applyLight(next); }); }
  else if (k === 'mood') { look.mood = cycle(MOODS, look.mood); applyMood(); }
  else if (k === 'shot') { setShot(SHOTS[(SHOTS.indexOf(look.shot) + 1) % SHOTS.length]); }
  else if (k === 'blur') { look.blur = !look.blur; bokeh.enabled = look.blur; }
  else if (k === 'bars') { look.bars = !look.bars; }
  syncCine();
}));
$('#fov').addEventListener('input', e => { look.fov = +e.target.value; });
$('#grain').addEventListener('input', e => { look.grain = +e.target.value / 100; grade.uniforms.grain.value = look.grain; });

function exposure() { renderer.toneMappingExposure = GRADES[look.grade].exp * MOODS[look.mood].exp * (LIGHTS[look.light].exp || 1); }
function applyGrade() {
  const g = GRADES[look.grade], u = grade.uniforms;
  renderer.toneMapping = g.tm === 'AgX' ? THREE.AgXToneMapping : THREE.ACESFilmicToneMapping;
  exposure();
  [bloom.strength, bloom.radius, bloom.threshold] = g.bloom;
  u.con.value = g.con; u.sat.value = g.sat; u.lift.value.fromArray(g.lift); u.gain.value.fromArray(g.gain);
  u.sh.value.fromArray(g.sh); u.hi.value.fromArray(g.hi); u.vig.value = g.vig; u.ca.value = g.ca;
}
function applyMood() {
  const m = MOODS[look.mood];
  scene.fog.density = m.fog;
  const fc = horizon.clone(); if (m.tint) fc.lerp(new THREE.Color(...m.tint).multiplyScalar(horizon.getHSL({}).l * 2.2), .6);
  scene.fog.color.copy(fc.multiplyScalar(m.fogMul));
  dustMat.color.copy(m.tint ? new THREE.Color(...m.tint) : new THREE.Color(0x9a8f80)).multiplyScalar(.5 + horizon.getHSL({}).l);
  groundU.uWet.value = m.wet; groundMat.envMapIntensity = .8 * m.env;
  exposure();
  if (current) current.mats.forEach(mt => { if (/^emit_/.test(mt.userData.name || '')) return; mt.roughness = mt.userData.baseRough * (m.wet ? .62 : 1); mt.envMapIntensity = mt.userData.baseEnv * m.env; });
  audio.ambience(m.wind, m.rain);
}

/* ------------------------------------------------------------------ *
 * Buttons: sound / freeze / first gesture
 * ------------------------------------------------------------------ */
const sndBtn = $('#sound');
function soundUI(on) { sndBtn.classList.toggle('on', on); sndBtn.textContent = on ? '◼ SOUND ON' : '◼ SOUND OFF'; }
sndBtn.onclick = () => { if (!audio.on) { if (audio.enable()) { soundUI(true); applyMood(); } } else { audio.disable(); soundUI(false); } };
let gestured = false; function firstGesture() { if (gestured) return; gestured = true; if (audio.enable()) { soundUI(true); applyMood(); } }
const frzBtn = $('#freeze');
frzBtn.onclick = () => { frozen = !frozen; audio.click(); frzBtn.classList.toggle('on', frozen); frzBtn.textContent = frozen ? '▶ RESUME' : '⏸ FREEZE'; rotorGoal = frozen ? 0 : (bootDone ? (selected ? .2 : 1) : rotorGoal); };

function resize() {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight); composer.setPixelRatio(DPR); composer.setSize(innerWidth, innerHeight);
  grade.uniforms.res.value.set(innerWidth * DPR, innerHeight * DPR);
}
addEventListener('resize', resize);

/* ------------------------------------------------------------------ *
 * Boot: real asset loading, gesture unlocks audio
 * ------------------------------------------------------------------ */
const boot = $('#boot'), bootFill = $('#bootFill'), bootStat = $('#bootStat'), bootPct = $('#bootPct'), bootD = $('#bootD');
let bootDone = false, clicked = false, envP = 0, acP = 0, ready = false, shown = 0;
function bootProgress() {
  const p = Math.round(envP * 35 + acP * 65); shown = Math.max(shown, p);
  bootFill.style.right = (100 - shown) + '%'; bootPct.textContent = String(shown).padStart(2, '0');
  const st = shown < 35 ? 'CALIBRATING OPTICS' : shown < 90 ? 'LOADING AIRFRAME' : shown < 100 ? 'SPOOLING ENGINES' : 'SYSTEMS ONLINE';
  bootStat.textContent = st; if (!clicked || shown >= 100) bootD.textContent = shown >= 100 ? (clicked ? 'ACCESS GRANTED' : 'READY') : st;
}
function finishBoot() {
  if (bootDone || !ready) return; bootDone = true;
  audio.power(); audio.swoosh(); if (!frozen) rotorGoal = 1;
  setTimeout(() => boot.classList.add('done'), 450);
}
['pointerdown', 'keydown', 'touchstart'].forEach(ev => boot.addEventListener(ev, () => { clicked = true; boot.classList.add('booting'); firstGesture(); audio.tick(); if (ready) finishBoot(); }, { once: true }));

applyGrade(); syncCine();
grade.uniforms.grain.value = look.grain;
Promise.all([
  loadEnv(look.light, e => { if (e.total) { envP = e.loaded / e.total; bootProgress(); } }).then(() => { envP = 1; applyLight(look.light); bootProgress(); }),
  (async () => { active = -1; await showModelBoot(0); })(),
]).then(() => { ready = true; acP = 1; bootProgress(); setTimeout(finishBoot, clicked ? 200 : 2200); })
  .catch(e => { console.error(e); bootD.textContent = 'LOAD ERROR — CHECK CONNECTION'; });
async function showModelBoot(i) {
  await loadAircraft(AIRCRAFT[i], e => { if (e.total) { acP = e.loaded / e.total; bootProgress(); } }).catch(() => null);
  await showModel(i);
}
// prefetch the other airframes in the background once the first is up
function prefetch() { if (MOBILE) return; AIRCRAFT.forEach((d, i) => { if (i !== active) setTimeout(() => loadAircraft(d).catch(() => null), 1500 + i * 1800); }); }

/* ------------------------------------------------------------------ *
 * Frame loop
 * ------------------------------------------------------------------ */
const clock = new THREE.Clock();
const shake = new THREE.Vector3(), shakeT = new THREE.Vector3(), tmpV = new THREE.Vector3();
let perfN = 0, perfT = 0, tuned = false, prefetched = false;
function frame() {
  const dt = Math.min(clock.getDelta(), .05), t = clock.elapsedTime;
  if (!current || !envState) { composer.render(); return; }
  if (!prefetched && bootDone) { prefetched = true; prefetch(); }

  // undo last frame's handheld offset before controls integrate
  camera.position.sub(shake); controls.target.sub(shakeT);

  // rotors
  rotorSpin = damp(rotorSpin, rotorGoal, .9, dt);
  const blur = clamp((rotorSpin - .35) / .5, 0, 1);
  for (const s of current.spinners) {
    const dA = dt * rotorSpin * (s.tail ? 24 : 26 / Math.max(1, s.R / 6)) * s.dir;
    s.node.rotateY(dA); s.angle += dA; s.blur = blur;
    s.disc.material.uniforms.uO.value = blur;
    s.disc.material.uniforms.uPh.value = -s.angle * s.disc.material.uniforms.uN.value;
    s.disc.visible = blur > .01;
  }
  const blurOf = {}; for (const s of current.spinners) blurOf[s.name] = s.blur;
  // lights: anti-collision double flash
  const ph = (t * .9) % 1, fl = (ph < .06 || (ph > .14 && ph < .2)) ? 1 : 0;
  current.beacons.forEach(b => { b.material.emissiveIntensity = .4 + fl * 14; });
  current.lights.forEach(l => { l.intensity = fl * 22; });

  // part focus: fade others to x-ray
  for (const m of current.mats) {
    const isOther = !!selected && m.userData.part !== selected;
    const nv = damp(m.userData.fade ?? 1, isOther ? .14 : 1, 7, dt); m.userData.fade = nv; m.userData.faded = isOther;
    const op = m.userData.baseOpacity * nv * (m.userData.spin ? 1 - (blurOf[m.userData.spin] || 0) * .82 : 1);
    const tr = m.userData.baseTransparent || op < .985;
    if (m.transparent !== tr) { m.transparent = tr; m.needsUpdate = true; }
    m.opacity = op; m.depthWrite = !tr || op > .6;
    if (m.emissive && !/^emit_/.test(m.userData.name || '')) { const h = (hovered === m.userData.part && !selected) ? .55 : (selected === m.userData.part ? .18 : 0); m.userData.hl = damp(m.userData.hl || 0, h, 10, dt); m.emissive.copy(HL).multiplyScalar(m.userData.hl); }
  }

  // camera: tween > shot > free orbit
  if (Math.abs(camera.fov - look.fov) > .01) { camera.fov = damp(camera.fov, look.fov, 6, dt); camera.updateProjectionMatrix(); }
  if (tw) {
    const k = easeIO(clamp((performance.now() - tw.t0) / tw.dur, 0, 1));
    controls.target.lerpVectors(tw.fT, tw.tT, k); camera.position.lerpVectors(tw.fP, tw.tP, k);
    if (k >= 1) { tw = null; shotT = 0; }
  } else if (look.shot !== 'Free' && !selected && !userDriving) {
    shotT += dt; shotPose(look.shot, shotT, current, pose);
    camera.position.lerp(pose.p, 1 - Math.exp(-2.2 * dt)); controls.target.lerp(pose.t, 1 - Math.exp(-2.2 * dt));
  }
  controls.update();
  if (camera.position.y < .4) camera.position.y = .4;

  // panel-aware framing (shift the optical centre left of the dossier)
  const want = panelOpen && !MOBILE ? Math.min(430, innerWidth * .88) * .5 : 0;
  viewOff = damp(viewOff, want, 6, dt);
  if (Math.abs(viewOff) > .5) camera.setViewOffset(innerWidth, innerHeight, viewOff, 0, innerWidth, innerHeight); else camera.clearViewOffset();

  // handheld: layered noise, stronger in rotor wash
  const amp = (selected ? .012 : .035) * (.4 + rotorSpin) * (look.shot === 'Fly-by' ? 1.4 : 1);
  shake.set(Math.sin(t * 1.7) * .6 + Math.sin(t * 4.3) * .25 + Math.sin(t * 11.1) * .08 * rotorSpin, Math.sin(t * 1.3 + 1) * .5 + Math.sin(t * 5.1) * .2, Math.sin(t * 2.1 + 2) * .4).multiplyScalar(amp);
  shakeT.set(Math.sin(t * .9 + 3) * .5, Math.sin(t * 1.1) * .4, Math.sin(t * .7 + 1) * .5).multiplyScalar(amp * .8);
  camera.position.add(shake); controls.target.add(shakeT); camera.lookAt(controls.target);

  // sun follows the HDRI's sun, shadow box follows the aircraft
  const L = sun.userData;
  sun.position.copy(current.center).addScaledVector(L.dir, 120); sun.target.position.copy(current.center);
  sun.intensity = L.base * (1 - .35 * MOODS[look.mood].rain);
  const night = !!LIGHTS[look.light].night;
  current.spot.visible = night; current.spot.intensity = 650; current.beam.visible = night; current.beam.material.uniforms.uI.value = .13 * (1 + MOODS[look.mood].fog * 25);
  // anamorphic flare when the sun is in frame
  const flareK = (LIGHTS[look.light].flare || 0) * (1 - MOODS[look.mood].rain);
  tmpV.copy(L.dir).multiplyScalar(800).add(camera.position).project(camera);
  const onScr = flareK > 0 && tmpV.z < 1 && Math.abs(tmpV.x) < 1.1 && Math.abs(tmpV.y) < 1.1;
  grade.uniforms.sunOn.value = onScr ? flareK : 0; grade.uniforms.sunUv.value.set(tmpV.x * .5 + .5, tmpV.y * .5 + .5);

  // DOF focus on the orbit target
  bokeh.uniforms.focus.value = camera.position.distanceTo(controls.target);
  bokeh.uniforms.aperture.value = .00009 * (35 / camera.fov);

  // dust kicked up by the downwash
  const M = MOODS[look.mood], wash = rotorSpin * M.dust, Rr = Math.max(...current.spinners.filter(s => !s.tail).map(s => s.R), 6);
  dustMat.opacity = clamp(wash * .32, 0, .5); dustPts.visible = dustMat.opacity > .005;
  if (dustPts.visible) {
    for (let i = 0; i < DUST_N; i++) {
      const p = dust[i]; p.life += dt * .22 * p.sp * (.3 + rotorSpin);
      if (p.life > 1) { p.life = 0; p.a = rand(0, 7); p.r = rand(.3, .8) * Rr; p.y = rand(0, .3); }
      p.r += dt * (5 + 9 * rotorSpin) * p.sp * (1 - p.life * .6); p.a += dt * .15 * p.sp; p.y += dt * (.25 + 1.4 * p.life) * p.sp;
      dustPos[i * 3] = current.center.x + Math.cos(p.a) * p.r; dustPos[i * 3 + 1] = p.y; dustPos[i * 3 + 2] = current.center.z + Math.sin(p.a) * p.r;
    }
    dustGeo.attributes.position.needsUpdate = true;
  }
  // rain
  rainMat.opacity = damp(rainMat.opacity, M.rain * .55, 3, dt); rain.visible = rainMat.opacity > .01;
  if (rain.visible) {
    const fx = Math.sin(controls.getAzimuthalAngle()), fz = Math.cos(controls.getAzimuthalAngle());
    const cx = camera.position.x - fx * 14, cz = camera.position.z - fz * 14;
    for (let i = 0; i < RAIN_N; i++) {
      const d = rainD[i]; d[1] -= dt * 24 * d[3]; if (d[1] < 0) { d[1] += 22; d[0] = rand(-18, 18); d[2] = rand(-18, 18); }
      const x = cx + d[0], z = cz + d[2], k = i * 6; rainPos[k] = x; rainPos[k + 1] = d[1]; rainPos[k + 2] = z; rainPos[k + 3] = x + .14; rainPos[k + 4] = d[1] + 1.1 * d[3]; rainPos[k + 5] = z + .06;
    }
    rainGeo.attributes.position.needsUpdate = true;
    if (t > nextBolt) { boltT = t; nextBolt = t + rand(7, 16); audio.thunder(rand(.5, 2.2)); }
  }
  const bt = t - boltT, flash = boltT > 0 && bt < .55 ? (bt < .07 ? 1 : bt < .13 ? .15 : bt < .2 ? .8 : Math.max(0, .5 - bt) * .6) : 0;
  grade.uniforms.flash.value = flash * .22; flashLight.intensity = flash * 6;
  scene.backgroundIntensity = LIGHTS[look.light].bg * (1 - .35 * M.rain) + flash * 1.8;

  grade.uniforms.time.value = t; grade.uniforms.bars.value = damp(grade.uniforms.bars.value, look.bars ? 1 : 0, 5, dt);
  audio.rotor(rotorSpin, BLADES[current.def.id] || 17, camera.position.distanceTo(current.center));
  composer.render();

  // auto quality: drop expensive passes on slow GPUs
  if (!tuned && bootDone) { perfN++; perfT += dt; if (perfN === 90) { tuned = true; const ms = perfT / perfN * 1000; if (ms > 30) { DPR = 1; gtao.enabled = false; resize(); } if (ms > 45) { bokeh.enabled = look.blur = false; syncCine(); } } }
}
renderer.setAnimationLoop(() => { if (!document.hidden) frame(); });
