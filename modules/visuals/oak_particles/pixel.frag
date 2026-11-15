
uniform vec4 uA;  // songtime, growth, kick, kick_hit
uniform vec4 uB;  // snare, snare_hit, hats, ride
uniform vec4 uC;  // sub, gtr_rhythm, gtr_lead, vox
uniform vec4 uD;  // low, mid, high, master
uniform vec4 uP;  // module params (see component)
out vec4 fragColor;
// inputs: 0 photo, 1 masks_a (trunk, branches, light), 2 masks_b (shadow, foliage, detail), 3 growth field
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; } return v; }
// Aspect "cover" fit: maps output UV -> image UV so the image fills any output shape (crops, never stretches).
// uP.x = horizontal focus (0..1) = where to centre the crop when the output is narrower than the image.
vec2 coverUV(vec2 uv) {
    vec2 o = uTDOutputInfo.res.zw;
    vec2 i = uTD2DInfos[0].res.zw;
    float ro = o.x / o.y, ri = i.x / i.y;
    vec2 s = (ro > ri) ? vec2(1.0, ri / ro) : vec2(ro / ri, 1.0);
    vec2 c = vec2(clamp(uP.x, s.x * 0.5, 1.0 - s.x * 0.5), 0.5);
    return (uv - 0.5) * s + c;
}

// oak_particles: the scene assembles from drifting points of light as the song grows it.
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    float t = uA.x, growth = uA.y, kick = uA.z, kickHit = uA.w;
    float snare = uB.x, snareHit = uB.y, hats = uB.z, ride = uB.w;
    float sub = uC.x, gtrR = uC.y, gtrL = uC.z;
    float cs = max(uP.y, 3.0);            // cell size in pixels
    float spread = uP.z;                  // drift amount (cells)
    float front = growth * 1.1 - 0.05;

    vec2 cell = floor(px / cs);
    vec3 acc = vec3(0.0);
    for (int j = -2; j <= 2; j++) {
        for (int i = -2; i <= 2; i++) {
            vec2 c = cell + vec2(i, j);
            float h1 = hash(c), h2 = hash(c + 17.31), h3 = hash(c + 41.7);
            vec2 home = (c + vec2(h1, h2)) * cs;
            vec2 huv = coverUV(home / res);
            vec3 pc = texture(sTD2DInputs[0], huv).rgb;
            vec4 mA = texture(sTD2DInputs[1], huv);
            vec4 mB = texture(sTD2DInputs[2], huv);
            float field = texture(sTD2DInputs[3], huv).r;
            float a = smoothstep(field - 0.02, field + 0.05, front);          // assembled 0..1

            vec2 drift = vec2(sin(t * 0.7 + h3 * 6.283 + h1 * 9.0), cos(t * 0.55 + h2 * 6.283)) * cs * spread;
            vec2 kickDir = normalize(vec2(h1 - 0.5, h2 - 0.5) + 1e-3);
            vec2 pos = home + drift * (1.0 - a)
                     + kickDir * cs * 0.9 * snareHit * mA.g                    // snare shakes the branches
                     + drift * 0.12 * hats;                                    // cymbals shimmer
            float lum = dot(pc, vec3(0.3, 0.59, 0.11));
            float treeness = clamp(mA.r + mA.g, 0.0, 1.0);
            float rad = cs * (0.28 + 0.22 * lum + 0.16 * treeness)
                      * (1.0 + mA.r * (0.6 * kickHit + 0.25 * kick))           // trunk swells with kick
                      * mix(0.5, 1.0, a)
                      * (1.0 - 0.35 * mB.r * sub);                             // bass pulls shadow points in
            float d = length(px - pos);
            float dotv = smoothstep(rad, rad * 0.35, d);

            vec3 col = pow(pc, vec3(0.8)) * 1.25 + 0.04;
            col = mix(col, col * vec3(1.18, 1.0, 0.82) + vec3(0.10, 0.07, 0.03), treeness * 0.7);  // warm bark points
            col = mix(vec3(dot(col, vec3(0.3, 0.59, 0.11))), col, 0.65 + mB.b * gtrL * 1.1 + mB.g * gtrR * 0.6);
            col += vec3(1.0, 0.93, 0.78) * mA.b * (hats + ride) * 0.7;          // sunlit points
            float alpha = mix(0.32, 1.0, a) * (0.8 + 0.2 * h3);
            acc = max(acc, col * dotv * alpha);
        }
    }
    vec3 bg = vec3(0.025, 0.03, 0.045) + texture(sTD2DInputs[0], coverUV(vUV.st)).rgb * 0.05 * growth;
    vec3 col = max(acc, bg);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
