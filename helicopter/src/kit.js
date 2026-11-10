// kit.js — shared modelling toolkit for the helicopter models.
// The star is loft(): a smooth fuselage lofted from elliptical cross-sections,
// which is what makes the airframes read as real aircraft instead of boxes.

export function makeKit(THREE) {
  const K = {};
  const C = (h) => new THREE.Color(h);

  K.mat = (hex, o = {}) => new THREE.MeshStandardMaterial({
    color: C(hex), roughness: o.rough ?? 0.62, metalness: o.metal ?? 0.2,
    envMapIntensity: o.env ?? 0.8, emissive: C(o.emissive || '#000000'), emissiveIntensity: o.emissiveI ?? 0,
    map: o.map || null, flatShading: !!o.flat,
  });
  K.glass = (hex = '#0a1a22', opacity = 0.55) => new THREE.MeshPhysicalMaterial({
    color: C(hex), roughness: 0.06, metalness: 0, transparent: true, opacity, envMapIntensity: 1.4, clearcoat: 1, clearcoatRoughness: 0.08,
  });

  // procedural camouflage texture
  K.camoTex = (cols, base) => {
    const c = document.createElement('canvas'); c.width = c.height = 512; const x = c.getContext('2d');
    x.fillStyle = base; x.fillRect(0, 0, 512, 512);
    for (let i = 0; i < 80; i++) {
      x.fillStyle = cols[(Math.random() * cols.length) | 0];
      const cx = Math.random() * 512, cy = Math.random() * 512, r = 28 + Math.random() * 70;
      x.beginPath();
      for (let a = 0; a <= 9; a++) { const ang = a / 9 * 6.283, rr = r * (0.55 + Math.random() * 0.85); const px = cx + Math.cos(ang) * rr, py = cy + Math.sin(ang) * rr; a ? x.lineTo(px, py) : x.moveTo(px, py); }
      x.closePath(); x.fill();
    }
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
  };

  // panel-line roughness/detail texture for a subtle plated look
  K.panelTex = (tint = '#8a8f85') => {
    const c = document.createElement('canvas'); c.width = c.height = 512; const x = c.getContext('2d');
    x.fillStyle = tint; x.fillRect(0, 0, 512, 512);
    x.strokeStyle = 'rgba(0,0,0,.18)'; x.lineWidth = 1;
    for (let i = 0; i < 512; i += 26) { x.beginPath(); x.moveTo(0, i); x.lineTo(512, i); x.stroke(); }
    for (let i = 0; i < 512; i += 40) { x.beginPath(); x.moveTo(i, 0); x.lineTo(i, 512); x.stroke(); }
    x.fillStyle = 'rgba(0,0,0,.25)';
    for (let i = 0; i < 300; i++) x.fillRect(Math.random() * 512, Math.random() * 512, 2, 2);
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
  };

  // LOFT: stations = [{x, w(half-width), h(half-height), y(vertical centre)}], nose→tail along X.
  K.loft = (stations, mat, radial = 20) => {
    const pos = [], uv = [], idx = [], S = stations.length;
    for (let s = 0; s < S; s++) { const st = stations[s]; for (let i = 0; i < radial; i++) { const a = i / radial * Math.PI * 2; pos.push(st.x, (st.y || 0) + Math.sin(a) * Math.max(st.h, 1e-4), Math.cos(a) * Math.max(st.w, 1e-4)); uv.push(i / radial, s / (S - 1)); } }
    for (let s = 0; s < S - 1; s++) for (let i = 0; i < radial; i++) {
      const a = s * radial + i, b = s * radial + (i + 1) % radial, c = (s + 1) * radial + i, d = (s + 1) * radial + (i + 1) % radial;
      idx.push(a, c, b, b, c, d);
    }
    const cap = (ring, cx, cy, cz, vv, flip) => { const ci = pos.length / 3; pos.push(cx, cy, cz); uv.push(0.5, vv); for (let i = 0; i < radial; i++) { const a = ring + i, b = ring + (i + 1) % radial; flip ? idx.push(ci, b, a) : idx.push(ci, a, b); } };
    const f = stations[0], l = stations[S - 1];
    cap(0, f.x, f.y || 0, 0, 0, true); cap((S - 1) * radial, l.x, l.y || 0, 0, 1, false);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
    return new THREE.Mesh(g, mat);
  };

  // cylinder with axis along +X (top radius faces nose)
  K.tube = (rT, rB, len, mat, seg = 24) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(rT, rB, len, seg), mat); m.rotation.z = -Math.PI / 2; return m; };
  K.box = (w, h, d, mat) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  K.sphere = (r, mat, sx = 1, sy = 1, sz = 1) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 18), mat); m.scale.set(sx, sy, sz); return m; };

  // a single rotor blade (root→tip along +X), slight taper + droop; geometry pre-translated so x=0 is the hub
  K.blade = (len, chord, thick, mat, { taper = 0.8, droop = 0.04, root = 0.5 } = {}) => {
    const g = new THREE.BoxGeometry(len, thick, chord, 10, 1, 1);
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), t = (x + len / 2) / len; // 0 root .. 1 tip
      p.setZ(i, p.getZ(i) * (1 - (1 - taper) * t));           // taper chord
      p.setY(i, p.getY(i) - Math.pow(t, 2) * droop * len);    // slight droop toward tip
    }
    g.computeVertexNormals(); g.translate(len / 2 + root, 0, 0);
    return new THREE.Mesh(g, mat);
  };

  // full main rotor: returns a Group spinning about Y with hub + N blades (+ optional disc)
  K.mainRotor = ({ blades = 4, radius = 8, chord = 0.5, thick = 0.09, mat, hubMat, hubR = 0.5, hubH = 0.35, grip = true }) => {
    const g = new THREE.Group();
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(hubR, hubR * 1.05, hubH, 18), hubMat); g.add(hub);
    for (let i = 0; i < blades; i++) {
      const bg = new THREE.Group(); bg.rotation.y = i / blades * Math.PI * 2;
      bg.add(K.blade(radius, chord, thick, mat, { root: hubR }));
      if (grip) { const gr = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.55, 10), hubMat); gr.rotation.z = Math.PI / 2; gr.position.x = hubR + 0.25; bg.add(gr); }
      g.add(bg);
    }
    return g;
  };

  // wheel on a strut (contact point at y=0 by default)
  K.wheel = (r, wheelMat, strutMat, strutLen = 0.9, strutAng = 0) => {
    const g = new THREE.Group();
    const strut = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.16, r * 0.16, strutLen, 10), strutMat); strut.position.y = strutLen / 2 + r; strut.rotation.x = strutAng; g.add(strut);
    const tyre = new THREE.Mesh(new THREE.TorusGeometry(r, r * 0.42, 12, 20), wheelMat); tyre.rotation.y = Math.PI / 2; tyre.position.y = r; g.add(tyre);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.42, r * 0.42, r * 0.5, 12), strutMat); hub.rotation.x = Math.PI / 2; hub.position.y = r; g.add(hub);
    return g;
  };

  return K;
}
