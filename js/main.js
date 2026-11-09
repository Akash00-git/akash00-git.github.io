import * as THREE from 'three';

const gsap = window.gsap, ScrollTrigger = window.ScrollTrigger, Lenis = window.Lenis;
gsap.registerPlugin(ScrollTrigger);
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const lerp = (a, b, t) => a + (b - a) * t;

/* ---------------- Smooth scroll (Lenis) ---------------- */
let lenis = null;
if (Lenis) {
  lenis = new Lenis({ lerp: 0.09, wheelMultiplier: 1, smoothWheel: true });
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add((t) => lenis.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);
}
const goTo = (target) => { if (lenis) lenis.scrollTo(target, { offset: -70, duration: 1.2 }); else target.scrollIntoView({ behavior: 'smooth' }); };

/* ---------------- Preloader ---------------- */
const loader = $('#loader'), pct = $('#loaderPct');
let p = 0;
const pint = setInterval(() => { p = Math.min(100, p + Math.random() * 18); pct.textContent = Math.floor(p); if (p >= 100) { clearInterval(pint); finishLoad(); } }, 110);
function finishLoad() {
  setTimeout(() => {
    loader.classList.add('done');
    gsap.fromTo('.hero-text .reveal, .hero-text', { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 1, ease: 'power3.out' });
    gsap.fromTo('.hero-photo', { y: 40, opacity: 0, scale: .96 }, { y: 0, opacity: 1, scale: 1, duration: 1.1, delay: .15, ease: 'power3.out' });
    $$('.hero .reveal').forEach(e => e.classList.add('in'));
  }, 350);
}

/* ---------------- Nav: scrolled, spy, mobile, anchor ---------------- */
const nav = $('#nav');
ScrollTrigger.create({ start: 'top -40', end: 99999, onUpdate: s => nav.classList.toggle('scrolled', s.progress > 0) });
ScrollTrigger.create({ trigger: 'main', start: 60, end: 99999, onToggle: s => nav.classList.toggle('scrolled', s.isActive) });

const navLinks = $$('.menu a');
const sections = ['home', 'about', 'experience', 'projects', 'skills', 'contact'];
sections.forEach(id => {
  const el = document.getElementById(id); if (!el) return;
  ScrollTrigger.create({
    trigger: el, start: 'top 55%', end: 'bottom 55%',
    onToggle: s => { if (s.isActive) { navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + id)); if (audio) audio.tick(); } }
  });
});

$$('[data-nav]').forEach(a => a.addEventListener('click', e => {
  const href = a.getAttribute('href');
  if (href && href.startsWith('#')) { e.preventDefault(); const t = document.querySelector(href); if (t) goTo(t); menu.classList.remove('open'); }
}));
const burger = $('#burger'), menu = $('#menu');
burger.addEventListener('click', () => menu.classList.toggle('open'));

/* progress bar */
const prog = $('#progress');
ScrollTrigger.create({ start: 0, end: 'max', onUpdate: s => prog.style.width = (s.progress * 100) + '%' });

/* ---------------- Reveals ---------------- */
ScrollTrigger.batch('.reveal:not(.in)', { start: 'top 86%', onEnter: els => els.forEach((e, i) => setTimeout(() => e.classList.add('in'), i * 70)) });

/* ---------------- Count-up stats ---------------- */
$$('.stat .num').forEach(el => {
  const target = +el.dataset.count, suffix = el.dataset.suffix || '';
  ScrollTrigger.create({
    trigger: el, start: 'top 90%', once: true,
    onEnter: () => {
      const o = { v: 0 };
      gsap.to(o, { v: target, duration: 1.8, ease: 'power2.out',
        onUpdate: () => { el.textContent = Math.floor(o.v).toLocaleString('en-US') + suffix; },
        onComplete: () => { el.textContent = target.toLocaleString('en-US') + suffix; } });
    }
  });
});

/* ---------------- Role rotator ---------------- */
const roles = ['Odoo ERP & CRM systems', 'WordPress & WooCommerce stores', 'interactive 3D / WebGL experiences', 'reliable, maintainable software'];
const roleEl = $('#roleRotate b'); let ri = 0;
setInterval(() => {
  ri = (ri + 1) % roles.length;
  gsap.to(roleEl, { opacity: 0, y: -8, duration: .35, ease: 'power2.in', onComplete: () => { roleEl.textContent = roles[ri]; gsap.fromTo(roleEl, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: .45, ease: 'power2.out' }); } });
}, 2600);

/* ---------------- Tilt (cards + photo) ---------------- */
$$('.tilt').forEach(el => {
  let rx = 0, ry = 0, tx = 0, ty = 0, raf = null;
  const loop = () => { rx = lerp(rx, tx, .12); ry = lerp(ry, ty, .12); el.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg)`; if (Math.abs(rx - tx) > .02 || Math.abs(ry - ty) > .02) raf = requestAnimationFrame(loop); else raf = null; };
  el.addEventListener('pointermove', e => { const r = el.getBoundingClientRect(); const px = (e.clientX - r.left) / r.width - .5, py = (e.clientY - r.top) / r.height - .5; ty = px * 9; tx = -py * 9; if (!raf) raf = requestAnimationFrame(loop); });
  el.addEventListener('pointerleave', () => { tx = 0; ty = 0; if (!raf) raf = requestAnimationFrame(loop); });
  el.addEventListener('pointerenter', () => { if (audio) audio.hover(); });
});

/* ---------------- Magnetic buttons ---------------- */
$$('.magnetic').forEach(el => {
  el.addEventListener('pointermove', e => { const r = el.getBoundingClientRect(); const x = e.clientX - r.left - r.width / 2, y = e.clientY - r.top - r.height / 2; gsap.to(el, { x: x * .3, y: y * .3, duration: .4, ease: 'power3.out' }); });
  el.addEventListener('pointerleave', () => gsap.to(el, { x: 0, y: 0, duration: .5, ease: 'elastic.out(1,.4)' }));
});

/* ---------------- WebGL shader background ---------------- */
(function hero3D() {
  const canvas = $('#bg');
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' }); }
  catch (e) { return; }
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.6));
  renderer.setSize(innerWidth, innerHeight);
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const uniforms = {
    uTime: { value: 0 }, uRes: { value: new THREE.Vector2(innerWidth, innerHeight) },
    uPointer: { value: new THREE.Vector2(.5, .5) }, uScroll: { value: 0 },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms, transparent: true,
    vertexShader: `varying vec2 v; void main(){ v=uv; gl_Position=vec4(position,1.0); }`,
    fragmentShader: `
      precision highp float; varying vec2 v;
      uniform float uTime, uScroll; uniform vec2 uRes, uPointer;
      float hash(vec2 p){ return fract(sin(dot(p,vec2(41.3,289.1)))*43758.5); }
      float noise(vec2 p){ vec2 i=floor(p),f=fract(p); f=f*f*(3.-2.*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y); }
      float fbm(vec2 p){ float s=0.,a=.5; for(int i=0;i<5;i++){ s+=a*noise(p); p*=2.03; a*=.5; } return s; }
      void main(){
        vec2 uv=v; vec2 asp=vec2(uRes.x/uRes.y,1.0); vec2 p=(uv-.5)*asp;
        float t=uTime*.045;
        vec2 q=vec2(fbm(p*1.3+t), fbm(p*1.3-t+5.2));
        float f=fbm(p*1.6+q*1.4+vec2(0.,t*2.));
        float g=fbm(p*2.2-q*1.1-vec2(t*1.5,0.));
        vec3 c1=vec3(0.03,0.08,0.14);         // deep blue-black
        vec3 c2=vec3(0.16,0.55,0.95);         // cyan
        vec3 c3=vec3(0.55,0.40,0.98);         // violet
        vec3 c4=vec3(0.20,0.85,0.70);         // teal
        vec3 col=mix(c1,c2,smoothstep(.2,.9,f));
        col=mix(col,c3,smoothstep(.3,1.,g)*.6);
        col=mix(col,c4,smoothstep(.55,1.,f*g)*.35);
        float d=length(p-(uPointer-.5)*asp*2.);
        col+=c2*.10*exp(-d*1.6);              // pointer glow
        col*=.26;                              // keep it dark/premium
        float vig=smoothstep(1.35,.2,length(p));
        col*=mix(.5,1.,vig);
        col+=(hash(uv*uRes+t)-.5)*.015;        // dither
        gl_FragColor=vec4(col,1.0);
      }`
  });
  scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat));
  addEventListener('pointermove', e => { uniforms.uPointer.value.set(e.clientX / innerWidth, 1 - e.clientY / innerHeight); }, { passive: true });
  addEventListener('resize', () => { renderer.setSize(innerWidth, innerHeight); uniforms.uRes.value.set(innerWidth, innerHeight); });
  const clock = new THREE.Clock();
  renderer.setAnimationLoop(() => { if (document.hidden) return; uniforms.uTime.value = clock.getElapsedTime(); renderer.render(scene, camera); });
})();

/* ---------------- Procedural sound ---------------- */
let audio = null;
class Audio {
  constructor() { this.on = false; this.ready = false; }
  init() { if (this.ready) return; try {
    const AC = window.AudioContext || window.webkitAudioContext; const ctx = this.ctx = new AC();
    this.master = ctx.createGain(); this.master.gain.value = 0; const comp = ctx.createDynamicsCompressor();
    this.master.connect(comp); comp.connect(ctx.destination);
    const n = ctx.sampleRate * 1.6, b = ctx.createBuffer(2, n, ctx.sampleRate);
    for (let c = 0; c < 2; c++){ const d = b.getChannelData(c); for (let i = 0; i < n; i++) d[i] = (Math.random()*2-1)*Math.pow(1-i/n,3); }
    this.verb = ctx.createConvolver(); this.verb.buffer = b; const vg = ctx.createGain(); vg.gain.value = .5; this.verb.connect(vg); vg.connect(this.master);
    this.pent = [523.25, 587.33, 659.25, 783.99, 880]; this.ready = true;
  } catch(e){ this.ready = false; } }
  enable(){ this.init(); if(!this.ready) return false; this.ctx.resume(); this.on = true; this.master.gain.setTargetAtTime(.5, this.ctx.currentTime, .3); return true; }
  disable(){ this.on = false; if(this.ready) this.master.gain.setTargetAtTime(0, this.ctx.currentTime, .2); }
  _tone(f, dur, g, type){ if(!this.ready||!this.on) return; const t=this.ctx.currentTime, o=this.ctx.createOscillator(), gn=this.ctx.createGain(), pan=this.ctx.createStereoPanner(); o.type=type||'sine'; o.frequency.value=f; pan.pan.value=(Math.random()*2-1)*.4; gn.gain.setValueAtTime(0,t); gn.gain.linearRampToValueAtTime(g,t+.01); gn.gain.exponentialRampToValueAtTime(.0005,t+dur); o.connect(gn); gn.connect(pan); pan.connect(this.master); pan.connect(this.verb); o.start(t); o.stop(t+dur+.05); }
  hover(){ this._tone(this.pent[Math.floor(Math.random()*this.pent.length)]*2, .5, .035, 'triangle'); }
  tick(){ this._tone(this.pent[Math.floor(Math.random()*this.pent.length)], 1.1, .05, 'sine'); }
}
audio = new Audio();
const sndBtn = $('#sound');
sndBtn.addEventListener('click', () => { if (!audio.on) { if (audio.enable()) sndBtn.classList.add('on'); } else { audio.disable(); sndBtn.classList.remove('on'); } });

/* refresh triggers once fonts/images settle */
addEventListener('load', () => setTimeout(() => ScrollTrigger.refresh(), 300));
