// prism_bloom.frag  --  8-fold radial bloom
// Prism layers: Goodness (low) / Beauty (mid) / Truth (high)
uniform vec4 uA;   // time, growth, low, mid
uniform vec4 uB;   // high, kick_hit, snare_hit, vox
uniform vec4 uC;   // master, hats, sub, gtr_lead
uniform vec4 uP;   // petals, twist speed, -, -
out vec4 fragColor;
#define PI 3.14159265

float petal(vec2 p, float R, float n, float sharp, float phase) {
    float r = length(p);
    float a = atan(p.y, p.x) + phase;
    float lobe = pow(abs(cos(a * n * 0.5)), sharp);
    float edge = R * (0.30 + 0.70 * lobe);
    return smoothstep(edge, edge - 0.015 - 0.05 * R, r);
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = (vUV.st - 0.5) * vec2(res.x / res.y, 1.0) * 2.0;
    float t = uA.x, growth = uA.y, low = uA.z, mid = uA.w;
    float high = uB.x, kick = uB.y, snare = uB.z, vox = uB.w;
    float master = uC.x, hats = uC.y;
    float n = uP.x, tw = uP.y * t;
    float r = length(p), a = atan(p.y, p.x);

    float R = mix(0.10, 0.92, smoothstep(0.0, 1.0, growth)) * (1.0 + 0.07 * kick);

    vec3 goodness = vec3(1.00, 0.74, 0.28);
    vec3 beauty   = vec3(0.96, 0.28, 0.56);
    vec3 truth    = vec3(0.28, 0.76, 1.00);

    float lG = petal(p, R * (0.78 + 0.35 * low),  n, 2.0,  tw);
    float lB = petal(p, R * (0.66 + 0.40 * mid),  n, 3.0, -tw * 1.3 + PI / n);
    float lT = petal(p, R * (0.55 + 0.45 * high), n, 4.0,  tw * 0.7);

    vec3 col = goodness * lG * (0.20 + 0.80 * low)
             + beauty   * lB * (0.20 + 0.80 * mid)
             + truth    * lT * (0.20 + 0.80 * high);

    // veins, lit by the voice
    float veins = pow(abs(sin(a * n * 3.0 + r * 7.0 - t * 0.6)), 36.0);
    col += vec3(1.0, 0.97, 0.92) * veins * max(lG, max(lB, lT)) * (0.05 + 0.6 * vox) * 0.5;

    // 8 radiating nodes, flash on snare
    for (int i = 0; i < 16; i++) {
        if (float(i) >= n) break;
        float ang = float(i) / n * 2.0 * PI + tw * 0.5;
        vec2 np = vec2(cos(ang), sin(ang)) * R * 1.12;
        float d = length(p - np);
        col += vec3(1.0, 0.94, 0.86) * (0.00012 + 0.0012 * snare + 0.0002 * hats) / (d * d + 0.0004);
    }

    // core, pulses with kick
    col += vec3(1.0, 0.88, 0.75) * (0.0004 + 0.004 * kick) / (r * r + 0.0025);

    // kick ring (the feedback loop carries it outward)
    col += goodness * kick * smoothstep(0.012, 0.0, abs(r - R * 1.02)) * 1.2;

    col = 1.0 - exp(-col * 1.15);   // soft tonemap
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
