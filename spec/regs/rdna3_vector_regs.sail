
// Vectors
register VCCZ :
    bits(1) // is VCC == 64'b0
// SGPR 107, 106 == VCC
register VGPR : vector(256, dec, vector(32, dec, DWORD))
