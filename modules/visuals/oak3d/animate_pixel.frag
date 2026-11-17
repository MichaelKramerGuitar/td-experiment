// animate: one pixel = one particle.  in: home (xyz, growth order)  out: (xyz, scale)
uniform vec4 uA;   // time, front (vitality*gain), drift amount, particle size
uniform vec4 uB;   // breath, kick_hit, snare_hit, hats
out vec4 fragColor;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void main() {
    ivec2 ij = ivec2(gl_FragCoord.xy);
    vec4 h = texelFetch(sTD2DInputs[0], ij, 0);
    vec3 home = h.xyz;
    float g = h.w;                                  // growth order: 0 at the roots -> 1 at the tips
    float t = uA.x;
    float front = uA.y * 1.1 - 0.05;
    float a = smoothstep(g - 0.02, g + 0.05, front);   // assembled 0..1

    vec2 id = vec2(ij);
    float h1 = hash(id), h2 = hash(id + 17.31), h3 = hash(id + 41.7);
    vec3 drift = vec3(sin(t * 0.6 + h1 * 6.283 + h3 * 9.0),
                      cos(t * 0.5 + h2 * 6.283),
                      sin(t * 0.45 + h3 * 6.283 + h1 * 3.0)) * uA.z;
    vec3 jolt = normalize(vec3(h1 - 0.5, h2 - 0.5, h3 - 0.5) + 1e-3) * 0.012 * uB.z;   // snare shakes
    vec3 pos = home + drift * (1.0 - a)        // unassembled particles drift as dust
             + drift * 0.06 * uB.w            // cymbals shimmer
             + jolt * a;

    float trunk = 1.0 - smoothstep(0.12, 0.25, g);    // near the roots
    float sc = uA.w * mix(0.3, 1.0, a) * (1.0 + 0.7 * uB.y * trunk) * (0.75 + 0.5 * h3);
    if (g > 1.5) sc = 0.0;                            // padding pixels
    fragColor = vec4(pos, sc);
}
