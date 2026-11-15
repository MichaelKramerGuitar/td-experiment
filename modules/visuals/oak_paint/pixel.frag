
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

// oak_paint: a pencil sketch on paper that is painted in as the song grows the tree.
// trunk=kick  branches=snare  light=overheads  shadow=bass(sub)  foliage=rhythm gtr  colour detail=lead gtr
void main() {
    vec2 uv = coverUV(vUV.st);
    float t = uA.x, growth = uA.y, kick = uA.z, kickHit = uA.w;
    float snare = uB.x, snareHit = uB.y, hats = uB.z, ride = uB.w;
    float sub = uC.x, gtrR = uC.y, gtrL = uC.z;
    float pastel = uP.y, sway = uP.z;

    // foliage sways with the rhythm guitar
    float fol0 = texture(sTD2DInputs[2], uv).g;
    vec2 disp = vec2(fbm(uv * 6.0 + t * 0.35) - 0.5, fbm(uv * 6.0 + 13.0 + t * 0.35) - 0.5);
    vec2 suv = uv + disp * 0.008 * sway * (0.25 + 1.6 * gtrR) * fol0;

    vec3 photo = texture(sTD2DInputs[0], suv).rgb;
    vec4 mA = texture(sTD2DInputs[1], suv);
    vec4 mB = texture(sTD2DInputs[2], suv);
    float trunk = mA.r, branch = mA.g, light = mA.b;
    float shadow = mB.r, foliage = mB.g, detail = mB.b;
    float field = texture(sTD2DInputs[3], uv).r;

    // growth front with an organic, noisy edge
    float front = growth * 1.1 - 0.05;
    float edgeN = fbm(uv * 9.0) * 0.07;
    float reveal = smoothstep(field + edgeN - 0.03, field + edgeN + 0.03, front);   // 1 once the front has passed
    float band = smoothstep(0.04, 0.0, abs(front - (field + edgeN)));

    vec3 col = photo;
    float lum = dot(col, vec3(0.299, 0.587, 0.114));
    col *= 1.0 + trunk * (0.25 * kick + 0.7 * kickHit);                        // trunk breathes with kick
    col += branch * vec3(1.0, 0.82, 0.62) * (0.08 * snare + 0.38 * snareHit);   // branches flash with snare
    col = mix(col, col * (0.45 + 0.55 * (1.0 - sub)), shadow * 0.85);          // bass deepens shadow (relief)
    col = mix(vec3(lum), col, 1.0 + detail * gtrL * 1.3);                      // lead gtr = colour detail
    col = mix(col, col * vec3(0.94, 1.08, 0.92), foliage * gtrR * 0.7);        // rhythm gtr = living foliage

    // overheads = sunlight: glow in light gaps + soft rays from the canopy
    float sun = clamp(hats * 0.7 + ride * 0.7, 0.0, 1.5);
    vec3 sunc = vec3(1.0, 0.93, 0.78);
    col += sunc * light * sun * 0.55;
    vec2 sunPos = vec2(0.32, 1.1);
    vec2 dir = (sunPos - uv) / 18.0; vec2 q = uv; float rays = 0.0;
    for (int i = 0; i < 18; i++) { q += dir; rays += texture(sTD2DInputs[1], q).b; }
    col += sunc * (rays / 18.0) * sun * 0.5;

    // pastel grade: lifted blacks, softened contrast, slight lilac in the shadows
    vec3 past = pow(clamp(col, 0.0, 2.0), vec3(0.78)) * 0.82 + vec3(0.11, 0.10, 0.13);
    col = mix(col, past, pastel);

    // unrevealed: graphite sketch on warm paper
    vec3 paper = vec3(0.96, 0.94, 0.89) - fbm(uv * 55.0) * 0.05;
    float g = length(vec2(dFdx(lum), dFdy(lum))) * 7.0;
    float ink = clamp(g * 0.9 + (trunk + branch) * 0.18, 0.0, 1.0);
    vec3 sketch = paper - vec3(0.42, 0.40, 0.37) * ink * (0.35 + 0.65 * growth);
    col = mix(sketch, col, reveal);
    col += vec3(1.0, 0.86, 0.62) * band * (0.25 + 0.35 * kick);               // living edge of growth

    float vig = smoothstep(1.15, 0.35, length((vUV.st - 0.5) * vec2(1.4, 1.0)));
    col *= mix(0.82, 1.0, vig);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
